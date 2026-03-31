"""Config flow v2.2 — alle aanwezigheidspatronen."""
from __future__ import annotations
from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN, CONF_CHILDREN, CONF_CHILD_COLORS, CONF_CHILD_PRESENCE,
    CONF_ROTATION_TASKS, CONF_WEEK_TASKS, CONF_MONTH_TASKS,
    DEFAULT_ROTATION_TASKS, DEFAULT_WEEK_TASKS, DEFAULT_MONTH_TASKS,
    DAYS_NL, WEEK_OF_MONTH_OPTIONS, PRESENCE_MODES,
    CHILD_COLOR_OPTIONS, DEFAULT_COLOR_ORDER,
)

NOBODY     = "niemand"
WEEK_MODES = ["Vast kind","Even weken","Oneven weken","Automatisch roteren"]
MAAND_WEEKS= ["1","2","3","4","laatste"]


def _children_order_str(children):
    return ", ".join(children)


class KindertakenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """7-stappen wizard."""

    VERSION = 4

    def __init__(self):
        self._children       = []
        self._child_colors   = {}
        self._child_presence = {}
        self._rotation_tasks = []
        self._week_tasks     = []
        self._month_tasks    = []

    # 1 ── Kinderen ────────────────────────────────────────────────────────────
    async def async_step_user(self, ui=None):
        errors = {}
        if ui is not None:
            ch = [c.strip() for c in ui.get("children","").split(",") if c.strip()]
            if not ch:        errors["children"] = "min_one_child"
            elif len(ch) > 8: errors["children"] = "max_eight_children"
            else:
                self._children = ch
                return await self.async_step_presence()
        return self.async_show_form(step_id="user",
            data_schema=vol.Schema({vol.Required("children"): str}),
            errors=errors,
            description_placeholders={"example":"Emma, Liam, Sophie"})

    # 2 ── Aanwezigheid per kind ───────────────────────────────────────────────
    async def async_step_presence(self, ui=None):
        if ui is not None:
            self._child_presence = self._parse_presence(ui)
            return await self.async_step_blocked_days()
        return self.async_show_form(step_id="presence",
            data_schema=vol.Schema(self._presence_fields({})))

    def _presence_fields(self, current: dict) -> dict:
        fields = {}
        for child in self._children:
            cur = current.get(child, {})
            cur_mode = {v:k for k,v in PRESENCE_MODES.items()}.get(cur.get("mode","altijd"),"Altijd aanwezig")
            fields[vol.Optional(f"mode__{child}", default=cur_mode)] = vol.In(list(PRESENCE_MODES.keys()))
            # Om de week
            fields[vol.Optional(f"start__{child}", default=cur.get("start_date","2024-01-05"))] = str
            fields[vol.Optional(f"here__{child}",  default=cur.get("start_present",True))]     = bool
            # Vaste dagen (checkboxes per dag)
            cur_days = set(cur.get("days_present",[]))
            for i, day in enumerate(DAYS_NL):
                fields[vol.Optional(f"day__{child}__{i}", default=(i in cur_days))] = bool
            # Weken per maand (1-4 + laatste)
            cur_weeks = set(str(w) for w in cur.get("weeks_present",[]))
            for w in MAAND_WEEKS:
                fields[vol.Optional(f"wk__{child}__{w}", default=(w in cur_weeks))] = bool
        return fields

    def _parse_presence(self, ui: dict) -> dict:
        result = {}
        for child in self._children:
            mode_label = ui.get(f"mode__{child}", "Altijd aanwezig")
            mode       = PRESENCE_MODES.get(mode_label, "altijd")
            days_present = [i for i in range(7) if ui.get(f"day__{child}__{i}", False)]
            weeks_present= [w for w in MAAND_WEEKS if ui.get(f"wk__{child}__{w}", False)]
            result[child] = {
                "mode":          mode,
                "start_date":    ui.get(f"start__{child}", "2024-01-05"),
                "start_present": ui.get(f"here__{child}", True),
                "days_present":  days_present,
                "weeks_present": [int(w) if w != "laatste" else "laatste" for w in weeks_present],
                "blocked_days":  [],
                "override_present": None,
            }
        return result

    # 3 ── Blokdagen ───────────────────────────────────────────────────────────
    async def async_step_blocked_days(self, ui=None):
        if ui is not None:
            for child in self._children:
                blocked = [{"day":i,"reason":ui.get(f"reason__{child}__{i}","geblokkeerd")}
                           for i in range(7) if ui.get(f"block__{child}__{i}", False)]
                self._child_presence[child]["blocked_days"] = blocked
            return await self.async_step_colors()
        fields = {}
        for child in self._children:
            for i, day in enumerate(DAYS_NL):
                fields[vol.Optional(f"block__{child}__{i}", default=False)] = bool
        return self.async_show_form(step_id="blocked_days", data_schema=vol.Schema(fields))

    # 4 ── Kleuren ─────────────────────────────────────────────────────────────
    async def async_step_colors(self, ui=None):
        if ui is not None:
            self._child_colors = {c: ui.get(f"color__{c}", DEFAULT_COLOR_ORDER[i % len(DEFAULT_COLOR_ORDER)])
                                   for i,c in enumerate(self._children)}
            return await self.async_step_rotation_tasks()
        fields = {vol.Optional(f"color__{c}", default=DEFAULT_COLOR_ORDER[i%len(DEFAULT_COLOR_ORDER)]): vol.In(list(CHILD_COLOR_OPTIONS.keys()))
                  for i,c in enumerate(self._children)}
        return self.async_show_form(step_id="colors", data_schema=vol.Schema(fields))

    # 5 ── Rotatietaken ────────────────────────────────────────────────────────
    async def async_step_rotation_tasks(self, ui=None):
        if ui is not None:
            sel   = [t for t in DEFAULT_ROTATION_TASKS if ui.get(f"rot__{t}", False)]
            extra = [t.strip() for t in ui.get("rot__extra","").split(",") if t.strip()]
            tasks = sel + [t for t in extra if t not in sel]
            volgorde = [c.strip() for c in ui.get("rot__volgorde","").split(",") if c.strip() in self._children] or self._children
            self._rotation_tasks = [{"name":t,"fixed_child":None,"children_order":volgorde} for t in tasks]
            return await self.async_step_week_tasks()
        fields = {vol.Optional(f"rot__{t}",default=True): bool for t in DEFAULT_ROTATION_TASKS}
        fields[vol.Optional("rot__extra",   default="")] = str
        fields[vol.Optional("rot__volgorde",default=_children_order_str(self._children))] = str
        return self.async_show_form(step_id="rotation_tasks", data_schema=vol.Schema(fields))

    # 6 ── Weektaken ───────────────────────────────────────────────────────────
    async def async_step_week_tasks(self, ui=None):
        if ui is not None:
            sel   = [t for t in DEFAULT_WEEK_TASKS if ui.get(f"wk__{t}", False)]
            extra = [t.strip() for t in ui.get("wk__extra","").split(",") if t.strip()]
            tasks = sel + [t for t in extra if t not in sel]
            mode_map = {"Vast kind":"fixed","Even weken":"even","Oneven weken":"odd","Automatisch roteren":"auto_rotate"}
            self._week_tasks = [{"name":t,"day":ui.get(f"wkday__{t}","Woensdag"),
                                  "mode":mode_map.get(ui.get(f"wkmode__{t}","Automatisch roteren"),"auto_rotate"),
                                  "fixed_child":self._children[0] if self._children else "",
                                  "even_child": self._children[0] if self._children else "",
                                  "odd_child":  self._children[1] if len(self._children)>1 else (self._children[0] if self._children else ""),
                                  "children_order":self._children} for t in tasks]
            return await self.async_step_month_tasks()
        fields = {}
        for t in DEFAULT_WEEK_TASKS:
            fields[vol.Optional(f"wk__{t}",   default=False)]                       = bool
            fields[vol.Optional(f"wkday__{t}",default="Woensdag")]                  = vol.In(DAYS_NL)
            fields[vol.Optional(f"wkmode__{t}",default="Automatisch roteren")]      = vol.In(WEEK_MODES)
        fields[vol.Optional("wk__extra",default="")] = str
        return self.async_show_form(step_id="week_tasks", data_schema=vol.Schema(fields))

    # 7 ── Maandtaken ──────────────────────────────────────────────────────────
    async def async_step_month_tasks(self, ui=None):
        if ui is not None:
            sel   = [t for t in DEFAULT_MONTH_TASKS if ui.get(f"mt__{t}", False)]
            extra = [t.strip() for t in ui.get("mt__extra","").split(",") if t.strip()]
            tasks = sel + [t for t in extra if t not in sel]
            self._month_tasks = [{"name":t,"all_children":True,
                                   "week_of_month":ui.get(f"mtwk__{t}","Laatste week"),
                                   "day_of_week":  ui.get(f"mtday__{t}","Zondag"),
                                   "assignments":{}} for t in tasks]
            return self.async_create_entry(title="Kindertaken Planner", data={
                CONF_CHILDREN:       self._children,
                CONF_CHILD_COLORS:   self._child_colors,
                CONF_CHILD_PRESENCE: self._child_presence,
                CONF_ROTATION_TASKS: self._rotation_tasks,
                CONF_WEEK_TASKS:     self._week_tasks,
                CONF_MONTH_TASKS:    self._month_tasks,
            })
        fields = {}
        for t in DEFAULT_MONTH_TASKS:
            fields[vol.Optional(f"mt__{t}",  default=True)]             = bool
            fields[vol.Optional(f"mtwk__{t}",default="Laatste week")]   = vol.In(WEEK_OF_MONTH_OPTIONS)
            fields[vol.Optional(f"mtday__{t}",default="Zondag")]        = vol.In(DAYS_NL)
        fields[vol.Optional("mt__extra",default="")] = str
        return self.async_show_form(step_id="month_tasks", data_schema=vol.Schema(fields))

    @staticmethod
    @callback
    def async_get_options_flow(entry):
        return KindertakenOptionsFlow(entry)


