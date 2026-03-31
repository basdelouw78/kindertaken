/**
 * Kindertaken Planner Card v2.1
 * Co-ouderschap + blokdagen + rotatie/week/maandtaken
 */

const DAYS_SHORT = ["Ma","Di","Wo","Do","Vr","Za","Zo"];
const DAYS_FULL  = ["Maandag","Dinsdag","Woensdag","Donderdag","Vrijdag","Zaterdag","Zondag"];

class KindertakenCard extends HTMLElement {
  constructor() { super(); this.attachShadow({mode:"open"}); }

  setConfig(config) {
    if (!config) throw new Error("Geen config.");
    this._config = Object.assign({entity:"sensor.kindertaken_week"}, config);
  }

  set hass(hass) { this._hass = hass; this._render(); }

  _render() {
    var state = this._hass.states[this._config.entity];
    if (!state) {
      this.shadowRoot.innerHTML = '<ha-card><div style="padding:20px;color:#c62828">Entiteit niet gevonden: '+this._config.entity+'</div></ha-card>';
      return;
    }
    var a = state.attributes;
    var children    = a.children || [];
    var themes      = a.child_themes || {};
    var week        = a.week || {};
    var today_name  = a.today_name || "";
    var month_ov    = a.month_overview || [];
    var coparenting = a.coparenting || {};

    // Taken per kind voor vandaag
    var todayData  = week[today_name] || {};
    var todayTasks = todayData.tasks || [];
    var todayPres  = todayData.presence || {};
    var byChild    = {};
    children.forEach(function(c){ byChild[c] = []; });
    todayTasks.forEach(function(t){ if(byChild[t.child]!==undefined) byChild[t.child].push(t); });

    this.shadowRoot.innerHTML =
      '<style>'+this._css()+'</style>'+
      '<ha-card>'+
        this._hdr(today_name)+
        this._todaySection(children, byChild, themes, todayPres)+
        this._weekSection(week, themes, children, coparenting)+
        (month_ov.length ? this._monthSection(month_ov, themes, children) : '')+
      '</ha-card>';

    this._listeners();
  }

  _hdr(todayName) {
    var sub = todayName ? "Vandaag: <strong>"+todayName+"</strong>" : "Weekplanning";
    return '<div class="hdr"><span style="font-size:32px">📋</span><div><div class="hdr-t">Kindertaken</div><div class="hdr-s">'+sub+'</div></div></div>';
  }

  // ── Vandaag ────────────────────────────────────────────────────────────────
  _todaySection(children, byChild, themes, todayPres) {
    if (!children.length) return '<div class="sec"><p class="muted">Geen kinderen ingesteld.</p></div>';
    var cards = children.map(function(child) {
      var th     = themes[child] || {bg:"#1565C0",light:"#42A5F5",emoji:"⭐"};
      var pres   = todayPres[child] || {present:true,available:true};
      var absent = !pres.present;
      var blocked= pres.present && !pres.available;
      var tasks  = byChild[child] || [];
      var allDone= tasks.length>0 && tasks.every(function(t){return t.done;});

      var statusBadge = "";
      if (absent)  statusBadge = '<span class="badge absent">🏠 Niet thuis</span>';
      else if (blocked) statusBadge = '<span class="badge blocked">⛔ Blokdag</span>';
      else if (allDone) statusBadge = '<span class="badge done-badge">✅ Klaar!</span>';

      var rows = "";
      if (absent || blocked) {
        rows = '<div class="free">'+(absent?"Niet thuis deze week":"Geblokkeerde dag")+'</div>';
      } else {
        var groups = {rotation:[],week:[],month:[]};
        tasks.forEach(function(t){ if(groups[t.type]) groups[t.type].push(t); });
        ["rotation","week","month"].forEach(function(type){
          var g = groups[type];
          if (!g.length) return;
          var lbl = {rotation:"🔄 Dagelijks",week:"📅 Wekelijks",month:"🗓️ Maand"}[type];
          rows += '<div class="glbl">'+lbl+'</div>';
          g.forEach(function(t){
            rows += '<button class="tbtn'+(t.done?" done":"")+'" data-key="'+t.key+'">' +
              '<span class="ti">'+(t.icon||"✔️")+'</span>' +
              '<span class="tn">'+t.task+'</span>' +
              '<span class="tk">'+(t.done?"✅":"⬜")+'</span>' +
            '</button>';
          });
        });
        if (!rows) rows = '<div class="free">Vrije dag 🎉</div>';
      }

      var opacity = (absent||blocked) ? 'style="opacity:.45"' : '';
      return '<div class="cc'+(absent||blocked?" cc-away":"")+(absent?" cc-absent":"")+'" '+opacity+' style="--bg:'+th.bg+';--lt:'+th.light+'">' +
        '<div class="ct"><span class="ce">'+th.emoji+'</span><span class="cn">'+child+'</span>'+statusBadge+'</div>' +
        '<div class="cb">'+rows+'</div>' +
      '</div>';
    }).join("");
    return '<div class="sec today-s"><div class="sl">📅 Vandaag</div><div class="today-g">'+cards+'</div></div>';
  }

