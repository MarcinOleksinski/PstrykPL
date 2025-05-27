
# --- Coordinator for API data ---
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import pytz

class PstrykDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api_key):
        super().__init__(
            hass,
            _LOGGER,
            name="Pstryk Data",
            update_interval=SCAN_INTERVAL,
        )
        self.api_key = api_key
        # Ustal strefę czasową z configu (jak w fetch_prices)
        timezone = "Europe/Warsaw"
        debug = False
        try:
            for entry in hass.config_entries.async_entries(DOMAIN):
                if entry.data.get("for_tz"):
                    timezone = entry.data["for_tz"]
                if entry.options.get("for_tz"):
                    timezone = entry.options["for_tz"]
                # Nowa opcja debug
                if entry.data.get("debug"):
                    debug = entry.data["debug"]
                if entry.options.get("debug"):
                    debug = entry.options["debug"]
        except Exception:
            timezone = "Europe/Warsaw"
        self.timezone = timezone
        self.debug = debug


    async def _async_update_data(self):
        today = datetime.utcnow().date()
        tomorrow = today + timedelta(days=1)
        headers = {"Authorization": self.api_key}
        session = async_get_clientsession(self.hass)

        import asyncio
        async def fetch_json(url):
            if self.debug:
                _LOGGER.warning(f"[PSTRYK DEBUG] Fetching URL: {url}")
            try:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 404:
                        if self.debug:
                            _LOGGER.info(f"Pstryk API 404 Not Found for {url} (endpoint or data not available)")
                        return {}
                    resp.raise_for_status()
                    data = await resp.json()
                    if self.debug:
                        _LOGGER.warning(f"[PSTRYK DEBUG] API response for {url}: {data}")
                    return data
            except asyncio.TimeoutError:
                _LOGGER.error(f"[PSTRYK ERROR] Timeout while fetching {url}")
                return {}
            except aiohttp.ClientResponseError as e:
                if e.status == 404:
                    if self.debug:
                        _LOGGER.info(f"Pstryk API 404 Not Found for {url} (endpoint or data not available)")
                    return {}
                if self.debug:
                    _LOGGER.warning(f"Error fetching {url}: {e}")
                return {}
            except Exception as e:
                _LOGGER.error(f"[PSTRYK ERROR] Exception while fetching {url}: {e}")
                return {}

        async def fetch_prosumer_prices(day):
            # Buduj URL zawsze z ukośnikiem przed znakiem zapytania
            base = "https://pstryk.pl/api/integrations/prosumer-pricing/"
            params = f"resolution=hour&window_start={day}T00:00:00Z&window_end={day}T23:59:59Z"
            url = f"{base}?{params}"
            return await fetch_json(url)

        async def fetch_prices(day, resolution="hour"):
            # Endpoint: https://api.pstryk.pl/integrations/pricing/?resolution=hour&window_start=UTC_START&window_end=UTC_END
            # Dla strefy Europe/Warsaw musimy przesunąć okno o -2h względem północy lokalnej
            import pytz
            import tzlocal
            base = "https://api.pstryk.pl/integrations/pricing/"
            # Ustal strefę czasową systemu lub z configu
            try:
                for entry in self.hass.config_entries.async_entries(DOMAIN):
                    if entry.data.get("for_tz"):
                        timezone = entry.data["for_tz"]
                        break
                    if entry.options.get("for_tz"):
                        timezone = entry.options["for_tz"]
                        break
                else:
                    timezone = "Europe/Warsaw"
            except Exception:
                timezone = "Europe/Warsaw"
            # Przesuń okno na UTC
            local = pytz.timezone(timezone)
            local_start = local.localize(datetime.combine(day, datetime.min.time()))
            local_end = local_start + timedelta(hours=23, minutes=59, seconds=59)
            utc_start = local_start.astimezone(pytz.utc)
            utc_end = local_end.astimezone(pytz.utc)
            window_start = utc_start.strftime("%Y-%m-%dT%H:%M:%SZ")
            window_end = utc_end.strftime("%Y-%m-%dT%H:%M:%SZ")
            params = f"resolution={resolution}&window_start={window_start}&window_end={window_end}"
            url = f"{base}?{params}"
            return await fetch_json(url)

        # carbon_footprint endpoint wyłączony 
        async def fetch_carbon_footprint(resolution="hour"):
            return {}

        # Helper to get window_end for a given resolution
        def get_window_end(start, resolution):
            if resolution == "hour" or resolution == "day":
                return start
            elif resolution == "week":
                # End of week (Sunday)
                return (start + timedelta(days=(6 - start.weekday())))
            elif resolution == "month":
                # End of month
                if start.month == 12:
                    return start.replace(year=start.year+1, month=1, day=1) - timedelta(days=1)
                else:
                    return start.replace(month=start.month+1, day=1) - timedelta(days=1)
            elif resolution == "year":
                return start.replace(month=12, day=31)
            return start

        async def fetch_energy_cost(resolution="hour", start=None):
            # Only hour, day, month supported for energy-cost
            if resolution not in ("hour", "day", "month"):
                return {}
            if start is None:
                start = today
            window_start = f"{start}T00:00:00Z"
            window_end = get_window_end(start, resolution)
            window_end = f"{window_end}T23:59:59Z"
            url = f"https://api.pstryk.pl/integrations/meter-data/energy-cost/?resolution={resolution}&window_start={window_start}&window_end={window_end}"
            return await fetch_json(url)

        async def fetch_energy_usage(resolution="hour", start=None):
            # All resolutions supported for energy-usage
            if start is None:
                start = today
            window_start = f"{start}T00:00:00Z"
            window_end = get_window_end(start, resolution)
            window_end = f"{window_end}T23:59:59Z"
            url = f"https://api.pstryk.pl/integrations/meter-data/energy-usage/?resolution={resolution}&window_start={window_start}&window_end={window_end}"
            return await fetch_json(url)

        data = {}
        # Standard pricing
        # Ustal okno czasowe dla agregacji (window_start, window_end)
        # Dla day/month/year window_start to pierwszy dzień okresu
        # UWAGA:
        # Po godzinie 14:00 API Pstryk publikuje ceny tylko na kolejny dzień.
        # Oznacza to, że po 14:00 price_today może być pusty (API zwraca pusty słownik),
        # a pojawiają się dane dla price_tomorrow. To nie jest błąd integracji.
        data["price_today"] = await fetch_prices(today, resolution="hour")
        if self.debug:
            _LOGGER.warning(f"[PSTRYK DEBUG] price_today result: {data['price_today']}")
        # Pobieraj price_tomorrow zawsze, niezależnie od godziny
        data["price_tomorrow"] = await fetch_prices(tomorrow, resolution="hour")
        # Prosumer pricing
        # Pobieraj prosumer_price_today i prosumer_price_tomorrow zawsze, niezależnie od godziny
        data["prosumer_price_today"] = await fetch_prosumer_prices(today)
        data["prosumer_price_tomorrow"] = await fetch_prosumer_prices(tomorrow)
        # Aggregaty pricing
        # Dzień
        data["price_day"] = await fetch_prices(today, resolution="day")
        # Miesiąc
        first_of_month = today.replace(day=1)
        data["price_month"] = await fetch_prices(first_of_month, resolution="month")
        # Rok
        first_of_year = today.replace(month=1, day=1)
        data["price_year"] = await fetch_prices(first_of_year, resolution="year")
        # carbon_footprint endpoint wyłączony
        data["carbon_footprint"] = {}
        data["carbon_footprint_day"] = {}
        data["carbon_footprint_month"] = {}
        data["carbon_footprint_year"] = {}
        data["energy_cost"] = await fetch_energy_cost(resolution="hour", start=today)
        data["energy_cost_day"] = await fetch_energy_cost(resolution="day", start=today)
        # Nie ma agregacji tygodniowej dla energy-cost
        data["energy_cost_week"] = {}
        data["energy_cost_month"] = await fetch_energy_cost(resolution="month", start=today)
        # No year aggregation for energy-cost
        data["energy_usage"] = await fetch_energy_usage(resolution="hour", start=today)
        data["energy_usage_day"] = await fetch_energy_usage(resolution="day", start=today)
        data["energy_usage_week"] = await fetch_energy_usage(resolution="week", start=today)
        data["energy_usage_month"] = await fetch_energy_usage(resolution="month", start=today)
        data["energy_usage_year"] = await fetch_energy_usage(resolution="year", start=today)
        return data

