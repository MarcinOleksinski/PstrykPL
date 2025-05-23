from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfEnergy
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["cost_coordinator"]
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        EnergyCostSensor(coordinator),
        EnergySoldSensor(coordinator),
        EnergyBalanceSensor(coordinator)
    ])


class EnergyCostSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Pstryk Całkowity koszt energii"
        self._attr_unique_id = "pstryk_cost_total"
        self._attr_native_unit_of_measurement = "PLN"
        self._attr_device_class = "monetary"
        self._attr_state_class = "total"

    @property
    def native_value(self):
        return self.coordinator.data.get("fae_total_cost")


class EnergySoldSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Pstryk Wartość energii sprzedanej"
        self._attr_unique_id = "pstryk_sold_value"
        self._attr_native_unit_of_measurement = "PLN"
        self._attr_device_class = "monetary"
        self._attr_state_class = "total"

    @property
    def native_value(self):
        return self.coordinator.data.get("total_energy_sold_value")


class EnergyBalanceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Pstryk Bilans energii (PLN)"
        self._attr_unique_id = "pstryk_energy_balance"
        self._attr_native_unit_of_measurement = "PLN"
        self._attr_device_class = "monetary"
        self._attr_state_class = "total"

    @property
    def native_value(self):
        return self.coordinator.data.get("total_energy_balance_value")
