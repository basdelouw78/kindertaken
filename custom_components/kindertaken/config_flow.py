"""
Kindertaken config flow v4.4
- Geen vaste taken meer — alles vrij invoeren als komma-gescheiden tekst
- Weektaken: naam, dag en modus per taak als losse regels
- Maandtaken: naam, week en dag per taak als losse regels
"""
from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_CHILDREN, CONF_CHILD_COLORS, CONF_CHILD_PRESENCE,
    CONF_ROTATION_TASKS, CONF_WEEK_TASKS, CONF_MONTH_TASKS,
    CHILD_COLOR_OPTIONS, DEFAULT_COLOR_ORDER,
)

LANG_OPTIONS = {
    "🇳🇱  Nederlands": "nl",
    "🇬🇧  English":    "en",
    "🇩🇪  Deutsch":    "de",
    "🇫🇷  Français":   "fr",
}

T = {
    "nl": {
        "presence": [
            "🏠  Altijd thuis",
            "🔄  Om de week (co-ouderschap)",
            "📅  Vaste dagen per week",
            "🗓️  Bepaalde weken per maand",
            "🔄📅  Om de week + vaste dagen",
        ],
        "presence_modes": ["altijd","om_de_week","vaste_dagen","weken_per_maand","combinatie"],
        "week_modes": ["Automatisch roteren","Even weken","Oneven weken","Vast kind"],
        "week_mode_keys": ["auto_rotate","even","odd","fixed"],
        "days": ["Maandag","Dinsdag","Woensdag","Donderdag","Vrijdag","Zaterdag","Zondag"],
        "month_weeks": ["1e week","2e week","3e week","4e week","Laatste week"],
        "month_week_keys": ["1e week","2e week","3e week","4e week","Laatste week"],
        "colors": {
            "⭐  Blauw":"Blauw","🌟  Groen":"Groen","🎯  Oranje":"Oranje","🌈  Roze":"Roze",
            "🦋  Paars":"Paars","🚀  Teal":"Teal","🏆  Indigo":"Indigo","💎  Rood":"Rood",
            "🌻  Geel":"Geel","🌊  Cyaan":"Cyaan",
        },
        "desc_pattern": (
            "Kies het aanwezigheidspatroon:\n\n"
            "🏠  Altijd thuis          → woont altijd bij jou\n"
            "🔄  Om de week            → week A bij jou, week B bij andere ouder\n"
            "📅  Vaste dagen           → bijv. elk weekend (vr/za/zo)\n"
            "🗓️  Bepaalde weken        → bijv. 1e en 3e week van de maand\n"
            "🔄📅  Combinatie          → om de week én alleen op vaste dagen"
        ),
        "desc_omdeweek": (
            "OM DE WEEK\n"
            "Startdatum → eerste MAANDAG van een week dat {kind} bij jou is.\n"
            "Formaat: JJJJ-MM-DD  (bijv. 2025-01-06)\n"
            "Aanwezig in startweek → vink aan als {kind} die startweek al hier is."
        ),
        "desc_vastedagen": (
            "AANWEZIGE DAGEN\n"
            "Vink aan op welke dagen {kind} bij jou is.\n"
            "Voorbeeld elk weekend: vink Vrijdag, Zaterdag en Zondag aan."
        ),
        "desc_wekenpermaand": (
            "AANWEZIGE WEKEN\n"
            "Vink aan in welke weken van de maand {kind} bij jou is."
        ),
        "desc_blok": (
            "GEEN TIJD VOOR TAKEN\n"
            "Vink dagen aan waarop {kind} WEL thuis is maar GEEN taken kan doen.\n"
            "Taken gaan die dag automatisch naar een ander kind."
        ),
        "rotation_desc": (
            "Taken die elke dag terugkomen en automatisch rouleren.\n"
            "Het systeem berekent dagelijks wie aan de beurt is.\n\n"
            "Vul de taaknamen in, gescheiden door komma's.\n"
            "Voorbeeld: Afwasmachine vullen, Tafel dekken\n\n"
            "VOLGORDE → bepaalt de rotatievolgorde. Standaard: {children}."
        ),
        "week_desc": (
            "Taken die één keer per week terugkomen op een vaste dag.\n\n"
            "Vul de taaknamen in, gescheiden door komma's.\n"
            "Voorbeeld: Stofzuigen, Vuilnis buiten\n\n"
            "DAG → op welke dag (geldt voor alle taken hierboven)\n"
            "VERDELING:\n"
            "  – Automatisch roteren → wisselt elke week\n"
            "  – Even weken → week A (co-ouderschap)\n"
            "  – Oneven weken → week B\n"
            "  – Vast kind → altijd hetzelfde kind\n\n"
            "Wil je per taak een andere dag/verdeling? Pas dit later aan via\n"
            "Instellingen → Kindertaken → Configureren → Wekelijkse taken."
        ),
        "month_desc": (
            "Taken die één keer per maand terugkomen.\n\n"
            "Vul de taaknamen in, gescheiden door komma's.\n"
            "Voorbeeld: Kamer opruimen, Ramen lappen, Badkamer schoonmaken\n\n"
            "WEEK → welke week van de maand (geldt voor alle taken hierboven)\n"
            "DAG → welke dag van die week\n\n"
            "Wil je per taak een andere week/dag? Pas dit later aan via\n"
            "Instellingen → Kindertaken → Configureren → Maandtaken."
        ),
        "samen_label": "Alle kinderen zijn altijd tegelijk thuis",
    },
    "en": {
        "presence": [
            "🏠  Always home",
            "🔄  Alternate weeks (co-parenting)",
            "📅  Fixed days per week",
            "🗓️  Specific weeks per month",
            "🔄📅  Alternate weeks + fixed days",
        ],
        "presence_modes": ["altijd","om_de_week","vaste_dagen","weken_per_maand","combinatie"],
        "week_modes": ["Auto rotate","Even weeks","Odd weeks","Fixed child"],
        "week_mode_keys": ["auto_rotate","even","odd","fixed"],
        "days": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
        "month_weeks": ["1st week","2nd week","3rd week","4th week","Last week"],
        "month_week_keys": ["1e week","2e week","3e week","4e week","Laatste week"],
        "colors": {
            "⭐  Blue":"Blauw","🌟  Green":"Groen","🎯  Orange":"Oranje","🌈  Pink":"Roze",
            "🦋  Purple":"Paars","🚀  Teal":"Teal","🏆  Indigo":"Indigo","💎  Red":"Rood",
            "🌻  Yellow":"Geel","🌊  Cyan":"Cyaan",
        },
        "desc_pattern": (
            "Choose the presence pattern:\n\n"
            "🏠  Always home       → lives with you full time\n"
            "🔄  Alternate weeks   → week A here, week B with other parent\n"
            "📅  Fixed days        → e.g. every weekend (fri/sat/sun)\n"
            "🗓️  Specific weeks    → e.g. 1st and 3rd week of the month\n"
            "🔄📅  Combination     → alternate weeks AND fixed days only"
        ),
        "desc_omdeweek": (
            "ALTERNATE WEEKS\n"
            "Start date → first MONDAY of a week when {kind} is here.\n"
            "Format: YYYY-MM-DD  (e.g. 2025-01-06)\n"
            "Present in start week → check if {kind} is already here that week."
        ),
        "desc_vastedagen": (
            "FIXED PRESENT DAYS\n"
            "Check which days {kind} is at your home.\n"
            "Example every weekend: check Friday, Saturday and Sunday."
        ),
        "desc_wekenpermaand": (
            "PRESENT WEEKS\n"
            "Check which weeks of the month {kind} is at your home."
        ),
        "desc_blok": (
            "NO TIME FOR TASKS\n"
            "Check days when {kind} IS home but has NO time for tasks.\n"
            "Tasks automatically go to another child on those days."
        ),
        "rotation_desc": (
            "Tasks that recur every day and rotate automatically.\n"
            "The system calculates daily who is next.\n\n"
            "Enter task names separated by commas.\n"
            "Example: Load dishwasher, Set table\n\n"
            "ORDER → determines the rotation sequence. Default: {children}."
        ),
        "week_desc": (
            "Tasks that recur once a week on a fixed day.\n\n"
            "Enter task names separated by commas.\n"
            "Example: Vacuum, Take out bins\n\n"
            "DAY → which day (applies to all tasks above)\n"
            "DISTRIBUTION:\n"
            "  – Auto rotate → changes weekly\n"
            "  – Even weeks → week A (co-parenting)\n"
            "  – Odd weeks → week B\n"
            "  – Fixed child → always the same child\n\n"
            "Want a different day/mode per task? Adjust later via\n"
            "Settings → Kindertaken → Configure → Weekly tasks."
        ),
        "month_desc": (
            "Tasks that recur once a month.\n\n"
            "Enter task names separated by commas.\n"
            "Example: Tidy room, Clean windows, Clean bathroom\n\n"
            "WEEK → which week of the month (applies to all tasks above)\n"
            "DAY → which day of that week\n\n"
            "Want a different week/day per task? Adjust later via\n"
            "Settings → Kindertaken → Configure → Monthly tasks."
        ),
        "samen_label": "All children are always home at the same time",
    },
    "de": {
        "presence": [
            "🏠  Immer zuhause",
            "🔄  Jede zweite Woche (Co-Elternschaft)",
            "📅  Feste Wochentage",
            "🗓️  Bestimmte Wochen im Monat",
            "🔄📅  Jede zweite Woche + feste Tage",
        ],
        "presence_modes": ["altijd","om_de_week","vaste_dagen","weken_per_maand","combinatie"],
        "week_modes": ["Automatisch rotieren","Gerade Wochen","Ungerade Wochen","Festes Kind"],
        "week_mode_keys": ["auto_rotate","even","odd","fixed"],
        "days": ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"],
        "month_weeks": ["1. Woche","2. Woche","3. Woche","4. Woche","Letzte Woche"],
        "month_week_keys": ["1e week","2e week","3e week","4e week","Laatste week"],
        "colors": {
            "⭐  Blau":"Blauw","🌟  Grün":"Groen","🎯  Orange":"Oranje","🌈  Rosa":"Roze",
            "🦋  Lila":"Paars","🚀  Blaugrün":"Teal","🏆  Indigo":"Indigo","💎  Rot":"Rood",
            "🌻  Gelb":"Geel","🌊  Cyan":"Cyaan",
        },
        "desc_pattern": (
            "Anwesenheitsmuster wählen:\n\n"
            "🏠  Immer zuhause     → wohnt immer bei dir\n"
            "🔄  Jede zweite Woche → Woche A hier, Woche B woanders\n"
            "📅  Feste Tage        → z.B. jedes Wochenende\n"
            "🗓️  Bestimmte Wochen  → z.B. 1. und 3. Woche\n"
            "🔄📅  Kombination     → jede zweite Woche UND feste Tage"
        ),
        "desc_omdeweek": "JEDE ZWEITE WOCHE\nStartdatum → erster MONTAG einer Woche wo {kind} hier ist.\nFormat: JJJJ-MM-TT",
        "desc_vastedagen": "FESTE ANWESENHEITSTAGE\nHake die Tage ab, an denen {kind} bei dir ist.",
        "desc_wekenpermaand": "ANWESENHEITSWOCHEN\nHake die Wochen des Monats ab, in denen {kind} bei dir ist.",
        "desc_blok": "KEINE ZEIT FÜR AUFGABEN\nTage abhaken, an denen {kind} zuhause ist aber keine Zeit hat.",
        "rotation_desc": "Tägliche Aufgaben, kommagetrennt eingeben.\nBeispiel: Geschirrspüler einräumen, Tisch decken",
        "week_desc": "Wöchentliche Aufgaben, kommagetrennt eingeben.",
        "month_desc": "Monatliche Aufgaben, kommagetrennt eingeben.",
        "samen_label": "Alle Kinder sind immer gleichzeitig zuhause",
    },
    "fr": {
        "presence": [
            "🏠  Toujours à la maison",
            "🔄  Une semaine sur deux (co-parentalité)",
            "📅  Jours fixes par semaine",
            "🗓️  Certaines semaines du mois",
            "🔄📅  Une semaine sur deux + jours fixes",
        ],
        "presence_modes": ["altijd","om_de_week","vaste_dagen","weken_per_maand","combinatie"],
        "week_modes": ["Rotation automatique","Semaines paires","Semaines impaires","Enfant fixe"],
        "week_mode_keys": ["auto_rotate","even","odd","fixed"],
        "days": ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"],
        "month_weeks": ["1re semaine","2e semaine","3e semaine","4e semaine","Dernière semaine"],
        "month_week_keys": ["1e week","2e week","3e week","4e week","Laatste week"],
        "colors": {
            "⭐  Bleu":"Blauw","🌟  Vert":"Groen","🎯  Orange":"Oranje","🌈  Rose":"Roze",
            "🦋  Violet":"Paars","🚀  Turquoise":"Teal","🏆  Indigo":"Indigo","💎  Rouge":"Rood",
            "🌻  Jaune":"Geel","🌊  Cyan":"Cyaan",
        },
        "desc_pattern": (
            "Choisissez le modèle de présence:\n\n"
            "🏠  Toujours là           → vit toujours chez vous\n"
            "🔄  Une semaine sur deux  → semaine A ici, semaine B ailleurs\n"
            "📅  Jours fixes           → ex. chaque week-end\n"
            "🗓️  Semaines spécifiques  → ex. 1re et 3e semaine\n"
            "🔄📅  Combinaison         → une semaine sur deux ET jours fixes"
        ),
        "desc_omdeweek": "UNE SEMAINE SUR DEUX\nDate de début → premier LUNDI d'une semaine où {kind} est ici.\nFormat: AAAA-MM-JJ",
        "desc_vastedagen": "JOURS DE PRÉSENCE FIXES\nCochez les jours où {kind} est chez vous.",
        "desc_wekenpermaand": "SEMAINES DE PRÉSENCE\nCochez les semaines du mois où {kind} est chez vous.",
        "desc_blok": "PAS DE TEMPS POUR LES TÂCHES\nCochez les jours où {kind} est là mais n'a pas le temps.",
        "rotation_desc": "Tâches quotidiennes, séparées par des virgules.\nExemple: Remplir le lave-vaisselle, Mettre la table",
        "week_desc": "Tâches hebdomadaires, séparées par des virgules.",
        "month_desc": "Tâches mensuelles, séparées par des virgules.",
        "samen_label": "Les enfants sont toujours présents en même temps",
    },
}


