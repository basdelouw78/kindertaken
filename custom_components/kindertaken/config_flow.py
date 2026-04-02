"""
Config flow v3.1 — twee stappen per kind, conditionele vervolgvragen.

Stap A per kind: naam + kleur + aanwezigheidspatroon kiezen
Stap B per kind: alleen de velden die bij dat patroon horen

Wizard volgorde:
  1. user         → namen invoeren
  2. child_N_a    → kind N: kleur + patroon
  3. child_N_b    → kind N: vervolgvragen (alleen relevant voor gekozen patroon)
  4. (herhaal 2-3 voor elk kind)
  5. rotation_tasks
  6. week_tasks
  7. month_tasks
"""
from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN, CONF_CHILDREN, CONF_CHILD_COLORS, CONF_CHILD_PRESENCE,
    CONF_ROTATION_TASKS, CONF_WEEK_TASKS, CONF_MONTH_TASKS,
    DEFAULT_ROTATION_TASKS, DEFAULT_WEEK_TASKS, DEFAULT_MONTH_TASKS,
    DAYS_NL, WEEK_OF_MONTH_OPTIONS,
    CHILD_COLOR_OPTIONS, DEFAULT_COLOR_ORDER,
)

# ── Constanten ────────────────────────────────────────────────────────────────

WEEK_MODES = ["Automatisch roteren", "Even weken", "Oneven weken", "Vast kind"]
MODE_MAP   = {"Automatisch roteren":"auto_rotate","Even weken":"even","Oneven weken":"odd","Vast kind":"fixed"}
MODE_RMAP  = {v:k for k,v in MODE_MAP.items()}

PRESENCE_CHOICES = [
    "🏠  Altijd thuis",
    "🔄  Om de week (co-ouderschap)",
    "📅  Vaste dagen per week (bijv. elk weekend)",
    "🗓️  Bepaalde weken per maand (bijv. 1e en 3e week)",
    "🔄📅  Om de week + alleen op vaste dagen",
]
PRESENCE_TO_MODE = {
    "🏠  Altijd thuis":                         "altijd",
    "🔄  Om de week (co-ouderschap)":           "om_de_week",
    "📅  Vaste dagen per week (bijv. elk weekend)":"vaste_dagen",
    "🗓️  Bepaalde weken per maand (bijv. 1e en 3e week)":"weken_per_maand",
    "🔄📅  Om de week + alleen op vaste dagen": "combinatie",
}
MODE_TO_PRESENCE = {v:k for k,v in PRESENCE_TO_MODE.items()}

COLORS_WITH_EMOJI = {
    f"⭐  Blauw":   "Blauw",
    f"🌟  Groen":   "Groen",
    f"🎯  Oranje":  "Oranje",
    f"🌈  Roze":    "Roze",
    f"🦋  Paars":   "Paars",
    f"🚀  Teal":    "Teal",
    f"🏆  Indigo":  "Indigo",
    f"💎  Rood":    "Rood",
    f"🌻  Geel":    "Geel",
    f"🌊  Cyaan":   "Cyaan",
}
COLOR_LABEL_TO_KEY = COLORS_WITH_EMOJI  # label → intern kleur-key
COLOR_KEY_TO_LABEL = {v:k for k,v in COLORS_WITH_EMOJI.items()}

