"""Collections, recorded lifts and read-only account values."""
from datetime import date, datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory, UnitOfMass
from homeassistant.util import dt as dt_util

from .const import STREAMS
from .entity import BarnaEntity
from .model import next_collection, stream_summary


async def async_setup_entry(hass, entry, async_add_entities):
    entities = [BarnaSensor(entry.runtime_data, key, name) for key, name in (
        ("summary", "Collection summary"), ("balance", "Account balance"),
        ("balance_status", "Balance status"), ("alerts", "Account alerts"),
        ("history", "Lift history"), ("calendar_status", "Calendar status"),
        ("last_successful_sync", "Last successful sync"))]
    for stream in STREAMS:
        for kind, name in (("next", "Next collection"), ("last_date", "Last lift"),
                           ("last_weight", "Last lift weight"), ("total", "Recorded weight"), ("count", "Recorded lifts")):
            entities.append(BarnaSensor(entry.runtime_data, kind, f"{stream.title()} {name.lower()}", stream))
    async_add_entities(entities)


class BarnaSensor(BarnaEntity, SensorEntity):
    def __init__(self, coordinator, key, name, stream=None):
        super().__init__(coordinator, f"{stream}_{key}" if stream else key, name)
        self.key, self.stream = key, stream
        self._attr_icon = "mdi:recycle"
        if key in {"next", "last_date"}:
            self._attr_device_class = SensorDeviceClass.DATE
        if key == "last_successful_sync":
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        if key == "balance":
            self._attr_device_class = SensorDeviceClass.MONETARY
            self._attr_native_unit_of_measurement = "EUR"
            self._attr_suggested_display_precision = 2
        if key in {"last_weight", "total"}:
            self._attr_device_class = SensorDeviceClass.WEIGHT
            self._attr_native_unit_of_measurement = UnitOfMass.KILOGRAMS
        if key in {"total", "count", "history"}:
            self._attr_entity_registry_enabled_default = False
        if key in {"calendar_status", "history"}:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        today = dt_util.now().date()
        if self.key == "summary":
            event = next_collection(data, today)
            return event["date"] if event else "No published collection"
        if self.key == "next":
            event = next_collection(data, today, self.stream)
            return date.fromisoformat(event["date"]) if event else None
        if self.stream:
            summary = stream_summary(data, self.stream)
            last = summary["last"]
            if self.key == "last_date":
                return date.fromisoformat(last["date"]) if last else None
            if self.key == "last_weight":
                return last["weight"] if last else None
            return summary["count" if self.key == "count" else "total_weight"]
        if self.key == "last_successful_sync":
            return datetime.fromisoformat(data[self.key]) if data.get(self.key) else None
        if self.key == "alerts":
            return len(data.get("alerts", []))
        if self.key == "history":
            return len(data.get("lifts", []))
        if self.key == "calendar_status":
            if data.get(self.key) == "ok" and not next_collection(data, today):
                return "exhausted"
        return data.get(self.key)

    @property
    def extra_state_attributes(self):
        attrs = super().extra_state_attributes
        data = self.coordinator.data or {}
        today = dt_util.now().date()
        if self.key == "summary":
            attrs.update({"barna_card": True, "next_collection": next_collection(data, today),
                          "collections": data.get("collections", []),
                          "streams": {s: stream_summary(data, s) for s in STREAMS},
                          "history_from": data.get("history_from"), "history_to": (data.get("last_successful_sync") or "")[:10],
                          "recent_lifts": data.get("lifts", [])[:12], "balance": data.get("balance"),
                          "balance_status": data.get("balance_status"), "alerts": data.get("alerts", []),
                          "calendar_status": data.get("calendar_status"), "calendar_years": data.get("calendar_years", []),
                          "calendar_advisories": data.get("calendar_advisories", [])})
        if self.key == "history":
            attrs.update({"records": data.get("lifts", []), "history_from": data.get("history_from"),
                          "history_to": (data.get("last_successful_sync") or "")[:10]})
        if self.stream:
            attrs.update({"history_from": data.get("history_from"), "last_record": stream_summary(data, self.stream)["last"]})
        if self.key == "next" or self.key == "calendar_status":
            attrs.update({"advisories": data.get("calendar_advisories", []), "published_years": data.get("calendar_years", [])})
        if self.key == "alerts":
            attrs["messages"] = data.get("alerts", [])
        if self.key == "balance":
            attrs.update({"status": data.get("balance_status"), "sign_convention": "Positive = debit owed; negative = credit"})
        return attrs