# ── Options flow ──────────────────────────────────────────────────────────────

class KindertakenOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry):
        self._entry = entry
        d = entry.data
        self._children       = list(d.get(CONF_CHILDREN,[]))
        self._child_colors   = dict(d.get(CONF_CHILD_COLORS,{}))
        self._child_presence = dict(d.get(CONF_CHILD_PRESENCE,{}))
        self._rotation_tasks = list(d.get(CONF_ROTATION_TASKS,[]))
        self._week_tasks     = list(d.get(CONF_WEEK_TASKS,[]))
        self._month_tasks    = list(d.get(CONF_MONTH_TASKS,[]))

    async def async_step_init(self, ui=None):
        return self.async_show_menu(step_id="init", menu_options=[
            "edit_children","edit_presence","edit_blocked_days","edit_colors",
            "edit_rotation_tasks","edit_week_tasks","edit_month_tasks",
        ])

    def _save(self, updates: dict):
        new = dict(self._entry.data)
        new.update(updates)
        return self.async_create_entry(title="", data=new)

    async def async_step_edit_children(self, ui=None):
        errors = {}
        if ui is not None:
            ch = [c.strip() for c in ui.get("children","").split(",") if c.strip()]
            if not ch: errors["children"] = "min_one_child"
            else: return self._save({CONF_CHILDREN: ch})
        return self.async_show_form(step_id="edit_children",
            data_schema=vol.Schema({vol.Required("children",default=", ".join(self._children)): str}),
            errors=errors)

    async def async_step_edit_presence(self, ui=None):
        flow = KindertakenConfigFlow()
        flow._children = self._children
        if ui is not None:
            presence = flow._parse_presence(ui)
            # Behoud bestaande blocked_days
            for child in self._children:
                presence[child]["blocked_days"] = self._child_presence.get(child,{}).get("blocked_days",[])
            return self._save({CONF_CHILD_PRESENCE: presence})
        return self.async_show_form(step_id="edit_presence",
            data_schema=vol.Schema(flow._presence_fields(self._child_presence)))

    async def async_step_edit_blocked_days(self, ui=None):
        if ui is not None:
            presence = dict(self._child_presence)
            for child in self._children:
                blocked = [{"day":i,"reason":"geblokkeerd"}
                           for i in range(7) if ui.get(f"block__{child}__{i}",False)]
                presence.setdefault(child,{})["blocked_days"] = blocked
            return self._save({CONF_CHILD_PRESENCE: presence})
        fields = {}
        for child in self._children:
            blocked_set = {(b if isinstance(b,int) else b.get("day",-1))
                           for b in self._child_presence.get(child,{}).get("blocked_days",[])}
            for i in range(7):
                fields[vol.Optional(f"block__{child}__{i}",default=(i in blocked_set))] = bool
        return self.async_show_form(step_id="edit_blocked_days", data_schema=vol.Schema(fields))

    async def async_step_edit_colors(self, ui=None):
        if ui is not None:
            return self._save({CONF_CHILD_COLORS: {c: ui.get(f"color__{c}", DEFAULT_COLOR_ORDER[i%len(DEFAULT_COLOR_ORDER)])
                                                    for i,c in enumerate(self._children)}})
        fields = {vol.Optional(f"color__{c}",default=self._child_colors.get(c,DEFAULT_COLOR_ORDER[i%len(DEFAULT_COLOR_ORDER)])): vol.In(list(CHILD_COLOR_OPTIONS.keys()))
                  for i,c in enumerate(self._children)}
        return self.async_show_form(step_id="edit_colors", data_schema=vol.Schema(fields))

    async def async_step_edit_rotation_tasks(self, ui=None):
        if ui is not None:
            sel   = [t for t in DEFAULT_ROTATION_TASKS if ui.get(f"rot__{t}",False)]
            extra = [t.strip() for t in ui.get("rot__extra","").split(",") if t.strip()]
            ee    = [t["name"] for t in self._rotation_tasks if t["name"] not in DEFAULT_ROTATION_TASKS]
            tasks = sel + [t for t in (extra if extra else ee) if t not in sel]
            volgorde = [c.strip() for c in ui.get("rot__volgorde","").split(",") if c.strip() in self._children] or self._children
            return self._save({CONF_ROTATION_TASKS: [{"name":t,"fixed_child":None,"children_order":volgorde} for t in tasks]})
        cur_extra = [t["name"] for t in self._rotation_tasks if t["name"] not in DEFAULT_ROTATION_TASKS]
        cur_vol   = (self._rotation_tasks[0].get("children_order") or self._children) if self._rotation_tasks else self._children
        fields = {vol.Optional(f"rot__{t}",default=any(x["name"]==t for x in self._rotation_tasks)): bool for t in DEFAULT_ROTATION_TASKS}
        fields[vol.Optional("rot__extra",   default=", ".join(cur_extra))] = str
        fields[vol.Optional("rot__volgorde",default=", ".join(cur_vol))]   = str
        return self.async_show_form(step_id="edit_rotation_tasks", data_schema=vol.Schema(fields))

    async def async_step_edit_week_tasks(self, ui=None):
        mode_map = {"Vast kind":"fixed","Even weken":"even","Oneven weken":"odd","Automatisch roteren":"auto_rotate"}
        rev_map  = {v:k for k,v in mode_map.items()}
        if ui is not None:
            sel   = [t for t in DEFAULT_WEEK_TASKS if ui.get(f"wk__{t}",False)]
            extra = [t.strip() for t in ui.get("wk__extra","").split(",") if t.strip()]
            ee    = [t["name"] for t in self._week_tasks if t["name"] not in DEFAULT_WEEK_TASKS]
            tasks = sel + [t for t in (extra if extra else ee) if t not in sel]
            existing = {t["name"]:t for t in self._week_tasks}
            new_tasks = []
            for t in tasks:
                ex = existing.get(t,{})
                new_tasks.append({"name":t,"day":ui.get(f"wkday__{t}","Woensdag"),
                                   "mode":mode_map.get(ui.get(f"wkmode__{t}","Automatisch roteren"),"auto_rotate"),
                                   "fixed_child":ex.get("fixed_child",self._children[0] if self._children else ""),
                                   "even_child": ex.get("even_child", self._children[0] if self._children else ""),
                                   "odd_child":  ex.get("odd_child",  self._children[1] if len(self._children)>1 else ""),
                                   "children_order":self._children})
            return self._save({CONF_WEEK_TASKS: new_tasks})
        fields = {}
        existing = {t["name"]:t for t in self._week_tasks}
        for t in DEFAULT_WEEK_TASKS:
            ex = existing.get(t,{})
            fields[vol.Optional(f"wk__{t}",   default=(t in existing))]                               = bool
            fields[vol.Optional(f"wkday__{t}",default=ex.get("day","Woensdag"))]                      = vol.In(DAYS_NL)
            fields[vol.Optional(f"wkmode__{t}",default=rev_map.get(ex.get("mode","auto_rotate"),"Automatisch roteren"))] = vol.In(WEEK_MODES)
        fields[vol.Optional("wk__extra",default=", ".join([t["name"] for t in self._week_tasks if t["name"] not in DEFAULT_WEEK_TASKS]))] = str
        return self.async_show_form(step_id="edit_week_tasks", data_schema=vol.Schema(fields))

    async def async_step_edit_month_tasks(self, ui=None):
        if ui is not None:
            sel   = [t for t in DEFAULT_MONTH_TASKS if ui.get(f"mt__{t}",False)]
            extra = [t.strip() for t in ui.get("mt__extra","").split(",") if t.strip()]
            ee    = [t["name"] for t in self._month_tasks if t["name"] not in DEFAULT_MONTH_TASKS]
            tasks = sel + [t for t in (extra if extra else ee) if t not in sel]
            existing = {t["name"]:t for t in self._month_tasks}
            return self._save({CONF_MONTH_TASKS: [{"name":t,"all_children":True,
                                                    "week_of_month":ui.get(f"mtwk__{t}","Laatste week"),
                                                    "day_of_week":  ui.get(f"mtday__{t}","Zondag"),
                                                    "assignments":{}} for t in tasks]})
        fields = {}
        existing = {t["name"]:t for t in self._month_tasks}
        for t in DEFAULT_MONTH_TASKS:
            ex = existing.get(t,{})
            fields[vol.Optional(f"mt__{t}",  default=(t in existing))]                           = bool
            fields[vol.Optional(f"mtwk__{t}",default=ex.get("week_of_month","Laatste week"))]    = vol.In(WEEK_OF_MONTH_OPTIONS)
            fields[vol.Optional(f"mtday__{t}",default=ex.get("day_of_week","Zondag"))]           = vol.In(DAYS_NL)
        fields[vol.Optional("mt__extra",default=", ".join([t["name"] for t in self._month_tasks if t["name"] not in DEFAULT_MONTH_TASKS]))] = str
        return self.async_show_form(step_id="edit_month_tasks", data_schema=vol.Schema(fields))
