"""
Aanwezigheidsberekening v2 — meerdere patronen.

Presence config per kind:
{
  "mode": "altijd" | "om_de_week" | "vaste_dagen" | "weken_per_maand" | "combinatie",

  # om_de_week:
  "start_date": "2024-01-05",   # vrijdag van week A (eerste week dat kind er is)
  "start_present": true,

  # vaste_dagen: lijst weekdagnummers 0=ma..6=zo
  "days_present": [4, 5, 6],    # vr, za, zo

  # weken_per_maand: welke weken (1-4, of "laatste")
  "weeks_present": [1, 3],      # 1e en 3e week

  # combinatie: om_de_week PLUS vaste_dagen (kind is er in 'zijn' week
  #             maar dan alleen op de vaste dagen)
  # gebruikt: start_date, start_present, days_present

  # vaste blokdagen (ongeacht aanwezigheid — bijv. werken)
  "blocked_days": [{"day": 0, "reason": "werk"}],

  # handmatige override (gezet door HA service of input_boolean)
  "override_present": null | true | false,  # null = gebruik berekening
}
"""
from __future__ import annotations
from datetime import date, timedelta
import math


PRESENCE_MODES = {
    "Altijd aanwezig":                  "altijd",
    "Om de week (startdatum)":          "om_de_week",
    "Vaste dagen per week":             "vaste_dagen",
    "Bepaalde weken per maand":         "weken_per_maand",
    "Combinatie: om de week + vaste dagen": "combinatie",
}


def _week_of_month(d: date) -> int:
    first_weekday = d.replace(day=1).weekday()
    return math.ceil((d.day + first_weekday) / 7)


def child_present_on(cfg: dict, d: date) -> bool:
    """Berekent of het kind aanwezig is op datum d (zonder blokdagen)."""
    # Handmatige override heeft altijd voorrang
    override = cfg.get("override_present")
    if override is not None:
        return bool(override)

    mode = cfg.get("mode", "altijd")

    if mode == "altijd":
        return True

    if mode == "om_de_week":
        return _om_de_week(cfg, d)

    if mode == "vaste_dagen":
        return d.weekday() in _days_set(cfg)

    if mode == "weken_per_maand":
        return _weken_per_maand(cfg, d)

    if mode == "combinatie":
        # Aanwezig in 'zijn' week EN op de vaste dagen
        return _om_de_week(cfg, d) and (d.weekday() in _days_set(cfg))

    return True


def child_available_on(cfg: dict, d: date) -> bool:
    """Aanwezig én niet geblokkeerd."""
    if not child_present_on(cfg, d):
        return False
    for b in cfg.get("blocked_days", []):
        bd = b if isinstance(b, int) else b.get("day", -1)
        if bd == d.weekday():
            return False
    return True


def _om_de_week(cfg: dict, d: date) -> bool:
    try:
        start = date.fromisoformat(cfg.get("start_date", "2024-01-01"))
    except ValueError:
        return True
    start_present = cfg.get("start_present", True)
    delta_weeks   = (d - start).days // 7
    return (delta_weeks % 2 == 0) == start_present


def _days_set(cfg: dict) -> set:
    return set(cfg.get("days_present", []))


def _weken_per_maand(cfg: dict, d: date) -> bool:
    weeks_present = cfg.get("weeks_present", [1, 3])
    wom = _week_of_month(d)
    # Ondersteuning voor "laatste" als string
    if "laatste" in [str(w).lower() for w in weeks_present]:
        # Bereken laatste week van de maand
        nxt  = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
        last = nxt - timedelta(days=1)
        last_wom = _week_of_month(last)
        if wom == last_wom:
            return True
    return wom in [int(w) for w in weeks_present if str(w).lower() != "laatste"]


def presence_week_summary(cfg: dict, week_start: date) -> dict:
    """Aanwezigheid + beschikbaarheid per dag van de week."""
    result = {}
    for i in range(7):
        d = week_start + timedelta(days=i)
        result[d.isoformat()] = {
            "present":   child_present_on(cfg, d),
            "available": child_available_on(cfg, d),
        }
    return result