  // ── Weekkalender ──────────────────────────────────────────────────────────
  _weekSection(week, themes, children, coparenting) {
    var cols = DAYS_FULL.map(function(day,i){
      var data  = week[day] || {};
      var tasks = data.tasks || [];
      var pres  = data.presence || {};
      var isToday = !!data.is_today;

      var badges = "";
      if (!tasks.length) {
        // Laat zien welke kinderen er niet zijn op deze dag
        var absent = children.filter(function(c){ return pres[c] && !pres[c].present; });
        if (absent.length) {
          badges = absent.map(function(c){
            var th = themes[c]||{bg:"#888",emoji:"?"};
            return '<div class="wb-absent" title="'+c+' niet thuis" style="background:'+th.bg+'">'+th.emoji+'</div>';
          }).join("") || '<div class="we">—</div>';
        } else {
          badges = '<div class="we">—</div>';
        }
      } else {
        tasks.forEach(function(t){
          var th = themes[t.child]||{bg:"#1565C0",emoji:"⭐"};
          var typeIcon = t.type==="month"?" 🗓️":t.type==="week"?" 📅":"";
          badges += '<div class="wb tbtn'+(t.done?" done":"")+'" style="background:'+th.bg+'" data-key="'+t.key+'" title="'+t.child+': '+t.task+typeIcon+'">'+
            th.emoji+' <span class="wn">'+t.task.split(/[\s\/]/)[0]+'</span>'+
          '</div>';
        });
        // Afwezige kinderen als kleine indicator
        children.forEach(function(c){
          if (pres[c] && !pres[c].present) {
            var th = themes[c]||{bg:"#888",emoji:"?"};
            badges += '<div class="wb-absent" title="'+c+' niet thuis" style="border-color:'+th.bg+'">'+th.emoji+'</div>';
          }
        });
      }

      return '<div class="wc'+(isToday?" today":"")+'">'+
        '<div class="wh"><div class="wd">'+DAYS_SHORT[i]+'</div><div class="wdt">'+((data.date_display)||"")+'</div></div>'+
        '<div class="wb-wrap">'+badges+'</div>'+
      '</div>';
    }).join("");

    // Co-ouderschap legenda voor deze week
    var coLegend = children.map(function(c){
      var co  = coparenting[c] || {present_this_week:true};
      var th  = themes[c]||{bg:"#1565C0",emoji:"⭐"};
      var cls = co.present_this_week ? "leg-present" : "leg-absent";
      return '<div class="leg '+cls+'"><span class="ldot" style="background:'+th.bg+'">'+th.emoji+'</span>'+c+(co.present_this_week?"":" 🏠")+'</div>';
    }).join("");

    return '<div class="sec week-s"><div class="sl">📆 Deze week</div><div class="wk-grid">'+cols+'</div>'+
      '<div class="leg-row">'+coLegend+'</div>'+
      '<div class="type-leg"><span>🔄 Dagelijks</span><span>📅 Wekelijks</span><span>🗓️ Maand</span><span style="opacity:.5">🏠 Niet thuis</span></div>'+
    '</div>';
  }

  // ── Maandoverzicht ────────────────────────────────────────────────────────
  _monthSection(month_ov, themes, children) {
    var rows = month_ov.map(function(mt){
      var hdr = '<div class="mo-hdr"><span class="mo-name">🏠 '+mt.name+'</span>' +
        '<span class="mo-when">'+mt.day_of_week+' · '+mt.week_of_month+'</span></div>';
      var childRows = children.map(function(child){
        var info = mt.next_by_child[child];
        if (!info) return '<div class="mo-child mo-na"><span class="mo-emoji">'+((themes[child]||{}).emoji||"⭐")+'</span><span class="mo-cn">'+child+'</span><span style="font-size:12px;opacity:.5">Niet ingepland</span></div>';
        var th   = themes[child]||{bg:"#1565C0",emoji:"⭐"};
        var d    = info.trigger || "";
        var parts = d.split("-");
        var disp  = parts.length===3 ? parts[2]+"/"+parts[1] : d;
        return '<div class="mo-child'+(info.done?" mo-done":"")+'" data-key="month__'+info.month_key+'__'+child+'__'+mt.name+'">' +
          '<span class="mo-emoji">'+th.emoji+'</span>' +
          '<span class="mo-cn">'+child+'</span>' +
          '<span class="mo-dt" style="background:'+th.bg+'">'+disp+'</span>' +
          '<span class="mo-tk">'+(info.done?"✅":"⬜")+'</span>' +
        '</div>';
      }).join("");
      return hdr+childRows;
    }).join("<hr class='mo-hr'>");
    return '<div class="sec month-s"><div class="sl">🗓️ Maandtaken</div><div class="mo-list">'+rows+'</div></div>';
  }

