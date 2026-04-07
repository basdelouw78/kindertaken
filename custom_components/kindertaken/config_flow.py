"""
Kindertaken config flow v4.1 — volledig schone implementatie.

Wizard:
  user        → taal kiezen
  children    → namen + samen aanwezig?
  child_a (×N)→ kleur + patroon per kind
  child_b (×N)→ vervolgvragen (alleen relevant voor gekozen patroon)
  rotation_tasks
  week_tasks
  month_tasks

Alle veldnamen zijn VASTE sleutels zonder kindnaam,
zodat translations altijd werken.
"""
from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_CHILDREN, CONF_CHILD_COLORS, CONF_CHILD_PRESENCE,
    CONF_ROTATION_TASKS, CONF_WEEK_TASKS, CONF_MONTH_TASKS,
    DEFAULT_ROTATION_TASKS, DEFAULT_WEEK_TASKS, DEFAULT_MONTH_TASKS,
    CHILD_COLOR_OPTIONS, DEFAULT_COLOR_ORDER,
)

# ── Taal-opties ───────────────────────────────────────────────────────────────

LANG_OPTIONS = {
    "🇳🇱  Nederlands": "nl",
    "🇬🇧  English":    "en",
    "🇩🇪  Deutsch":    "de",
    "🇫🇷  Français":   "fr",
}

