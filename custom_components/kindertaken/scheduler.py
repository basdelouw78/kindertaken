"""Taakplanner v2.2 — eerlijke fallback bij afwezigheid."""
from __future__ import annotations
from datetime import date, timedelta
import math
from .const import DAY_MAP, DAYS_NL, WEEK_OF_MONTH_OPTIONS
from .presence import child_available_on, child_present_on


def _iso_week(d: date) -> int:
    return d.isocalendar()[1]

def _nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date | None:
    if n == -1:
        nxt  = (date(year, month, 28) + timedelta(days=4)).replace(day=1)
        last = nxt - timedelta(days=1)
        return last - timedelta(days=(last.weekday() - weekday) % 7)
    first = date(year, month, 1)
    cand  = first + timedelta(days=(weekday - first.weekday()) % 7 + (n-1)*7)
    return cand if cand.month == month else None


def _available_children(children, presence_map, d: date) -> list[str]:
    return [c for c in children if child_available_on(presence_map.get(c, {}), d)]


def _fewest_tasks_child(candidates: list[str], already_assigned: dict[str, int]) -> str:
    """Geeft het kind met de minste taken terug (eerlijke verdeling)."""
    return min(candidates, key=lambda c: already_assigned.get(c, 0))


# ── Rotatietaken ─────────────────────────────────────────────────────────────

def rotation_assignments(task_cfg, children, presence_map, d: date, assigned_count=None) -> list[dict]:
    """
    Dagelijkse rotatietaken.
    - Roteert cyclisch op basis van datum
    - Slaat kinderen over die er niet zijn
    - Fallback: kind met minste taken die dag
    assigned_count: dict {kind: aantal_taken} voor eerlijke verdeling
    """
    if assigned_count is None:
        assigned_count = {c: 0 for c in children}

    epoch   = date(2024, 1, 1)
    day_idx = (d - epoch).days
    available = _available_children(children, presence_map, d)
    result  = []

    for i, task in enumerate(task_cfg):
        fixed = task.get("fixed_child")
        if fixed and fixed in available:
            child = fixed
        elif not available:
            continue
        else:
            order = [c for c in (task.get("children_order") or children) if c in available]
            if not order:
                continue
            # Roteer op basis van dag + taak-index
            child = order[(day_idx + i) % len(order)]

        assigned_count[child] = assigned_count.get(child, 0) + 1
        result.append({"task": task["name"], "child": child, "type": "rotation"})
    return result


# ── Weektaken ────────────────────────────────────────────────────────────────

def week_assignments(task_cfg, children, presence_map, d: date, assigned_count=None) -> list[dict]:
    """
    Wekelijkse taken op vaste dag.
    Fallback bij afwezigheid: kind met minste taken die dag.
    """
    if assigned_count is None:
        assigned_count = {c: 0 for c in children}

    today_wd = d.weekday()
    is_even  = _iso_week(d) % 2 == 0
    week_num = _iso_week(d)
    available = _available_children(children, presence_map, d)
    result   = []

    for task in task_cfg:
        if DAY_MAP.get(task.get("day","Maandag"), 0) != today_wd:
            continue

        mode = task.get("mode", "auto_rotate")
        order = task.get("children_order") or children

        if mode == "fixed":
            candidate = task.get("fixed_child","")
        elif mode == "even":
            candidate = task.get("even_child","") if is_even else task.get("odd_child","")
        elif mode == "odd":
            candidate = task.get("odd_child","") if not is_even else task.get("even_child","")
        else:  # auto_rotate
            avail_ordered = [c for c in order if c in available]
            candidate = avail_ordered[week_num % len(avail_ordered)] if avail_ordered else ""

        # Fallback als aangewezen kind niet beschikbaar is
        if not candidate or not child_available_on(presence_map.get(candidate,{}), d):
            if available:
                candidate = _fewest_tasks_child(available, assigned_count)
            else:
                continue

        if candidate in children:
            assigned_count[candidate] = assigned_count.get(candidate, 0) + 1
            result.append({"task":task["name"],"child":candidate,"type":"week","day":task.get("day","")})
    return result


# ── Maandtaken ───────────────────────────────────────────────────────────────

def month_assignments_for_date(task_cfg, children, presence_map, d: date) -> list[dict]:
    """
    Maandtaken. Als trigger-dag niet beschikbaar: verschuif max 6 dagen.
    """
    result = []
    for task in task_cfg:
        all_ch = task.get("all_children", True)
        cfg_pc = ({c: {"week_of_month": task.get("week_of_month","Laatste week"),
                       "day_of_week":   task.get("day_of_week","Zondag")}
                   for c in children}
                  if all_ch else task.get("assignments", {}))

        for child in ([c for c in children if c in cfg_pc] if not all_ch else children):
            cfg       = cfg_pc.get(child, {})
            wl        = cfg.get("week_of_month","Laatste week")
            day_name  = cfg.get("day_of_week","Zondag")
            day_num   = DAY_MAP.get(day_name, 6)
            n         = -1 if wl == "Laatste week" else (WEEK_OF_MONTH_OPTIONS.index(wl)+1 if wl in WEEK_OF_MONTH_OPTIONS else 1)
            trigger   = _nth_weekday_of_month(d.year, d.month, day_num, n)
            if not trigger:
                continue

            # Verschuif als kind niet beschikbaar is (max 6 dagen)
            actual = trigger
            for offset in range(7):
                check = trigger + timedelta(days=offset)
                if child_available_on(presence_map.get(child,{}), check):
                    actual = check
                    break
            else:
                continue

            if actual == d:
                result.append({
                    "task": task["name"], "child": child, "type": "month",
                    "trigger_date": actual.isoformat(),
                    "original_trigger": trigger.isoformat(),
                    "shifted": actual != trigger,
                })
    return result


def next_month_occurrence(task, children, presence_map, from_date: date) -> dict:
    result = {}
    for mo in range(13):
        d   = from_date + timedelta(days=mo*28)
        yr, mn = d.year, d.month
        if mn > 12:
            yr += 1; mn -= 12

        all_ch = task.get("all_children", True)
        cfg_pc = ({c: {"week_of_month": task.get("week_of_month","Laatste week"),
                       "day_of_week":   task.get("day_of_week","Zondag")} for c in children}
                  if all_ch else task.get("assignments",{}))

        for child in children:
            if child in result:
                continue
            cfg    = cfg_pc.get(child,{})
            wl     = cfg.get("week_of_month","Laatste week")
            dn     = DAY_MAP.get(cfg.get("day_of_week","Zondag"),6)
            n      = -1 if wl=="Laatste week" else (WEEK_OF_MONTH_OPTIONS.index(wl)+1 if wl in WEEK_OF_MONTH_OPTIONS else 1)
            trigger= _nth_weekday_of_month(yr, mn, dn, n)
            if not trigger or trigger < from_date:
                continue
            for off in range(7):
                check = trigger + timedelta(days=off)
                if child_available_on(presence_map.get(child,{}), check):
                    result[child] = check.isoformat()
                    break
    return result
