"""Published all-day collection events with exclusive end dates."""
from datetime import date, timedelta
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.util import dt as dt_util
from .const import STREAMS
from .entity import BarnaEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(BarnaCalendar(entry.runtime_data, stream) for stream in (None, *STREAMS))


class BarnaCalendar(BarnaEntity, CalendarEntity):
    def __init__(self, coordinator, stream):
        super().__init__(coordinator, f"calendar_{stream or 'all'}", f"{stream.title() if stream else 'All'} collections")
        self.stream = stream

    def events(self):
        data = self.coordinator.data or {}
        description = "\n".join(data.get("calendar_advisories", []))
        if self.coordinator.stale:
            description = "Cached schedule: latest portal refresh failed.\n" + description
        for row in data.get("collections", []):
            if self.stream and self.stream not in row["streams"]:
                continue
            start = date.fromisoformat(row["date"])
            yield CalendarEvent(start=start, end=start + timedelta(days=1),
                                summary=" / ".join(s.title() for s in ([self.stream] if self.stream else row["streams"])),
                                description=description)

    @property
    def event(self):
        today = dt_util.now().date()
        return next((event for event in self.events() if event.start >= today), None)

    async def async_get_events(self, hass, start_date, end_date):
        # Convert each all-day event into the HA timezone before interval testing.
        return [event for event in self.events()
                if dt_util.start_of_local_day(event.start) < end_date
                and dt_util.start_of_local_day(event.end) > start_date]