# ── Meertalige content ────────────────────────────────────────────────────────

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
            "Kies het aanwezigheidspatroon voor {kind}:\n\n"
            "🏠  Altijd thuis          → woont altijd bij jou, geen co-ouderschap\n"
            "🔄  Om de week            → week A bij jou, week B bij andere ouder\n"
            "📅  Vaste dagen           → bijv. elk weekend (vr/za/zo) bij jou\n"
            "🗓️  Bepaalde weken        → bijv. 1e en 3e week van de maand bij jou\n"
            "🔄📅  Combinatie          → om de week én alleen op de vaste dagen"
        ),
        "desc_omdeweek": (
            "OM DE WEEK\n"
            "Startdatum  →  eerste MAANDAG van een week dat {kind} bij jou is.\n"
            "Formaat: JJJJ-MM-DD  (bijv. 2025-01-06)\n"
            "Aanwezig in startweek  →  vink aan als {kind} die startweek al hier is.\n"
            "Daarna wisselt het systeem automatisch elke week."
        ),
        "desc_vastedagen": (
            "AANWEZIGE DAGEN\n"
            "Vink aan op welke dagen {kind} bij jou is.\n"
            "Voorbeeld elk weekend: Vrijdag + Zaterdag + Zondag aanvinken."
        ),
        "desc_wekenpermaand": (
            "AANWEZIGE WEKEN\n"
            "Vink aan in welke weken van de maand {kind} bij jou is.\n"
            "Voorbeeld: 1e week en 3e week aanvinken."
        ),
        "desc_blok": (
            "GEEN TIJD VOOR TAKEN\n"
            "Vink dagen aan waarop {kind} WEL thuis is maar GEEN taken kan doen.\n"
            "Bijv. Emma werkt op maandag, Liam heeft sport op donderdag.\n"
            "Taken gaan op die dagen automatisch naar een ander kind."
        ),
        "desc_rotation": (
            "DAGELIJKSE ROTATIETAKEN — komen elke dag terug en rouleren automatisch.\n"
            "Het systeem berekent dagelijks wie aan de beurt is op basis van de datum.\n"
            "Is een kind afwezig of heeft het een blokdag? Dan pakt het kind met\n"
            "de minste taken automatisch over.\n\n"
            "VOLGORDE  →  bepaalt de rotatievolgorde tussen de kinderen.\n"
            "EXTRA TAKEN  →  eigen dagelijkse taken toevoegen (komma-gescheiden)."
        ),
        "desc_week": (
            "WEKELIJKSE TAKEN — eenmalig per week op een vaste dag.\n\n"
            "Per taak kun je instellen:\n"
            "• Op welke DAG de taak gedaan wordt\n"
            "• Hoe de taak verdeeld wordt (MODUS):\n"
            "  – Automatisch roteren  → wisselt elke week van kind\n"
            "  – Even weken           → handig bij co-ouderschap (week A)\n"
            "  – Oneven weken         → co-ouderschap (week B)\n"
            "  – Vast kind            → altijd hetzelfde kind\n\n"
            "Is het aangewezen kind er niet? Dan neemt het kind met de minste taken over."
        ),
        "desc_month": (
            "MAANDTAKEN — eenmalig per maand.\n"
            "Alle kinderen die er die dag zijn doen de taak.\n\n"
            "Per taak stel je in:\n"
            "• WEEK  →  welke week van de maand (1e t/m laatste week)\n"
            "• DAG   →  welke dag van die week (bijv. zondag)\n\n"
            "Is een kind er niet op de geplande dag? Dan verschuift de taak\n"
            "automatisch naar de eerstvolgende dag dat het kind er wél is."
        ),
        "samen_ja": "Zijn de kinderen altijd tegelijk bij jou thuis?",
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
            "Choose the presence pattern for {kind}:\n\n"
            "🏠  Always home       → lives with you full time\n"
            "🔄  Alternate weeks   → week A here, week B with other parent\n"
            "📅  Fixed days        → e.g. every weekend (fri/sat/sun)\n"
            "🗓️  Specific weeks    → e.g. 1st and 3rd week of the month\n"
            "🔄📅  Combination     → alternate weeks AND only on fixed days"
        ),
        "desc_omdeweek": (
            "ALTERNATE WEEKS\n"
            "Start date  →  first MONDAY of a week when {kind} is here.\n"
            "Format: YYYY-MM-DD  (e.g. 2025-01-06)\n"
            "Present in start week  →  check if {kind} is already here that week.\n"
            "The system will alternate automatically every week after that."
        ),
        "desc_vastedagen": (
            "FIXED PRESENT DAYS\n"
            "Check which days {kind} is at your home.\n"
            "Example every weekend: Friday + Saturday + Sunday."
        ),
        "desc_wekenpermaand": (
            "PRESENT WEEKS\n"
            "Check which weeks of the month {kind} is at your home.\n"
            "Example: 1st week and 3rd week."
        ),
        "desc_blok": (
            "NO TIME FOR TASKS\n"
            "Check days when {kind} IS home but has NO time for tasks.\n"
            "E.g. Emma works on Monday, Liam has sport on Thursday.\n"
            "Tasks on those days automatically go to another child."
        ),
        "desc_rotation": (
            "DAILY ROTATION TASKS — recur every day and rotate automatically.\n"
            "The system calculates daily who is up based on the date.\n"
            "Child absent or blocked? The child with fewest tasks takes over.\n\n"
            "ORDER  →  determines the rotation sequence between children.\n"
            "EXTRA TASKS  →  add your own daily tasks (comma-separated)."
        ),
        "desc_week": (
            "WEEKLY TASKS — once per week on a fixed day.\n\n"
            "Per task you can set:\n"
            "• Which DAY the task is done\n"
            "• How the task is distributed (MODE):\n"
            "  – Auto rotate   → changes child every week\n"
            "  – Even weeks    → useful for co-parenting (week A)\n"
            "  – Odd weeks     → co-parenting (week B)\n"
            "  – Fixed child   → always the same child\n\n"
            "Child not available? The child with fewest tasks takes over."
        ),
        "desc_month": (
            "MONTHLY TASKS — once per month.\n"
            "All children present that day do the task.\n\n"
            "Per task set:\n"
            "• WEEK  →  which week of the month (1st through last)\n"
            "• DAY   →  which day of that week (e.g. Sunday)\n\n"
            "Child absent on that day? The task shifts automatically\n"
            "to the next day the child is available."
        ),
        "samen_ja": "Are all children always home at the same time?",
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
            "Anwesenheitsmuster für {kind} wählen:\n\n"
            "🏠  Immer zuhause       → wohnt immer bei dir\n"
            "🔄  Jede zweite Woche   → Woche A hier, Woche B beim anderen Elternteil\n"
            "📅  Feste Tage          → z.B. jedes Wochenende (Fr/Sa/So)\n"
            "🗓️  Bestimmte Wochen    → z.B. 1. und 3. Woche des Monats\n"
            "🔄📅  Kombination       → jede zweite Woche UND nur an festen Tagen"
        ),
        "desc_omdeweek": (
            "JEDE ZWEITE WOCHE\n"
            "Startdatum  →  erster MONTAG einer Woche, in der {kind} hier ist.\n"
            "Format: JJJJ-MM-TT  (z.B. 2025-01-06)\n"
            "In Startwoche anwesend  →  abhaken wenn {kind} diese Woche schon hier ist."
        ),
        "desc_vastedagen": (
            "FESTE ANWESENHEITSTAGE\n"
            "Hake die Tage ab, an denen {kind} bei dir ist."
        ),
        "desc_wekenpermaand": (
            "ANWESENHEITSWOCHEN\n"
            "Hake die Wochen des Monats ab, in denen {kind} bei dir ist."
        ),
        "desc_blok": (
            "KEINE ZEIT FÜR AUFGABEN\n"
            "Tage abhaken, an denen {kind} zuhause ist aber KEINE Zeit hat.\n"
            "Diese Aufgaben gehen automatisch an ein anderes Kind."
        ),
        "desc_rotation": "TÄGLICHE ROTATIONSAUFGABEN — rotieren automatisch jeden Tag.",
        "desc_week":     "WÖCHENTLICHE AUFGABEN — einmal pro Woche an einem festen Tag.",
        "desc_month":    "MONATLICHE AUFGABEN — einmal pro Monat.",
        "samen_ja":      "Sind alle Kinder immer gleichzeitig bei dir zuhause?",
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
            "Choisissez le modèle de présence pour {kind}:\n\n"
            "🏠  Toujours là           → vit toujours chez vous\n"
            "🔄  Une semaine sur deux  → semaine A ici, semaine B chez l'autre parent\n"
            "📅  Jours fixes           → ex. chaque week-end (ven/sam/dim)\n"
            "🗓️  Semaines spécifiques  → ex. 1re et 3e semaine du mois\n"
            "🔄📅  Combinaison         → une semaine sur deux ET jours fixes seulement"
        ),
        "desc_omdeweek": (
            "UNE SEMAINE SUR DEUX\n"
            "Date de début  →  premier LUNDI d'une semaine où {kind} est ici.\n"
            "Format: AAAA-MM-JJ  (ex. 2025-01-06)\n"
            "Présent la semaine de début  →  cochez si {kind} est déjà là cette semaine."
        ),
        "desc_vastedagen": (
            "JOURS DE PRÉSENCE FIXES\n"
            "Cochez les jours où {kind} est chez vous."
        ),
        "desc_wekenpermaand": (
            "SEMAINES DE PRÉSENCE\n"
            "Cochez les semaines du mois où {kind} est chez vous."
        ),
        "desc_blok": (
            "PAS DE TEMPS POUR LES TÂCHES\n"
            "Cochez les jours où {kind} est là mais n'a PAS le temps.\n"
            "Ces tâches vont automatiquement à un autre enfant."
        ),
        "desc_rotation": "TÂCHES QUOTIDIENNES EN ROTATION — tournent automatiquement chaque jour.",
        "desc_week":     "TÂCHES HEBDOMADAIRES — une fois par semaine un jour fixe.",
        "desc_month":    "TÂCHES MENSUELLES — une fois par mois.",
        "samen_ja":      "Les enfants sont-ils toujours présents en même temps?",
    },
}


