
# --- Coordinator for API data ---
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

class PstrykDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api_key):
        super().__init__(
            hass,
            _LOGGER,
            name="Pstryk Data",
            update_interval=SCAN_INTERVAL,
        )
        self.api_key = api_key

    async def _async_update_data(self):
        today = datetime.utcnow().date()
        tomorrow = today + timedelta(days=1)
        headers = {"Authorization": f"Token {self.api_key}"}
        session = async_get_clientsession(self.hass)

        async def fetch_json(url):
            try:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    _LOGGER.debug(f"Pstryk API response for {url}: {data}")
                    return data
            except Exception as e:
                _LOGGER.error(f"Error fetching {url}: {e}")
                return None

        async def fetch_prosumer_prices(day):
            url = f"https://pstryk.pl/api/integrations/prosumer-pricing/?resolution=hour&window_start={day}T00:00:00Z&window_end={day}T23:59:59Z"
            return await fetch_json(url)

        async def fetch_prices(day, resolution="hour"):
            url = f"https://pstryk.pl/api/integrations/pricing/?resolution={resolution}&window_start={day}T00:00:00Z&window_end={day}T23:59:59Z"
            return await fetch_json(url)

        async def fetch_carbon_footprint(resolution="hour"):
            url = f"https://pstryk.pl/api/integrations/meter-data/carbon-footprint/?resolution={resolution}&window_start={today}T00:00:00Z"
            return await fetch_json(url)

        async def fetch_energy_cost(resolution="hour"):
            url = f"https://pstryk.pl/api/integrations/meter-data/energy-cost/?resolution={resolution}&window_start={today}T00:00:00Z"
            return await fetch_json(url)

        async def fetch_energy_usage(resolution="hour"):
            url = f"https://pstryk.pl/api/integrations/meter-data/energy-usage/?resolution={resolution}&window_start={today}T00:00:00Z"
            return await fetch_json(url)

        data = {}
        # Standard pricing
        data["price_today"] = await fetch_prices(today)
        if datetime.utcnow().hour >= 14:
            data["price_tomorrow"] = await fetch_prices(tomorrow)
        else:
            data["price_tomorrow"] = None
        # Prosumer pricing
        data["prosumer_price_today"] = await fetch_prosumer_prices(today)
        if datetime.utcnow().hour >= 14:
            data["prosumer_price_tomorrow"] = await fetch_prosumer_prices(tomorrow)
        else:
            data["prosumer_price_tomorrow"] = None
        # Aggregates
        data["price_day"] = await fetch_prices(today, resolution="day")
        data["price_month"] = await fetch_prices(today, resolution="month")
        data["price_year"] = await fetch_prices(today, resolution="year")
        data["carbon_footprint"] = await fetch_carbon_footprint()
        data["carbon_footprint_day"] = await fetch_carbon_footprint(resolution="day")
        data["carbon_footprint_month"] = await fetch_carbon_footprint(resolution="month")
        data["carbon_footprint_year"] = await fetch_carbon_footprint(resolution="year")
        data["energy_cost"] = await fetch_energy_cost()
        data["energy_cost_day"] = await fetch_energy_cost(resolution="day")
        data["energy_cost_month"] = await fetch_energy_cost(resolution="month")
        data["energy_cost_year"] = await fetch_energy_cost(resolution="year")
        data["energy_usage"] = await fetch_energy_usage()
        data["energy_usage_day"] = await fetch_energy_usage(resolution="day")
        data["energy_usage_month"] = await fetch_energy_usage(resolution="month")
        data["energy_usage_year"] = await fetch_energy_usage(resolution="year")
        return data
import logging
from datetime import timedelta, datetime
import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.components.sensor import SensorEntity

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN, CONF_API_KEY, API_BASE_URL

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=1)

