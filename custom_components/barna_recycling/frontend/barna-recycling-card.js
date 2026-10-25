// SPDX-License-Identifier: GPL-3.0-only
import {cardModel, escapeHtml as e, formatDate, localClock} from './card-model.js';
const defaults = {title:"Barna Recycling", compact:false, compact_buttons:false, show_links:false, show_balance:false, show_history:true, highlight_time:"18:00"};
const styles = `
 :host{display:block;container-type:inline-size;color:var(--primary-text-color,#17252b)}*{box-sizing:border-box}
 ha-card{display:block;overflow:hidden;background:var(--ha-card-background,var(--card-background-color,#fff));border:1px solid var(--divider-color,#e1e7e4);border-radius:var(--ha-card-border-radius,18px);box-shadow:var(--ha-card-box-shadow,none)}
 .body{padding:22px}header{display:flex;align-items:center;justify-content:space-between;gap:12px}h2{margin:0;font-size:19px;font-weight:650;line-height:1.3;overflow-wrap:anywhere}.badge{font-size:11px;padding:5px 8px;border-radius:20px;background:color-mix(in srgb,#3d9c50 12%,transparent);color:var(--primary-text-color,#203d28);white-space:nowrap}.muted{color:var(--secondary-text-color,#66736d);font-size:12px}.hero{display:flex;gap:18px;align-items:center;margin:26px 0 20px}.cal{background:color-mix(in srgb,#4f9e42 12%,transparent);border-radius:16px;width:66px;height:70px;flex-shrink:0;display:grid;place-items:center;color:#44943a}.cal svg{width:38px;height:38px}.eyebrow{font-size:10px;font-weight:650;letter-spacing:1.5px;color:var(--secondary-text-color,#66736d);text-transform:uppercase}.date{font-size:29px;font-weight:700;letter-spacing:-.7px;line-height:1.2;margin:5px 0;overflow-wrap:anywhere}.date.due{color:var(--error-color,#d32f2f)}.bins{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin:20px 0}.bin{padding:12px 8px;border:1px solid var(--divider-color,#e1e7e4);border-top:3px solid var(--bin);border-radius:10px;text-align:center;min-width:0}.bin .name{font-size:12px;font-weight:600}.bin .kg{font-weight:650;font-size:19px;margin:8px 0 3px}.bin small{display:block;font-size:10px;color:var(--secondary-text-color,#66736d)}.note{font-size:12px;line-height:1.5;padding:10px 12px;border-radius:8px;background:color-mix(in srgb,#e89834 13%,transparent);margin:8px 0;overflow-wrap:anywhere}.coverage{margin:12px 0;font-size:11px;color:var(--secondary-text-color,#66736d)}details{border-top:1px solid var(--divider-color,#e1e7e4);padding-top:12px;margin-top:14px}summary{cursor:pointer;font-size:13px;color:var(--secondary-text-color,#66736d)}table{width:100%;border-collapse:collapse;font-size:12px;margin-top:8px}td,th{padding:9px 3px;text-align:left;border-bottom:1px solid var(--divider-color,#e1e7e4)}td:last-child,th:last-child{text-align:right}.links{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}.links a{font-size:12px;color:var(--primary-text-color,#17252b);text-decoration:none;border:1px solid var(--divider-color,#e1e7e4);padding:8px 10px;border-radius:8px}.balance{display:flex;justify-content:space-between;font-size:13px;margin:12px 0;gap:12px}.compact .body{padding:16px}.compact .hero{margin:16px 0 8px}.compact .date{font-size:25px}.compact .cal{width:52px;height:58px}.footer{margin-top:14px;font-size:10px;color:var(--secondary-text-color,#66736d)}.unavailable{padding:24px 0;font-size:14px;color:var(--secondary-text-color,#66736d)}
 @media(max-width:340px){.body{padding:16px}.date{font-size:25px}.hero{gap:12px}.bin{padding:10px 4px}h2{font-size:17px}}
`;
const calendarIcon=`<img src="${new URL('./bins.svg',import.meta.url)}" alt="Black waste, blue recycling and brown compost bins" style="width:100%;height:100%;object-fit:contain">`;
const popupStyles=`.cal{background:transparent;width:88px;height:72px}.compact .cal{width:76px;height:62px}button{font:inherit;color:inherit;cursor:pointer}.links button{font-size:12px;background:transparent;color:var(--primary-text-color,#17252b);border:1px solid var(--divider-color,#e1e7e4);padding:8px 10px;border-radius:8px}button:focus-visible,a:focus-visible,[role=button]:focus-visible{outline:2px solid var(--primary-color,#398b45);outline-offset:3px}.compact ha-card,.compact-click{cursor:pointer}dialog{color:var(--primary-text-color,#17252b);background:var(--ha-card-background,var(--card-background-color,#fff));border:1px solid var(--divider-color,#e1e7e4);border-radius:20px;padding:0;width:min(580px,calc(100vw - 24px));max-height:85dvh;box-shadow:0 24px 80px #0006}dialog::backdrop{background:#0008;backdrop-filter:blur(2px)}.modal{padding:22px;overflow:auto}.modal header{margin-bottom:20px}.close{border:0;border-radius:50%;background:var(--secondary-background-color,#f0f3f1);font-size:23px;width:34px;height:34px}.tabs{display:flex;gap:8px;margin:0 0 20px}.tabs button{border:1px solid var(--divider-color,#dfe6e1);border-radius:20px;background:transparent;font-size:13px;padding:8px 15px}.tabs button.active{background:#3e8d3d;color:white;border-color:#3e8d3d}.month-nav{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}.month-nav button{background:transparent;border:1px solid var(--divider-color,#dfe6e1);border-radius:8px;padding:5px 12px;font-size:22px}.month-title{font-weight:650}.month{table-layout:fixed;font-size:13px;margin:0}.month td,.month th{text-align:center!important;border:0;height:37px;padding:4px}.month th{font-size:11px;color:var(--secondary-text-color,#64736c)}.day{display:grid;place-items:center;border-radius:9px;width:30px;height:30px;margin:auto}.collection{background:#3e8d3d;color:white;font-weight:700}.calendar-key{display:flex;align-items:center;gap:8px;font-size:12px;margin:18px 0}.dot{height:10px;width:10px;border-radius:50%;background:#3e8d3d}.event-row{padding:10px 0;border-top:1px solid var(--divider-color,#e1e7e4);font-size:13px;display:flex;gap:12px;justify-content:space-between}.history-table{font-size:12px}.history-table td{vertical-align:top}.history-table small{font-size:10px;color:var(--secondary-text-color,#66736d)}.modal .coverage{line-height:1.5} @media(max-width:400px){.modal{padding:16px}.history-table{font-size:11px}.day{width:27px;height:27px}}`;

