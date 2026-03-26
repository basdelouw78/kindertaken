"""Config flow voor Kindertaken Planner."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN, CONF_CHILDREN, CONF_TASKS, CONF_SCHEDULE,
    DEFAULT_TASKS, DAYS_NL,
)

NOBODY = "niemand"


def _build_schedule_schema(children: list, tasks: list, current: dict) -> vol.Schema:
    child_options = [NOBODY] + children
    fields = {}
    for day in DAYS_NL:
        for task in tasks:
            key = f"{day}__{task}"
            default = current.get(day, {}).get(task, NOBODY)
            if default not in child_options:
                default = NOBODY
            fields[vol.Optional(key, default=default)] = vol.In(child_options)
    return vol.Schema(fields)


def _parse_schedule(user_input: dict) -> dict:
    schedule = {}
    for key, child in user_input.items():
        if "__" in key and child and child != NOBODY:
            day, task = key.split("__", 1)
            schedule.setdefault(day, {})[task] = child
    return schedule


class KindertakenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """3-stappen wizard: kinderen > taken > planning."""

    VERSION = 1

    def __init__(self):
        self._children = []
        self._tasks = []

    async def async_step_user(self, user_input=None):
        """Stap 1: Namen van de kinderen."""
        errors = {}
        if user_input is not None:
            children = [c.strip() for c in user_input.get("children", "").split(",") if c.strip()]
            if len(children) < 1:
                errors["children"] = "min_one_child"
            elif len(children) > 8:
                errors["children"] = "max_eight_children"
            else:
                self._children = children
                return await self.async_step_tasks()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("children"): str}),
            errors=errors,
            description_placeholders={"example": "Emma, Liam, Sophie"},
        )

    async def async_step_tasks(self, user_input=None):
        """Stap 2: Taken kiezen en eigen taken toevoegen."""
        errors = {}
        if user_input is not None:
            selected = [t for t in DEFAULT_TASKS if user_input.get(f"task__{t}", False)]
            extra_raw = user_input.get("extra_tasks", "")
            extra = [t.strip() for t in extra_raw.split(",") if t.strip()]
            all_tasks = selected + [t for t in extra if t not in selected]
            if len(all_tasks) < 1:
                errors["base"] = "min_one_task"
            else:
                self._tasks = all_tasks
                return await self.async_step_schedule()

        fields = {}
        for task in DEFAULT_TASKS:
            fields[vol.Optional(f"task__{task}", default=True)] = bool
        fields[vol.Optional("extra_tasks", default="")] = str

        return self.async_show_form(
            step_id="tasks",
            data_schema=vol.Schema(fields),
            errors=errors,
        )

    async def async_step_schedule(self, user_input=None):
        """Stap 3: Weekplanning instellen."""
        if user_input is not None:
            return self.async_create_entry(
                title="Kindertaken Planner",
                data={
                    CONF_CHILDREN: self._children,
                    CONF_TASKS: self._tasks,
                    CONF_SCHEDULE: _parse_schedule(user_input),
                },
            )

        return self.async_show_form(
            step_id="schedule",
            data_schema=_build_schedule_schema(self._children, self._tasks, {}),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return KindertakenOptionsFlow(config_entry)


class KindertakenOptionsFlow(config_entries.OptionsFlow):
    """Opties: kinderen, taken of planning aanpassen."""

    def __init__(self, config_entry):
        self._entry = config_entry
        self._children = list(config_entry.data.get(CONF_CHILDREN, []))
        self._tasks = list(config_entry.data.get(CONF_TASKS, DEFAULT_TASKS))
        self._schedule = dict(config_entry.data.get(CONF_SCHEDULE, {}))

    async def async_step_init(self, user_input=None):
        return self.async_show_menu(
            step_id="init",
            menu_options=["edit_children", "edit_tasks", "edit_schedule"],
        )

    async def async_step_edit_children(self, user_input=None):
        errors = {}
        if user_input is not None:
            children = [c.strip() for c in user_input.get("children", "").split(",") if c.strip()]
            if not children:
                errors["children"] = "min_one_child"
            else:
                self._children = children
                return await self.async_step_edit_schedule()
        return self.async_show_form(
            step_id="edit_children",
            data_schema=vol.Schema({vol.Required("children", default=", ".join(self._children)): str}),
            errors=errors,
        )

    async def async_step_edit_tasks(self, user_input=None):
        errors = {}
        if user_input is not None:
            selected = [t for t in DEFAULT_TASKS if user_input.get(f"task__{t}", False)]
            extra_raw = user_input.get("extra_tasks", "")
            extra = [t.strip() for t in extra_raw.split(",") if t.strip()]
            existing_extra = [t for t in self._tasks if t not in DEFAULT_TASKS]
            all_tasks = selected + [t for t in (extra if extra else existing_extra) if t not in selected]
            if not all_tasks:
                errors["base"] = "min_one_task"
            else:
                self._tasks = all_tasks
                return await self.async_step_edit_schedule()

        current_extra = [t for t in self._tasks if t not in DEFAULT_TASKS]
        fields = {}
        for task in DEFAULT_TASKS:
            fields[vol.Optional(f"task__{task}", default=(task in self._tasks))] = bool
        fields[vol.Optional("extra_tasks", default=", ".join(current_extra))] = str
        return self.async_show_form(
            step_id="edit_tasks",
            data_schema=vol.Schema(fields),
            errors=errors,
        )

    async def async_step_edit_schedule(self, user_input=None):
        if user_input is not None:
            new_config = dict(self._entry.data)
            new_config[CONF_CHILDREN] = self._children
            new_config[CONF_TASKS] = self._tasks
            new_config[CONF_SCHEDULE] = _parse_schedule(user_input)
            return self.async_create_entry(title="", data=new_config)
        return self.async_show_form(
            step_id="edit_schedule",
            data_schema=_build_schedule_schema(self._children, self._tasks, self._schedule),
        )
