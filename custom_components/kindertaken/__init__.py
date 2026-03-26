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
    """Stel de integratie in vanuit een config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Gebruik persistente opslag zodat afgevinkte taken overleven na herstart
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    stored = await store.async_load() or {}
    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "done": stored,
        "store": store,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # --- Service: taak afvinken ---
    async def handle_mark_done(call):
        child = call.data.get("child")
        task = call.data.get("task")
        date = call.data.get("date", datetime.now().strftime("%Y-%m-%d"))
        key = f"{date}__{child}__{task}"
        entry_data = hass.data[DOMAIN][entry.entry_id]
        done = entry_data["done"]
        # Toggle: als al gedaan → ongedaan maken
        done[key] = not done.get(key, False)
        await entry_data["store"].async_save(done)
        hass.bus.async_fire(f"{DOMAIN}_updated")
        _LOGGER.debug("Toggle taak: %s voor %s op %s → %s", task, child, date, done[key])

    # --- Service: week resetten ---
    async def handle_reset_week(call):
        entry_data = hass.data[DOMAIN][entry.entry_id]
        entry_data["done"] = {}
        await entry_data["store"].async_save({})
        hass.bus.async_fire(f"{DOMAIN}_updated")
        _LOGGER.info("Alle taken gereset")

    # --- Service: kind toevoegen (zonder herstart) ---
    async def handle_add_child(call):
        name = call.data.get("name", "").strip()
        if not name:
            return
        config = dict(hass.data[DOMAIN][entry.entry_id]["config"])
        children = list(config.get("children", []))
        if name not in children:
            children.append(name)
            config["children"] = children
            hass.config_entries.async_update_entry(entry, data=config)
            hass.data[DOMAIN][entry.entry_id]["config"] = config
            hass.bus.async_fire(f"{DOMAIN}_updated")
            _LOGGER.info("Kind toegevoegd: %s", name)

    hass.services.async_register(DOMAIN, "mark_done", handle_mark_done)
    hass.services.async_register(DOMAIN, "reset_week", handle_reset_week)
    hass.services.async_register(DOMAIN, "add_child", handle_add_child)

    # Luister naar config updates (opties flow)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
