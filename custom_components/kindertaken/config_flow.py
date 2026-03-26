"""Config flow voor Kindertaken Planner."""
from __future__ import annotations
from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN, CONF_CHILDREN, CONF_CHILD_COLORS, CONF_TASKS, CONF_MONTH_TASKS,
    CONF_SCHEDULE, CONF_MONTH_SCHEDULE,
    DEFAULT_TASKS, DEFAULT_MONTH_TASKS, DAYS_NL, MONTHS_NL,
    CHILD_COLOR_OPTIONS, DEFAULT_COLOR_ORDER,
)

NOBODY = "niemand"


def _schedule_schema(children, tasks, current):
    opts = [NOBODY] + children
    fields = {}
    for day in DAYS_NL:
        for task in tasks:
            key = f"{day}__{task}"
            default = current.get(day, {}).get(task, NOBODY)
            if default not in opts:
                default = NOBODY
            fields[vol.Optional(key, default=default)] = vol.In(opts)
    return vol.Schema(fields)


def _month_schedule_schema(children, tasks, current):
    opts = [NOBODY] + children
    fields = {}
    for month in MONTHS_NL:
        for task in tasks:
            key = f"{month}__{task}"
            default = current.get(month, {}).get(task, NOBODY)
            if default not in opts:
                default = NOBODY
            fields[vol.Optional(key, default=default)] = vol.In(opts)
    return vol.Schema(fields)


def _parse_schedule(user_input):
    schedule = {}
    for key, child in user_input.items():
        if "__" in key and child and child != NOBODY:
            part1, part2 = key.split("__", 1)
            schedule.setdefault(part1, {})[part2] = child
    return schedule


class KindertakenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """5-stappen wizard: kinderen → kleuren → taken → planning → maandplanning."""

    VERSION = 1

    def __init__(self):
        self._children = []
        self._child_colors = {}
        self._tasks = []
        self._month_tasks = []

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
                return await self.async_step_colors()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("children"): str}),
            errors=errors,
            description_placeholders={"example": "Emma, Liam, Sophie"},
        )

    async def async_step_colors(self, user_input=None):
        """Stap 2: Kleur per kind kiezen."""
        if user_input is not None:
            colors = {}
            for child in self._children:
                key = f"color__{child}"
                colors[child] = user_input.get(key, DEFAULT_COLOR_ORDER[self._children.index(child) % len(DEFAULT_COLOR_ORDER)])
            self._child_colors = colors
            return await self.async_step_tasks()

        color_names = list(CHILD_COLOR_OPTIONS.keys())
        fields = {}
        for i, child in enumerate(self._children):
            default_color = DEFAULT_COLOR_ORDER[i % len(DEFAULT_COLOR_ORDER)]
            fields[vol.Optional(f"color__{child}", default=default_color)] = vol.In(color_names)

        return self.async_show_form(
            step_id="colors",
            data_schema=vol.Schema(fields),
            description_placeholders={"children": ", ".join(self._children)},
        )

    async def async_step_tasks(self, user_input=None):
        """Stap 3: Wekelijkse taken instellen."""
        errors = {}
        if user_input is not None:
            selected = [t for t in DEFAULT_TASKS if user_input.get(f"task__{t}", False)]
            extra = [t.strip() for t in user_input.get("extra_tasks", "").split(",") if t.strip()]
            all_tasks = selected + [t for t in extra if t not in selected]
            if not all_tasks:
                errors["base"] = "min_one_task"
            else:
                self._tasks = all_tasks
                return await self.async_step_month_tasks()

        fields = {}
        for task in DEFAULT_TASKS:
            fields[vol.Optional(f"task__{task}", default=True)] = bool
        fields[vol.Optional("extra_tasks", default="")] = str
        return self.async_show_form(step_id="tasks", data_schema=vol.Schema(fields), errors=errors)

    async def async_step_month_tasks(self, user_input=None):
        """Stap 4: Maandtaken instellen."""
        errors = {}
        if user_input is not None:
            selected = [t for t in DEFAULT_MONTH_TASKS if user_input.get(f"mtask__{t}", False)]
            extra = [t.strip() for t in user_input.get("extra_month_tasks", "").split(",") if t.strip()]
            all_tasks = selected + [t for t in extra if t not in selected]
            self._month_tasks = all_tasks
            return await self.async_step_schedule()

        fields = {}
        for task in DEFAULT_MONTH_TASKS:
            fields[vol.Optional(f"mtask__{task}", default=True)] = bool
        fields[vol.Optional("extra_month_tasks", default="")] = str
        return self.async_show_form(step_id="month_tasks", data_schema=vol.Schema(fields), errors=errors)

    async def async_step_schedule(self, user_input=None):
        """Stap 5a: Weekplanning."""
        if user_input is not None:
            self._week_schedule = _parse_schedule(user_input)
            if self._month_tasks:
                return await self.async_step_month_schedule()
            return self.async_create_entry(
                title="Kindertaken Planner",
                data={
                    CONF_CHILDREN: self._children,
                    CONF_CHILD_COLORS: self._child_colors,
                    CONF_TASKS: self._tasks,
                    CONF_MONTH_TASKS: self._month_tasks,
                    CONF_SCHEDULE: self._week_schedule,
                    CONF_MONTH_SCHEDULE: {},
                },
            )
        return self.async_show_form(
            step_id="schedule",
            data_schema=_schedule_schema(self._children, self._tasks, {}),
        )

    async def async_step_month_schedule(self, user_input=None):
        """Stap 5b: Maandplanning."""
        if user_input is not None:
            return self.async_create_entry(
                title="Kindertaken Planner",
                data={
                    CONF_CHILDREN: self._children,
                    CONF_CHILD_COLORS: self._child_colors,
                    CONF_TASKS: self._tasks,
                    CONF_MONTH_TASKS: self._month_tasks,
                    CONF_SCHEDULE: self._week_schedule,
                    CONF_MONTH_SCHEDULE: _parse_schedule(user_input),
                },
            )
        return self.async_show_form(
            step_id="month_schedule",
            data_schema=_month_schedule_schema(self._children, self._month_tasks, {}),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return KindertakenOptionsFlow(config_entry)


class KindertakenOptionsFlow(config_entries.OptionsFlow):
    """Opties flow."""

    def __init__(self, config_entry):
        self._entry = config_entry
        self._children = list(config_entry.data.get(CONF_CHILDREN, []))
        self._child_colors = dict(config_entry.data.get(CONF_CHILD_COLORS, {}))
        self._tasks = list(config_entry.data.get(CONF_TASKS, DEFAULT_TASKS))
        self._month_tasks = list(config_entry.data.get(CONF_MONTH_TASKS, []))
        self._schedule = dict(config_entry.data.get(CONF_SCHEDULE, {}))
        self._month_schedule = dict(config_entry.data.get(CONF_MONTH_SCHEDULE, {}))

    async def async_step_init(self, user_input=None):
        return self.async_show_menu(
            step_id="init",
            menu_options=["edit_children", "edit_colors", "edit_tasks", "edit_month_tasks", "edit_schedule", "edit_month_schedule"],
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

    async def async_step_edit_colors(self, user_input=None):
        if user_input is not None:
            for child in self._children:
                key = f"color__{child}"
                if key in user_input:
                    self._child_colors[child] = user_input[key]
            new_config = dict(self._entry.data)
            new_config[CONF_CHILD_COLORS] = self._child_colors
            return self.async_create_entry(title="", data=new_config)

        color_names = list(CHILD_COLOR_OPTIONS.keys())
        fields = {}
        for i, child in enumerate(self._children):
            current = self._child_colors.get(child, DEFAULT_COLOR_ORDER[i % len(DEFAULT_COLOR_ORDER)])
            fields[vol.Optional(f"color__{child}", default=current)] = vol.In(color_names)
        return self.async_show_form(step_id="edit_colors", data_schema=vol.Schema(fields))

    async def async_step_edit_tasks(self, user_input=None):
        errors = {}
        if user_input is not None:
            selected = [t for t in DEFAULT_TASKS if user_input.get(f"task__{t}", False)]
            extra = [t.strip() for t in user_input.get("extra_tasks", "").split(",") if t.strip()]
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
        return self.async_show_form(step_id="edit_tasks", data_schema=vol.Schema(fields), errors=errors)

    async def async_step_edit_month_tasks(self, user_input=None):
        if user_input is not None:
            selected = [t for t in DEFAULT_MONTH_TASKS if user_input.get(f"mtask__{t}", False)]
            extra = [t.strip() for t in user_input.get("extra_month_tasks", "").split(",") if t.strip()]
            existing_extra = [t for t in self._month_tasks if t not in DEFAULT_MONTH_TASKS]
            all_tasks = selected + [t for t in (extra if extra else existing_extra) if t not in selected]
            self._month_tasks = all_tasks
            return await self.async_step_edit_month_schedule()
        current_extra = [t for t in self._month_tasks if t not in DEFAULT_MONTH_TASKS]
        fields = {}
        for task in DEFAULT_MONTH_TASKS:
            fields[vol.Optional(f"mtask__{task}", default=(task in self._month_tasks))] = bool
        fields[vol.Optional("extra_month_tasks", default=", ".join(current_extra))] = str
        return self.async_show_form(step_id="edit_month_tasks", data_schema=vol.Schema(fields))

    async def async_step_edit_schedule(self, user_input=None):
        if user_input is not None:
            new_config = dict(self._entry.data)
            new_config[CONF_CHILDREN] = self._children
            new_config[CONF_TASKS] = self._tasks
            new_config[CONF_SCHEDULE] = _parse_schedule(user_input)
            return self.async_create_entry(title="", data=new_config)
        return self.async_show_form(
            step_id="edit_schedule",
            data_schema=_schedule_schema(self._children, self._tasks, self._schedule),
        )

    async def async_step_edit_month_schedule(self, user_input=None):
        if user_input is not None:
            new_config = dict(self._entry.data)
            new_config[CONF_MONTH_TASKS] = self._month_tasks
            new_config[CONF_MONTH_SCHEDULE] = _parse_schedule(user_input)
            return self.async_create_entry(title="", data=new_config)
        return self.async_show_form(
            step_id="edit_month_schedule",
            data_schema=_month_schedule_schema(self._children, self._month_tasks, self._month_schedule),
        )
