"""Sensor Pstryk.pl – pojedyncza encja z bieżącą godzinową ceną."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    await coordinator.async_config_entry_first_refresh()
    async_add_entities([PstrykPriceSensor(coordinator)])


class PstrykPriceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "pstryk_energy_price"
        self._attr_name = "Pstryk Cena energii"
        self._attr_native_unit_of_measurement = "PLN"
        self._attr_device_class = "monetary"
        self._attr_state_class = None

    @property
    def native_value(self):
        """Zwróć najnowszą cenę brutto."""
        frames = self.coordinator.data.get("frames", [])
        if not frames:
            return None
        latest = frames[-1]
        return latest.get("price_gross")

    @property
    def extra_state_attributes(self):
        frames = self.coordinator.data.get("frames", [])
        if not frames:
            return {}
        latest = frames[-1]
        return {
            "price_net": latest.get("price_net"),
            "is_cheap": latest.get("is_cheap"),
            "is_expensive": latest.get("is_expensive"),
            "start": latest.get("start"),
            "end": latest.get("end"),
        }