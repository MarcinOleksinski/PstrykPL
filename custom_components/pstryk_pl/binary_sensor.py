from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        PstrykIsCheapSensor(coordinator),
        PstrykIsExpensiveSensor(coordinator)
    ])


class PstrykIsCheapSensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Pstryk Cena tania"
        self._attr_unique_id = "pstryk_price_cheap"

    @property
    def is_on(self):
        frames = self.coordinator.data.get("frames", [])
        return frames[-1]["is_cheap"] if frames else False


class PstrykIsExpensiveSensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Pstryk Cena droga"
        self._attr_unique_id = "pstryk_price_expensive"

    @property
    def is_on(self):
        frames = self.coordinator.data.get("frames", [])
        return frames[-1]["is_expensive"] if frames else False
