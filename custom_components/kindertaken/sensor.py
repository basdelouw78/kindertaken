"""Sensor platform voor Kindertaken Planner."""
from __future__ import annotations
import logging
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN, CONF_CHILDREN, CONF_CHILD_COLORS, CONF_TASKS, CONF_MONTH_TASKS,
    CONF_SCHEDULE, CONF_MONTH_SCHEDULE,
    DEFAULT_TASKS, DEFAULT_MONTH_TASKS, DAYS_NL, DAY_MAP, MONTHS_NL,
    TASK_ICON_LIST, MONTH_TASK_ICON_LIST,
    CHILD_COLOR_OPTIONS, COLOR_EMOJI, DEFAULT_COLOR_ORDER,
)

_LOGGER = logging.getLogger(__name__)


def _icons(tasks, icon_list):
    return {t: icon_list[i % len(icon_list)] for i, t in enumerate(tasks)}


def _child_theme(child, children, child_colors):
    """Geef bg/light/emoji terug voor een kind op basis van gekozen kleur."""
    idx = children.index(child) if child in children else 0
    color_name = child_colors.get(child, DEFAULT_COLOR_ORDER[idx % len(DEFAULT_COLOR_ORDER)])
    colors = CHILD_COLOR_OPTIONS.get(color_name, list(CHILD_COLOR_OPTIONS.values())[0])
    emoji = COLOR_EMOJI.get(color_name, "⭐")
    return {"bg": colors[0], "light": colors[1], "emoji": emoji, "color_name": color_name}


async def async_setup_entry(hass, entry, async_add_entities):
    children = entry.data.get(CONF_CHILDREN, [])
    entities = [KindertakenWeekSensor(hass, entry), KindertakenMonthSensor(hass, entry)]
    for child in children:
        entities.append(KindertakenChildSensor(hass, entry, child))
    async_add_entities(entities, True)


def _week_data(hass, entry):
    ed = hass.data[DOMAIN].get(entry.entry_id, {})
    config = ed.get("config", entry.data)
    schedule = config.get(CONF_SCHEDULE, {})
    tasks = config.get(CONF_TASKS, DEFAULT_TASKS)
    children = config.get(CONF_CHILDREN, [])
    child_colors = config.get(CONF_CHILD_COLORS, {})
    done = ed.get("done", {})
    icons = _icons(tasks, TASK_ICON_LIST)

    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())

    result = {}
    for day_name in DAYS_NL:
        offset = DAY_MAP[day_name]
        day_date = week_start + timedelta(days=offset)
        date_str = day_date.strftime("%Y-%m-%d")
        tasks_list = []
        for task in tasks:
            child = schedule.get(day_name, {}).get(task)
            if child:
                key = f"{date_str}__{child}__{task}"
                theme = _child_theme(child, children, child_colors)
                tasks_list.append({
                    "task": task, "icon": icons.get(task, "✔️"),
                    "child": child, "done": done.get(key, False),
                    "date": date_str,
                    "bg": theme["bg"], "light": theme["light"], "emoji": theme["emoji"],
                })
        result[day_name] = {
            "date": date_str,
            "date_display": day_date.strftime("%-d %b"),
            "tasks": tasks_list,
            "is_today": date_str == today.strftime("%Y-%m-%d"),
        }
    return result


def _month_data(hass, entry):
    ed = hass.data[DOMAIN].get(entry.entry_id, {})
    config = ed.get("config", entry.data)
    month_schedule = config.get(CONF_MONTH_SCHEDULE, {})
    month_tasks = config.get(CONF_MONTH_TASKS, [])
    children = config.get(CONF_CHILDREN, [])
    child_colors = config.get(CONF_CHILD_COLORS, {})
    done = ed.get("done", {})
    icons = _icons(month_tasks, MONTH_TASK_ICON_LIST)

    today = datetime.now()
    result = {}
    for i, month_name in enumerate(MONTHS_NL):
        month_num = i + 1
        year = today.year
        month_key = f"{year}-{month_num:02d}"
        tasks_list = []
        for task in month_tasks:
            child = month_schedule.get(month_name, {}).get(task)
            if child:
                done_key = f"month__{month_key}__{child}__{task}"
                theme = _child_theme(child, children, child_colors)
                tasks_list.append({
                    "task": task, "icon": icons.get(task, "🏠"),
                    "child": child, "done": done.get(done_key, False),
                    "month_key": month_key,
                    "bg": theme["bg"], "light": theme["light"], "emoji": theme["emoji"],
                })
        result[month_name] = {
            "month_key": month_key,
            "month_num": month_num,
            "tasks": tasks_list,
            "is_current": month_num == today.month,
        }
    return result


