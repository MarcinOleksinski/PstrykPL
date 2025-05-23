# custom_components/pstryk_pl/binary_sensor.py

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    await coordinator.async_config_entry_first_refresh()

    entities = [
        PstrykIsCheapSensor(coordinator),
        PstrykIsExpensiveSensor(coordinator),
    ]

    async_add_entities(entities)


class PstrykIsCheapSensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Pstryk Cena tania"
        self._attr_unique_id = "pstryk_price_cheap"
        self._attr_device_class = "running"

    @property
    def is_on(self):
        frames = self.coordinator.data.get("frames", [])
        return frames[-1]["is_cheap"] if frames else False

    @property
    def extra_state_attributes(self):
        frames = self.coordinator.data.get("frames", [])
        if not frames:
            return {}
        return {
            "start": frames[-1]["start"],
            "end": frames[-1]["end"],
            "price_gross": frames[-1]["price_gross"]
        }


class PstrykIsExpensiveSensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Pstryk Cena droga"
        self._attr_unique_id = "pstryk_price_expensive"
        self._attr_device_class = "problem"

    @property
    def is_on(self):
        frames = self.coordinator.data.get("frames", [])
        return frames[-1]["is_expensive"] if frames else False

    @property
    def extra_state_attributes(self):
        frames = self.coordinator.data.get("frames", [])
        if not frames:
            return {}
        return {
            "start": frames[-1]["start"],
            "end": frames[-1]["end"],
            "price_gross": frames[-1]["price_gross"]
        }