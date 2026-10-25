"""Freshness and account notice flags."""
from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import EntityCategory
from .entity import BarnaEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([BarnaBinarySensor(entry.runtime_data, "data_stale", "Data stale"),
                        BarnaBinarySensor(entry.runtime_data, "account_notice", "Account notice")])


class BarnaBinarySensor(BarnaEntity, BinarySensorEntity):
    def __init__(self, coordinator, key, name):
        super().__init__(coordinator, key, name)
        self.key = key
        if key == "data_stale":
            self._attr_device_class = BinarySensorDeviceClass.PROBLEM
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        else:
            self._attr_icon = "mdi:message-alert-outline"

    @property
    def is_on(self):
        return self.coordinator.stale if self.key == "data_stale" else bool((self.coordinator.data or {}).get("alerts"))
