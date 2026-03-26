"""Constanten voor de Kindertaken Planner."""

DOMAIN = "kindertaken"
PLATFORMS = ["sensor"]

# Configuratie sleutels
CONF_CHILDREN = "children"
CONF_CHILD_COLORS = "child_colors"
CONF_TASKS = "tasks"
CONF_MONTH_TASKS = "month_tasks"
CONF_SCHEDULE = "schedule"
CONF_MONTH_SCHEDULE = "month_schedule"

# Standaard taken
DEFAULT_TASKS = [
    "Afwasmachine vullen",
    "Tafel dekken/opruimen",
    "Stofzuigen",
    "Vuilnis buiten",
]

# Standaard maandtaken
DEFAULT_MONTH_TASKS = [
    "Kamer opruimen",
    "Ramen lappen",
    "Badkamer schoonmaken",
]

# Dagen van de week (NL)
DAYS_NL = [
    "Maandag", "Dinsdag", "Woensdag", "Donderdag",
    "Vrijdag", "Zaterdag", "Zondag",
]

DAY_MAP = {
    "Maandag": 0, "Dinsdag": 1, "Woensdag": 2, "Donderdag": 3,
    "Vrijdag": 4, "Zaterdag": 5, "Zondag": 6,
}

# Maanden (NL)
MONTHS_NL = [
    "Januari", "Februari", "Maart", "April", "Mei", "Juni",
    "Juli", "Augustus", "September", "Oktober", "November", "December",
]

# Taak iconen
TASK_ICON_LIST = ["🍽️", "🪑", "🧹", "🗑️", "🛒", "🐶", "🌱", "🧺", "🪥", "🧴"]
MONTH_TASK_ICON_LIST = ["🏠", "🪟", "🛁", "🧽", "🪴", "📦", "🛋️", "🪣", "🧹", "✨"]

# Kleuropties voor kinderen (naam → [donker, licht])
CHILD_COLOR_OPTIONS = {
    "Blauw":    ["#1565C0", "#42A5F5"],
    "Groen":    ["#2E7D32", "#66BB6A"],
    "Oranje":   ["#E65100", "#FFA726"],
    "Roze":     ["#AD1457", "#F48FB1"],
    "Paars":    ["#6A1B9A", "#CE93D8"],
    "Teal":     ["#00695C", "#4DB6AC"],
    "Indigo":   ["#283593", "#7986CB"],
    "Rood":     ["#B71C1C", "#EF9A9A"],
    "Geel":     ["#F57F17", "#FFF176"],
    "Cyaan":    ["#006064", "#80DEEA"],
}

# Emoji's per kleur
COLOR_EMOJI = {
    "Blauw": "⭐", "Groen": "🌟", "Oranje": "🎯", "Roze": "🌈",
    "Paars": "🦋", "Teal": "🚀", "Indigo": "🏆", "Rood": "💎",
    "Geel": "🌻", "Cyaan": "🌊",
}

# Standaard kleurvolgorde
DEFAULT_COLOR_ORDER = list(CHILD_COLOR_OPTIONS.keys())