DAYS_CHECK = ["Maandag","Dinsdag","Woensdag","Donderdag","Vrijdag","Zaterdag","Zondag"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _color_label(key: str) -> str:
    return COLOR_KEY_TO_LABEL.get(key, f"⭐  {key}")

def _color_key(label: str) -> str:
    return COLOR_LABEL_TO_KEY.get(label, label.split("  ")[-1] if "  " in label else label)

def _default_color(idx: int, child_colors: dict, child: str) -> str:
    cur = child_colors.get(child)
    return _color_label(cur) if cur else _color_label(DEFAULT_COLOR_ORDER[idx % len(DEFAULT_COLOR_ORDER)])


# ── Hoofd config flow ─────────────────────────────────────────────────────────

class KindertakenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 6

    def __init__(self):
        self._children       = []
        self._child_idx      = 0
        self._child_colors   = {}
        self._child_presence = {}
        self._pending_mode   = {}   # tijdelijk: gekozen patroon per kind
        self._rotation_tasks = []
        self._week_tasks     = []
        self._month_tasks    = []

    # ── Stap 1: Namen ─────────────────────────────────────────────────────────
    async def async_step_user(self, ui=None):
        errors = {}
        if ui is not None:
            ch = [c.strip() for c in ui.get("children","").split(",") if c.strip()]
            if not ch:        errors["children"] = "min_one_child"
            elif len(ch) > 8: errors["children"] = "max_eight_children"
            else:
                self._children  = ch
                self._child_idx = 0
                return await self.async_step_child_a()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("children"): str}),
            errors=errors,
            description_placeholders={
                "example": "Emma, Liam, Sophie",
                "uitleg": "Voer de namen in, gescheiden door komma's.",
            },
        )

    # ── Stap 2A per kind: kleur + patroon ─────────────────────────────────────
    async def async_step_child_a(self, ui=None):
        child = self._children[self._child_idx]
        n     = self._child_idx + 1
        total = len(self._children)

        if ui is not None:
            self._child_colors[child]  = _color_key(ui.get("kleur", _color_label(DEFAULT_COLOR_ORDER[self._child_idx % len(DEFAULT_COLOR_ORDER)])))
            self._pending_mode[child]  = ui.get("patroon", "🏠  Altijd thuis")
            # Als het patroon geen vervolgvragen heeft → direct door
            mode = PRESENCE_TO_MODE.get(self._pending_mode[child], "altijd")
            if mode == "altijd":
                self._child_presence[child] = {
                    "mode":"altijd","start_date":"","start_present":True,
                    "days_present":[],"weeks_present":[],"blocked_days":[],"override_present":None,
                }
                return await self._next_child_or_tasks()
            return await self.async_step_child_b()

        default_kleur = _default_color(self._child_idx, self._child_colors, child)
        return self.async_show_form(
            step_id="child_a",
            data_schema=vol.Schema({
                vol.Optional("kleur",   default=default_kleur):                  vol.In(list(COLORS_WITH_EMOJI.keys())),
                vol.Optional("patroon", default="🔄  Om de week (co-ouderschap)"): vol.In(PRESENCE_CHOICES),
            }),
            description_placeholders={
                "kind":  child,
                "n":     str(n),
                "total": str(total),
                "uitleg": (
                    f"Stel {child} in  ({n}/{total})\n\n"
                    "KLEUR  →  Kies een herkenbare kleur voor het dashboard.\n\n"
                    "AANWEZIGHEIDSPATROON  →  Kies hoe {kind} bij jou is:\n"
                    "🏠  Altijd thuis            → woont altijd bij jou, geen co-ouderschap\n"
                    "🔄  Om de week              → week A bij jou, week B bij andere ouder\n"
                    "📅  Vaste dagen per week    → bijv. elk weekend (vr/za/zo) bij jou\n"
                    "🗓️  Bepaalde weken per maand → bijv. 1e en 3e week bij jou\n"
                    "🔄📅  Combinatie             → om de week + alleen op vaste dagen"
                ).replace("{kind}", child),
            },
        )

    # ── Stap 2B per kind: vervolgvragen op basis van patroon ──────────────────
    async def async_step_child_b(self, ui=None):
        child = self._children[self._child_idx]
        n     = self._child_idx + 1
        total = len(self._children)
        mode_label = self._pending_mode.get(child, "🔄  Om de week (co-ouderschap)")
        mode       = PRESENCE_TO_MODE.get(mode_label, "om_de_week")
        cur        = self._child_presence.get(child, {})

        if ui is not None:
            # Verwerk invoer op basis van gekozen modus
            days_present  = [i for i in range(7) if ui.get(f"dag_{i}", False)]
            weeks_present_raw = [str(i+1) for i in range(4) if ui.get(f"week_{i}", False)]
            if ui.get("week_laatste", False): weeks_present_raw.append("laatste")
            weeks_present = [int(w) if w != "laatste" else "laatste" for w in weeks_present_raw]
            blocked_days  = [{"day":i,"reason":"geblokkeerd"} for i in range(7) if ui.get(f"blok_{i}", False)]

            self._child_presence[child] = {
                "mode":          mode,
                "start_date":    ui.get("startdatum", "2024-01-06"),
                "start_present": ui.get("startweek_aanwezig", True),
                "days_present":  days_present,
                "weeks_present": weeks_present,
                "blocked_days":  blocked_days,
                "override_present": None,
            }
            return await self._next_child_or_tasks()

        # Bouw schema op basis van patroon
        fields = {}
        desc_lines = [f"Instellingen voor {child}  ({n}/{total}) — vervolg\n"]

        # ── Om de week ──
        if mode in ("om_de_week", "combinatie"):
            fields[vol.Optional("startdatum",        default=cur.get("start_date","2024-01-06"))] = str
            fields[vol.Optional("startweek_aanwezig",default=cur.get("start_present",True))]      = bool
            desc_lines += [
                "OM DE WEEK",
                "• Startdatum → vul de datum in van de eerste MAANDAG van een week dat",
                f"  {child} bij jou is. Formaat: JJJJ-MM-DD  (bijv. 2025-01-06)",
                f"• '{child} is aanwezig in de startweek' → vink aan als {child} er",
                "  die startweek al is; laat uit als de week daarna pas begint.\n",
            ]

        # ── Vaste dagen ──
        if mode in ("vaste_dagen", "combinatie"):
            cur_days = set(cur.get("days_present", []))
            for i, dag in enumerate(DAYS_CHECK):
                fields[vol.Optional(f"dag_{i}", default=(i in cur_days))] = bool
            desc_lines += [
                "AANWEZIGE DAGEN",
                f"• Vink aan op welke dagen {child} bij jou is.",
                "  Voorbeeld co-ouderschap elk weekend: vink Vrijdag, Zaterdag, Zondag aan.\n",
            ]

        # ── Weken per maand ──
        if mode == "weken_per_maand":
            cur_weeks = set(str(w) for w in cur.get("weeks_present", []))
            for i in range(4):
                fields[vol.Optional(f"week_{i}", default=(str(i+1) in cur_weeks))] = bool
            fields[vol.Optional("week_laatste", default=("laatste" in cur_weeks))] = bool
            desc_lines += [
                "AANWEZIGE WEKEN",
                f"• Vink aan in welke weken van de maand {child} bij jou is.",
                "  Voorbeeld: vink '1e week' en '3e week' aan.\n",
            ]

        # ── Blokdagen (altijd tonen) ──
        cur_blocked = {(b if isinstance(b,int) else b.get("day",-1)) for b in cur.get("blocked_days",[])}
        for i, dag in enumerate(DAYS_CHECK):
            fields[vol.Optional(f"blok_{i}", default=(i in cur_blocked))] = bool
        desc_lines += [
            "GEBLOKKEERDE DAGEN",
            f"• Vink dagen aan waarop {child} WEL thuis is maar GEEN taken kan doen.",
            "  Bijv. maandag school, donderdag sport.",
            "  Taken die op die dag zouden vallen, gaan dan automatisch naar een ander kind.",
        ]

        return self.async_show_form(
            step_id="child_b",
            data_schema=vol.Schema(fields),
            description_placeholders={"uitleg": "\n".join(desc_lines), "kind": child},
        )

    async def _next_child_or_tasks(self):
        self._child_idx += 1
        if self._child_idx < len(self._children):
            return await self.async_step_child_a()
        return await self.async_step_rotation_tasks()

    # ── Rotatietaken ──────────────────────────────────────────────────────────
    async def async_step_rotation_tasks(self, ui=None):
        if ui is not None:
            sel   = [t for t in DEFAULT_ROTATION_TASKS if ui.get(f"rot_{t}", False)]
            extra = [t.strip() for t in ui.get("rot_extra","").split(",") if t.strip()]
            tasks = sel + [t for t in extra if t not in sel]
            volgorde = [c.strip() for c in ui.get("rot_volgorde","").split(",")
                        if c.strip() in self._children] or self._children
            self._rotation_tasks = [{"name":t,"fixed_child":None,"children_order":volgorde} for t in tasks]
            return await self.async_step_week_tasks()

        fields = {vol.Optional(f"rot_{t}", default=True): bool for t in DEFAULT_ROTATION_TASKS}
        fields[vol.Optional("rot_extra",   default="")] = str
        fields[vol.Optional("rot_volgorde",default=", ".join(self._children))] = str
        return self.async_show_form(
            step_id="rotation_tasks",
            data_schema=vol.Schema(fields),
            description_placeholders={"uitleg": (
                "DAGELIJKSE ROTATIETAKEN\n\n"
                "Deze taken komen elke dag terug en wisselen automatisch per kind.\n"
                "Het systeem berekent dagelijks wie aan de beurt is.\n"
                "Is een kind er niet of heeft het een blokdag? Dan pakt het volgende kind het over.\n\n"
                "VOLGORDE  →  Bepaalt de rotatievolgorde. Standaard: " + ", ".join(self._children) + ".\n"
                "Pas aan als je een andere volgorde wilt (bijv. oudste eerst).\n\n"
                "EXTRA TAKEN  →  Eigen taken toevoegen, komma-gescheiden."
            )},
        )

    # ── Weektaken ─────────────────────────────────────────────────────────────
    async def async_step_week_tasks(self, ui=None):
        if ui is not None:
            sel   = [t for t in DEFAULT_WEEK_TASKS if ui.get(f"wk_{t}", False)]
            extra = [t.strip() for t in ui.get("wk_extra","").split(",") if t.strip()]
            tasks = sel + [t for t in extra if t not in sel]
            ch0 = self._children[0] if self._children else ""
            ch1 = self._children[1] if len(self._children) > 1 else ch0
            self._week_tasks = [{
                "name": t,
                "day":  ui.get(f"wkdag_{t}","Woensdag"),
                "mode": MODE_MAP.get(ui.get(f"wkmodus_{t}","Automatisch roteren"),"auto_rotate"),
                "fixed_child": ch0, "even_child": ch0, "odd_child": ch1,
                "children_order": self._children,
            } for t in tasks]
            return await self.async_step_month_tasks()

        fields = {}
        for t in DEFAULT_WEEK_TASKS:
            fields[vol.Optional(f"wk_{t}",     default=False)]               = bool
            fields[vol.Optional(f"wkdag_{t}",  default="Woensdag")]          = vol.In(DAYS_NL)
            fields[vol.Optional(f"wkmodus_{t}",default="Automatisch roteren")] = vol.In(WEEK_MODES)
        fields[vol.Optional("wk_extra", default="")] = str
        return self.async_show_form(
            step_id="week_tasks",
            data_schema=vol.Schema(fields),
            description_placeholders={"uitleg": (
                "WEKELIJKSE TAKEN\n\n"
                "Taken die één keer per week terugkomen op een vaste dag.\n\n"
                "Per taak stel je in:\n"
                "• DAG  →  op welke dag de taak gedaan wordt\n"
                "• MODUS:\n"
                "  – Automatisch roteren    → systeem wisselt wekelijks wie het doet\n"
                "  – Even weken             → handig bij co-ouderschap (week A)\n"
                "  – Oneven weken           → co-ouderschap (week B)\n"
                "  – Vast kind              → altijd hetzelfde kind\n\n"
                "Is het aangewezen kind er niet? Dan pakt het kind met de minste taken\n"
                "die dag automatisch de taak over."
            )},
        )

    # ── Maandtaken ────────────────────────────────────────────────────────────
    async def async_step_month_tasks(self, ui=None):
        if ui is not None:
            sel   = [t for t in DEFAULT_MONTH_TASKS if ui.get(f"mt_{t}", False)]
            extra = [t.strip() for t in ui.get("mt_extra","").split(",") if t.strip()]
            tasks = sel + [t for t in extra if t not in sel]
            self._month_tasks = [{
                "name": t, "all_children": True,
                "week_of_month": ui.get(f"mtwk_{t}","Laatste week"),
                "day_of_week":   ui.get(f"mtdag_{t}","Zondag"),
                "assignments": {},
            } for t in tasks]
            return self.async_create_entry(
                title="Kindertaken Planner",
                data={
                    CONF_CHILDREN:       self._children,
                    CONF_CHILD_COLORS:   self._child_colors,
                    CONF_CHILD_PRESENCE: self._child_presence,
                    CONF_ROTATION_TASKS: self._rotation_tasks,
                    CONF_WEEK_TASKS:     self._week_tasks,
                    CONF_MONTH_TASKS:    self._month_tasks,
                },
            )

        fields = {}
        for t in DEFAULT_MONTH_TASKS:
            fields[vol.Optional(f"mt_{t}",  default=True)]           = bool
            fields[vol.Optional(f"mtwk_{t}",default="Laatste week")] = vol.In(WEEK_OF_MONTH_OPTIONS)
            fields[vol.Optional(f"mtdag_{t}",default="Zondag")]      = vol.In(DAYS_NL)
        fields[vol.Optional("mt_extra", default="")] = str
        return self.async_show_form(
            step_id="month_tasks",
            data_schema=vol.Schema(fields),
            description_placeholders={"uitleg": (
                "MAANDTAKEN\n\n"
                "Taken die één keer per maand terugkomen.\n"
                "Alle kinderen die er die dag zijn, doen de taak.\n\n"
                "Per taak stel je in:\n"
                "• WEEK  →  welke week van de maand (1e t/m 4e, of laatste week)\n"
                "• DAG   →  welke dag van die week (bijv. Zondag)\n\n"
                "Het systeem berekent automatisch de exacte datum.\n"
                "Is een kind er niet op de geplande dag?\n"
                "Dan verschuift de taak naar de eerstvolgende dag dat het kind er wél is."
            )},
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry):
        return KindertakenOptionsFlow(entry)


