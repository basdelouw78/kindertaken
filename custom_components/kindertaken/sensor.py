"""Sensor platform voor Kindertaken Planner."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_CHILDREN, CONF_SCHEDULE, DAYS_NL, DAY_MAP, TASKS, TASK_ICONS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Maak sensoren aan voor week + elk kind."""
    children = entry.data.get(CONF_CHILDREN, [])
    entities: list[SensorEntity] = [KindertakenWeekSensor(hass, entry)]
    for child in children:
        entities.append(KindertakenChildSensor(hass, entry, child))
    async_add_entities(entities, True)


def _week_data(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    """Bereken het volledige weekschema met done-status."""
    entry_data = hass.data[DOMAIN].get(entry.entry_id, {})
    schedule = entry_data.get("config", {}).get(CONF_SCHEDULE, {})
    done = entry_data.get("done", {})

    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())  # Maandag

    result = {}
    for day_name in DAYS_NL:
        offset = DAY_MAP[day_name]
        day_date = week_start + timedelta(days=offset)
        date_str = day_date.strftime("%Y-%m-%d")

        day_tasks = schedule.get(day_name, {})
        tasks_list = []
        for task in TASKS:
            child = day_tasks.get(task)
            if child:
                key = f"{date_str}__{child}__{task}"
                tasks_list.append({
                    "task": task,
                    "icon": TASK_ICONS.get(task, "✔️"),
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
    """Sensor die het volledige weekoverzicht blootstelt."""

    _attr_icon = "mdi:calendar-week"
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_name = "Kindertaken Week"
        self._attr_unique_id = f"{DOMAIN}_week_{entry.entry_id}"

    async def async_added_to_hass(self) -> None:
        @callback
        def _on_update(_event):
            self.async_write_ha_state()

        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_updated", _on_update)
        )

    @property
    def state(self) -> str:
        return "actief"

    @property
    def extra_state_attributes(self) -> dict:
        children = self._entry.data.get(CONF_CHILDREN, [])
        week = _week_data(self.hass, self._entry)
        today_name = next((d for d, v in week.items() if v["is_today"]), "")
        return {
            "week": week,
            "children": children,
            "tasks": TASKS,
            "task_icons": TASK_ICONS,
            "today": datetime.now().strftime("%Y-%m-%d"),
            "today_name": today_name,
        }


class KindertakenChildSensor(SensorEntity):
    """Sensor met de taken van één kind voor vandaag."""

    _attr_icon = "mdi:account-check"
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, child: str) -> None:
        self.hass = hass
        self._entry = entry
        self._child = child
        self._attr_name = f"Kindertaken {child}"
        self._attr_unique_id = f"{DOMAIN}_child_{child.lower()}_{entry.entry_id}"

    async def async_added_to_hass(self) -> None:
        @callback
        def _on_update(_event):
            self.async_write_ha_state()

        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_updated", _on_update)
        )

    def _todays_tasks(self) -> list[dict]:
        today = datetime.now()
        day_name = DAYS_NL[today.weekday()]
        date_str = today.strftime("%Y-%m-%d")
        entry_data = self.hass.data[DOMAIN].get(self._entry.entry_id, {})
        schedule = entry_data.get("config", {}).get(CONF_SCHEDULE, {})
        done = entry_data.get("done", {})

        tasks = []
        for task in TASKS:
            child = schedule.get(day_name, {}).get(task)
            if child == self._child:
                key = f"{date_str}__{child}__{task}"
                tasks.append({
                    "task": task,
                    "icon": TASK_ICONS.get(task, "✔️"),
                    "done": done.get(key, False),
                    "date": date_str,
                })
        return tasks

    @property
    def state(self) -> int:
        return len(self._todays_tasks())

    @property
    def extra_state_attributes(self) -> dict:
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
