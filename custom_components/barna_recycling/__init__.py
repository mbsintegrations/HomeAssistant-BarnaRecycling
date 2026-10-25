"""Read-only Barna Recycling monitoring."""
from homeassistant.const import Platform
from homeassistant.core import SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.storage import Store
import voluptuous as vol

from .const import DOMAIN
from .coordinator import BarnaCoordinator
from .frontend import async_setup_frontend

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.CALENDAR]


async def async_setup(hass, config):
    async def get_lift_history(call):
        entity = er.async_get(hass).async_get(call.data["entity_id"])
        entry = hass.config_entries.async_get_entry(entity.config_entry_id) if entity and entity.platform == DOMAIN else None
        coordinator = getattr(entry, "runtime_data", None) if entry else None
        if coordinator is None or coordinator.data is None:
            raise HomeAssistantError("Select an available Barna Recycling entity")
        data = coordinator.data
        return {"records": data["lifts"], "history_from": data["history_from"],
                "last_successful_sync": data["last_successful_sync"], "data_stale": coordinator.stale}

    hass.services.async_register(DOMAIN, "get_lift_history", get_lift_history,
                                 schema=vol.Schema({vol.Required("entity_id"): cv.entity_id}),
                                 supports_response=SupportsResponse.ONLY)
    return True


async def async_setup_entry(hass, entry):
    coordinator = BarnaCoordinator(hass, entry)
    await coordinator.async_load_cache()
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await async_setup_frontend(hass)
    return True


async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass, entry):
    await Store(hass, 1, f"{DOMAIN}_{entry.entry_id}", private=True, atomic_writes=True).async_remove()