def _t(lang):
    return T.get(lang, T["nl"])

def _color_label(key, lang):
    rev = {v: k for k, v in _t(lang)["colors"].items()}
    return rev.get(key, list(_t(lang)["colors"].keys())[0])

def _color_key(label, lang):
    return _t(lang)["colors"].get(label, "Blauw")

def _default_color_label(idx, child, child_colors, lang):
    key = child_colors.get(child, DEFAULT_COLOR_ORDER[idx % len(DEFAULT_COLOR_ORDER)])
    return _color_label(key, lang)

def _presence_label(mode, lang):
    t = _t(lang)
    try:
        return t["presence"][t["presence_modes"].index(mode)]
    except (ValueError, IndexError):
        return t["presence"][0]

def _week_mode_label(key, lang):
    t = _t(lang)
    try:
        return t["week_modes"][t["week_mode_keys"].index(key)]
    except (ValueError, IndexError):
        return t["week_modes"][0]

def _month_week_label(key, lang):
    t = _t(lang)
    try:
        return t["month_weeks"][t["month_week_keys"].index(key)]
    except (ValueError, IndexError):
        return t["month_weeks"][-1]

def _split(raw):
    """Komma-gescheiden tekst naar lijst."""
    return [s.strip() for s in raw.split(",") if s.strip()]