# --- Helper function: find_frame_for_local_hour ---
def find_frame_for_local_hour(frames, hour, timezone):
    """
    Szuka frame, którego 'start' odpowiada danej godzinie lokalnej (w strefie timezone).
    Zwraca frame lub None.
    """
    if not frames:
        return None
    import pytz
    from datetime import datetime, date, time
    import re
    local = pytz.timezone(timezone)
    today = datetime.now(local).date()
    local_dt = local.localize(datetime.combine(today, time(hour, 0)))
    utc_dt = local_dt.astimezone(pytz.utc)
    # Akceptuj zarówno 'Z' jak i '+00:00' w polu start
    def normalize_utc_string(dt):
        # Zamień np. '2025-05-27T10:00:00+00:00' na '2025-05-27T10:00:00Z'
        if dt.endswith('+00:00'):
            return dt[:-6] + 'Z'
        return dt
    utc_str = utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    for frame in frames:
        start = frame.get("start")
        if not start:
            continue
        if normalize_utc_string(start) == utc_str:
            return frame
    # Jeśli nie ma dokładnego, znajdź najbliższy czasowo (parsuj oba formaty)
    min_diff = None
    best_frame = None
    for frame in frames:
        try:
            start = frame.get("start")
            # Obsłuż oba formaty: 'Z' i '+00:00'
            if start.endswith('Z'):
                frame_start = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
                frame_start = frame_start.replace(tzinfo=pytz.utc)
            elif start.endswith('+00:00'):
                frame_start = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S+00:00")
                frame_start = frame_start.replace(tzinfo=pytz.utc)
            else:
                continue
            diff = abs((frame_start - utc_dt).total_seconds())
            if min_diff is None or diff < min_diff:
                min_diff = diff
                best_frame = frame
        except Exception:
            continue
    return best_frame
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
        PstrykEnergyCostSensor(coordinator),
        PstrykEnergyUsageSensor(coordinator),
        # Prosumer pricing sensors
        PstrykProsumerPriceSensor(coordinator, "prosumer_price_today"),
        PstrykProsumerPriceSensor(coordinator, "prosumer_price_tomorrow"),
        # Hourly price sensors for today (24h)
        *[PstrykHourlyPriceSensor(coordinator, hour) for hour in range(24)],
        # Total value sensors
        PstrykTotalSensor(coordinator, "fae_total_cost", "Pstryk Total Energy Cost", "PLN", "mdi:cash-multiple"),
        PstrykTotalSensor(coordinator, "fae_total_usage", "Pstryk Total Energy Usage", "kWh", "mdi:flash"),
        PstrykTotalSensor(coordinator, "total_energy_sold_value", "Pstryk Total Energy Sold", "PLN", "mdi:transmission-tower-export"),
        # Flag sensors
        PstrykFlagSensor(coordinator, "is_expensive_now", "Pstryk Is Expensive Now", "mdi:alert"),
        PstrykFlagSensor(coordinator, "is_cheap_now", "Pstryk Is Cheap Now", "mdi:tag"),
        PstrykFlagSensor(coordinator, "is_live", "Pstryk Is Live", "mdi:clock"),
        # Daily aggregated sensor (example)
        PstrykAggregatedSensor(coordinator, "day"),
        # VAT, excise, fixed/variable cost sensors
        PstrykCostComponentSensor(coordinator, "vat"),
        PstrykCostComponentSensor(coordinator, "excise"),
        PstrykCostComponentSensor(coordinator, "fix_dist_cost_net"),
        PstrykCostComponentSensor(coordinator, "var_dist_cost_net"),
        # Info sensors
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
        # Encja zawsze dostępna, nawet jeśli nie ma jeszcze danych (frames)
        return True

    @property
    def native_value(self):
        data = self.coordinator.data.get(self._sensor_type)
        if not data or not data.get("frames"):
            return None
        frames = data["frames"]
        # Użyj mapowania po godzinie lokalnej
        hour = datetime.now(pytz.timezone(self.coordinator.timezone)).hour
        frame = find_frame_for_local_hour(frames, hour, self.coordinator.timezone)
        if frame:
            return frame.get("price_gross_avg")
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
        frame = find_frame_for_local_hour(frames, self._hour, self.coordinator.timezone)
        if frame:
            return frame.get("price_gross_avg")
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
        frames = data["frames"]
        # Użyj bieżącej godziny lokalnej
        hour = datetime.now(pytz.timezone(self.coordinator.timezone)).hour
        frame = find_frame_for_local_hour(frames, hour, self.coordinator.timezone)
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
        # Prefer price_gross_avg if available, else try to average frames
        if data.get("price_gross_avg") is not None:
            return data.get("price_gross_avg")
        frames = data.get("frames")
        if frames:
            prices = [f.get("price_gross_avg") for f in frames if f.get("price_gross_avg") is not None]
            if prices:
                return sum(prices) / len(prices)
        return None

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
            import os
            import json
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
        # Encja zawsze dostępna, nawet jeśli nie ma jeszcze danych (frames)
        return True

    @property
    def native_value(self):
        data = self.coordinator.data.get(self._sensor_type)
        if not data or not data.get("frames"):
            return None
        frames = data["frames"]
        # Użyj bieżącej godziny lokalnej
        hour = datetime.now(pytz.timezone(self.coordinator.timezone)).hour
        frame = find_frame_for_local_hour(frames, hour, self.coordinator.timezone)
        if frame:
            return frame.get("price_gross_avg")
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

# Usunięto klasę PstrykCarbonFootprintSensor - endpoint nieobsługiwany przez API

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
