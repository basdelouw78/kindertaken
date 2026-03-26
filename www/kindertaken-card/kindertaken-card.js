/**
 * Kindertaken Planner Card v1.3
 * Kleurthema per kind (uit HA config), week- én maandtaken
 */

const DAYS_SHORT = ["Ma","Di","Wo","Do","Vr","Za","Zo"];
const DAYS_FULL  = ["Maandag","Dinsdag","Woensdag","Donderdag","Vrijdag","Zaterdag","Zondag"];
const MONTHS_NL  = ["Januari","Februari","Maart","April","Mei","Juni","Juli","Augustus","September","Oktober","November","December"];
const MONTHS_SHORT = ["Jan","Feb","Mrt","Apr","Mei","Jun","Jul","Aug","Sep","Okt","Nov","Dec"];

class KindertakenCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._activeMonth = null; // voor maand-collapse
  }

  setConfig(config) {
    if (!config) throw new Error("Geen config.");
    this._config = Object.assign({
      entity: "sensor.kindertaken_week",
      month_entity: "sensor.kindertaken_maand",
    }, config);
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    const hass = this._hass;
    const weekState  = hass.states[this._config.entity];
    const monthState = hass.states[this._config.month_entity];

    if (!weekState) {
      this.shadowRoot.innerHTML = '<ha-card><div style="padding:20px;color:#c62828">Entiteit niet gevonden: ' + this._config.entity + '<br><small>Controleer integratie en herstart HA.</small></div></ha-card>';
      return;
    }

    const wa = weekState.attributes;
    const week         = wa.week || {};
    const children     = wa.children || [];
    const today_name   = wa.today_name || "";
    const child_themes = wa.child_themes || {};

    // Vandaag taken per kind
    const todayData  = week[today_name] || {};
    const todayTasks = todayData.tasks || [];
    const byChild = {};
    children.forEach(function(c) { byChild[c] = []; });
    todayTasks.forEach(function(t) { if (byChild[t.child] !== undefined) byChild[t.child].push(t); });

    // Maand data
    const ma = monthState ? monthState.attributes : {};
    const months       = ma.months || {};
    const month_tasks  = ma.month_tasks || [];
    const current_month = ma.current_month || "";
    const current_year  = ma.current_year || new Date().getFullYear();

    // Actieve maand: default = huidige maand
    if (!this._activeMonth) this._activeMonth = current_month;

    const html =
      '<style>' + this._css() + '</style>' +
      '<ha-card>' +
        this._renderHeader(today_name) +
        this._renderToday(children, byChild, child_themes) +
        this._renderWeek(week, children, child_themes) +
        (month_tasks.length > 0 ? this._renderMonths(months, children, child_themes, current_month) : '') +
      '</ha-card>';

    this.shadowRoot.innerHTML = html;
    this._attachListeners();
  }

  _renderHeader(todayName) {
    var sub = todayName ? "Vandaag: <strong>" + todayName + "</strong>" : "Weekplanning";
    return '<div class="hdr"><span class="hdr-icon">📋</span><div><div class="hdr-title">Kindertaken</div><div class="hdr-sub">' + sub + '</div></div></div>';
  }

  _renderToday(children, byChild, child_themes) {
    if (!children.length) return '<div class="section"><p class="muted">Geen kinderen ingesteld.</p></div>';

    var self = this;
    var cards = children.map(function(child) {
      var theme = child_themes[child] || { bg:"#1565C0", light:"#42A5F5", emoji:"⭐" };
      var tasks = byChild[child] || [];
      var allDone = tasks.length > 0 && tasks.every(function(t) { return t.done; });

      var rows = tasks.length === 0
        ? '<div class="free-day">Vrije dag 🎉</div>'
        : tasks.map(function(t) {
            return '<button class="task-btn week-task' + (t.done ? ' done' : '') + '" data-child="' + t.child + '" data-task="' + t.task + '" data-date="' + t.date + '">' +
              '<span class="t-icon">' + (t.icon||"✔️") + '</span>' +
              '<span class="t-name">' + t.task + '</span>' +
              '<span class="t-tick">' + (t.done ? "✅" : "⬜") + '</span>' +
            '</button>';
          }).join("");

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

  _renderWeek(week, children, child_themes) {
    var self = this;
    var cols = DAYS_FULL.map(function(day, i) {
      var data  = week[day] || {};
      var tasks = data.tasks || [];
      var isToday = !!data.is_today;

      var badges = tasks.length === 0
        ? '<div class="wk-empty">—</div>'
        : tasks.map(function(t) {
            var theme = child_themes[t.child] || { bg:"#1565C0", emoji:"⭐" };
            return '<div class="wk-badge week-task' + (t.done ? ' done' : '') +
              '" style="background:' + theme.bg + '"' +
              ' data-child="' + t.child + '" data-task="' + t.task + '" data-date="' + data.date + '"' +
              ' title="' + t.child + ': ' + t.task + '">' +
              theme.emoji + ' <span class="wk-nm">' + t.task.split(/[\s\/]/)[0] + '</span>' +
            '</div>';
          }).join("");

      return '<div class="wk-col' + (isToday ? ' today' : '') + '">' +
        '<div class="wk-hd"><div class="wk-day">' + DAYS_SHORT[i] + '</div><div class="wk-date">' + (data.date_display||"") + '</div></div>' +
        '<div class="wk-body">' + badges + '</div>' +
      '</div>';
    }).join("");

    // Legenda
    var legend = children.map(function(c) {
      var theme = child_themes[c] || { bg:"#1565C0" };
      return '<div class="leg"><span class="leg-dot" style="background:' + theme.bg + '"></span>' + c + '</div>';
    }).join("");

    return '<div class="section week-sec"><div class="sec-lbl">📆 Deze week</div><div class="week-grid">' + cols + '</div><div class="legend">' + legend + '</div></div>';
  }

  _renderMonths(months, children, child_themes, current_month) {
    var self = this;

    // Bouw jaar-rij: 12 maandblokjes
    var monthNav = MONTHS_NL.map(function(month, i) {
      var data = months[month] || {};
      var isCurrent = !!data.is_current;
      var isActive = month === self._activeMonth;
      var hasTasks = (data.tasks || []).length > 0;
      var allDone = hasTasks && data.tasks.every(function(t) { return t.done; });
      var cls = "mn-pill" + (isCurrent ? " current" : "") + (isActive ? " active" : "") + (allDone ? " all-done" : "");
      return '<button class="' + cls + '" data-month="' + month + '">' +
        MONTHS_SHORT[i] +
        (hasTasks ? '<span class="mn-dot' + (allDone ? ' mn-done' : '') + '"></span>' : '') +
      '</button>';
    }).join("");

    // Geselecteerde maand uitklappen
    var activeData = months[this._activeMonth] || {};
    var activeTasks = activeData.tasks || [];

    var taskList;
    if (activeTasks.length === 0) {
      taskList = '<div class="mt-empty">Geen maandtaken gepland voor ' + this._activeMonth + '.</div>';
    } else {
      taskList = activeTasks.map(function(t) {
        var theme = child_themes[t.child] || { bg:"#1565C0", light:"#42A5F5", emoji:"⭐" };
        return '<button class="task-btn month-task' + (t.done ? ' done' : '') + '"' +
          ' data-child="' + t.child + '" data-task="' + t.task + '" data-month-key="' + t.month_key + '"' +
          ' style="--bg:' + theme.bg + ';--light:' + theme.light + '">' +
          '<span class="t-icon">' + (t.icon||"🏠") + '</span>' +
          '<div class="mt-info">' +
            '<span class="t-name">' + t.task + '</span>' +
            '<span class="mt-child" style="background:' + theme.bg + '">' + theme.emoji + ' ' + t.child + '</span>' +
          '</div>' +
          '<span class="t-tick">' + (t.done ? "✅" : "⬜") + '</span>' +
        '</button>';
      }).join("");
    }

    return '<div class="section month-sec">' +
      '<div class="sec-lbl">🗓️ Maandtaken ' + activeData.month_key ? activeData.month_key.split("-")[0] : "" + '</div>' +
      '<div class="month-nav">' + monthNav + '</div>' +
      '<div class="month-tasks">' + taskList + '</div>' +
    '</div>';
  }

  _attachListeners() {
    var self = this;

    // Week- en vandaag-taken
    this.shadowRoot.querySelectorAll(".week-task").forEach(function(btn) {
      btn.addEventListener("click", function() {
        var child = btn.dataset.child;
        var task  = btn.dataset.task;
        var date  = btn.dataset.date;
        btn.classList.toggle("done");
        self._hass.callService("kindertaken", "mark_done", { child: child, task: task, date: date });
      });
    });

    // Maandtaken
    this.shadowRoot.querySelectorAll(".month-task").forEach(function(btn) {
      btn.addEventListener("click", function() {
        var child     = btn.dataset.child;
        var task      = btn.dataset.task;
        var monthKey  = btn.dataset.monthKey;
        btn.classList.toggle("done");
        self._hass.callService("kindertaken", "mark_done", { child: child, task: task, month_key: monthKey });
      });
    });

    // Maandnavigatie
    this.shadowRoot.querySelectorAll(".mn-pill").forEach(function(btn) {
      btn.addEventListener("click", function() {
        self._activeMonth = btn.dataset.month;
        self._render();
      });
    });
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
      ".week-sec { border-bottom: 1px solid var(--divider-color, #ddd); }",
      ".sec-lbl { font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; color: var(--secondary-text-color); margin-bottom: 12px; }",
      ".muted { color: var(--secondary-text-color); font-size: 13px; }",

      /* Kind-kaarten vandaag */
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

      /* Maand navigatie */
      ".month-sec { background: var(--secondary-background-color, #f4f4f4); }",
      ".month-nav { display: grid; grid-template-columns: repeat(6, 1fr); gap: 5px; margin-bottom: 14px; }",
      ".mn-pill { border: none; border-radius: 8px; padding: 6px 4px; font-size: 11px; font-weight: 700; cursor: pointer; background: var(--card-background-color, #fff); color: var(--primary-text-color); position: relative; transition: all .15s; border: 2px solid transparent; }",
      ".mn-pill:hover { background: #e8eaf6; }",
      ".mn-pill.current { border-color: #1a237e; color: #1a237e; }",
      ".mn-pill.active { background: linear-gradient(135deg, #1a237e, #4527A0); color: #fff; border-color: transparent; }",
      ".mn-pill.all-done { background: #e8f5e9; }",
      ".mn-pill.active.all-done { background: linear-gradient(135deg, #2E7D32, #43A047); }",
      ".mn-dot { position: absolute; top: 3px; right: 4px; width: 6px; height: 6px; border-radius: 50%; background: #E65100; }",
      ".mn-dot.mn-done { background: #2E7D32; }",

      /* Maandtaken lijst */
      ".month-tasks { display: flex; flex-direction: column; gap: 8px; }",
      ".mt-empty { color: var(--secondary-text-color); font-size: 13px; padding: 8px 0; font-style: italic; }",
      ".month-task { background: linear-gradient(135deg, var(--light, #42A5F5), var(--bg, #1565C0)) !important; }",
      ".mt-info { flex: 1; display: flex; flex-direction: column; gap: 3px; }",
      ".mt-child { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; font-weight: 700; background: rgba(255,255,255,.25); border-radius: 12px; padding: 2px 8px; width: fit-content; }",
    ].join("\n");
  }

  getCardSize() { return 7; }

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
    var we = (this._config.entity) || "sensor.kindertaken_week";
    var me = (this._config.month_entity) || "sensor.kindertaken_maand";
    this.innerHTML =
      '<div style="padding:16px;font-family:Roboto,sans-serif;display:flex;flex-direction:column;gap:12px">' +
        '<div><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px">Week sensor</label>' +
        '<input id="we" type="text" value="' + we + '" style="width:100%;padding:8px;border:1px solid #ccc;border-radius:8px;font-size:14px"></div>' +
        '<div><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px">Maand sensor</label>' +
        '<input id="me" type="text" value="' + me + '" style="width:100%;padding:8px;border:1px solid #ccc;border-radius:8px;font-size:14px"></div>' +
      '</div>';
    var self = this;
    function fire() {
      self.dispatchEvent(new CustomEvent("config-changed", {
        detail: { config: { entity: self.querySelector("#we").value.trim(), month_entity: self.querySelector("#me").value.trim() } },
        bubbles: true, composed: true,
      }));
    }
    this.querySelector("#we").addEventListener("change", fire);
    this.querySelector("#me").addEventListener("change", fire);
  }
}

customElements.define("kindertaken-card", KindertakenCard);
customElements.define("kindertaken-card-editor", KindertakenCardEditor);

window.customCards = window.customCards || [];
if (!window.customCards.find(function(c) { return c.type === "kindertaken-card"; })) {
  window.customCards.push({ type: "kindertaken-card", name: "Kindertaken Planner", description: "Week + maandtaken per kind.", preview: true });
}
console.info("%c KINDERTAKEN %c v1.3 ", "color:white;background:#1a237e;padding:3px 8px;border-radius:4px 0 0 4px;font-weight:700", "color:#1a237e;background:#fff;padding:3px 8px;border-radius:0 4px 4px 0;border:1px solid #1a237e");