def _t(lang: str) -> dict:
    return T.get(lang, T["nl"])

def _color_label(key: str, lang: str) -> str:
    rev = {v: k for k, v in _t(lang)["colors"].items()}
    return rev.get(key, list(_t(lang)["colors"].keys())[0])

def _color_key(label: str, lang: str) -> str:
    return _t(lang)["colors"].get(label, "Blauw")

def _default_color_label(idx: int, child: str, child_colors: dict, lang: str) -> str:
    key = child_colors.get(child, DEFAULT_COLOR_ORDER[idx % len(DEFAULT_COLOR_ORDER)])
    return _color_label(key, lang)

def _presence_label(mode: str, lang: str) -> str:
    t = _t(lang)
    try:
        return t["presence"][t["presence_modes"].index(mode)]
    except (ValueError, IndexError):
        return t["presence"][0]

def _week_mode_label(key: str, lang: str) -> str:
    t = _t(lang)
    try:
        return t["week_modes"][t["week_mode_keys"].index(key)]
    except (ValueError, IndexError):
        return t["week_modes"][0]

def _month_week_key(label: str, lang: str) -> str:
    t = _t(lang)
    try:
        return t["month_week_keys"][t["month_weeks"].index(label)]
    except (ValueError, IndexError):
        return "Laatste week"

