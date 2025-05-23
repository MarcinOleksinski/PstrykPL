from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfEnergy
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        PstrykLivePriceSensor(coordinator),
        PstrykAvgPriceSensor(coordinator, "gross"),
        PstrykAvgPriceSensor(coordinator, "net")
    ])


class PstrykLivePriceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Pstryk Cena bieżąca (brutto)"
        self._attr_unique_id = "pstryk_price_now"
        self._attr_native_unit_of_measurement = "PLN"
        self._attr_device_class = "monetary"
        self._attr_state_class = None

    @property
    def native_value(self):
        frames = self.coordinator.data.get("frames", [])
        return frames[-1]["price_gross"] if frames else None

    @property
    def extra_state_attributes(self):
        frames = self.coordinator.data.get("frames", [])
        if not frames:
            return {}
        f = frames[-1]
        return {
            "price_net": f.get("price_net"),
            "is_cheap": f.get("is_cheap"),
            "is_expensive": f.get("is_expensive"),
            "start": f.get("start"),
            "end": f.get("end")
        }


class PstrykAvgPriceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, mode: str = "gross"):
        super().__init__(coordinator)
        self.mode = mode
        self._attr_name = f"Pstryk Cena średnia ({'brutto' if mode == 'gross' else 'netto'})"
        self._attr_unique_id = f"pstryk_price_avg_{mode}"
        self._attr_native_unit_of_measurement = "PLN"
        self._attr_device_class = "monetary"
        self._attr_state_class = None

    @property
    def native_value(self):
        return self.coordinator.data.get(f"price_{self.mode}_avg")