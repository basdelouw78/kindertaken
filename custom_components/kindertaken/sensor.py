"""Sensor platform voor Kindertaken Planner."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_CHILDREN, CONF_TASKS, CONF_SCHEDULE, DAYS_NL, DAY_MAP, DEFAULT_TASKS, TASK_ICON_LIST

_LOGGER = logging.getLogger(__name__)


def _get_task_icons(tasks: list) -> dict:
    """Wijs automatisch iconen toe aan taken op volgorde."""
    return {task: TASK_ICON_LIST[i % len(TASK_ICON_LIST)] for i, task in enumerate(tasks)}


async def async_setup_entry(hass, entry, async_add_entities):
    children = entry.data.get(CONF_CHILDREN, [])
    entities = [KindertakenWeekSensor(hass, entry)]
    for child in children:
        entities.append(KindertakenChildSensor(hass, entry, child))
    async_add_entities(entities, True)


def _week_data(hass, entry):
    entry_data = hass.data[DOMAIN].get(entry.entry_id, {})
    config = entry_data.get("config", entry.data)
    schedule = config.get(CONF_SCHEDULE, {})
    tasks = config.get(CONF_TASKS, DEFAULT_TASKS)
    done = entry_data.get("done", {})
    icons = _get_task_icons(tasks)

    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())

    result = {}
    for day_name in DAYS_NL:
        offset = DAY_MAP[day_name]
        day_date = week_start + timedelta(days=offset)
        date_str = day_date.strftime("%Y-%m-%d")
        day_tasks = schedule.get(day_name, {})
        tasks_list = []
        for task in tasks:
            child = day_tasks.get(task)
            if child:
                key = f"{date_str}__{child}__{task}"
                tasks_list.append({
                    "task": task,
                    "icon": icons.get(task, "✔️"),
                    "child": child,
                    "done": done.get(key, False),
                    "date": date_str,
                })
        result[day_name] = {
            "date": date_str,
            "date_display": day_date.strftime("%-d %b"),
            "tasks": tasks_list,
            "is_today": date_str == today.strftime("%Y-%m-%d"),
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
        def _on_update(_event):
            self.async_write_ha_state()
        self.async_on_remove(self.hass.bus.async_listen(f"{DOMAIN}_updated", _on_update))

    @property
    def state(self):
        return "actief"

    @property
    def extra_state_attributes(self):
        entry_data = self.hass.data[DOMAIN].get(self._entry.entry_id, {})
        config = entry_data.get("config", self._entry.data)
        children = config.get(CONF_CHILDREN, [])
        tasks = config.get(CONF_TASKS, DEFAULT_TASKS)
        week = _week_data(self.hass, self._entry)
        today_name = next((d for d, v in week.items() if v["is_today"]), "")
        return {
            "week": week,
            "children": children,
            "tasks": tasks,
            "task_icons": _get_task_icons(tasks),
            "today": datetime.now().strftime("%Y-%m-%d"),
            "today_name": today_name,
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
        def _on_update(_event):
            self.async_write_ha_state()
        self.async_on_remove(self.hass.bus.async_listen(f"{DOMAIN}_updated", _on_update))

    def _todays_tasks(self):
        today = datetime.now()
        day_name = DAYS_NL[today.weekday()]
        date_str = today.strftime("%Y-%m-%d")
        entry_data = self.hass.data[DOMAIN].get(self._entry.entry_id, {})
        config = entry_data.get("config", self._entry.data)
        schedule = config.get(CONF_SCHEDULE, {})
        tasks = config.get(CONF_TASKS, DEFAULT_TASKS)
        done = entry_data.get("done", {})
        icons = _get_task_icons(tasks)
        result = []
        for task in tasks:
            if schedule.get(day_name, {}).get(task) == self._child:
                key = f"{date_str}__{self._child}__{task}"
                result.append({"task": task, "icon": icons.get(task, "✔️"), "done": done.get(key, False), "date": date_str})
        return result

    @property
    def state(self):
        return len(self._todays_tasks())

    @property
    def extra_state_attributes(self):
        tasks = self._todays_tasks()
        done_count = sum(1 for t in tasks if t["done"])
        return {
            "child": self._child,
            "tasks_today": tasks,
            "total": len(tasks),
            "done_count": done_count,
            "all_done": done_count == len(tasks) and len(tasks) > 0,
            "free_day": len(tasks) == 0,
        }
