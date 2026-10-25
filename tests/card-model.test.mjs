import test from 'node:test';
import assert from 'node:assert/strict';
import {highlightDate,localClock,cardModel,escapeHtml,dayNumber} from '../custom_components/barna_recycling/frontend/card-model.js';
test('highlight threshold uses HA timezone, not browser timezone',()=>{
  assert.equal(highlightDate('2026-06-11',new Date('2026-06-10T16:59:00Z'),'Europe/Dublin','18:00'),false);
  assert.equal(highlightDate('2026-06-11',new Date('2026-06-10T17:00:00Z'),'Europe/Dublin','18:00'),true);
  assert.equal(highlightDate('2026-06-11',new Date('2026-06-11T22:59:00Z'),'Europe/Dublin','18:00'),true);
  assert.equal(highlightDate('2026-06-11',new Date('2026-06-11T23:00:00Z'),'Europe/Dublin','18:00'),false);
});
test('calendar-day arithmetic survives spring and autumn DST',()=>{
  assert.equal(highlightDate('2026-03-30',new Date('2026-03-29T17:00:00Z'),'Europe/Dublin','18:00'),true);
  assert.equal(highlightDate('2026-10-26',new Date('2026-10-25T18:00:00Z'),'Europe/Dublin','18:00'),true);
  assert.equal(highlightDate('2027-01-01',new Date('2026-12-31T00:00:00Z'),'Europe/Dublin','00:00'),true);
});
test('missing, past and invalid dates do not highlight',()=>{
  for(const d of [null,'bad','2026-02-30','2020-01-01'])assert.equal(highlightDate(d,new Date('2026-10-25T20:00:00Z'),'Europe/Dublin'),false);
  assert.equal(Number.isNaN(dayNumber('2026-02-30')),true);
});
test('unknown states remain unavailable and old next dates are hidden',()=>{
  assert.equal(cardModel({state:'unavailable'},new Date(),'UTC').available,false);
  assert.equal(cardModel({state:'ok',attributes:{next_collection:{date:'2020-01-01'}}},new Date(),'UTC').date,null);
});
test('portal text cannot inject card HTML',()=>{
  assert.equal(escapeHtml('<script>"&\''),'&lt;script&gt;&quot;&amp;&#39;');
});
