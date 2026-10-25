"""Allowlisted diagnostics: never credentials, routes, weights or finances."""
from .const import VERSION


async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = entry.runtime_data
    data = coordinator.data or {}
    return {"version": VERSION, "data_stale": coordinator.stale,
            "error": coordinator.error, "calendar_status": data.get("calendar_status"),
            "calendar_years": data.get("calendar_years", []),
            "lift_record_count": len(data.get("lifts", [])),
            "collection_count": len(data.get("collections", []))}