class KindertakenWeekSensor(SensorEntity):
    _attr_icon = "mdi:calendar-week"

    def __init__(self, hass, entry):
        self.hass = hass
        self._entry = entry
        self._attr_name = "Kindertaken Week"
        self._attr_unique_id = f"{DOMAIN}_week_{entry.entry_id}"

    async def async_added_to_hass(self):
        @callback
        def _upd(_event): self.async_write_ha_state()
        self.async_on_remove(self.hass.bus.async_listen(f"{DOMAIN}_updated", _upd))

    @property
    def state(self): return "actief"

    @property
    def extra_state_attributes(self):
        ed = self.hass.data[DOMAIN].get(self._entry.entry_id, {})
        config = ed.get("config", self._entry.data)
        children = config.get(CONF_CHILDREN, [])
        child_colors = config.get(CONF_CHILD_COLORS, {})
        tasks = config.get(CONF_TASKS, DEFAULT_TASKS)
        week = _week_data(self.hass, self._entry)
        today_name = next((d for d, v in week.items() if v["is_today"]), "")
        # Bouw child_themes op voor de kaart
        child_themes = {c: _child_theme(c, children, child_colors) for c in children}
        return {
            "week": week,
            "children": children,
            "child_themes": child_themes,
            "tasks": tasks,
            "today": datetime.now().strftime("%Y-%m-%d"),
            "today_name": today_name,
        }


class KindertakenMonthSensor(SensorEntity):
    _attr_icon = "mdi:calendar-month"

    def __init__(self, hass, entry):
        self.hass = hass
        self._entry = entry
        self._attr_name = "Kindertaken Maand"
        self._attr_unique_id = f"{DOMAIN}_month_{entry.entry_id}"

    async def async_added_to_hass(self):
        @callback
        def _upd(_event): self.async_write_ha_state()
        self.async_on_remove(self.hass.bus.async_listen(f"{DOMAIN}_updated", _upd))

    @property
    def state(self): return "actief"

    @property
    def extra_state_attributes(self):
        ed = self.hass.data[DOMAIN].get(self._entry.entry_id, {})
        config = ed.get("config", self._entry.data)
        children = config.get(CONF_CHILDREN, [])
        child_colors = config.get(CONF_CHILD_COLORS, {})
        month_tasks = config.get(CONF_MONTH_TASKS, [])
        months = _month_data(self.hass, self._entry)
        current_month = next((m for m, v in months.items() if v["is_current"]), "")
        child_themes = {c: _child_theme(c, children, child_colors) for c in children}
        return {
            "months": months,
            "children": children,
            "child_themes": child_themes,
            "month_tasks": month_tasks,
            "current_month": current_month,
            "current_year": datetime.now().year,
        }


class KindertakenChildSensor(SensorEntity):
    _attr_icon = "mdi:account-check"

    def __init__(self, hass, entry, child):
        self.hass = hass
        self._entry = entry
        self._child = child
        self._attr_name = f"Kindertaken {child}"
        self._attr_unique_id = f"{DOMAIN}_child_{child.lower()}_{entry.entry_id}"

    async def async_added_to_hass(self):
        @callback
        def _upd(_event): self.async_write_ha_state()
        self.async_on_remove(self.hass.bus.async_listen(f"{DOMAIN}_updated", _upd))

    def _today_tasks(self):
        today = datetime.now()
        day_name = DAYS_NL[today.weekday()]
        date_str = today.strftime("%Y-%m-%d")
        ed = self.hass.data[DOMAIN].get(self._entry.entry_id, {})
        config = ed.get("config", self._entry.data)
        schedule = config.get(CONF_SCHEDULE, {})
        tasks = config.get(CONF_TASKS, DEFAULT_TASKS)
        done = ed.get("done", {})
        icons = _icons(tasks, TASK_ICON_LIST)
        result = []
        for task in tasks:
            if schedule.get(day_name, {}).get(task) == self._child:
                key = f"{date_str}__{self._child}__{task}"
                result.append({"task": task, "icon": icons.get(task, "✔️"), "done": done.get(key, False), "date": date_str})
        return result

    def _month_tasks(self):
        today = datetime.now()
        month_name = MONTHS_NL[today.month - 1]
        month_key = today.strftime("%Y-%m")
        ed = self.hass.data[DOMAIN].get(self._entry.entry_id, {})
        config = ed.get("config", self._entry.data)
        month_schedule = config.get(CONF_MONTH_SCHEDULE, {})
        month_tasks = config.get(CONF_MONTH_TASKS, [])
        done = ed.get("done", {})
        icons = _icons(month_tasks, MONTH_TASK_ICON_LIST)
        result = []
        for task in month_tasks:
            if month_schedule.get(month_name, {}).get(task) == self._child:
                key = f"month__{month_key}__{self._child}__{task}"
                result.append({"task": task, "icon": icons.get(task, "🏠"), "done": done.get(key, False), "month_key": month_key})
        return result

    @property
    def state(self):
        return len(self._today_tasks())

    @property
    def extra_state_attributes(self):
        day_tasks = self._today_tasks()
        mon_tasks = self._month_tasks()
        done_day = sum(1 for t in day_tasks if t["done"])
        done_mon = sum(1 for t in mon_tasks if t["done"])
        return {
            "child": self._child,
            "tasks_today": day_tasks,
            "month_tasks_this_month": mon_tasks,
            "total_today": len(day_tasks),
            "done_today": done_day,
            "all_done_today": done_day == len(day_tasks) and len(day_tasks) > 0,
            "free_day": len(day_tasks) == 0,
            "total_month": len(mon_tasks),
            "done_month": done_mon,
        }
