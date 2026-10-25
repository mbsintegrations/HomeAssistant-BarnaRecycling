"""Common identity and freshness attributes."""
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BASE_URL, DOMAIN


class BarnaEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key, name):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.account_id}_{key}"
        self._attr_name = name
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, coordinator.account_id)},
                                           name="Barna Recycling", manufacturer="Barna Recycling",
                                           model="Customer portal", configuration_url=BASE_URL)

    @property
    def available(self):
        return self.coordinator.data is not None

    @property
    def extra_state_attributes(self):
        return {"data_stale": self.coordinator.stale, "last_refresh_error": self.coordinator.error,
                "last_successful_sync": (self.coordinator.data or {}).get("last_successful_sync")}
