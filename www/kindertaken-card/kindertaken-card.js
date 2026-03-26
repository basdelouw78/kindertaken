/**
 * Kindertaken Planner Card v1.2
 * Kindvriendelijke weekkaart voor Home Assistant
 *
 * Gebruik in Lovelace:
 *   type: custom:kindertaken-card
 */

const THEMES = [
  { bg: "#1565C0", light: "#42A5F5", emoji: "⭐" },
  { bg: "#2E7D32", light: "#66BB6A", emoji: "🌟" },
  { bg: "#E65100", light: "#FFA726", emoji: "🎯" },
  { bg: "#AD1457", light: "#F48FB1", emoji: "🌈" },
  { bg: "#6A1B9A", light: "#CE93D8", emoji: "🦋" },
  { bg: "#00695C", light: "#4DB6AC", emoji: "🚀" },
  { bg: "#4527A0", light: "#9575CD", emoji: "🏆" },
  { bg: "#BF360C", light: "#FF8A65", emoji: "💎" },
];

const DAYS_SHORT = ["Ma","Di","Wo","Do","Vr","Za","Zo"];
const DAYS_FULL  = ["Maandag","Dinsdag","Woensdag","Donderdag","Vrijdag","Zaterdag","Zondag"];

class KindertakenCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._themes = {};
  }

  setConfig(config) {
    if (!config) throw new Error("Geen configuratie opgegeven.");
    this._config = Object.assign({ entity: "sensor.kindertaken_week" }, config);
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    const hass = this._hass;
    const entityId = this._config.entity;
    const state = hass.states[entityId];

    if (!state) {
      this.shadowRoot.innerHTML = '<ha-card><div style="padding:20px;color:#c62828">Entiteit niet gevonden: ' + entityId + '</div></ha-card>';
      return;
    }

    const attrs = state.attributes;
    const week = attrs.week || {};
    const children = attrs.children || [];
    const today_name = attrs.today_name || "";

    children.forEach(function(c, i) {
      if (!this._themes[c]) this._themes[c] = THEMES[i % THEMES.length];
    }, this);

    var todayData = week[today_name] || {};
    var todayTasks = todayData.tasks || [];
    var byChild = {};
    children.forEach(function(c) { byChild[c] = []; });
    todayTasks.forEach(function(t) {
      if (byChild[t.child] !== undefined) byChild[t.child].push(t);
    });

    this.shadowRoot.innerHTML =
      '<style>' + this._css() + '</style>' +
      '<ha-card>' +
        this._header(today_name) +
        this._todaySection(children, byChild) +
        this._weekSection(week, children) +
      '</ha-card>';

    var self = this;
    this.shadowRoot.querySelectorAll(".task-btn").forEach(function(btn) {
      btn.addEventListener("click", function() {
        var child = btn.dataset.child;
        var task  = btn.dataset.task;
        var date  = btn.dataset.date;
        btn.classList.toggle("done");
        self._hass.callService("kindertaken", "mark_done", { child: child, task: task, date: date });
      });
    });
  }

  _header(todayName) {
    var sub = todayName ? "Vandaag: <strong>" + todayName + "</strong>" : "Weekplanning";
    return '<div class="hdr"><span class="hdr-icon">📋</span><div><div class="hdr-title">Kindertaken</div><div class="hdr-sub">' + sub + '</div></div></div>';
  }

  _todaySection(children, byChild) {
    var self = this;
    if (!children.length) {
      return '<div class="section"><p class="muted">Nog geen kinderen ingesteld.</p></div>';
    }
    var cards = children.map(function(child) {
      var theme = self._themes[child];
      var tasks = byChild[child] || [];
      var allDone = tasks.length > 0 && tasks.every(function(t) { return t.done; });

      var rows;
      if (tasks.length === 0) {
        rows = '<div class="free-day">Vrije dag 🎉</div>';
      } else {
        rows = tasks.map(function(t) {
          return '<button class="task-btn' + (t.done ? ' done' : '') + '" data-child="' + child + '" data-task="' + t.task + '" data-date="' + t.date + '">' +
            '<span class="t-icon">' + (t.icon || "✔️") + '</span>' +
            '<span class="t-name">' + t.task + '</span>' +
            '<span class="t-tick">' + (t.done ? "✅" : "⬜") + '</span>' +
          '</button>';
        }).join("");
      }

      return '<div class="child-card" style="--bg:' + theme.bg + ';--light:' + theme.light + '">' +
        '<div class="child-top">' +
          '<span class="c-emoji">' + theme.emoji + '</span>' +
          '<span class="c-name">' + child + '</span>' +
          (allDone ? '<span class="done-chip">✅ Klaar!</span>' : '') +
        '</div>' +
        '<div class="child-body">' + rows + '</div>' +
      '</div>';
    }).join("");

    return '<div class="section today-sec"><div class="sec-lbl">📅 Vandaag</div><div class="today-grid">' + cards + '</div></div>';
  }

  _weekSection(week, children) {
    var self = this;
    var cols = DAYS_FULL.map(function(day, i) {
      var data  = week[day] || {};
      var tasks = data.tasks || [];
      var isToday = !!data.is_today;

      var badges;
      if (tasks.length === 0) {
        badges = '<div class="wk-empty">—</div>';
      } else {
        badges = tasks.map(function(t) {
          var theme = self._themes[t.child] || THEMES[0];
          var firstWord = t.task.split(/[\s\/]/)[0];
          return '<div class="wk-badge task-btn' + (t.done ? ' done' : '') +
            '" style="background:' + theme.bg + '"' +
            ' data-child="' + t.child + '" data-task="' + t.task + '" data-date="' + data.date + '"' +
            ' title="' + t.child + ': ' + t.task + '">' +
            theme.emoji + ' <span class="wk-nm">' + firstWord + '</span>' +
          '</div>';
        }).join("");
      }

      return '<div class="wk-col' + (isToday ? ' today' : '') + '">' +
        '<div class="wk-hd"><div class="wk-day">' + DAYS_SHORT[i] + '</div><div class="wk-date">' + (data.date_display || "") + '</div></div>' +
        '<div class="wk-body">' + badges + '</div>' +
      '</div>';
    }).join("");

    var legend = children.map(function(c) {
      var theme = self._themes[c];
      return '<div class="leg"><span class="leg-dot" style="background:' + theme.bg + '"></span>' + c + '</div>';
    }).join("");

    return '<div class="section week-sec"><div class="sec-lbl">📆 Deze week</div><div class="week-grid">' + cols + '</div><div class="legend">' + legend + '</div></div>';
  }

  _css() {
    return [
      "*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }",
      "ha-card { font-family: var(--primary-font-family, Roboto, sans-serif); background: var(--card-background-color, #fff); border-radius: 16px; overflow: hidden; }",

      /* Header */
      ".hdr { display: flex; align-items: center; gap: 14px; padding: 16px 20px; background: linear-gradient(135deg, #1a237e 0%, #4527A0 100%); color: #fff; }",
      ".hdr-icon { font-size: 36px; line-height: 1; }",
      ".hdr-title { font-size: 22px; font-weight: 800; }",
      ".hdr-sub { font-size: 13px; opacity: .85; margin-top: 3px; }",

      /* Sections */
      ".section { padding: 14px; }",
      ".today-sec { background: var(--secondary-background-color, #f4f4f4); border-bottom: 1px solid var(--divider-color, #ddd); }",
      ".sec-lbl { font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; color: var(--secondary-text-color); margin-bottom: 12px; }",
      ".muted { color: var(--secondary-text-color); font-size: 13px; }",

      /* Kind-kaarten */
      ".today-grid { display: flex; gap: 10px; flex-wrap: wrap; }",
      ".child-card { flex: 1; min-width: 150px; border-radius: 14px; background: linear-gradient(145deg, var(--light), var(--bg)); color: #fff; box-shadow: 0 4px 14px rgba(0,0,0,.18); overflow: hidden; }",
      ".child-top { display: flex; align-items: center; gap: 8px; padding: 12px 14px 8px; }",
      ".c-emoji { font-size: 28px; }",
      ".c-name { font-size: 19px; font-weight: 800; flex: 1; }",
      ".done-chip { font-size: 11px; font-weight: 700; background: rgba(255,255,255,.25); border-radius: 20px; padding: 3px 9px; white-space: nowrap; }",
      ".child-body { padding: 4px 10px 12px; display: flex; flex-direction: column; gap: 7px; }",

      /* Taak-knoppen */
      ".task-btn { display: flex; align-items: center; gap: 10px; background: rgba(255,255,255,.2); border: none; border-radius: 10px; padding: 9px 12px; cursor: pointer; color: #fff; font-size: 14px; font-weight: 600; text-align: left; width: 100%; transition: background .15s, opacity .15s; }",
      ".task-btn:hover { background: rgba(255,255,255,.35); }",
      ".task-btn.done { background: rgba(255,255,255,.08); opacity: .5; text-decoration: line-through; }",
      ".t-icon { font-size: 20px; flex-shrink: 0; }",
      ".t-name { flex: 1; }",
      ".t-tick { font-size: 20px; flex-shrink: 0; }",
      ".free-day { padding: 10px 4px 4px; font-size: 15px; text-align: center; }",

      /* Week grid */
      ".week-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; }",
      ".wk-col { border-radius: 10px; border: 2px solid var(--divider-color, #e0e0e0); overflow: hidden; }",
      ".wk-col.today { border-color: #1a237e; box-shadow: 0 2px 10px rgba(26,35,126,.25); }",
      ".wk-hd { padding: 6px 4px; text-align: center; background: var(--secondary-background-color, #f4f4f4); }",
      ".wk-col.today .wk-hd { background: linear-gradient(135deg, #1a237e, #4527A0); color: #fff; }",
      ".wk-day { font-size: 12px; font-weight: 800; }",
      ".wk-date { font-size: 9px; opacity: .7; margin-top: 1px; }",
      ".wk-body { padding: 4px; display: flex; flex-direction: column; gap: 4px; min-height: 40px; }",
      ".wk-badge { border-radius: 6px; padding: 4px 5px; font-size: 10px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 3px; cursor: pointer; transition: opacity .15s; line-height: 1.3; }",
      ".wk-badge:hover { opacity: .8; }",
      ".wk-badge.done { opacity: .3; text-decoration: line-through; }",
      ".wk-nm { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 50px; }",
      ".wk-empty { color: var(--disabled-text-color, #bbb); font-size: 11px; text-align: center; padding: 10px 0; }",

      /* Legenda */
      ".legend { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }",
      ".leg { display: flex; align-items: center; gap: 6px; font-size: 13px; color: var(--secondary-text-color); }",
      ".leg-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }",
    ].join("\n");
  }

  getCardSize() { return 5; }

  static getConfigElement() {
    return document.createElement("kindertaken-card-editor");
  }

  static getStubConfig() {
    return { entity: "sensor.kindertaken_week" };
  }
}

