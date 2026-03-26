"""Config flow voor Kindertaken Planner."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_CHILDREN, CONF_SCHEDULE, TASKS, DAYS_NL

NOBODY = "— niemand —"


def _build_schedule_schema(children: list[str], current_schedule: dict) -> vol.Schema:
    """Bouw een dynamisch formulier op voor de weekplanning."""
    child_options = [NOBODY] + children
    fields = {}
    for day in DAYS_NL:
        for task in TASKS:
            key = f"{day}__{task}"
            current = current_schedule.get(day, {}).get(task, NOBODY)
            if current not in child_options:
                current = NOBODY
            fields[vol.Optional(key, default=current)] = vol.In(child_options)
    return vol.Schema(fields)


def _parse_schedule(user_input: dict) -> dict:
    """Verwerk formulier input naar geneste dict {dag: {taak: kind}}."""
    schedule: dict = {}
    for key, child in user_input.items():
        if "__" in key and child and child != NOBODY:
            day, task = key.split("__", 1)
            schedule.setdefault(day, {})[task] = child
    return schedule


class KindertakenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Stap-voor-stap configuratie wizard."""

    VERSION = 1
    _children: list[str] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Stap 1: Namen van de kinderen invoeren."""
        errors: dict = {}

        if user_input is not None:
            raw = user_input.get("children", "")
            children = [c.strip() for c in raw.split(",") if c.strip()]
            if len(children) < 1:
                errors["children"] = "min_one_child"
            elif len(children) > 8:
                errors["children"] = "max_eight_children"
            else:
                self._children = children
                return await self.async_step_schedule()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("children"): str,
            }),
            errors=errors,
            description_placeholders={"example": "Emma, Liam, Sophie"},
        )

    async def async_step_schedule(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Stap 2: Weekplanning instellen."""
        if user_input is not None:
            return self.async_create_entry(
                title="Kindertaken Planner",
                data={
                    CONF_CHILDREN: self._children,
                    CONF_SCHEDULE: _parse_schedule(user_input),
                },
            )

        return self.async_show_form(
            step_id="schedule",
            data_schema=_build_schedule_schema(self._children, {}),
            description_placeholders={
                "children": ", ".join(self._children),
                "nobody": NOBODY,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return KindertakenOptionsFlow(config_entry)


class KindertakenOptionsFlow(config_entries.OptionsFlow):
    """Opties flow: planning of kinderlijst aanpassen."""

    def __init__(self, config_entry):
        self._entry = config_entry
        self._children: list[str] = list(config_entry.data.get(CONF_CHILDREN, []))
        self._schedule: dict = dict(config_entry.data.get(CONF_SCHEDULE, {}))

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Kies wat je wil aanpassen."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["edit_children", "edit_schedule"],
        )

    async def async_step_edit_children(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Kinderlijst aanpassen."""
        errors: dict = {}
        if user_input is not None:
            raw = user_input.get("children", "")
            children = [c.strip() for c in raw.split(",") if c.strip()]
            if len(children) < 1:
                errors["children"] = "min_one_child"
            else:
                self._children = children
                # Sla op en ga door naar planning
                return await self.async_step_edit_schedule()

        return self.async_show_form(
            step_id="edit_children",
            data_schema=vol.Schema({
                vol.Required(
                    "children",
                    default=", ".join(self._children),
                ): str,
            }),
            errors=errors,
        )

    async def async_step_edit_schedule(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Weekplanning aanpassen."""
        if user_input is not None:
            new_config = dict(self._entry.data)
            new_config[CONF_CHILDREN] = self._children
            new_config[CONF_SCHEDULE] = _parse_schedule(user_input)
            # Sla op via options (triggert reload)
            return self.async_create_entry(title="", data=new_config)

        return self.async_show_form(
            step_id="edit_schedule",
            data_schema=_build_schedule_schema(self._children, self._schedule),
        )