def _month_week_label(key: str, lang: str) -> str:
    t = _t(lang)
    try:
        return t["month_weeks"][t["month_week_keys"].index(key)]
    except (ValueError, IndexError):
        return t["month_weeks"][-1]


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
        self._pending_mode   = {}   # {kind: mode-string}
        self._rotation_tasks = []
        self._week_tasks     = []
        self._month_tasks    = []

    # ── Taal ──────────────────────────────────────────────────────────────────
    async def async_step_user(self, ui=None):
        if ui is not None:
            self._lang = LANG_OPTIONS.get(ui.get("taal", "🇳🇱  Nederlands"), "nl")
            return await self.async_step_children()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional("taal", default="🇳🇱  Nederlands"): vol.In(list(LANG_OPTIONS.keys())),
            }),
        )

    # ── Namen + samen ─────────────────────────────────────────────────────────
    async def async_step_children(self, ui=None):
        lang = self._lang
        errors = {}
        if ui is not None:
            ch = [c.strip() for c in ui.get("children", "").split(",") if c.strip()]
            if not ch:        errors["children"] = "min_one_child"
            elif len(ch) > 8: errors["children"] = "max_eight_children"
            else:
                self._children  = ch
                self._together  = ui.get("samen", True)
                self._child_idx = 0
                return await self.async_step_child_a()

        descs = {
            "nl": "Voer de namen in van de kinderen, gescheiden door komma's.\n\nZijn de kinderen altijd tegelijk bij jou thuis?\n• Ja  →  geen co-ouderschap, geen individueel rooster\n• Nee →  elk kind krijgt een eigen aanwezigheidspatroon",
            "en": "Enter the children's names separated by commas.\n\nAre all children always home at the same time?\n• Yes  →  no co-parenting, no individual schedule\n• No   →  each child gets their own presence pattern",
            "de": "Gib die Namen der Kinder kommagetrennt ein.\n\nSind alle Kinder immer gleichzeitig bei dir?\n• Ja  →  keine Co-Elternschaft\n• Nein →  jedes Kind bekommt ein eigenes Anwesenheitsmuster",
            "fr": "Entrez les prénoms des enfants séparés par des virgules.\n\nLes enfants sont-ils toujours présents en même temps?\n• Oui  →  pas de co-parentalité\n• Non  →  chaque enfant a son propre planning",
        }
        return self.async_show_form(
            step_id="children",
            data_schema=vol.Schema({
                vol.Required("children"): str,
                vol.Optional("samen", default=True): bool,
            }),
            errors=errors,
            description_placeholders={"uitleg": descs.get(lang, descs["nl"])},
        )

    # ── Kind stap A: kleur + patroon ──────────────────────────────────────────
    async def async_step_child_a(self, ui=None):
        child = self._children[self._child_idx]
        n, total = self._child_idx + 1, len(self._children)
        lang = self._lang
        t    = _t(lang)

        if ui is not None:
            self._child_colors[child] = _color_key(ui.get("kleur", ""), lang)
            if self._together:
                # Geen patroon nodig: altijd aanwezig
                self._child_presence[child] = {
                    "mode": "altijd", "start_date": "", "start_present": True,
                    "days_present": [], "weeks_present": [], "blocked_days": [],
                    "override_present": None,
                }
                return await self._advance_child()
            chosen = ui.get("patroon", t["presence"][0])
            self._pending_mode[child] = chosen
            mode = t["presence_modes"][t["presence"].index(chosen)] if chosen in t["presence"] else "altijd"
            if mode == "altijd":
                self._child_presence[child] = {
                    "mode": "altijd", "start_date": "", "start_present": True,
                    "days_present": [], "weeks_present": [], "blocked_days": [],
                    "override_present": None,
                }
                return await self._advance_child()
            return await self.async_step_child_b()

        default_kleur = _default_color_label(self._child_idx, child, self._child_colors, lang)

        if self._together:
            desc = {"nl": f"Kind {n} van {total}: {child}\n\nKies een kleur voor het dashboard.",
                    "en": f"Child {n} of {total}: {child}\n\nChoose a colour for the dashboard.",
                    "de": f"Kind {n} von {total}: {child}\n\nFarbe für das Dashboard wählen.",
                    "fr": f"Enfant {n} sur {total}: {child}\n\nChoisissez une couleur pour le tableau de bord."}.get(lang, child)
            return self.async_show_form(
                step_id="child_a",
                data_schema=vol.Schema({
                    vol.Optional("kleur", default=default_kleur): vol.In(list(t["colors"].keys())),
                }),
                description_placeholders={"kind": child, "n": str(n), "total": str(total), "uitleg": desc},
            )

        return self.async_show_form(
            step_id="child_a",
            data_schema=vol.Schema({
                vol.Optional("kleur",   default=default_kleur):    vol.In(list(t["colors"].keys())),
                vol.Optional("patroon", default=t["presence"][1]): vol.In(t["presence"]),
            }),
            description_placeholders={
                "kind": child, "n": str(n), "total": str(total),
                "uitleg": f"Kind {n}/{total}: {child}\n\n" + t["desc_pattern"].replace("{kind}", child),
            },
        )

    # ── Kind stap B: vervolgvragen ────────────────────────────────────────────
    async def async_step_child_b(self, ui=None):
        child = self._children[self._child_idx]
        n, total = self._child_idx + 1, len(self._children)
        lang = self._lang
        t    = _t(lang)
        chosen = self._pending_mode.get(child, t["presence"][1])
        mode   = t["presence_modes"][t["presence"].index(chosen)] if chosen in t["presence"] else "om_de_week"
        cur    = self._child_presence.get(child, {})

        if ui is not None:
            days_present  = [i for i in range(7) if ui.get(f"dag_{i}", False)]
            weeks_raw     = [t["month_week_keys"][i] for i in range(4) if ui.get(f"mweek_{i}", False)]
            if ui.get("mweek_laatste", False):
                weeks_raw.append("Laatste week")
            blocked_days = [{"day": i, "reason": "blocked"} for i in range(7) if ui.get(f"blok_{i}", False)]
            self._child_presence[child] = {
                "mode":          mode,
                "start_date":    ui.get("startdatum", "2025-01-06"),
                "start_present": ui.get("startweek", True),
                "days_present":  days_present,
                "weeks_present": weeks_raw,
                "blocked_days":  blocked_days,
                "override_present": None,
            }
            return await self._advance_child()

        fields = {}
        desc_parts = [f"Kind {n}/{total}: {child}\n"]
        cur_days    = set(cur.get("days_present", []))
        cur_weeks   = set(cur.get("weeks_present", []))
        cur_blocked = {(b if isinstance(b, int) else b.get("day", -1)) for b in cur.get("blocked_days", [])}

        # Om de week
        if mode in ("om_de_week", "combinatie"):
            fields[vol.Optional("startdatum", default=cur.get("start_date", "2025-01-06"))] = str
            fields[vol.Optional("startweek",  default=cur.get("start_present", True))]      = bool
            desc_parts.append(t["desc_omdeweek"].replace("{kind}", child))

        # Vaste dagen
        if mode in ("vaste_dagen", "combinatie"):
            for i, dag in enumerate(t["days"]):
                fields[vol.Optional(f"dag_{i}", default=(i in cur_days))] = bool
            desc_parts.append(t["desc_vastedagen"].replace("{kind}", child))

        # Weken per maand
        if mode == "weken_per_maand":
            for i in range(4):
                wk_key = t["month_week_keys"][i]
                fields[vol.Optional(f"mweek_{i}", default=(wk_key in cur_weeks))] = bool
            fields[vol.Optional("mweek_laatste", default=("Laatste week" in cur_weeks))] = bool
            desc_parts.append(t["desc_wekenpermaand"].replace("{kind}", child))

        # Blokdagen altijd
        for i, dag in enumerate(t["days"]):
            fields[vol.Optional(f"blok_{i}", default=(i in cur_blocked))] = bool
        desc_parts.append(t["desc_blok"].replace("{kind}", child))

        return self.async_show_form(
            step_id="child_b",
            data_schema=vol.Schema(fields),
            description_placeholders={"uitleg": "\n\n".join(desc_parts), "kind": child},
        )

    async def _advance_child(self):
        self._child_idx += 1
        if self._child_idx < len(self._children):
            return await self.async_step_child_a()
        return await self.async_step_rotation_tasks()

    # ── Rotatietaken ──────────────────────────────────────────────────────────
    async def async_step_rotation_tasks(self, ui=None):
        lang = self._lang
        t    = _t(lang)
        if ui is not None:
            sel      = [DEFAULT_ROTATION_TASKS[i] for i in range(len(DEFAULT_ROTATION_TASKS)) if ui.get(f"taak_{i}", False)]
            extra    = [x.strip() for x in ui.get("extra_taken", "").split(",") if x.strip()]
            tasks    = sel + [x for x in extra if x not in sel]
            volgorde = [c.strip() for c in ui.get("volgorde", "").split(",") if c.strip() in self._children] or self._children
            self._rotation_tasks = [{"name": x, "fixed_child": None, "children_order": volgorde} for x in tasks]
            return await self.async_step_week_tasks()

        fields = {vol.Optional(f"taak_{i}", default=True): bool for i in range(len(DEFAULT_ROTATION_TASKS))}
        fields[vol.Optional("extra_taken", default="")] = str
        fields[vol.Optional("volgorde",    default=", ".join(self._children))] = str
        return self.async_show_form(
            step_id="rotation_tasks",
            data_schema=vol.Schema(fields),
            description_placeholders={"uitleg": t["desc_rotation"]},
        )

    # ── Weektaken ─────────────────────────────────────────────────────────────
    async def async_step_week_tasks(self, ui=None):
        lang = self._lang
        t    = _t(lang)
        ch0  = self._children[0] if self._children else ""
        ch1  = self._children[1] if len(self._children) > 1 else ch0

        if ui is not None:
            sel   = [DEFAULT_WEEK_TASKS[i] for i in range(len(DEFAULT_WEEK_TASKS)) if ui.get(f"wtaak_{i}", False)]
            extra = [x.strip() for x in ui.get("extra_taken", "").split(",") if x.strip()]
            tasks = sel + [x for x in extra if x not in sel]
            result = []
            for i, task in enumerate(tasks):
                dag_label   = ui.get(f"wdag_{i}", t["days"][2])       # string dagnaam
                modus_label = ui.get(f"wmodus_{i}", t["week_modes"][0])
                # dag_label is nu altijd een echte dagnaam (via vol.In)
                day_nl = _dag_to_nl(dag_label, lang)
                mode_key = t["week_mode_keys"][t["week_modes"].index(modus_label)] if modus_label in t["week_modes"] else "auto_rotate"
                result.append({
                    "name": task, "day": day_nl, "mode": mode_key,
                    "fixed_child": ch0, "even_child": ch0, "odd_child": ch1,
                    "children_order": self._children,
                })
            self._week_tasks = result
            return await self.async_step_month_tasks()

        fields = {}
        for i, task in enumerate(DEFAULT_WEEK_TASKS):
            fields[vol.Optional(f"wtaak_{i}", default=False)]                  = bool
            fields[vol.Optional(f"wdag_{i}",  default=t["days"][2])]           = vol.In(t["days"])
            fields[vol.Optional(f"wmodus_{i}",default=t["week_modes"][0])]     = vol.In(t["week_modes"])
        fields[vol.Optional("extra_taken", default="")] = str
        return self.async_show_form(
            step_id="week_tasks",
            data_schema=vol.Schema(fields),
            description_placeholders={"uitleg": t["desc_week"]},
        )

    # ── Maandtaken ────────────────────────────────────────────────────────────
    async def async_step_month_tasks(self, ui=None):
        lang = self._lang
        t    = _t(lang)

        if ui is not None:
            sel   = [DEFAULT_MONTH_TASKS[i] for i in range(len(DEFAULT_MONTH_TASKS)) if ui.get(f"mtaak_{i}", False)]
            extra = [x.strip() for x in ui.get("extra_taken", "").split(",") if x.strip()]
            tasks = sel + [x for x in extra if x not in sel]
            result = []
            for i, task in enumerate(tasks):
                wk_label  = ui.get(f"mwk_{i}",  t["month_weeks"][-1])
                dag_label = ui.get(f"mdag_{i}", t["days"][-1])
                wk_nl  = t["month_week_keys"][t["month_weeks"].index(wk_label)] if wk_label in t["month_weeks"] else "Laatste week"
                dag_nl = _dag_to_nl(dag_label, lang)
                result.append({
                    "name": task, "all_children": True,
                    "week_of_month": wk_nl, "day_of_week": dag_nl,
                    "assignments": {},
                })
            self._month_tasks = result
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

        fields = {}
        for i, task in enumerate(DEFAULT_MONTH_TASKS):
            fields[vol.Optional(f"mtaak_{i}", default=True)]                    = bool
            fields[vol.Optional(f"mwk_{i}",   default=t["month_weeks"][-1])]   = vol.In(t["month_weeks"])
            fields[vol.Optional(f"mdag_{i}",   default=t["days"][-1])]         = vol.In(t["days"])
        fields[vol.Optional("extra_taken", default="")] = str
        return self.async_show_form(
            step_id="month_tasks",
            data_schema=vol.Schema(fields),
            description_placeholders={"uitleg": t["desc_month"]},
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry):
        return KindertakenOptionsFlow(entry)