# ── Options flow ──────────────────────────────────────────────────────────────

class KindertakenOptionsFlow(config_entries.OptionsFlow):

    def __init__(self, entry):
        self._entry          = entry
        d                    = entry.data
        self._children       = list(d.get(CONF_CHILDREN,[]))
        self._child_colors   = dict(d.get(CONF_CHILD_COLORS,{}))
        self._child_presence = dict(d.get(CONF_CHILD_PRESENCE,{}))
        self._rotation_tasks = list(d.get(CONF_ROTATION_TASKS,[]))
        self._week_tasks     = list(d.get(CONF_WEEK_TASKS,[]))
        self._month_tasks    = list(d.get(CONF_MONTH_TASKS,[]))
        self._edit_child     = None
        self._pending_mode   = {}

    def _save(self, updates):
        new = dict(self._entry.data)
        new.update(updates)
        return self.async_create_entry(title="", data=new)

    async def async_step_init(self, ui=None):
        return self.async_show_menu(step_id="init", menu_options=[
            "edit_children",
            "edit_child_settings",
            "edit_rotation_tasks",
            "edit_week_tasks",
            "edit_month_tasks",
        ])

    # ── Kinderen ──────────────────────────────────────────────────────────────
    async def async_step_edit_children(self, ui=None):
        errors = {}
        if ui is not None:
            ch = [c.strip() for c in ui.get("children","").split(",") if c.strip()]
            if not ch: errors["children"] = "min_one_child"
            else: return self._save({CONF_CHILDREN: ch})
        return self.async_show_form(
            step_id="edit_children",
            data_schema=vol.Schema({vol.Required("children",default=", ".join(self._children)): str}),
            description_placeholders={"uitleg":"Namen komma-gescheiden. Verwijder je een naam, dan valt dat kind weg uit de planning."},
            errors=errors,
        )

    # ── Kind-instellingen: kies kind ──────────────────────────────────────────
    async def async_step_edit_child_settings(self, ui=None):
        if ui is not None:
            self._edit_child = ui.get("kind","")
            return await self.async_step_edit_child_a()
        return self.async_show_form(
            step_id="edit_child_settings",
            data_schema=vol.Schema({vol.Required("kind"): vol.In(self._children)}),
            description_placeholders={"uitleg":"Kies het kind waarvan je de instellingen wil wijzigen."},
        )

    async def async_step_edit_child_a(self, ui=None):
        child = self._edit_child
        idx   = self._children.index(child) if child in self._children else 0
        if ui is not None:
            self._child_colors[child]  = _color_key(ui.get("kleur", _color_label(DEFAULT_COLOR_ORDER[idx % len(DEFAULT_COLOR_ORDER)])))
            self._pending_mode[child]  = ui.get("patroon","🏠  Altijd thuis")
            mode = PRESENCE_TO_MODE.get(self._pending_mode[child],"altijd")
            if mode == "altijd":
                pres = dict(self._child_presence.get(child,{}))
                pres.update({"mode":"altijd","start_date":"","start_present":True,
                              "days_present":[],"weeks_present":[],"blocked_days":[],"override_present":None})
                self._child_presence[child] = pres
                return self._save({CONF_CHILD_COLORS:self._child_colors,CONF_CHILD_PRESENCE:self._child_presence})
            return await self.async_step_edit_child_b()

        cur_pres  = self._child_presence.get(child,{})
        cur_mode  = MODE_TO_PRESENCE.get(cur_pres.get("mode","altijd"),"🏠  Altijd thuis")
        cur_kleur = _default_color(idx, self._child_colors, child)
        return self.async_show_form(
            step_id="edit_child_a",
            data_schema=vol.Schema({
                vol.Optional("kleur",   default=cur_kleur): vol.In(list(COLORS_WITH_EMOJI.keys())),
                vol.Optional("patroon", default=cur_mode):  vol.In(PRESENCE_CHOICES),
            }),
            description_placeholders={
                "uitleg": (
                    f"Instellingen voor {child}  —  stap 1 van 2\n\n"
                    "KLEUR  →  Hoe dit kind verschijnt op het dashboard.\n\n"
                    "AANWEZIGHEIDSPATROON:\n"
                    "🏠  Altijd thuis                → woont altijd bij jou\n"
                    "🔄  Om de week                  → week A bij jou, week B elders\n"
                    "📅  Vaste dagen per week        → bijv. elk weekend\n"
                    "🗓️  Bepaalde weken per maand    → bijv. 1e en 3e week\n"
                    "🔄📅  Combinatie                → om de week + vaste dagen"
                ),
                "kind": child,
            },
        )

    async def async_step_edit_child_b(self, ui=None):
        child      = self._edit_child
        mode_label = self._pending_mode.get(child,"🔄  Om de week (co-ouderschap)")
        mode       = PRESENCE_TO_MODE.get(mode_label,"om_de_week")
        cur        = self._child_presence.get(child,{})

        if ui is not None:
            days_present  = [i for i in range(7) if ui.get(f"dag_{i}",False)]
            weeks_raw     = [str(i+1) for i in range(4) if ui.get(f"week_{i}",False)]
            if ui.get("week_laatste",False): weeks_raw.append("laatste")
            weeks_present = [int(w) if w!="laatste" else "laatste" for w in weeks_raw]
            blocked_days  = [{"day":i,"reason":"geblokkeerd"} for i in range(7) if ui.get(f"blok_{i}",False)]
            self._child_presence[child] = {
                "mode":mode,"start_date":ui.get("startdatum","2024-01-06"),
                "start_present":ui.get("startweek_aanwezig",True),
                "days_present":days_present,"weeks_present":weeks_present,
                "blocked_days":blocked_days,"override_present":None,
            }
            return self._save({CONF_CHILD_COLORS:self._child_colors,CONF_CHILD_PRESENCE:self._child_presence})

        # Zelfde logica als in de hoofd config flow
        fields = {}
        desc_lines = [f"Instellingen voor {child}  —  stap 2 van 2\n"]
        cur_days    = set(cur.get("days_present",[]))
        cur_weeks   = set(str(w) for w in cur.get("weeks_present",[]))
        cur_blocked = {(b if isinstance(b,int) else b.get("day",-1)) for b in cur.get("blocked_days",[])}

        if mode in ("om_de_week","combinatie"):
            fields[vol.Optional("startdatum",        default=cur.get("start_date","2024-01-06"))] = str
            fields[vol.Optional("startweek_aanwezig",default=cur.get("start_present",True))]      = bool
            desc_lines += ["OM DE WEEK",
                           f"• Startdatum  →  eerste MAANDAG van een week dat {child} hier is",
                           "  Formaat: JJJJ-MM-DD  (bijv. 2025-01-06)",
                           f"• Aanwezig in startweek  →  vink aan als {child} er die week al is\n"]

        if mode in ("vaste_dagen","combinatie"):
            for i,dag in enumerate(DAYS_CHECK):
                fields[vol.Optional(f"dag_{i}",default=(i in cur_days))] = bool
            desc_lines += ["AANWEZIGE DAGEN  →  vink aan op welke dagen het kind bij jou is\n"]

        if mode == "weken_per_maand":
            for i in range(4):
                fields[vol.Optional(f"week_{i}",default=(str(i+1) in cur_weeks))] = bool
            fields[vol.Optional("week_laatste",default=("laatste" in cur_weeks))] = bool
            desc_lines += ["AANWEZIGE WEKEN  →  vink aan in welke weken van de maand\n"]

        for i,dag in enumerate(DAYS_CHECK):
            fields[vol.Optional(f"blok_{i}",default=(i in cur_blocked))] = bool
        desc_lines += ["GEBLOKKEERDE DAGEN  →  kind IS thuis maar heeft GEEN tijd voor taken",
                       "(bijv. maandag werkt Emma, donderdag sport Liam)"]

        return self.async_show_form(
            step_id="edit_child_b",
            data_schema=vol.Schema(fields),
            description_placeholders={"uitleg":"\n".join(desc_lines),"kind":child},
        )

    # ── Taken bewerken ────────────────────────────────────────────────────────
    async def async_step_edit_rotation_tasks(self, ui=None):
        if ui is not None:
            sel   = [t for t in DEFAULT_ROTATION_TASKS if ui.get(f"rot_{t}",False)]
            extra = [t.strip() for t in ui.get("rot_extra","").split(",") if t.strip()]
            ee    = [t["name"] for t in self._rotation_tasks if t["name"] not in DEFAULT_ROTATION_TASKS]
            tasks = sel + [t for t in (extra if extra else ee) if t not in sel]
            volgorde = [c.strip() for c in ui.get("rot_volgorde","").split(",") if c.strip() in self._children] or self._children
            return self._save({CONF_ROTATION_TASKS:[{"name":t,"fixed_child":None,"children_order":volgorde} for t in tasks]})
        cur_vol   = (self._rotation_tasks[0].get("children_order") or self._children) if self._rotation_tasks else self._children
        cur_extra = [t["name"] for t in self._rotation_tasks if t["name"] not in DEFAULT_ROTATION_TASKS]
        fields    = {vol.Optional(f"rot_{t}",default=any(x["name"]==t for x in self._rotation_tasks)):bool for t in DEFAULT_ROTATION_TASKS}
        fields[vol.Optional("rot_extra",   default=", ".join(cur_extra))] = str
        fields[vol.Optional("rot_volgorde",default=", ".join(cur_vol))]   = str
        return self.async_show_form(step_id="edit_rotation_tasks",data_schema=vol.Schema(fields),
            description_placeholders={"uitleg":"Dagelijkse taken die automatisch rouleren.\nVolgorde bepaalt wie wanneer aan de beurt is."})

    async def async_step_edit_week_tasks(self, ui=None):
        if ui is not None:
            sel   = [t for t in DEFAULT_WEEK_TASKS if ui.get(f"wk_{t}",False)]
            extra = [t.strip() for t in ui.get("wk_extra","").split(",") if t.strip()]
            ee    = [t["name"] for t in self._week_tasks if t["name"] not in DEFAULT_WEEK_TASKS]
            tasks = sel + [t for t in (extra if extra else ee) if t not in sel]
            existing = {t["name"]:t for t in self._week_tasks}
            ch0 = self._children[0] if self._children else ""
            ch1 = self._children[1] if len(self._children)>1 else ch0
            result = []
            for t in tasks:
                ex = existing.get(t,{})
                result.append({"name":t,"day":ui.get(f"wkdag_{t}","Woensdag"),
                                "mode":MODE_MAP.get(ui.get(f"wkmodus_{t}","Automatisch roteren"),"auto_rotate"),
                                "fixed_child":ex.get("fixed_child",ch0),"even_child":ex.get("even_child",ch0),"odd_child":ex.get("odd_child",ch1),
                                "children_order":self._children})
            return self._save({CONF_WEEK_TASKS:result})
        existing = {t["name"]:t for t in self._week_tasks}
        fields = {}
        for t in DEFAULT_WEEK_TASKS:
            ex = existing.get(t,{})
            fields[vol.Optional(f"wk_{t}",    default=(t in existing))]                                                   = bool
            fields[vol.Optional(f"wkdag_{t}", default=ex.get("day","Woensdag"))]                                          = vol.In(DAYS_NL)
            fields[vol.Optional(f"wkmodus_{t}",default=MODE_RMAP.get(ex.get("mode","auto_rotate"),"Automatisch roteren"))]= vol.In(WEEK_MODES)
        fields[vol.Optional("wk_extra",default=", ".join([t["name"] for t in self._week_tasks if t["name"] not in DEFAULT_WEEK_TASKS]))] = str
        return self.async_show_form(step_id="edit_week_tasks",data_schema=vol.Schema(fields),
            description_placeholders={"uitleg":"Wekelijkse taken.\nPer taak: dag + modus (auto/even/oneven weken/vast kind)."})

    async def async_step_edit_month_tasks(self, ui=None):
        if ui is not None:
            sel   = [t for t in DEFAULT_MONTH_TASKS if ui.get(f"mt_{t}",False)]
            extra = [t.strip() for t in ui.get("mt_extra","").split(",") if t.strip()]
            ee    = [t["name"] for t in self._month_tasks if t["name"] not in DEFAULT_MONTH_TASKS]
            tasks = sel + [t for t in (extra if extra else ee) if t not in sel]
            existing = {t["name"]:t for t in self._month_tasks}
            return self._save({CONF_MONTH_TASKS:[{"name":t,"all_children":True,
                "week_of_month":ui.get(f"mtwk_{t}","Laatste week"),"day_of_week":ui.get(f"mtdag_{t}","Zondag"),"assignments":{}} for t in tasks]})
        existing = {t["name"]:t for t in self._month_tasks}
        fields = {}
        for t in DEFAULT_MONTH_TASKS:
            ex = existing.get(t,{})
            fields[vol.Optional(f"mt_{t}",  default=(t in existing))]                        = bool
            fields[vol.Optional(f"mtwk_{t}",default=ex.get("week_of_month","Laatste week"))] = vol.In(WEEK_OF_MONTH_OPTIONS)
            fields[vol.Optional(f"mtdag_{t}",default=ex.get("day_of_week","Zondag"))]        = vol.In(DAYS_NL)
        fields[vol.Optional("mt_extra",default=", ".join([t["name"] for t in self._month_tasks if t["name"] not in DEFAULT_MONTH_TASKS]))] = str
        return self.async_show_form(step_id="edit_month_tasks",data_schema=vol.Schema(fields),
            description_placeholders={"uitleg":"Maandelijkse taken. Per taak: welke week van de maand + welke dag."})
