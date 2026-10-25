// SPDX-License-Identifier: GPL-3.0-only
export const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

export function localClock(now, timeZone) {
  const parts = new Intl.DateTimeFormat("en-GB", {timeZone, year:"numeric", month:"2-digit", day:"2-digit", hour:"2-digit", minute:"2-digit", hourCycle:"h23"}).formatToParts(now);
  const p = Object.fromEntries(parts.map(x => [x.type,x.value]));
  return {date:`${p.year}-${p.month}-${p.day}`, time:`${p.hour}:${p.minute}`};
}
export function dayNumber(iso) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(iso || "")) return NaN;
  const d = new Date(`${iso}T12:00:00Z`);
  return Number.isFinite(d.getTime()) && d.toISOString().slice(0,10) === iso ? Math.floor(d.getTime()/86400000) : NaN;
}
export function highlightDate(collection, now, timeZone, at="18:00") {
  const clock = localClock(now,timeZone);
  const days = dayNumber(collection) - dayNumber(clock.date);
  return days === 0 || (days === 1 && clock.time >= at.slice(0,5));
}
export function formatDate(iso, locale="en-IE") {
  return Number.isFinite(dayNumber(iso)) ? new Intl.DateTimeFormat(locale,{weekday:"short",day:"numeric",month:"short",timeZone:"UTC"}).format(new Date(`${iso}T12:00:00Z`)) : "No published date";
}
export function cardModel(state, now, timeZone, highlightTime="18:00") {
  if (!state || ["unavailable","unknown"].includes(state.state)) return {available:false};
  const a=state.attributes || {}, next=a.next_collection;
  const clock=localClock(now,timeZone);
  const date = Number.isFinite(dayNumber(next?.date)) && next.date >= clock.date ? next.date : null;
  return {available:true, a, date, red:highlightDate(date,now,timeZone,highlightTime),
    days:date ? dayNumber(date)-dayNumber(clock.date) : null, stale:a.data_stale === true};
}
