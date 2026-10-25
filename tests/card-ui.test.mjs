// Exercise actual card rendering/actions with minimal DOM adapters.
// Browser layout and native dialog behaviour are verified separately.
import test from 'node:test';
import assert from 'node:assert/strict';
const registered=new Map();
globalThis.HTMLElement=class {};
globalThis.customElements={define:(name,cls)=>registered.set(name,cls)};
globalThis.window={};
await import('../custom_components/barna_recycling/frontend/barna-recycling-card.js');
const state={state:'2099-01-01',attributes:{barna_card:true,next_collection:{date:'2099-01-01',streams:['waste']},collections:[{date:'2099-01-01',streams:['waste']}],calendar_status:'ok',data_stale:false,recent_lifts:[{date:'2026-01-08',description:'DEMO <script>bad</script>',vehicle:'DEMO',weight:2}],history_from:'2026-01-01',streams:{},last_successful_sync:'2026-01-08T00:00:00+00:00'}};
function card(type='barna-recycling-card'){
  const c=new (registered.get(type))();c.localName=type;
  c.shadowRoot={innerHTML:'',querySelector:()=>null};
  c.setConfig({entity:'sensor.demo'});
  c.hass={states:{'sensor.demo':structuredClone(state)},config:{time_zone:'Europe/Dublin'},locale:{language:'en-IE'},
    callWS:async()=>({response:{records:state.attributes.recent_lifts,history_from:'2026-01-01'}})};
  return c;
}
test('all four presets register and invalid config fails safely',()=>{
  assert.equal(window.customCards.length,4);
  assert.throws(()=>card().setConfig({entity:'switch.demo'}),/summary sensor/);
  assert.throws(()=>card().setConfig({entity:'sensor.demo',highlight_time:'25:00'}),/HH:MM/);
});
test('compact presets retain distinct sizing and popup actions',()=>{
  const tiny=card('barna-recycling-card-compact'), buttons=card('barna-recycling-card-compact-buttons');
  assert.equal(tiny.getGridOptions().columns,6);assert.equal(buttons.getGridOptions().columns,12);
  assert.match(tiny.shadowRoot.innerHTML,/Open calendar and lift history/);
  assert.match(buttons.shadowRoot.innerHTML,/data-action="calendar"/);
  assert.match(buttons.shadowRoot.innerHTML,/data-action="history"/);
});
test('history uses only cached HA service response, escapes source strings and includes year',async()=>{
  const c=card();let request;
  c._hass.callWS=async value=>{request=value;return {response:{records:state.attributes.recent_lifts}}};
  await c.openPopup('history');
  assert.equal(request.type,'call_service');assert.equal(request.service,'get_lift_history');
  assert.equal(request.return_response,true);assert.equal(request.service_data.entity_id,'sensor.demo');
  assert.match(c.shadowRoot.innerHTML,/2026-01-08/);
  assert.match(c.shadowRoot.innerHTML,/&lt;script&gt;/);
  assert.doesNotMatch(c.shadowRoot.innerHTML,/<script>bad/);
});
test('failed history response explicitly labels recent fallback',async()=>{
  const c=card();c._hass.callWS=async()=>{throw Error('offline')};
  await c.openPopup('history');
  assert.match(c.shadowRoot.innerHTML,/Full history could not be loaded; showing recent records/);
  assert.match(c.shadowRoot.innerHTML,/2026-01-08/);
});
test('calendar popup uses published dates and no external calendar link',async()=>{
  const c=card();c.month='2099-01';await c.openPopup('calendar');
  assert.match(c.shadowRoot.innerHTML,/January 2099/);
  assert.match(c.shadowRoot.innerHTML,/class="day collection"/);
  assert.doesNotMatch(c.shadowRoot.innerHTML,/href=.*\.pdf/);
});
test('account change clears fetched history and unavailable state remains explicit',async()=>{
  const c=card();await c.openPopup('history');
  c.popup=null;c.hass={...c._hass,states:{'sensor.demo':{state:'unavailable',attributes:{}}}};
  assert.equal(c.history,null);assert.match(c.shadowRoot.innerHTML,/Unavailable/);
});
