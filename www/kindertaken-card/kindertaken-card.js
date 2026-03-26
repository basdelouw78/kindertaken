/**
 * Kindertaken Planner Card v1.1
 * Kindvriendelijke weekkaart voor Home Assistant
 */

const CHILD_THEMES = [
  { gradient: ["#4FC3F7", "#0288D1"], emoji: "⭐", badge: "#0288D1" },
  { gradient: ["#81C784", "#2E7D32"], emoji: "🌟", badge: "#2E7D32" },
  { gradient: ["#FFB74D", "#E65100"], emoji: "🎯", badge: "#E65100" },
  { gradient: ["#F48FB1", "#AD1457"], emoji: "🌈", badge: "#AD1457" },
  { gradient: ["#CE93D8", "#6A1B9A"], emoji: "🦋", badge: "#6A1B9A" },
  { gradient: ["#80DEEA", "#00695C"], emoji: "🚀", badge: "#00695C" },
  { gradient: ["#FFCC80", "#BF360C"], emoji: "🏆", badge: "#BF360C" },
  { gradient: ["#EF9A9A", "#B71C1C"], emoji: "💎", badge: "#B71C1C" },
];

const DAYS_SHORT = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"];
const DAYS_FULL = ["Maandag","Dinsdag","Woensdag","Donderdag","Vrijdag","Zaterdag","Zondag"];

class KindertakenCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._childThemes = {};
  }

  setConfig(config) {
    this._config = {
      entity: "sensor.kindertaken_week",
      show_done_confetti: true,
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _getTheme(child, children) {
    if (!this._childThemes[child]) {
      const idx = (children || []).indexOf(child);
      this._childThemes[child] = CHILD_THEMES[Math.max(0, idx) % CHILD_THEMES.length];
    }
    return this._childThemes[child];
  }

  _render() {
    const hass = this._hass;
    const entityId = this._config.entity;
    const stateObj = hass.states[entityId];

    if (!stateObj) {
      this.shadowRoot.innerHTML = `<ha-card><div class="err">
        Entiteit niet gevonden: <code>${entityId}</code><br>
        Controleer of de Kindertaken integratie is geconfigureerd en herstart Home Assistant.
      </div></ha-card>`;
      return;
    }

    const { week = {}, children = [], today, today_name } = stateObj.attributes;

    // Bouw kind→thema mapping
    children.forEach((c, i) => {
      if (!this._childThemes[c]) this._childThemes[c] = CHILD_THEMES[i % CHILD_THEMES.length];
    });

    // Vandaag taken per kind
    const todayData = week[today_name] || {};
    const todayTasks = todayData.tasks || [];
    const tasksByChild = {};
    children.forEach(c => { tasksByChild[c] = []; });
    todayTasks.forEach(t => { if (tasksByChild[t.child] !== undefined) tasksByChild[t.child].push(t); });

    const css = this._css(children);
    const todayHTML = this._renderToday(children, tasksByChild);
    const weekHTML = this._renderWeek(week, children);
    const legendHTML = this._renderLegend(children);

    this.shadowRoot.innerHTML = `
      <style>${css}</style>
      <ha-card>
        <div class="card-header">
          <span class="header-icon">📋</span>
          <div class="header-text">
            <div class="header-title">Kindertaken</div>
            <div class="header-sub">${today_name ? `Vandaag: <strong>${today_name}</strong>` : "Weekplanning"}</div>
          </div>
        </div>

        <div class="section today-section">
          <div class="section-label">📅 Vandaag</div>
          <div class="today-grid">${todayHTML}</div>
        </div>

        <div class="section week-section">
          <div class="section-label">📆 Deze week</div>
          <div class="week-grid">${weekHTML}</div>
          <div class="legend">${legendHTML}</div>
        </div>
      </ha-card>`;

    // Click handlers
    this.shadowRoot.querySelectorAll("[data-toggle]").forEach(el => {
      el.addEventListener("click", e => {
        e.stopPropagation();
        const { child, task, date } = el.dataset;
        this._toggle(child, task, date, el);
      });
    });
  }

  _renderToday(children, tasksByChild) {
    if (children.length === 0) return `<p class="empty">Nog geen kinderen ingesteld.</p>`;
    return children.map(child => {
      const theme = this._childThemes[child];
      const tasks = tasksByChild[child] || [];
      const allDone = tasks.length > 0 && tasks.every(t => t.done);
      const taskRows = tasks.length === 0
        ? `<div class="free-day">Vrije dag 🎉</div>`
        : tasks.map(t => `
            <button class="task-row ${t.done ? "done" : ""}"
                    data-toggle data-child="${child}" data-task="${t.task}" data-date="${t.date}"
                    title="Klik om af te vinken">
              <span class="task-icon">${t.icon || "✔️"}</span>
              <span class="task-label">${t.task}</span>
              <span class="task-check">${t.done ? "✅" : "⬜"}</span>
            </button>`).join("");

      return `
        <div class="child-card ${allDone ? "all-done" : ""}"
             style="--c1:${theme.gradient[0]};--c2:${theme.gradient[1]}">
          <div class="child-header">
            <span class="child-emoji">${theme.emoji}</span>
            <span class="child-name">${child}</span>
            ${allDone ? `<span class="done-badge">✅ Klaar!</span>` : ""}
          </div>
          <div class="child-tasks">${taskRows}</div>
        </div>`;
    }).join("");
  }

  _renderWeek(week, children) {
    return DAYS_FULL.map((day, idx) => {
      const data = week[day] || {};
      const isToday = data.is_today;
      const tasks = data.tasks || [];

      const cells = tasks.length === 0
        ? `<div class="wk-empty">—</div>`
        : tasks.map(t => {
            const theme = this._childThemes[t.child] || CHILD_THEMES[0];
            return `<div class="wk-badge ${t.done ? "done" : ""}"
                        style="background:${theme.badge}"
                        data-toggle data-child="${t.child}" data-task="${t.task}" data-date="${data.date}"
                        title="${t.child}: ${t.task}${t.done ? " ✅" : ""}">
              <span>${theme.emoji}</span>
              <span class="wk-task-name">${t.task.split(" ")[0]}</span>
            </div>`;
          }).join("");

      return `
        <div class="wk-col ${isToday ? "today" : ""}">
          <div class="wk-head">
            <div class="wk-day">${DAYS_SHORT[idx]}</div>
            <div class="wk-date">${data.date_display || ""}</div>
          </div>
          <div class="wk-cells">${cells}</div>
        </div>`;
    }).join("");
  }

  _renderLegend(children) {
    return children.map(c => {
      const theme = this._childThemes[c];
      return `<div class="legend-item">
        <span class="legend-dot" style="background:${theme.badge}"></span>
        <span>${c}</span>
      </div>`;
    }).join("");
  }

  _css(children) {
    return `
      *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
      ha-card { background: var(--card-background-color, #fff); border-radius: 16px; overflow: hidden; font-family: var(--primary-font-family, Roboto, sans-serif); }

      .err { padding: 16px; color: var(--error-color, red); font-size: 13px; }

      /* ── Header ── */
      .card-header {
        display: flex; align-items: center; gap: 14px;
        padding: 16px 20px 14px;
        background: linear-gradient(135deg, #5c6bc0 0%, #7e57c2 100%);
        color: white;
      }
      .header-icon { font-size: 34px; line-height: 1; }
      .header-title { font-size: 20px; font-weight: 800; letter-spacing: -.3px; }
      .header-sub { font-size: 13px; opacity: .85; margin-top: 2px; }

      /* ── Sections ── */
      .section { padding: 14px 14px 10px; }
      .today-section { background: var(--secondary-background-color, #f7f7f7); border-bottom: 1px solid var(--divider-color, #e0e0e0); }
      .section-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .9px; color: var(--secondary-text-color); margin-bottom: 10px; }

      /* ── Today: child cards ── */
      .today-grid { display: flex; gap: 10px; flex-wrap: wrap; }
      .child-card {
        flex: 1; min-width: 140px;
        border-radius: 14px;
        background: linear-gradient(145deg, var(--c1), var(--c2));
        color: white;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,.15);
        transition: transform .15s;
      }
      .child-card:hover { transform: translateY(-2px); }
      .child-card.all-done { opacity: .85; }
      .child-header {
        display: flex; align-items: center; gap: 8px;
        padding: 10px 12px 6px;
      }
      .child-emoji { font-size: 26px; }
      .child-name { font-size: 17px; font-weight: 800; flex: 1; }
      .done-badge { font-size: 11px; font-weight: 700; background: rgba(255,255,255,.25); border-radius: 20px; padding: 2px 8px; }
      .child-tasks { padding: 0 10px 10px; display: flex; flex-direction: column; gap: 6px; }

      .task-row {
        display: flex; align-items: center; gap: 8px;
        background: rgba(255,255,255,.22); border: none; border-radius: 10px;
        padding: 7px 10px; cursor: pointer; color: white;
        font-size: 13px; font-weight: 600; text-align: left;
        transition: background .15s, opacity .15s;
        width: 100%;
      }
      .task-row:hover { background: rgba(255,255,255,.38); }
      .task-row.done { background: rgba(255,255,255,.1); opacity: .65; text-decoration: line-through; }
      .task-icon { font-size: 17px; flex-shrink: 0; }
      .task-label { flex: 1; }
      .task-check { font-size: 17px; flex-shrink: 0; }

      .free-day { padding: 10px 4px; font-size: 14px; opacity: .85; font-style: italic; text-align: center; }
      .empty { padding: 8px 4px; color: var(--secondary-text-color); font-size: 13px; }

      /* ── Week grid ── */
      .week-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; }
      .wk-col { border-radius: 10px; border: 2px solid var(--divider-color, #e8e8e8); overflow: hidden; }
      .wk-col.today { border-color: #5c6bc0; box-shadow: 0 2px 10px rgba(92,107,192,.3); }
      .wk-head { padding: 5px 3px; text-align: center; background: var(--secondary-background-color, #f5f5f5); }
      .wk-col.today .wk-head { background: linear-gradient(135deg, #5c6bc0, #7e57c2); color: white; }
      .wk-day { font-size: 11px; font-weight: 800; }
      .wk-date { font-size: 9px; opacity: .7; margin-top: 1px; }
      .wk-cells { padding: 4px; display: flex; flex-direction: column; gap: 3px; min-height: 36px; }
      .wk-badge {
        border-radius: 6px; padding: 3px 4px;
        font-size: 10px; font-weight: 700; color: white;
        display: flex; align-items: center; gap: 3px;
        cursor: pointer; transition: opacity .15s;
        overflow: hidden;
      }
      .wk-badge:hover { opacity: .85; }
      .wk-badge.done { opacity: .35; text-decoration: line-through; }
      .wk-task-name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 52px; }
      .wk-empty { color: var(--disabled-text-color, #ccc); font-size: 11px; text-align: center; padding: 8px 2px; }

      /* ── Legend ── */
      .legend { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; }
      .legend-item { display: flex; align-items: center; gap: 5px; font-size: 12px; color: var(--secondary-text-color); }
      .legend-dot { width: 11px; height: 11px; border-radius: 50%; flex-shrink: 0; }
    `;
  }

  _toggle(child, task, date, el) {
    // Optimistische UI feedback
    el.classList.toggle("done");
    this._hass.callService("kindertaken", "mark_done", { child, task, date });
  }

  getCardSize() { return 5; }

  static getConfigElement() {
    const el = document.createElement("kindertaken-card-editor");
    return el;
  }

  static getStubConfig() {
    return { entity: "sensor.kindertaken_week" };
  }
}

// ─── Config editor ────────────────────────────────────────────────────────────
class KindertakenCardEditor extends HTMLElement {
  setConfig(config) { this._config = config; }

  connectedCallback() {
    this.innerHTML = `
      <div style="padding:16px;font-family:Roboto,sans-serif">
        <label style="display:block;margin-bottom:6px;font-size:13px;color:#555">Sensor entiteit</label>
        <input id="ent" type="text" value="${this._config.entity || "sensor.kindertaken_week"}"
          style="width:100%;padding:8px;border:1px solid #ccc;border-radius:6px;font-size:14px">
        <p style="font-size:11px;color:#888;margin-top:4px">Standaard: sensor.kindertaken_week</p>
      </div>`;
    this.querySelector("#ent").addEventListener("change", e => {
      this.dispatchEvent(new CustomEvent("config-changed", {
        detail: { config: { ...this._config, entity: e.target.value } }
      }));
    });
  }
}

customElements.define("kindertaken-card", KindertakenCard);
customElements.define("kindertaken-card-editor", KindertakenCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "kindertaken-card",
  name: "Kindertaken Planner",
  description: "Weekoverzicht van huishoudtaken per kind, met afvinkfunctie.",
  preview: true,
});

console.info(
  "%c KINDERTAKEN %c v1.1 ",
  "color:white;background:#5c6bc0;padding:3px 8px;border-radius:4px 0 0 4px;font-weight:700",
  "color:#5c6bc0;background:#fff;padding:3px 8px;border-radius:0 4px 4px 0;border:1px solid #5c6bc0"
);
