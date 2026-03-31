"""Constanten voor de Kindertaken Planner v2.2."""

DOMAIN = "kindertaken"
PLATFORMS = ["sensor"]

CONF_CHILDREN           = "children"
CONF_CHILD_COLORS       = "child_colors"
CONF_CHILD_PRESENCE     = "child_presence"
CONF_ROTATION_TASKS     = "rotation_tasks"
CONF_WEEK_TASKS         = "week_tasks"
CONF_MONTH_TASKS        = "month_tasks"

DAYS_NL   = ["Maandag","Dinsdag","Woensdag","Donderdag","Vrijdag","Zaterdag","Zondag"]
DAYS_SHORT= ["Ma","Di","Wo","Do","Vr","Za","Zo"]
DAY_MAP   = {"Maandag":0,"Dinsdag":1,"Woensdag":2,"Donderdag":3,"Vrijdag":4,"Zaterdag":5,"Zondag":6}
MONTHS_NL = ["Januari","Februari","Maart","April","Mei","Juni","Juli","Augustus","September","Oktober","November","December"]

WEEK_OF_MONTH_OPTIONS = ["1e week","2e week","3e week","4e week","Laatste week"]

# Aanwezigheidspatronen
PRESENCE_MODES = {
    "Altijd aanwezig":                      "altijd",
    "Om de week (startdatum + wissel)":     "om_de_week",
    "Vaste dagen per week":                 "vaste_dagen",
    "Bepaalde weken per maand":             "weken_per_maand",
    "Combinatie: om de week + vaste dagen": "combinatie",
}

DEFAULT_ROTATION_TASKS = ["Afwasmachine vullen","Tafel dekken/opruimen"]
DEFAULT_WEEK_TASKS     = ["Stofzuigen","Vuilnis buiten","Plastic buiten","Container buiten","Afvalbakken leegmaken"]
DEFAULT_MONTH_TASKS    = ["Kamer opruimen","Ramen lappen","Badkamer schoonmaken"]

TASK_ICON_LIST = ["🍽️","🪑","🧹","🗑️","♻️","🗃️","🪣","🛒","🐶","🌱","🧺","🏠","🪟","🛁","✨"]

CHILD_COLOR_OPTIONS = {
    "Blauw":  ["#1565C0","#42A5F5"],
    "Groen":  ["#2E7D32","#66BB6A"],
    "Oranje": ["#E65100","#FFA726"],
    "Roze":   ["#AD1457","#F48FB1"],
    "Paars":  ["#6A1B9A","#CE93D8"],
    "Teal":   ["#00695C","#4DB6AC"],
    "Indigo": ["#283593","#7986CB"],
    "Rood":   ["#B71C1C","#EF9A9A"],
    "Geel":   ["#F57F17","#FFF176"],
    "Cyaan":  ["#006064","#80DEEA"],
}
COLOR_EMOJI      = {"Blauw":"⭐","Groen":"🌟","Oranje":"🎯","Roze":"🌈","Paars":"🦋","Teal":"🚀","Indigo":"🏆","Rood":"💎","Geel":"🌻","Cyaan":"🌊"}
DEFAULT_COLOR_ORDER = list(CHILD_COLOR_OPTIONS.keys())