  _listeners() {
    var self = this;
    this.shadowRoot.querySelectorAll("[data-key]").forEach(function(el){
      el.addEventListener("click",function(e){
        e.stopPropagation();
        el.classList.toggle("done");
        self._hass.callService("kindertaken","mark_done",{key:el.dataset.key});
      });
    });
  }

  _css() { return [
    "*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}",
    "ha-card{font-family:var(--primary-font-family,Roboto,sans-serif);background:var(--card-background-color,#fff);border-radius:16px;overflow:hidden}",
    ".hdr{display:flex;align-items:center;gap:14px;padding:16px 20px;background:linear-gradient(135deg,#1a237e,#4527A0);color:#fff}",
    ".hdr-t{font-size:22px;font-weight:800}",
    ".hdr-s{font-size:13px;opacity:.85;margin-top:3px}",
    ".sec{padding:14px}",
    ".today-s{background:var(--secondary-background-color,#f4f4f4);border-bottom:1px solid var(--divider-color,#ddd)}",
    ".week-s{border-bottom:1px solid var(--divider-color,#ddd)}",
    ".month-s{background:var(--secondary-background-color,#f4f4f4)}",
    ".sl{font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:1px;color:var(--secondary-text-color);margin-bottom:12px}",
    ".muted{color:var(--secondary-text-color);font-size:13px}",
    /* Kind-kaarten */
    ".today-g{display:flex;gap:10px;flex-wrap:wrap}",
    ".cc{flex:1;min-width:140px;border-radius:14px;background:linear-gradient(145deg,var(--lt),var(--bg));color:#fff;box-shadow:0 4px 14px rgba(0,0,0,.18);overflow:hidden;transition:opacity .2s}",
    ".cc-absent{background:var(--secondary-background-color,#f4f4f4)!important;box-shadow:none;border:2px dashed var(--divider-color,#ccc)}",
    ".ct{display:flex;align-items:center;gap:8px;padding:10px 12px 6px;flex-wrap:wrap}",
    ".ce{font-size:24px}",
    ".cn{font-size:17px;font-weight:800;flex:1}",
    ".badge{font-size:10px;font-weight:700;border-radius:20px;padding:2px 8px;white-space:nowrap}",
    ".done-badge{background:rgba(255,255,255,.25);color:#fff}",
    ".absent{background:#fff3cd;color:#856404}",
    ".blocked{background:#f8d7da;color:#842029}",
    ".cb{padding:4px 10px 10px;display:flex;flex-direction:column;gap:5px}",
    ".glbl{font-size:10px;font-weight:700;opacity:.7;text-transform:uppercase;letter-spacing:.8px;margin-top:4px;padding-left:2px}",
    ".free{padding:8px 4px;font-size:13px;text-align:center;opacity:.7}",
    /* Taak-knoppen */
    ".tbtn{display:flex;align-items:center;gap:8px;background:rgba(255,255,255,.2);border:none;border-radius:10px;padding:8px 10px;cursor:pointer;color:#fff;font-size:13px;font-weight:600;text-align:left;width:100%;transition:background .15s,opacity .15s}",
    ".tbtn:hover{background:rgba(255,255,255,.35)}",
    ".tbtn.done{background:rgba(255,255,255,.08);opacity:.5;text-decoration:line-through}",
    ".ti{font-size:17px;flex-shrink:0}",
    ".tn{flex:1}",
    ".tk{font-size:17px;flex-shrink:0}",
    /* Week grid */
    ".wk-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:5px}",
    ".wc{border-radius:10px;border:2px solid var(--divider-color,#e0e0e0);overflow:hidden}",
    ".wc.today{border-color:#1a237e;box-shadow:0 2px 10px rgba(26,35,126,.25)}",
    ".wh{padding:5px 3px;text-align:center;background:var(--secondary-background-color,#f4f4f4)}",
    ".wc.today .wh{background:linear-gradient(135deg,#1a237e,#4527A0);color:#fff}",
    ".wd{font-size:12px;font-weight:800}",
    ".wdt{font-size:9px;opacity:.7;margin-top:1px}",
    ".wb-wrap{padding:4px;display:flex;flex-direction:column;gap:3px;min-height:36px}",
    ".wb{border-radius:5px;padding:3px 4px;font-size:10px;font-weight:700;color:#fff;display:flex;align-items:center;gap:2px;cursor:pointer;width:100%;transition:opacity .15s;border:none}",
    ".wb:hover{opacity:.8}",
    ".wb.done{opacity:.3;text-decoration:line-through}",
    ".wb-absent{border-radius:5px;padding:3px 4px;font-size:9px;color:var(--secondary-text-color);display:flex;align-items:center;justify-content:center;border:1.5px dashed;opacity:.45}",
    ".wn{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:44px}",
    ".we{color:var(--disabled-text-color,#bbb);font-size:11px;text-align:center;padding:8px 0}",
    /* Legenda */
    ".leg-row{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}",
    ".leg{display:flex;align-items:center;gap:5px;font-size:12px;color:var(--secondary-text-color)}",
    ".leg-absent{opacity:.5;text-decoration:line-through}",
    ".ldot{font-size:14px}",
    ".type-leg{display:flex;gap:12px;margin-top:6px;font-size:11px;color:var(--secondary-text-color)}",
    /* Maand */
    ".mo-list{display:flex;flex-direction:column;gap:10px}",
    ".mo-hr{border:none;border-top:1px solid var(--divider-color,#e8e8e8);margin:4px 0}",
    ".mo-hdr{display:flex;align-items:center;gap:8px;margin-bottom:6px}",
    ".mo-name{font-size:14px;font-weight:700;color:var(--primary-text-color);flex:1}",
    ".mo-when{font-size:11px;color:var(--secondary-text-color);background:var(--divider-color,#e8e8e8);padding:2px 8px;border-radius:10px}",
    ".mo-child{display:flex;align-items:center;gap:8px;background:var(--card-background-color,#fff);border:1px solid var(--divider-color,#e8e8e8);border-radius:10px;padding:8px 12px;cursor:pointer;transition:opacity .15s;margin-bottom:4px}",
    ".mo-child:hover{opacity:.85}",
    ".mo-child.mo-done{opacity:.4;text-decoration:line-through}",
    ".mo-child.mo-na{cursor:default;opacity:.5}",
    ".mo-emoji{font-size:18px;flex-shrink:0}",
    ".mo-cn{flex:1;font-size:14px;font-weight:600;color:var(--primary-text-color)}",
    ".mo-dt{font-size:11px;font-weight:700;color:#fff;padding:3px 8px;border-radius:10px}",
    ".mo-tk{font-size:18px;flex-shrink:0}",
  ].join("\n"); }

