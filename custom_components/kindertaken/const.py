"""Constanten voor de Kindertaken Planner."""

DOMAIN = "kindertaken"
PLATFORMS = ["sensor"]

# Configuratie sleutels
CONF_CHILDREN = "children"
CONF_TASKS = "tasks"
CONF_SCHEDULE = "schedule"

# Standaard taken (gebruiker kan zelf aanpassen/toevoegen tijdens setup)
DEFAULT_TASKS = [
    "Afwasmachine vullen",
    "Tafel dekken/opruimen",
    "Stofzuigen",
    "Vuilnis buiten",
]

# Dagen van de week (NL)
DAYS_NL = [
    "Maandag",
    "Dinsdag",
    "Woensdag",
    "Donderdag",
    "Vrijdag",
    "Zaterdag",
    "Zondag",
]

# Dag nummers (Python weekday: 0=maandag)
DAY_MAP = {
    "Maandag": 0,
    "Dinsdag": 1,
    "Woensdag": 2,
    "Donderdag": 3,
    "Vrijdag": 4,
    "Zaterdag": 5,
    "Zondag": 6,
}

# Taak iconen voor de UI (automatisch toegewezen op volgorde)
TASK_ICON_LIST = ["🍽️", "🪑", "🧹", "🗑️", "🛒", "🐶", "🌱", "🧺", "🪥", "🧴"]
