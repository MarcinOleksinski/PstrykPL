"""Sensory Pstryk.pl z cenami energii."""
from homeassistant.components.sensor import SensorEntity
#from homeassistant.const import CURRENCY_ZLOTY
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    await coordinator.async_config_entry_first_refresh()

    sensors = []
    for idx, frame in enumerate(coordinator.data.get("frames", [])):
        sensors.append(PstrykPriceSensor(coordinator, f"frame_{idx}", frame))

    async_add_entities(sensors)


class PstrykPriceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, unique_id: str, frame: dict):
        super().__init__(coordinator)
        self._attr_unique_id = f"pstryk_price_{unique_id}"
        self._attr_name = f"Pstryk Cena energii ({frame.get('start', '')[-8:-3]})"
        self._attr_native_unit_of_measurement = "PLN"
        self._attr_device_class = "monetary"
        self._attr_state_class = "measurement"
        self.frame = frame

    @property
    def native_value(self):
        return self.frame.get("price_gross")

    @property
    def extra_state_attributes(self):
        return {
            "price_net": self.frame.get("price_net"),
            "is_cheap": self.frame.get("is_cheap"),
            "is_expensive": self.frame.get("is_expensive"),
            "start": self.frame.get("start"),
            "end": self.frame.get("end"),
        }