  getCardSize(){ return 7; }
  static getConfigElement(){ return document.createElement("kindertaken-card-editor"); }
  static getStubConfig(){ return {entity:"sensor.kindertaken_week"}; }
}

class KindertakenCardEditor extends HTMLElement {
  setConfig(c){ this._config=c||{}; }
  connectedCallback(){
    var e=(this._config.entity)||"sensor.kindertaken_week";
    this.innerHTML='<div style="padding:16px"><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px">Sensor entiteit</label><input id="e" type="text" value="'+e+'" style="width:100%;padding:8px;border:1px solid #ccc;border-radius:8px;font-size:14px"></div>';
    var self=this;
    this.querySelector("#e").addEventListener("change",function(ev){
      self.dispatchEvent(new CustomEvent("config-changed",{detail:{config:{entity:ev.target.value.trim()}},bubbles:true,composed:true}));
    });
  }
}

customElements.define("kindertaken-card",KindertakenCard);
customElements.define("kindertaken-card-editor",KindertakenCardEditor);
window.customCards=window.customCards||[];
if(!window.customCards.find(function(c){return c.type==="kindertaken-card";})){
  window.customCards.push({type:"kindertaken-card",name:"Kindertaken Planner",description:"Co-ouderschap + rotatie/week/maandtaken.",preview:true});
}
console.info("%c KINDERTAKEN %c v2.1 ","color:white;background:#1a237e;padding:3px 8px;border-radius:4px 0 0 4px;font-weight:700","color:#1a237e;background:#fff;padding:3px 8px;border-radius:0 4px 4px 0;border:1px solid #1a237e");