SENSOR_TYPES = {
    "price_today": {
        "name": "Pstryk Price Today",
        "unit": "PLN/kWh",
        "icon": "mdi:currency-usd",
    },
    "price_tomorrow": {
        "name": "Pstryk Price Tomorrow",
        "unit": "PLN/kWh",
        "icon": "mdi:currency-usd",
    },
    "carbon_footprint": {
        "name": "Pstryk Carbon Footprint",
        "unit": "gCO2eq",
        "icon": "mdi:cloud",
    },
    "energy_cost": {
        "name": "Pstryk Energy Cost",
        "unit": "PLN",
        "icon": "mdi:cash",
    },
    "energy_usage": {
        "name": "Pstryk Energy Usage",
        "unit": "kWh",
        "icon": "mdi:flash",
    },
}

async def async_setup_entry(hass, entry, async_add_entities):
    api_key = entry.data[CONF_API_KEY]
    coordinator = PstrykDataUpdateCoordinator(hass, api_key)
    await coordinator.async_config_entry_first_refresh()
    sensors = [
        PstrykPriceSensor(coordinator, "price_today"),
        PstrykPriceSensor(coordinator, "price_tomorrow"),
        PstrykCarbonFootprintSensor(coordinator),
        PstrykEnergyCostSensor(coordinator),
        PstrykEnergyUsageSensor(coordinator),
        # 1. Prosumer pricing sensors
        PstrykProsumerPriceSensor(coordinator, "prosumer_price_today"),
        PstrykProsumerPriceSensor(coordinator, "prosumer_price_tomorrow"),
        # 2. Hourly price sensors for today (example: 24h)
        *[PstrykHourlyPriceSensor(coordinator, hour) for hour in range(24)],
        # 3. Total value sensors
        PstrykTotalSensor(coordinator, "fae_total_cost", "Pstryk Total Energy Cost", "PLN", "mdi:cash-multiple"),
        PstrykTotalSensor(coordinator, "carbon_footprint_total", "Pstryk Total Carbon Footprint", "gCO2eq", "mdi:cloud"),
        PstrykTotalSensor(coordinator, "fae_total_usage", "Pstryk Total Energy Usage", "kWh", "mdi:flash"),
        PstrykTotalSensor(coordinator, "total_energy_sold_value", "Pstryk Total Energy Sold", "PLN", "mdi:transmission-tower-export"),
        # 4. Flag sensors
        PstrykFlagSensor(coordinator, "is_expensive_now", "Pstryk Is Expensive Now", "mdi:alert"),
        PstrykFlagSensor(coordinator, "is_cheap_now", "Pstryk Is Cheap Now", "mdi:tag"),
        PstrykFlagSensor(coordinator, "is_live", "Pstryk Is Live", "mdi:clock"),
        # 5. Daily/weekly/monthly/yearly sensors (example for daily)
        PstrykAggregatedSensor(coordinator, "day"),
        # 6. VAT, excise, fixed/variable cost sensors
        PstrykCostComponentSensor(coordinator, "vat"),
        PstrykCostComponentSensor(coordinator, "excise"),
        PstrykCostComponentSensor(coordinator, "fix_dist_cost_net"),
        PstrykCostComponentSensor(coordinator, "var_dist_cost_net"),
        # 7. Info sensors
        PstrykInfoSensor(coordinator, "last_update", "Pstryk Last Update", None, "mdi:update"),
        PstrykInfoSensor(coordinator, "integration_version", "Pstryk Integration Version", None, "mdi:information-outline"),
        PstrykApiStatusSensor(coordinator),
    ]
    async_add_entities(sensors)
class PstrykProsumerPriceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, sensor_type):
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = f"Pstryk Prosumer Price {'Today' if 'today' in sensor_type else 'Tomorrow'}"
        self._attr_icon = "mdi:solar-power"
        self._attr_native_unit_of_measurement = "PLN/kWh"
        self._attr_unique_id = f"pstryk_{sensor_type}"


    @property
    def available(self):
        data = self.coordinator.data.get(self._sensor_type)
        return data is not None and data.get("frames") is not None

    @property
    def native_value(self):
        data = self.coordinator.data.get(self._sensor_type)
        if not data or not data.get("frames"):
            return None
        now = datetime.utcnow().hour
        frames = data["frames"]
        if now < len(frames):
            return frames[now].get("price_gross_avg")
        return None

    @property
    def extra_state_attributes(self):
        return {}

class PstrykHourlyPriceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, hour):
        super().__init__(coordinator)
        self._hour = hour
        self._attr_name = f"Pstryk Price Hour {hour:02d}"
        self._attr_icon = "mdi:clock-time-four-outline"
        self._attr_native_unit_of_measurement = "PLN/kWh"
        self._attr_unique_id = f"pstryk_price_hour_{hour:02d}"

    @property
    def available(self):
        data = self.coordinator.data.get("price_today")
        return bool(data and data.get("frames"))

    @property
    def native_value(self):
        data = self.coordinator.data.get("price_today")
        if not data or not data.get("frames"):
            return None
        frames = data["frames"]
        if self._hour < len(frames):
            return frames[self._hour].get("price_gross_avg")
        return None

    @property
    def extra_state_attributes(self):
        return {}

class PstrykTotalSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, key, name, unit, icon):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"pstryk_total_{key}"

    @property
    def available(self):
        # Try all data dicts
        for d in self.coordinator.data.values():
            if isinstance(d, dict) and self._key in d:
                return True
        return False

    @property
    def native_value(self):
        for d in self.coordinator.data.values():
            if isinstance(d, dict) and self._key in d:
                return d[self._key]
        return None

    @property
    def extra_state_attributes(self):
        return {}

class PstrykFlagSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, flag, name, icon):
        super().__init__(coordinator)
        self._flag = flag
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"pstryk_flag_{flag}"

    @property
    def available(self):
        data = self.coordinator.data.get("price_today")
        return bool(data and data.get("frames"))

    @property
    def native_value(self):
        data = self.coordinator.data.get("price_today")
        if not data or not data.get("frames"):
            return None
        now = datetime.utcnow().hour
        frame = data["frames"][now] if now < len(data["frames"]) else None
        if not frame:
            return None
        return frame.get(self._flag)

    @property
    def extra_state_attributes(self):
        return {}

class PstrykAggregatedSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, resolution):
        super().__init__(coordinator)
        self._resolution = resolution
        self._attr_name = f"Pstryk Price {resolution.capitalize()}"
        self._attr_icon = "mdi:calendar"
        self._attr_native_unit_of_measurement = "PLN/kWh"
        self._attr_unique_id = f"pstryk_price_{resolution}"


    @property
    def available(self):
        key = f"price_{self._resolution}"
        data = self.coordinator.data.get(key)
        return data is not None and (data.get("price_gross_avg") is not None or data.get("frames") is not None)

    @property
    def native_value(self):
        key = f"price_{self._resolution}"
        data = self.coordinator.data.get(key)
        if not data:
            return None
        # Prefer price_gross_avg if available, else None
        return data.get("price_gross_avg")

    @property
    def extra_state_attributes(self):
        return {}

class PstrykCostComponentSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, component):
        super().__init__(coordinator)
        self._component = component
        self._attr_name = f"Pstryk {component.replace('_', ' ').title()}"
        self._attr_icon = "mdi:cash"
        self._attr_unique_id = f"pstryk_cost_{component}"

    @property
    def available(self):
        data = self.coordinator.data.get("energy_cost")
        return bool(data and data.get("frames"))

    @property
    def native_value(self):
        data = self.coordinator.data.get("energy_cost")
        if not data or not data.get("frames"):
            return None
        now = datetime.utcnow().hour
        frame = data["frames"][now] if now < len(data["frames"]) else None
        if not frame:
            return None
        return frame.get(self._component)

    @property
    def extra_state_attributes(self):
        return {}

class PstrykInfoSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, key, name, unit, icon):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"pstryk_info_{key}"

    @property
    def available(self):
        return True

    @property
    def native_value(self):
        if self._key == "last_update":
            return datetime.utcnow().isoformat()
        if self._key == "integration_version":
            # Try to read version from version file, fallback to manifest.json
            import os
            import json
            try:
                version_path = os.path.join(os.path.dirname(__file__), "version")
                with open(version_path, "r") as f:
                    return f.read().strip()
            except Exception:
                try:
                    manifest_path = os.path.join(os.path.dirname(__file__), "manifest.json")
                    with open(manifest_path, "r") as f:
                        manifest = json.load(f)
                        return manifest.get("version")
                except Exception:
                    return None
        return None

    @property
    def extra_state_attributes(self):
        return {}

class PstrykApiStatusSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Pstryk API Status"
        self._attr_icon = "mdi:api"
        self._attr_unique_id = "pstryk_api_status"

    @property
    def available(self):
        return True

    @property
    def native_value(self):
        return "online"

    @property
    def extra_state_attributes(self):
        return {}

class PstrykPriceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, sensor_type):
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = SENSOR_TYPES[sensor_type]["name"]
        self._attr_icon = SENSOR_TYPES[sensor_type]["icon"]
        self._attr_native_unit_of_measurement = SENSOR_TYPES[sensor_type]["unit"]
        self._attr_unique_id = f"pstryk_{sensor_type}"

    @property
    def available(self):
        return self.coordinator.data.get(self._sensor_type) is not None

    @property
    def native_value(self):
        data = self.coordinator.data.get(self._sensor_type)
        if not data or not data.get("frames"):
            return None
        now = datetime.utcnow().hour
        frames = data["frames"]
        if now < len(frames):
            return frames[now].get("price_gross_avg")
        return None

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get(self._sensor_type)
        if not data:
            return {}
        return {
            "frames": data.get("frames", []),
            "price_net_avg": data.get("price_net_avg"),
            "price_gross_avg": data.get("price_gross_avg"),
        }

class PstrykCarbonFootprintSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = SENSOR_TYPES["carbon_footprint"]["name"]
        self._attr_icon = SENSOR_TYPES["carbon_footprint"]["icon"]
        self._attr_native_unit_of_measurement = SENSOR_TYPES["carbon_footprint"]["unit"]
        self._attr_unique_id = "pstryk_carbon_footprint"

    @property
    def available(self):
        return self.coordinator.data.get("carbon_footprint") is not None

    @property
    def native_value(self):
        data = self.coordinator.data.get("carbon_footprint")
        if not data:
            return None
        return data.get("carbon_footprint_total")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get("carbon_footprint")
        if not data:
            return {}
        return {
            "frames": data.get("frames", []),
            "resolution": data.get("resolution"),
        }

class PstrykEnergyCostSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = SENSOR_TYPES["energy_cost"]["name"]
        self._attr_icon = SENSOR_TYPES["energy_cost"]["icon"]
        self._attr_native_unit_of_measurement = SENSOR_TYPES["energy_cost"]["unit"]
        self._attr_unique_id = "pstryk_energy_cost"

    @property
    def available(self):
        return self.coordinator.data.get("energy_cost") is not None

    @property
    def native_value(self):
        data = self.coordinator.data.get("energy_cost")
        if not data:
            return None
        return data.get("fae_total_cost")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get("energy_cost")
        if not data:
            return {}
        return {
            "frames": data.get("frames", []),
            "total_energy_sold_value": data.get("total_energy_sold_value"),
            "total_energy_balance_value": data.get("total_energy_balance_value"),
        }

class PstrykEnergyUsageSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = SENSOR_TYPES["energy_usage"]["name"]
        self._attr_icon = SENSOR_TYPES["energy_usage"]["icon"]
        self._attr_native_unit_of_measurement = SENSOR_TYPES["energy_usage"]["unit"]
        self._attr_unique_id = "pstryk_energy_usage"

    @property
    def available(self):
        return self.coordinator.data.get("energy_usage") is not None

    @property
    def native_value(self):
        data = self.coordinator.data.get("energy_usage")
        if not data:
            return None
        return data.get("fae_total_usage")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data.get("energy_usage")
        if not data:
            return {}
        return {
            "frames": data.get("frames", []),
            "rae_total": data.get("rae_total"),
            "energy_balance": data.get("energy_balance"),
        }