class BarnaCard extends HTMLElement {
  static getConfigElement(){return document.createElement('barna-recycling-card-editor');}
  static getStubConfig(hass){return {entity:Object.keys(hass.states).find(id=>hass.states[id].attributes?.barna_card) || ""};}
  setConfig(config){
    if (!config.entity || typeof config.entity!=="string" || !config.entity.startsWith('sensor.')) throw new Error('Choose the Barna Collection summary sensor.');
    const preset=this.localName.endsWith('-compact-buttons') ? {compact:true,compact_buttons:true} : this.localName.endsWith('-compact') ? {compact:true} : this.localName.endsWith('-with-links') ? {show_links:true} : {};
    this.config={...defaults,...preset,...config};
    if(!/^([01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?$/.test(this.config.highlight_time)) throw new Error('Highlight time must be HH:MM, for example 18:00.');
    this.render();
  }
  set hass(value){const previous=this._hass?.states[this.config?.entity];this._hass=value;if(previous!==value.states[this.config?.entity]){this.history=null;this.render();}}
  getCardSize(){return this.config?.compact ? 2 : 6;}
  getGridOptions(){return this.config?.compact?{columns:this.config.compact_buttons?12:6,min_columns:this.config.compact_buttons?6:3,rows:2}:{columns:12,min_columns:6,rows:'auto'};}
  connectedCallback(){if(!this.shadowRoot){this.attachShadow({mode:'open'});this.shadowRoot.addEventListener('click',event=>this.handleClick(event));this.shadowRoot.addEventListener('keydown',event=>{if(this.config?.compact && event.target.matches('[role=button]') && ['Enter',' '].includes(event.key)){event.preventDefault();this.openPopup('calendar');}});}this.timer=setInterval(()=>{if(!this.popup)this.render();},30000);this.render();}
  disconnectedCallback(){clearInterval(this.timer);}
  handleClick(event){
    const button=event.target.closest('[data-action]');
    if(button){
      const action=button.dataset.action;
      if(action==='close'){this.popup=null;this.shadowRoot.querySelector('dialog')?.close();return;}
      if(action==='previous'||action==='next'){const [year,month]=this.month.split('-').map(Number);const d=new Date(Date.UTC(year,month-1+(action==='next'?1:-1),1));this.month=d.toISOString().slice(0,7);this.render();return;}
      this.openPopup(action);return;
    }
    if(event.target.tagName==='DIALOG'){this.popup=null;event.target.close();return;}
    if(this.config?.compact && !event.target.closest('a,button,dialog'))this.openPopup('calendar');
  }
  async openPopup(tab){
    this.popup=tab;
    this.month=this.month || localClock(new Date(),this._hass.config?.time_zone || 'Europe/Dublin').date.slice(0,7);
    this.render();
    if(tab==='history' && !this.history && !this.loadingHistory){
      this.loadingHistory=true;
      try{
        const reply=await this._hass.callWS({type:'call_service',domain:'barna_recycling',service:'get_lift_history',service_data:{entity_id:this.config.entity},return_response:true});
        this.history=reply.response;
        if(!Array.isArray(this.history?.records))throw new Error('Invalid history');
        this.historyError=false;
      }catch(_){this.historyError=true;}
      this.loadingHistory=false;
      if(this.popup==='history')this.render();
    }
  }
  popupContent(a,locale){
    if(!this.popup)return '';
    let body='';
    if(this.popup==='calendar'){
      const [year,month]=this.month.split('-').map(Number), first=new Date(Date.UTC(year,month-1,1));
      const offset=(first.getUTCDay()+6)%7, count=new Date(Date.UTC(year,month,0)).getUTCDate();
      const events=(a.collections || []).filter(row=>row.date.startsWith(this.month));
      const dates=new Set(events.map(row=>row.date));
      const cells=Array.from({length:Math.ceil((offset+count)/7)*7},(_,i)=>{const day=i-offset+1,iso=`${this.month}-${String(day).padStart(2,'0')}`;return `<td>${day>0&&day<=count?`<span class="day ${dates.has(iso)?'collection':''}">${day}</span>`:''}</td>`;});
      body=`<div class="month-nav"><button data-action="previous" aria-label="Previous month">‹</button><span class="month-title">${e(new Intl.DateTimeFormat(locale,{month:'long',year:'numeric',timeZone:'UTC'}).format(first))}</span><button data-action="next" aria-label="Next month">›</button></div><table class="month" aria-label="Collection dates"><thead><tr>${['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map(d=>`<th>${d}</th>`).join('')}</tr></thead><tbody>${Array.from({length:cells.length/7},(_,i)=>`<tr>${cells.slice(i*7,i*7+7).join('')}</tr>`).join('')}</tbody></table><div class="calendar-key"><span class="dot"></span>Published collection</div>${events.map(row=>`<div class="event-row"><strong>${e(formatDate(row.date,locale))}</strong><span>${e(row.streams.map(s=>s[0].toUpperCase()+s.slice(1)).join(' / '))}</span></div>`).join('') || '<div class="muted">No published collections for this month.</div>'}`;
    } else {
      const records=this.history?.records || (this.historyError ? a.recent_lifts || [] : []);
      body=`<div class="coverage">Recorded lifts from ${e(this.history?.history_from || a.history_from || 'unknown')}. ${this.historyError?'Full history could not be loaded; showing recent records.':!this.history?'Loading lift history…':`${records.length} records`}</div><table class="history-table"><thead><tr><th>Date</th><th>Bin / vehicle</th><th>kg</th></tr></thead><tbody>${records.map(row=>`<tr><td>${e(row.date)}</td><td>${e(row.description)}<br><small>${e(row.vehicle)}</small></td><td>${e(row.weight)}</td></tr>`).join('')}</tbody></table>`;
    }
    const sync=a.last_successful_sync?new Date(a.last_successful_sync).toLocaleString(locale,{timeZone:this._hass.config?.time_zone || 'Europe/Dublin'}):'Not yet available';
    return `<dialog aria-labelledby="barna-popup-title"><div class="modal"><header><h2 id="barna-popup-title">${e(this.config.title)}</h2><button class="close" data-action="close" aria-label="Close popup">×</button></header><nav class="tabs" aria-label="Collection details"><button data-action="calendar" class="${this.popup==='calendar'?'active':''}" aria-pressed="${this.popup==='calendar'}">Calendar</button><button data-action="history" class="${this.popup==='history'?'active':''}" aria-pressed="${this.popup==='history'}">Lift history</button></nav>${body}<div class="sync">Last successful sync<br><strong>${e(sync)}</strong>${a.data_stale?'<p>Saved data — the latest refresh failed.</p>':''}</div></div></dialog>`;
  }
  render(){
    if(!this.shadowRoot || !this.config || !this._hass)return;
    const c=this.config, state=this._hass.states[c.entity];
    const m=cardModel(state,new Date(),this._hass.config?.time_zone || 'Europe/Dublin',c.highlight_time);
    const locale=this._hass.locale?.language || 'en-IE';
    const fmt=d=>formatDate(d,locale), open=this.shadowRoot.querySelector('details')?.open;
    const a=m.a || {}, streams=a.next_collection?.streams || [];
    const badge=!m.available?'Unavailable':m.stale?'Saved data':a.calendar_status !== 'ok'?'Check calendar':'Updated';
    let content=`<div class="unavailable">${state && !state.attributes?.barna_card?'Select the Barna Collection summary sensor.':'Waiting for Barna data. Check the integration status.'}</div>`;
    if(m.available && a.barna_card){
      const subtitle=m.days===0?'Collection today':m.days===1?'Collection tomorrow':m.days!==null?`In ${m.days} days`:'Check the published calendar';
      content=`<div class="hero"><div class="cal">${calendarIcon}</div><div><div class="eyebrow">Next collection</div><div class="date ${m.red?'due':''}">${e(fmt(m.date))}</div><div class="muted">${e(subtitle)}${m.date?' · '+e(streams.map(s=>s[0].toUpperCase()+s.slice(1)).join(' / ')):''}</div></div></div>`;
      if(!c.compact) content+=`<div class="bins">${['waste','recycling','compost'].map((s,i)=>{const last=a.streams?.[s]?.last;return `<div class="bin" style="--bin:${['#292f33','#087fc4','#965018'][i]}"><div class="name">${e(s[0].toUpperCase()+s.slice(1))}</div><div class="kg">${last?e(last.weight)+' <small style="display:inline">kg</small>':'—'}</div><small>${last?e(fmt(last.date)):'No recorded lift'}</small></div>`;}).join('')}</div><div class="coverage">Last recorded lift per bin. History from ${e(a.history_from || 'unknown')}.</div>`;
      if(m.stale) content+=`<div class="note">Saved readings — latest refresh failed. Check the portal before relying on this schedule.</div>`;
      if(a.calendar_status!=='ok') content+=`<div class="note">Calendar ${e(a.calendar_status || 'unavailable')}. Collection dates have not been guessed.</div>`;
      if(c.show_balance){
        const balance=Number.isFinite(a.balance)?new Intl.NumberFormat(locale,{style:'currency',currency:'EUR'}).format(Math.abs(a.balance)):'—';
        content+=`<div class="balance"><span>Account ${a.balance_status==='credit'?'credit':'balance owed'}</span><strong>${e(balance)}</strong></div>`;
      }
      if(!c.compact)content+=`<div class="links"><button data-action="calendar">Calendar</button>${c.show_history?'<button data-action="history">Lift history</button>':''}${c.show_links?'<a href="https://cportal.barnarecycling.com/" target="_blank" rel="noopener noreferrer">Customer portal ↗</a>':''}</div>`;
      else content+=`<div class="muted">Tap for calendar & lift history</div>`;
    }
    const compact=`<div class="compact-main" ${c.compact_buttons?'role="button" tabindex="0" aria-label="Open calendar and lift history"':''}><div class="compact-bins">${calendarIcon}</div><div><div class="compact-label">Next Bin Day</div><div class="date ${m.red?'due':''}">${e(m.available?fmt(m.date):'Unavailable')}</div></div></div>${c.compact_buttons?'<div class="links compact-actions"><button data-action="calendar">Calendar</button><button data-action="history">Lift history</button></div>':''}`;
    this.shadowRoot.innerHTML=`<style>${styles}${popupStyles}.sync{font-size:14px;line-height:1.6;border-top:1px solid var(--divider-color,#e1e7e4);margin-top:20px;padding-top:16px;color:var(--secondary-text-color,#66736d)}.sync strong{color:var(--primary-text-color,#17252b);font-weight:500}.compact{width:fit-content;max-width:100%;height:94px}.compact .body{padding:10px;height:92px;display:grid;place-items:center}.compact-main{display:grid;grid-template-columns:64px max-content;gap:8px;align-items:center}.compact-bins{width:64px;height:55px}.compact-label{font-size:13px;font-weight:500;line-height:18px}.compact .date{font-size:16px;font-weight:500;line-height:22px;letter-spacing:0;margin:0}.compact .date.due{font-weight:700}.compact-buttons{width:100%}.compact-buttons .body{display:flex;justify-content:space-between;gap:12px}.compact-actions{margin:0;display:flex;flex-direction:column;gap:6px}.compact-actions button{padding:6px 10px;min-width:85px}.compact-buttons .compact-main{cursor:pointer;grid-template-columns:96px max-content}.compact-buttons .compact-bins{width:96px;height:76px}.compact-buttons .compact-bins img{object-fit:cover!important}.compact-buttons .compact-label{font-size:16px;line-height:22px}.compact-buttons .date{font-size:22px;line-height:28px}.compact-buttons .body{padding-top:8px;padding-bottom:8px}@container(max-width:350px){.compact-buttons .compact-main{grid-template-columns:76px max-content;gap:6px}.compact-buttons .compact-bins{width:76px;height:70px}.compact-buttons .date{font-size:20px}.compact-buttons .body{gap:8px;padding-left:8px;padding-right:8px}}@container(max-width:310px){.compact-buttons .compact-main{grid-template-columns:64px max-content}.compact-buttons .compact-bins{width:64px;height:65px}.compact-buttons .date{font-size:18px}.compact-buttons .compact-label{font-size:14px}}</style><ha-card class="${c.compact?'compact compact-click'+(c.compact_buttons?' compact-buttons':''):''}" ${c.compact&&!c.compact_buttons?'role="button" tabindex="0" aria-label="Open calendar and lift history"':''}><div class="body">${c.compact?compact:`<header><h2>${e(c.title)}</h2><span class="badge">${e(badge)}</span></header>${content}`}</div></ha-card>${this.popupContent(a,locale)}`;
    const dialog=this.shadowRoot.querySelector('dialog');if(dialog){dialog.addEventListener('cancel',()=>{this.popup=null;});dialog.showModal();}
  }
}
class BarnaEditor extends HTMLElement {
  setConfig(config){this.config=config;this.render();}
  set hass(hass){this._hass=hass;this.render();}
  connectedCallback(){this.render();}
  render(){
    if(!this._hass || !this.config)return;
    if(!this.form){
      this.form=document.createElement('ha-form');this.append(this.form);
      this.form.schema=[{name:'entity',required:true,selector:{entity:{domain:'sensor',integration:'barna_recycling'}}},
        {name:'title',selector:{text:{}}},{name:'highlight_time',selector:{text:{}}},
        ...['compact','compact_buttons','show_links','show_balance','show_history'].map(name=>({name,selector:{boolean:{}}}))];
      const labels={entity:'Collection summary sensor',title:'Title',highlight_time:'Turn date red the day before at (HH:MM)',compact:'Compact layout',compact_buttons:'Buttons beside compact date',show_links:'Show portal links',show_balance:'Show account balance',show_history:'Show lift history'};
      this.form.computeLabel=s=>labels[s.name] || s.name;
      this.form.addEventListener('value-changed',event=>{this.config={...this.config,...event.detail.value};this.dispatchEvent(new CustomEvent('config-changed',{detail:{config:this.config},bubbles:true,composed:true}));});
    }
    this.form.hass=this._hass;this.form.data={...defaults,...(this.config.type?.endsWith('-compact-buttons')?{compact:true,compact_buttons:true}:this.config.type?.endsWith('-compact')?{compact:true}:{}),...(this.config.type?.endsWith('-with-links')?{show_links:true}:{}),...this.config};
  }
}
customElements.define('barna-recycling-card',BarnaCard);
customElements.define('barna-recycling-card-with-links',class extends BarnaCard{});
customElements.define('barna-recycling-card-compact',class extends BarnaCard{});
customElements.define('barna-recycling-card-compact-buttons',class extends BarnaCard{});
customElements.define('barna-recycling-card-editor',BarnaEditor);
window.customCards=window.customCards || [];
for(const [type,name,description] of [
  ['barna-recycling-card','Barna Recycling','Collections, weights and lift history'],
  ['barna-recycling-card-with-links','Barna Recycling · with links','Collection overview and customer portal links'],
  ['barna-recycling-card-compact','Barna Recycling · compact','Compact date and bin reminder'],
  ['barna-recycling-card-compact-buttons','Barna Recycling · compact with buttons','Compact bins and date with calendar and history buttons'],
])window.customCards.push({type,name,description,preview:true});
