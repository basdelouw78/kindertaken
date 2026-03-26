"""Kindertaken Planner integratie voor Home Assistant."""
from __future__ import annotations
import logging
from datetime import datetime
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store
from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)
STORAGE_KEY = f"{DOMAIN}_done_tasks"
STORAGE_VERSION = 1


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    stored = await store.async_load() or {}
    hass.data[DOMAIN][entry.entry_id] = {
        "config": dict(entry.data),
        "done": stored,
        "store": store,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_mark_done(call):
        """Toggle een taak als gedaan/ongedaan. Werkt voor week- én maandtaken."""
        child = call.data.get("child")
        task = call.data.get("task")
        date = call.data.get("date")          # voor weektaken: YYYY-MM-DD
        month_key = call.data.get("month_key")  # voor maandtaken: YYYY-MM

        if month_key:
            key = f"month__{month_key}__{child}__{task}"
        else:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            key = f"{date}__{child}__{task}"

        ed = hass.data[DOMAIN][entry.entry_id]
        ed["done"][key] = not ed["done"].get(key, False)
        await ed["store"].async_save(ed["done"])
        hass.bus.async_fire(f"{DOMAIN}_updated")

    async def handle_reset_week(call):
        ed = hass.data[DOMAIN][entry.entry_id]
        # Verwijder alleen week-sleutels (beginnen niet met 'month__')
        ed["done"] = {k: v for k, v in ed["done"].items() if k.startswith("month__")}
        await ed["store"].async_save(ed["done"])
        hass.bus.async_fire(f"{DOMAIN}_updated")

    async def handle_reset_month(call):
        ed = hass.data[DOMAIN][entry.entry_id]
        today = datetime.now().strftime("%Y-%m")
        ed["done"] = {k: v for k, v in ed["done"].items() if f"month__{today}" not in k}
        await ed["store"].async_save(ed["done"])
        hass.bus.async_fire(f"{DOMAIN}_updated")

    async def handle_reset_all(call):
        ed = hass.data[DOMAIN][entry.entry_id]
        ed["done"] = {}
        await ed["store"].async_save({})
        hass.bus.async_fire(f"{DOMAIN}_updated")

    hass.services.async_register(DOMAIN, "mark_done", handle_mark_done)
    hass.services.async_register(DOMAIN, "reset_week", handle_reset_week)
    hass.services.async_register(DOMAIN, "reset_month", handle_reset_month)
    hass.services.async_register(DOMAIN, "reset_all", handle_reset_all)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_reload_entry(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
