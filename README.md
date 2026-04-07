# 📋 Kindertaken Planner — Home Assistant integratie

Kindvriendelijke HACS integratie voor het bijhouden van huishoudtaken per kind. Ondersteunt co-ouderschap, automatische rotatie, en week- en maandtaken.

**Talen:** 🇳🇱 Nederlands · 🇬🇧 English · 🇩🇪 Deutsch · 🇫🇷 Français

---

## ✨ Functies

| Functie | Details |
|---------|---------|
| 👦👧 Flexibel | 1–8 kinderen, namen vrij in te stellen |
| 🎨 Kleuren | Elke kind een eigen kleur + emoji op het dashboard |
| 🏠 Co-ouderschap | Om de week, vaste dagen, bepaalde weken per maand, of combinatie |
| ⛔ Blokdagen | Kind is thuis maar heeft die dag geen tijd (werk, sport) |
| 🔄 Rotatietaken | Dagelijks, roulerend — systeem berekent automatisch wie aan de beurt is |
| 📅 Weektaken | Wekelijks op vaste dag — automatisch, even/oneven weken, of vast kind |
| 🗓️ Maandtaken | 1× per maand, vaste week + dag — automatisch doorschuiven bij afwezigheid |
| ✅ Afvinken | Taken op het dashboard aanklikken = afgevinkt (persistent na herstart) |
| 🔁 Eerlijke verdeling | Afwezig kind? Taken gaan naar kind met minste taken die dag |

---

## 📦 Installatie

### 1. Bestanden kopiëren

Pak het ZIP-bestand uit en kopieer:

```
config/
├── custom_components/
│   └── kindertaken/          ← kopieer deze map volledig
└── www/
    └── kindertaken-card/
        └── kindertaken-card.js   ← kopieer dit bestand
```

### 2. Lovelace resource registreren

**Instellingen → Dashboard → Hulpbronnen → Toevoegen:**

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

**Instellingen → Apparaten & Diensten → + Integratie toevoegen → "Kindertaken"**

De wizard begeleidt je stap voor stap:
1. **Taal kiezen** — NL / EN / DE / FR
2. **Kinderen** — namen invoeren + zijn ze tegelijk thuis?
3. **Per kind** — kleur + aanwezigheidspatroon instellen
4. **Rotatietaken** — dagelijkse taken die automatisch rouleren
5. **Weektaken** — wekelijks op vaste dag
6. **Maandtaken** — maandelijks met vaste week + dag

### 5. Dashboard kaart toevoegen

```yaml
type: custom:kindertaken-card
entity: sensor.kindertaken_week
```

---

## ⚙️ Aanwezigheidspatronen

| Patroon | Gebruik |
|---------|---------|
| 🏠 Altijd thuis | Kind woont altijd bij jou |
| 🔄 Om de week | Co-ouderschap week-op-week-af. Startdatum = eerste maandag van week A |
| 📅 Vaste dagen | Bijv. elk weekend (vr/za/zo) bij jou |
| 🗓️ Bepaalde weken | Bijv. 1e en 3e week van de maand |
| 🔄📅 Combinatie | Om de week én alleen op vaste dagen |

---

## 🔧 Services

### `kindertaken.mark_done`
Vinkt een taak af (of maakt hem ongedaan — toggle).
```yaml
service: kindertaken.mark_done
data:
  key: "rot__2025-01-06__Emma__Afwasmachine vullen"
```

### `kindertaken.set_presence`
Handmatige override van aanwezigheid. Handig voor afwijkende weken.
```yaml
service: kindertaken.set_presence
data:
  child: "Emma"
  present: false   # true / false / null (reset naar automatisch)
```

### `kindertaken.reset_week`
Reset alle afgevinkte weektaken (maandtaken blijven).

### `kindertaken.reset_all`
Reset alle afgevinkte taken.

---

## 🤖 Handige automatiseringen

### Wekelijkse reset (elke maandag om middernacht)
```yaml
automation:
  - alias: "Kindertaken wekelijks resetten"
    trigger:
      platform: time
      at: "00:01:00"
    condition:
      condition: time
      weekday: [mon]
    action:
      service: kindertaken.reset_week
```

### Aanwezigheid via schakelaar (input_boolean)
```yaml
automation:
  - alias: "Emma aanwezigheid bijwerken"
    trigger:
      platform: state
      entity_id: input_boolean.emma_thuis
    action:
      service: kindertaken.set_presence
      data:
        child: "Emma"
        present: "{{ trigger.to_state.state == 'on' }}"
```

### Felicitatie als kind klaar is
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
      service: notify.mobile_app
      data:
        title: "🎉 Goed gedaan Emma!"
        message: "Alle taken van vandaag zijn klaar!"
```

---

## 🧩 Entiteiten

| Entiteit | Beschrijving |
|----------|-------------|
| `sensor.kindertaken_week` | Volledig weekoverzicht — gebruikt door de dashboard kaart |
| `sensor.kindertaken_<naam>` | Taken van vandaag per kind |

### Attributen `sensor.kindertaken_<naam>`
```
child:           "Emma"
tasks_today:     [{task, icon, type, done, date, key}, ...]
total:           2
done_count:      1
all_done:        false
free_day:        false
present:         true
available:       true
```