def _join_tasks(tasks):
    """Taken-lijst (van dicts of strings) naar komma-string."""
    return ", ".join(tk["name"] if isinstance(tk, dict) else tk for tk in tasks)

_DAG_NL  = {
    "nl": ["Maandag","Dinsdag","Woensdag","Donderdag","Vrijdag","Zaterdag","Zondag"],
    "en": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
    "de": ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"],
    "fr": ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"],
}
_NL_DAYS = ["Maandag","Dinsdag","Woensdag","Donderdag","Vrijdag","Zaterdag","Zondag"]

def _dag_to_nl(label, lang):
    days = _DAG_NL.get(lang, _NL_DAYS)
    try:
        return _NL_DAYS[days.index(label)]
    except (ValueError, IndexError):
        return label

def _dag_to_lang(nl_day, lang):
    try:
        return _DAG_NL.get(lang, _NL_DAYS)[_NL_DAYS.index(nl_day)]
    except (ValueError, IndexError):
        return nl_day


# ── Hoofd config flow ─────────────────────────────────────────────────────────

class KindertakenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 8

    def __init__(self):
        self._lang           = "nl"
        self._children       = []
        self._together       = True
        self._child_idx      = 0
        self._child_colors   = {}
        self._child_presence = {}
        self._pending_mode   = {}
        self._rotation_tasks = []
        self._week_tasks     = []
        self._month_tasks    = []

    # ── Taal ──────────────────────────────────────────────────────────────────
    async def async_step_user(self, ui=None):
        if ui is not None:
            self._lang = LANG_OPTIONS.get(ui.get("taal","🇳🇱  Nederlands"), "nl")
            return await self.async_step_children()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional("taal", default="🇳🇱  Nederlands"): vol.In(list(LANG_OPTIONS.keys())),
            }),
            description_placeholders={},
        )

    # ── Namen + samen ─────────────────────────────────────────────────────────
    async def async_step_children(self, ui=None):
        errors = {}
        if ui is not None:
            ch = _split(ui.get("children",""))
            if not ch:        errors["children"] = "min_one_child"
            elif len(ch) > 8: errors["children"] = "max_eight_children"
            else:
                self._children  = ch
                self._together  = ui.get("samen", True)
                self._child_idx = 0
                return await self.async_step_child_a()
        return self.async_show_form(
            step_id="children",
            data_schema=vol.Schema({
                vol.Required("children"): str,
                vol.Optional("samen", default=True): bool,
            }),
            errors=errors,
            description_placeholders={},
        )

    # ── Kind A: kleur + patroon ───────────────────────────────────────────────
    async def async_step_child_a(self, ui=None):
        child = self._children[self._child_idx]
        n, total = self._child_idx + 1, len(self._children)
        lang = self._lang
        t    = _t(lang)

        if ui is not None:
            self._child_colors[child] = _color_key(ui.get("kleur",""), lang)
            if self._together:
                self._child_presence[child] = {
                    "mode":"altijd","start_date":"","start_present":True,
                    "days_present":[],"weeks_present":[],"blocked_days":[],"override_present":None,
                }
                return await self._advance_child()
            chosen = ui.get("patroon", t["presence"][0])
            self._pending_mode[child] = chosen
            mode = t["presence_modes"][t["presence"].index(chosen)] if chosen in t["presence"] else "altijd"
            if mode == "altijd":
                self._child_presence[child] = {
                    "mode":"altijd","start_date":"","start_present":True,
                    "days_present":[],"weeks_present":[],"blocked_days":[],"override_present":None,
                }
                return await self._advance_child()
            return await self.async_step_child_b()

        default_kleur = _default_color_label(self._child_idx, child, self._child_colors, lang)
        schema_fields = {vol.Optional("kleur", default=default_kleur): vol.In(list(t["colors"].keys()))}
        if not self._together:
            schema_fields[vol.Optional("patroon", default=t["presence"][1])] = vol.In(t["presence"])

        return self.async_show_form(
            step_id="child_a",
            data_schema=vol.Schema(schema_fields),
            description_placeholders={"kind": child, "n": str(n), "total": str(total)},
        )

    # ── Kind B: vervolgvragen ─────────────────────────────────────────────────
    async def async_step_child_b(self, ui=None):
        child = self._children[self._child_idx]
        n, total = self._child_idx + 1, len(self._children)
        lang   = self._lang
        t      = _t(lang)
        chosen = self._pending_mode.get(child, t["presence"][1])
        mode   = t["presence_modes"][t["presence"].index(chosen)] if chosen in t["presence"] else "om_de_week"
        cur    = self._child_presence.get(child, {})

        if ui is not None:
            days_present  = [i for i in range(7) if ui.get(f"dag_{i}", False)]
            weeks_raw     = [t["month_week_keys"][i] for i in range(4) if ui.get(f"mweek_{i}", False)]
            if ui.get("mweek_laatste", False): weeks_raw.append("Laatste week")
            blocked_days  = [{"day":i,"reason":"blocked"} for i in range(7) if ui.get(f"blok_{i}", False)]
            self._child_presence[child] = {
                "mode": mode,
                "start_date":    ui.get("startdatum","2025-01-06"),
                "start_present": ui.get("startweek", True),
                "days_present":  days_present,
                "weeks_present": weeks_raw,
                "blocked_days":  blocked_days,
                "override_present": None,
            }
            return await self._advance_child()

        fields = {}
        desc_parts = []
        cur_days    = set(cur.get("days_present", []))
        cur_weeks   = set(cur.get("weeks_present", []))
        cur_blocked = {(b if isinstance(b,int) else b.get("day",-1)) for b in cur.get("blocked_days",[])}

        if mode in ("om_de_week","combinatie"):
            fields[vol.Optional("startdatum", default=cur.get("start_date","2025-01-06"))] = str
            fields[vol.Optional("startweek",  default=cur.get("start_present",True))]      = bool
            desc_parts.append(t["desc_omdeweek"].replace("{kind}", child))

        if mode in ("vaste_dagen","combinatie"):
            for i in range(7): fields[vol.Optional(f"dag_{i}", default=(i in cur_days))] = bool
            desc_parts.append(t["desc_vastedagen"].replace("{kind}", child))

        if mode == "weken_per_maand":
            for i in range(4): fields[vol.Optional(f"mweek_{i}", default=(t["month_week_keys"][i] in cur_weeks))] = bool
            fields[vol.Optional("mweek_laatste", default=("Laatste week" in cur_weeks))] = bool
            desc_parts.append(t["desc_wekenpermaand"].replace("{kind}", child))

        for i in range(7): fields[vol.Optional(f"blok_{i}", default=(i in cur_blocked))] = bool
        desc_parts.append(t["desc_blok"].replace("{kind}", child))

        return self.async_show_form(
            step_id="child_b",
            data_schema=vol.Schema(fields),
            description_placeholders={"uitleg": "\n\n".join(desc_parts), "kind": child, "n": str(n), "total": str(total)},
        )

    async def _advance_child(self):
        self._child_idx += 1
        if self._child_idx < len(self._children):
            return await self.async_step_child_a()
        return await self.async_step_rotation_tasks()

    # ── Rotatietaken: één tekstveld ───────────────────────────────────────────
    async def async_step_rotation_tasks(self, ui=None):
        lang = self._lang
        t    = _t(lang)
        if ui is not None:
            taken    = _split(ui.get("taken",""))
            volgorde = [c.strip() for c in ui.get("volgorde","").split(",") if c.strip() in self._children] or self._children
            self._rotation_tasks = [{"name": tk, "fixed_child": None, "children_order": volgorde} for tk in taken]
            return await self.async_step_week_tasks()

        desc = t["rotation_desc"].replace("{children}", ", ".join(self._children))
        return self.async_show_form(
            step_id="rotation_tasks",
            data_schema=vol.Schema({
                vol.Optional("taken",    default="Afwasmachine vullen, Tafel dekken"): str,
                vol.Optional("volgorde", default=", ".join(self._children)): str,
            }),
            description_placeholders={"uitleg": desc},
        )

    # ── Weektaken: tekstveld + dag + modus ───────────────────────────────────
    async def async_step_week_tasks(self, ui=None):
        lang = self._lang
        t    = _t(lang)
        ch0  = self._children[0] if self._children else ""
        ch1  = self._children[1] if len(self._children) > 1 else ch0

        if ui is not None:
            taken    = _split(ui.get("taken",""))
            dag_nl   = _dag_to_nl(ui.get("dag", t["days"][2]), lang)
            mode_key = t["week_mode_keys"][t["week_modes"].index(ui.get("modus", t["week_modes"][0]))] if ui.get("modus") in t["week_modes"] else "auto_rotate"
            self._week_tasks = [{
                "name": tk, "day": dag_nl, "mode": mode_key,
                "fixed_child": ch0, "even_child": ch0, "odd_child": ch1,
                "children_order": self._children,
            } for tk in taken]
            return await self.async_step_month_tasks()

        return self.async_show_form(
            step_id="week_tasks",
            data_schema=vol.Schema({
                vol.Optional("taken",  default=""): str,
                vol.Optional("dag",    default=t["days"][2]): vol.In(t["days"]),
                vol.Optional("modus",  default=t["week_modes"][0]): vol.In(t["week_modes"]),
            }),
            description_placeholders={"uitleg": t["week_desc"]},
        )

    # ── Maandtaken: tekstveld + week + dag ───────────────────────────────────
    async def async_step_month_tasks(self, ui=None):
        lang = self._lang
        t    = _t(lang)

        if ui is not None:
            taken    = _split(ui.get("taken",""))
            wk_label = ui.get("week", t["month_weeks"][-1])
            wk_nl    = t["month_week_keys"][t["month_weeks"].index(wk_label)] if wk_label in t["month_weeks"] else "Laatste week"
            dag_nl   = _dag_to_nl(ui.get("dag", t["days"][-1]), lang)
            self._month_tasks = [{
                "name": tk, "all_children": True,
                "week_of_month": wk_nl, "day_of_week": dag_nl, "assignments": {},
            } for tk in taken]
            return self.async_create_entry(
                title="Kindertaken Planner",
                data={
                    "lang":              self._lang,
                    CONF_CHILDREN:       self._children,
                    CONF_CHILD_COLORS:   self._child_colors,
                    CONF_CHILD_PRESENCE: self._child_presence,
                    CONF_ROTATION_TASKS: self._rotation_tasks,
                    CONF_WEEK_TASKS:     self._week_tasks,
                    CONF_MONTH_TASKS:    self._month_tasks,
                },
            )

        return self.async_show_form(
            step_id="month_tasks",
            data_schema=vol.Schema({
                vol.Optional("taken", default=""): str,
                vol.Optional("week",  default=t["month_weeks"][-1]): vol.In(t["month_weeks"]),
                vol.Optional("dag",   default=t["days"][-1]): vol.In(t["days"]),
            }),
            description_placeholders={"uitleg": t["month_desc"]},
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
        self._lang           = d.get("lang","nl")
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
            "edit_children","edit_child_settings",
            "edit_rotation_tasks","edit_week_tasks","edit_month_tasks",
        ])

    async def async_step_edit_children(self, ui=None):
        errors = {}
        if ui is not None:
            ch = _split(ui.get("children",""))
            if not ch: errors["children"] = "min_one_child"
            else: return self._save({CONF_CHILDREN: ch})
        return self.async_show_form(
            step_id="edit_children",
            data_schema=vol.Schema({vol.Required("children", default=", ".join(self._children)): str}),
            errors=errors,
            description_placeholders={},
        )

    async def async_step_edit_child_settings(self, ui=None):
        if ui is not None:
            self._edit_child = ui.get("kind","")
            return await self.async_step_edit_child_a()
        return self.async_show_form(
            step_id="edit_child_settings",
            data_schema=vol.Schema({vol.Required("kind"): vol.In(self._children)}),
            description_placeholders={},
        )

    async def async_step_edit_child_a(self, ui=None):
        child = self._edit_child
        lang  = self._lang
        t     = _t(lang)
        idx   = self._children.index(child) if child in self._children else 0
        cur   = self._child_presence.get(child, {})

        if ui is not None:
            self._child_colors[child] = _color_key(ui.get("kleur",""), lang)
            chosen = ui.get("patroon", t["presence"][0])
            self._pending_mode[child] = chosen
            mode = t["presence_modes"][t["presence"].index(chosen)] if chosen in t["presence"] else "altijd"
            if mode == "altijd":
                self._child_presence[child] = {
                    "mode":"altijd","start_date":"","start_present":True,
                    "days_present":[],"weeks_present":[],"blocked_days":[],"override_present":None,
                }
                return self._save({CONF_CHILD_COLORS:self._child_colors, CONF_CHILD_PRESENCE:self._child_presence})
            return await self.async_step_edit_child_b()

        cur_mode  = _presence_label(cur.get("mode","altijd"), lang)
        cur_kleur = _default_color_label(idx, child, self._child_colors, lang)
        return self.async_show_form(
            step_id="edit_child_a",
            data_schema=vol.Schema({
                vol.Optional("kleur",   default=cur_kleur): vol.In(list(t["colors"].keys())),
                vol.Optional("patroon", default=cur_mode):  vol.In(t["presence"]),
            }),
            description_placeholders={"uitleg": t["desc_pattern"], "kind": child},
        )

    async def async_step_edit_child_b(self, ui=None):
        child  = self._edit_child
        lang   = self._lang
        t      = _t(lang)
        chosen = self._pending_mode.get(child, t["presence"][1])
        mode   = t["presence_modes"][t["presence"].index(chosen)] if chosen in t["presence"] else "om_de_week"
        cur    = self._child_presence.get(child, {})

        if ui is not None:
            days_present  = [i for i in range(7) if ui.get(f"dag_{i}",False)]
            weeks_raw     = [t["month_week_keys"][i] for i in range(4) if ui.get(f"mweek_{i}",False)]
            if ui.get("mweek_laatste",False): weeks_raw.append("Laatste week")
            blocked_days  = [{"day":i,"reason":"blocked"} for i in range(7) if ui.get(f"blok_{i}",False)]
            self._child_presence[child] = {
                "mode":mode, "start_date":ui.get("startdatum","2025-01-06"),
                "start_present":ui.get("startweek",True), "days_present":days_present,
                "weeks_present":weeks_raw, "blocked_days":blocked_days, "override_present":None,
            }
            return self._save({CONF_CHILD_COLORS:self._child_colors, CONF_CHILD_PRESENCE:self._child_presence})

        fields = {}
        desc_parts = []
        cur_days    = set(cur.get("days_present",[]))
        cur_weeks   = set(cur.get("weeks_present",[]))
        cur_blocked = {(b if isinstance(b,int) else b.get("day",-1)) for b in cur.get("blocked_days",[])}

        if mode in ("om_de_week","combinatie"):
            fields[vol.Optional("startdatum", default=cur.get("start_date","2025-01-06"))] = str
            fields[vol.Optional("startweek",  default=cur.get("start_present",True))]      = bool
            desc_parts.append(t["desc_omdeweek"].replace("{kind}",child))
        if mode in ("vaste_dagen","combinatie"):
            for i in range(7): fields[vol.Optional(f"dag_{i}", default=(i in cur_days))] = bool
            desc_parts.append(t["desc_vastedagen"].replace("{kind}",child))
        if mode == "weken_per_maand":
            for i in range(4): fields[vol.Optional(f"mweek_{i}", default=(t["month_week_keys"][i] in cur_weeks))] = bool
            fields[vol.Optional("mweek_laatste", default=("Laatste week" in cur_weeks))] = bool
            desc_parts.append(t["desc_wekenpermaand"].replace("{kind}",child))
        for i in range(7): fields[vol.Optional(f"blok_{i}", default=(i in cur_blocked))] = bool
        desc_parts.append(t["desc_blok"].replace("{kind}",child))

        return self.async_show_form(
            step_id="edit_child_b",
            data_schema=vol.Schema(fields),
            description_placeholders={"uitleg":"\n\n".join(desc_parts),"kind":child},
        )

    async def async_step_edit_rotation_tasks(self, ui=None):
        lang = self._lang
        t    = _t(lang)
        if ui is not None:
            taken    = _split(ui.get("taken",""))
            volgorde = [c.strip() for c in ui.get("volgorde","").split(",") if c.strip() in self._children] or self._children
            return self._save({CONF_ROTATION_TASKS: [{"name":tk,"fixed_child":None,"children_order":volgorde} for tk in taken]})

        cur = _join_tasks(self._rotation_tasks)
        cur_vol = (self._rotation_tasks[0].get("children_order") or self._children) if self._rotation_tasks else self._children
        desc = t["rotation_desc"].replace("{children}", ", ".join(self._children))
        return self.async_show_form(
            step_id="edit_rotation_tasks",
            data_schema=vol.Schema({
                vol.Optional("taken",    default=cur): str,
                vol.Optional("volgorde", default=", ".join(cur_vol)): str,
            }),
            description_placeholders={"uitleg": desc},
        )

    async def async_step_edit_week_tasks(self, ui=None):
        lang = self._lang
        t    = _t(lang)
        ch0  = self._children[0] if self._children else ""
        ch1  = self._children[1] if len(self._children) > 1 else ch0

        if ui is not None:
            taken    = _split(ui.get("taken",""))
            dag_nl   = _dag_to_nl(ui.get("dag", t["days"][2]), lang)
            mode_key = t["week_mode_keys"][t["week_modes"].index(ui.get("modus",t["week_modes"][0]))] if ui.get("modus") in t["week_modes"] else "auto_rotate"
            existing = {wt["name"]: wt for wt in self._week_tasks}
            result = []
            for tk in taken:
                ex = existing.get(tk, {})
                result.append({
                    "name": tk,
                    "day":  ex.get("day", dag_nl),
                    "mode": ex.get("mode", mode_key),
                    "fixed_child": ex.get("fixed_child", ch0),
                    "even_child":  ex.get("even_child",  ch0),
                    "odd_child":   ex.get("odd_child",   ch1),
                    "children_order": self._children,
                })
            return self._save({CONF_WEEK_TASKS: result})

        cur = _join_tasks(self._week_tasks)
        cur_dag  = _dag_to_lang(self._week_tasks[0].get("day","Woensdag"), lang) if self._week_tasks else t["days"][2]
        cur_mode = _week_mode_label(self._week_tasks[0].get("mode","auto_rotate"), lang) if self._week_tasks else t["week_modes"][0]
        return self.async_show_form(
            step_id="edit_week_tasks",
            data_schema=vol.Schema({
                vol.Optional("taken", default=cur): str,
                vol.Optional("dag",   default=cur_dag):  vol.In(t["days"]),
                vol.Optional("modus", default=cur_mode): vol.In(t["week_modes"]),
            }),
            description_placeholders={"uitleg": t["week_desc"]},
        )

    async def async_step_edit_month_tasks(self, ui=None):
        lang = self._lang
        t    = _t(lang)

        if ui is not None:
            taken    = _split(ui.get("taken",""))
            wk_label = ui.get("week", t["month_weeks"][-1])
            wk_nl    = t["month_week_keys"][t["month_weeks"].index(wk_label)] if wk_label in t["month_weeks"] else "Laatste week"
            dag_nl   = _dag_to_nl(ui.get("dag", t["days"][-1]), lang)
            existing = {mt["name"]: mt for mt in self._month_tasks}
            result = []
            for tk in taken:
                ex = existing.get(tk, {})
                result.append({
                    "name": tk, "all_children": True,
                    "week_of_month": ex.get("week_of_month", wk_nl),
                    "day_of_week":   ex.get("day_of_week",   dag_nl),
                    "assignments":   {},
                })
            return self._save({CONF_MONTH_TASKS: result})

        cur = _join_tasks(self._month_tasks)
        cur_wk  = _month_week_label(self._month_tasks[0].get("week_of_month","Laatste week"), lang) if self._month_tasks else t["month_weeks"][-1]
        cur_dag = _dag_to_lang(self._month_tasks[0].get("day_of_week","Zondag"), lang) if self._month_tasks else t["days"][-1]
        return self.async_show_form(
            step_id="edit_month_tasks",
            data_schema=vol.Schema({
                vol.Optional("taken", default=cur): str,
                vol.Optional("week",  default=cur_wk):  vol.In(t["month_weeks"]),
                vol.Optional("dag",   default=cur_dag): vol.In(t["days"]),
            }),
            description_placeholders={"uitleg": t["month_desc"]},
        )