# ── Dag-conversie helper ──────────────────────────────────────────────────────

_DAG_NL = {
    "nl": ["Maandag","Dinsdag","Woensdag","Donderdag","Vrijdag","Zaterdag","Zondag"],
    "en": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
    "de": ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"],
    "fr": ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"],
}
_NL_DAYS = ["Maandag","Dinsdag","Woensdag","Donderdag","Vrijdag","Zaterdag","Zondag"]

def _dag_to_nl(label: str, lang: str) -> str:
    """Vertaal dagnaam naar NL (intern formaat voor scheduler)."""
    days_lang = _DAG_NL.get(lang, _NL_DAYS)
    try:
        return _NL_DAYS[days_lang.index(label)]
    except (ValueError, IndexError):
        return label  # al NL of onbekend


# ── Options flow ──────────────────────────────────────────────────────────────

class KindertakenOptionsFlow(config_entries.OptionsFlow):

    def __init__(self, entry):
        self._entry          = entry
        d                    = entry.data
        self._lang           = d.get("lang", "nl")
        self._children       = list(d.get(CONF_CHILDREN, []))
        self._child_colors   = dict(d.get(CONF_CHILD_COLORS, {}))
        self._child_presence = dict(d.get(CONF_CHILD_PRESENCE, {}))
        self._rotation_tasks = list(d.get(CONF_ROTATION_TASKS, []))
        self._week_tasks     = list(d.get(CONF_WEEK_TASKS, []))
        self._month_tasks    = list(d.get(CONF_MONTH_TASKS, []))
        self._edit_child     = None
        self._pending_mode   = {}

    def _save(self, updates: dict):
        new = dict(self._entry.data)
        new.update(updates)
        return self.async_create_entry(title="", data=new)

    async def async_step_init(self, ui=None):
        return self.async_show_menu(step_id="init", menu_options=[
            "edit_children", "edit_child_settings",
            "edit_rotation_tasks", "edit_week_tasks", "edit_month_tasks",
        ])

    # ── Kinderen ──────────────────────────────────────────────────────────────
    async def async_step_edit_children(self, ui=None):
        errors = {}
        if ui is not None:
            ch = [c.strip() for c in ui.get("children", "").split(",") if c.strip()]
            if not ch: errors["children"] = "min_one_child"
            else: return self._save({CONF_CHILDREN: ch})
        return self.async_show_form(
            step_id="edit_children",
            data_schema=vol.Schema({vol.Required("children", default=", ".join(self._children)): str}),
            errors=errors,
        )

    # ── Kind-instellingen ─────────────────────────────────────────────────────
    async def async_step_edit_child_settings(self, ui=None):
        if ui is not None:
            self._edit_child = ui.get("kind", "")
            return await self.async_step_edit_child_a()
        return self.async_show_form(
            step_id="edit_child_settings",
            data_schema=vol.Schema({vol.Required("kind"): vol.In(self._children)}),
        )

    async def async_step_edit_child_a(self, ui=None):
        child = self._edit_child
        lang  = self._lang
        t     = _t(lang)
        idx   = self._children.index(child) if child in self._children else 0
        cur   = self._child_presence.get(child, {})

        if ui is not None:
            self._child_colors[child] = _color_key(ui.get("kleur", ""), lang)
            chosen = ui.get("patroon", t["presence"][0])
            self._pending_mode[child] = chosen
            mode = t["presence_modes"][t["presence"].index(chosen)] if chosen in t["presence"] else "altijd"
            if mode == "altijd":
                self._child_presence[child] = {
                    "mode": "altijd", "start_date": "", "start_present": True,
                    "days_present": [], "weeks_present": [], "blocked_days": [],
                    "override_present": None,
                }
                return self._save({CONF_CHILD_COLORS: self._child_colors, CONF_CHILD_PRESENCE: self._child_presence})
            return await self.async_step_edit_child_b()

        cur_mode  = _presence_label(cur.get("mode", "altijd"), lang)
        cur_kleur = _default_color_label(idx, child, self._child_colors, lang)
        return self.async_show_form(
            step_id="edit_child_a",
            data_schema=vol.Schema({
                vol.Optional("kleur",   default=cur_kleur): vol.In(list(t["colors"].keys())),
                vol.Optional("patroon", default=cur_mode):  vol.In(t["presence"]),
            }),
            description_placeholders={
                "uitleg": t["desc_pattern"].replace("{kind}", child),
                "kind": child,
            },
        )

    async def async_step_edit_child_b(self, ui=None):
        child  = self._edit_child
        lang   = self._lang
        t      = _t(lang)
        chosen = self._pending_mode.get(child, t["presence"][1])
        mode   = t["presence_modes"][t["presence"].index(chosen)] if chosen in t["presence"] else "om_de_week"
        cur    = self._child_presence.get(child, {})

        if ui is not None:
            days_present  = [i for i in range(7) if ui.get(f"dag_{i}", False)]
            weeks_raw     = [t["month_week_keys"][i] for i in range(4) if ui.get(f"mweek_{i}", False)]
            if ui.get("mweek_laatste", False): weeks_raw.append("Laatste week")
            blocked_days  = [{"day": i, "reason": "blocked"} for i in range(7) if ui.get(f"blok_{i}", False)]
            self._child_presence[child] = {
                "mode": mode, "start_date": ui.get("startdatum", "2025-01-06"),
                "start_present": ui.get("startweek", True), "days_present": days_present,
                "weeks_present": weeks_raw, "blocked_days": blocked_days, "override_present": None,
            }
            return self._save({CONF_CHILD_COLORS: self._child_colors, CONF_CHILD_PRESENCE: self._child_presence})

        fields = {}
        desc_parts = [child]
        cur_days    = set(cur.get("days_present", []))
        cur_weeks   = set(cur.get("weeks_present", []))
        cur_blocked = {(b if isinstance(b, int) else b.get("day", -1)) for b in cur.get("blocked_days", [])}

        if mode in ("om_de_week", "combinatie"):
            fields[vol.Optional("startdatum", default=cur.get("start_date", "2025-01-06"))] = str
            fields[vol.Optional("startweek",  default=cur.get("start_present", True))]      = bool
            desc_parts.append(t["desc_omdeweek"].replace("{kind}", child))
        if mode in ("vaste_dagen", "combinatie"):
            for i in range(7): fields[vol.Optional(f"dag_{i}", default=(i in cur_days))] = bool
            desc_parts.append(t["desc_vastedagen"].replace("{kind}", child))
        if mode == "weken_per_maand":
            for i in range(4): fields[vol.Optional(f"mweek_{i}", default=(t["month_week_keys"][i] in cur_weeks))] = bool
            fields[vol.Optional("mweek_laatste", default=("Laatste week" in cur_weeks))] = bool
            desc_parts.append(t["desc_wekenpermaand"].replace("{kind}", child))
        for i in range(7): fields[vol.Optional(f"blok_{i}", default=(i in cur_blocked))] = bool
        desc_parts.append(t["desc_blok"].replace("{kind}", child))

        return self.async_show_form(
            step_id="edit_child_b",
            data_schema=vol.Schema(fields),
            description_placeholders={"uitleg": "\n\n".join(desc_parts), "kind": child},
        )

    # ── Taken bewerken ────────────────────────────────────────────────────────
    async def async_step_edit_rotation_tasks(self, ui=None):
        lang = self._lang
        t    = _t(lang)
        if ui is not None:
            sel      = [DEFAULT_ROTATION_TASKS[i] for i in range(len(DEFAULT_ROTATION_TASKS)) if ui.get(f"taak_{i}", False)]
            extra    = [x.strip() for x in ui.get("extra_taken", "").split(",") if x.strip()]
            ee       = [x["name"] for x in self._rotation_tasks if x["name"] not in DEFAULT_ROTATION_TASKS]
            tasks    = sel + [x for x in (extra if extra else ee) if x not in sel]
            volgorde = [c.strip() for c in ui.get("volgorde", "").split(",") if c.strip() in self._children] or self._children
            return self._save({CONF_ROTATION_TASKS: [{"name": x, "fixed_child": None, "children_order": volgorde} for x in tasks]})
        cur_vol = (self._rotation_tasks[0].get("children_order") or self._children) if self._rotation_tasks else self._children
        ee      = [x["name"] for x in self._rotation_tasks if x["name"] not in DEFAULT_ROTATION_TASKS]
        fields  = {vol.Optional(f"taak_{i}", default=any(x["name"] == DEFAULT_ROTATION_TASKS[i] for x in self._rotation_tasks)): bool
                   for i in range(len(DEFAULT_ROTATION_TASKS))}
        fields[vol.Optional("extra_taken", default=", ".join(ee))]     = str
        fields[vol.Optional("volgorde",    default=", ".join(cur_vol))] = str
        return self.async_show_form(step_id="edit_rotation_tasks", data_schema=vol.Schema(fields),
                                    description_placeholders={"uitleg": t["desc_rotation"]})

    async def async_step_edit_week_tasks(self, ui=None):
        lang = self._lang
        t    = _t(lang)
        ch0  = self._children[0] if self._children else ""
        ch1  = self._children[1] if len(self._children) > 1 else ch0
        if ui is not None:
            sel   = [DEFAULT_WEEK_TASKS[i] for i in range(len(DEFAULT_WEEK_TASKS)) if ui.get(f"wtaak_{i}", False)]
            extra = [x.strip() for x in ui.get("extra_taken", "").split(",") if x.strip()]
            ee    = [x["name"] for x in self._week_tasks if x["name"] not in DEFAULT_WEEK_TASKS]
            tasks = sel + [x for x in (extra if extra else ee) if x not in sel]
            existing = {x["name"]: x for x in self._week_tasks}
            result = []
            for i, task in enumerate(tasks):
                ex = existing.get(task, {})
                dag_label   = ui.get(f"wdag_{i}",   t["days"][2])
                modus_label = ui.get(f"wmodus_{i}", t["week_modes"][0])
                mode_key = t["week_mode_keys"][t["week_modes"].index(modus_label)] if modus_label in t["week_modes"] else "auto_rotate"
                result.append({"name": task, "day": _dag_to_nl(dag_label, lang), "mode": mode_key,
                                "fixed_child": ex.get("fixed_child", ch0), "even_child": ex.get("even_child", ch0),
                                "odd_child": ex.get("odd_child", ch1), "children_order": self._children})
            return self._save({CONF_WEEK_TASKS: result})
        existing = {x["name"]: x for x in self._week_tasks}
        fields = {}
        for i, task in enumerate(DEFAULT_WEEK_TASKS):
            ex = existing.get(task, {})
            cur_dag   = _dag_to_lang(ex.get("day", "Woensdag"), lang)
            cur_modus = _week_mode_label(ex.get("mode", "auto_rotate"), lang)
            fields[vol.Optional(f"wtaak_{i}", default=(task in existing))]  = bool
            fields[vol.Optional(f"wdag_{i}",  default=cur_dag)]             = vol.In(t["days"])
            fields[vol.Optional(f"wmodus_{i}",default=cur_modus)]           = vol.In(t["week_modes"])
        ee = [x["name"] for x in self._week_tasks if x["name"] not in DEFAULT_WEEK_TASKS]
        fields[vol.Optional("extra_taken", default=", ".join(ee))] = str
        return self.async_show_form(step_id="edit_week_tasks", data_schema=vol.Schema(fields),
                                    description_placeholders={"uitleg": t["desc_week"]})

    async def async_step_edit_month_tasks(self, ui=None):
        lang = self._lang
        t    = _t(lang)
        if ui is not None:
            sel   = [DEFAULT_MONTH_TASKS[i] for i in range(len(DEFAULT_MONTH_TASKS)) if ui.get(f"mtaak_{i}", False)]
            extra = [x.strip() for x in ui.get("extra_taken", "").split(",") if x.strip()]
            ee    = [x["name"] for x in self._month_tasks if x["name"] not in DEFAULT_MONTH_TASKS]
            tasks = sel + [x for x in (extra if extra else ee) if x not in sel]
            result = []
            for i, task in enumerate(tasks):
                wk_label  = ui.get(f"mwk_{i}",  t["month_weeks"][-1])
                dag_label = ui.get(f"mdag_{i}", t["days"][-1])
                wk_nl  = t["month_week_keys"][t["month_weeks"].index(wk_label)] if wk_label in t["month_weeks"] else "Laatste week"
                result.append({"name": task, "all_children": True, "week_of_month": wk_nl,
                                "day_of_week": _dag_to_nl(dag_label, lang), "assignments": {}})
            return self._save({CONF_MONTH_TASKS: result})
        existing = {x["name"]: x for x in self._month_tasks}
        fields = {}
        for i, task in enumerate(DEFAULT_MONTH_TASKS):
            ex = existing.get(task, {})
            cur_wk  = _month_week_label(ex.get("week_of_month", "Laatste week"), lang)
            cur_dag = _dag_to_lang(ex.get("day_of_week", "Zondag"), lang)
            fields[vol.Optional(f"mtaak_{i}", default=(task in existing))] = bool
            fields[vol.Optional(f"mwk_{i}",   default=cur_wk)]             = vol.In(t["month_weeks"])
            fields[vol.Optional(f"mdag_{i}",   default=cur_dag)]           = vol.In(t["days"])
        ee = [x["name"] for x in self._month_tasks if x["name"] not in DEFAULT_MONTH_TASKS]
        fields[vol.Optional("extra_taken", default=", ".join(ee))] = str
        return self.async_show_form(step_id="edit_month_tasks", data_schema=vol.Schema(fields),
                                    description_placeholders={"uitleg": t["desc_month"]})


def _dag_to_lang(nl_day: str, lang: str) -> str:
    """Vertaal NL dagnaam naar gewenste taal."""
    try:
        return _DAG_NL.get(lang, _NL_DAYS)[_NL_DAYS.index(nl_day)]
    except (ValueError, IndexError):
        return nl_day
