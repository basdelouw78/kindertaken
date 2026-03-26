# 📋 Kindertaken Planner — Home Assistant integratie

Een kindvriendelijke HACS integratie waarmee kinderen op het dashboard **in één oogopslag** zien welke taken zij die dag hebben. Inclusief weekkalender, afvinkfunctie en eenvoudige configuratie via de HA UI.

---

## ✨ Wat doet het?

| Functie | Details |
|--------|---------|
| 👦👧 **Flexibel aantal kinderen** | 1 tot 8 kinderen, namen vrij in te stellen |
| 📅 **Vandaag-overzicht** | Grote, gekleurde kaart per kind met hun taken van vandaag |
| 📆 **Weekkalender** | Alle 7 dagen in één raster met taken per kind |
| ✅ **Aftikken** | Taken aanklikken = afgevinkt (toggle, persistente opslag) |
| ⚙️ **UI-configuratie** | Alles instelbaar via Instellingen, geen YAML nodig |
| 🔄 **Services** | Taken afvinken, week resetten, kind toevoegen |

### Taken
- 🍽️ Afwasmachine vullen
- 🪑 Tafel dekken/opruimen
- 🧹 Stofzuigen
- 🗑️ Vuilnis buiten

---

## 📦 Installatie

### 1. Bestanden kopiëren

Pak het ZIP-bestand uit en kopieer de mappen naar je HA configuratiemap:

```
config/
├── custom_components/
│   └── kindertaken/          ← kopieer deze map
│       ├── __init__.py
│       ├── config_flow.py
│       ├── const.py
│       ├── manifest.json
│       ├── sensor.py
│       ├── services.yaml
│       └── translations/
│           └── nl.json
└── www/
    └── kindertaken-card/
        └── kindertaken-card.js   ← kopieer deze map
```

### 2. Lovelace resource registreren

Ga naar **Instellingen → Dashboard → Hulpbronnen** en voeg toe:

| URL | Type |
|-----|------|
| `/local/kindertaken-card/kindertaken-card.js` | JavaScript module |

Of in `configuration.yaml`:
```yaml
lovelace:
  resources:
    - url: /local/kindertaken-card/kindertaken-card.js
      type: module
```

### 3. Home Assistant herstarten

### 4. Integratie instellen

1. **Instellingen → Apparaten & Diensten → + Integratie toevoegen**
2. Zoek op **Kindertaken**
3. **Stap 1**: Voer namen in, bijv. `Emma, Liam` of `Sophie, Thomas, Mia`
4. **Stap 2**: Wijs per dag en taak een kind toe

### 5. Kaart toevoegen aan dashboard

```yaml
type: custom:kindertaken-card
entity: sensor.kindertaken_week
```

---

## ⚙️ Planning aanpassen

Ga naar **Instellingen → Apparaten & Diensten → Kindertaken → Configureren**. Je kunt kiezen:
- **Kinderen beheren** — namen toevoegen of wijzigen
- **Weekplanning aanpassen** — taken opnieuw verdelen

---

## 🔧 Services

### `kindertaken.mark_done`
Vinkt een taak af (of maakt hem ongedaan bij opnieuw aanroepen — toggle).

```yaml
service: kindertaken.mark_done
data:
  child: "Emma"
  task: "Afwasmachine vullen"
  # date: "2024-09-02"  # optioneel, standaard = vandaag
```

### `kindertaken.reset_week`
Reset alle afgevinkte taken van de huidige week.
```yaml
service: kindertaken.reset_week
```

### `kindertaken.add_child`
Voegt een kind toe zonder HA-herstart.
```yaml
service: kindertaken.add_child
data:
  name: "Sophie"
```

---

## 🤖 Automatisering voorbeelden

### Wekelijks resetten (elke maandag om middernacht)
```yaml
automation:
  - alias: "Kindertaken wekelijkse reset"
    trigger:
      platform: time
      at: "00:01:00"
    condition:
      condition: time
      weekday: [mon]
    action:
      service: kindertaken.reset_week
```

### Felicitatie als kind alle taken heeft afgedaan
```yaml
automation:
  - alias: "Emma alle taken klaar"
    trigger:
      platform: state
      entity_id: sensor.kindertaken_emma
    condition:
      condition: template
      value_template: "{{ state_attr('sensor.kindertaken_emma', 'all_done') }}"
    action:
      service: notify.mobile_app_telefoon_emma
      data:
        title: "🎉 Goed gedaan Emma!"
        message: "Al je taken van vandaag zijn klaar!"
```

---

## 🧩 Entiteiten

| Entiteit | Beschrijving |
|----------|-------------|
| `sensor.kindertaken_week` | Volledig weekoverzicht (gebruikt door de kaart) |
| `sensor.kindertaken_<naam>` | Taken van vandaag per kind |

### Attributen `sensor.kindertaken_<naam>`
```
child: "Emma"
tasks_today: [{task, icon, done, date}, ...]
total: 2
done_count: 1
all_done: false
free_day: false
```
