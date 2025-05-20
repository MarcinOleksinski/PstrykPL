"""Example sensor for Pstryk.pl integration."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import ENERGY_KILO_WATT_HOUR
from .const import DOMAIN, DEFAULT_NAME


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor platform."""
    async_add_entities([PstrykDummySensor()])


class PstrykDummySensor(SensorEntity):
    """A dummy sensor for demonstration."""

    _attr_name = DEFAULT_NAME
    _attr_unit_of_measurement = ENERGY_KILO_WATT_HOUR
    _attr_unique_id = "pstryk_dummy_sensor"

    def __init__(self):
        """Initialize the sensor."""
        self._attr_native_value = 123.45  # przykładowa wartość

    async def async_update(self):
        """Fetch new state data for the sensor."""
        # Tu w przyszłości będzie zapytanie do API Pstryk.pl
        self._attr_native_value = 123.45