class KindertakenCardEditor extends HTMLElement {
  setConfig(config) { this._config = config || {}; }
  connectedCallback() {
    var entity = (this._config && this._config.entity) || "sensor.kindertaken_week";
    this.innerHTML = '<div style="padding:16px;font-family:Roboto,sans-serif"><label style="display:block;font-size:13px;font-weight:600;margin-bottom:6px">Sensor entiteit</label><input id="ent" type="text" value="' + entity + '" style="width:100%;padding:8px 10px;border:1px solid #ccc;border-radius:8px;font-size:14px"><p style="font-size:11px;color:#888;margin-top:6px">Standaard: sensor.kindertaken_week</p></div>';
    var self = this;
    this.querySelector("#ent").addEventListener("change", function(e) {
      self.dispatchEvent(new CustomEvent("config-changed", {
        detail: { config: Object.assign({}, self._config, { entity: e.target.value.trim() }) },
        bubbles: true, composed: true,
      }));
    });
  }
}

customElements.define("kindertaken-card", KindertakenCard);
customElements.define("kindertaken-card-editor", KindertakenCardEditor);

window.customCards = window.customCards || [];
if (!window.customCards.find(function(c) { return c.type === "kindertaken-card"; })) {
  window.customCards.push({
    type: "kindertaken-card",
    name: "Kindertaken Planner",
    description: "Weekoverzicht van huishoudtaken per kind, met afvinkfunctie.",
    preview: true,
  });
}

console.info(
  "%c KINDERTAKEN %c v1.2 ",
  "color:white;background:#1a237e;padding:3px 8px;border-radius:4px 0 0 4px;font-weight:700",
  "color:#1a237e;background:#fff;padding:3px 8px;border-radius:0 4px 4px 0;border:1px solid #1a237e"
);
