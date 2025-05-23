# custom_components/pstryk_pl/__init__.py

import logging
from aiohttp import ClientSession
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .api import PstrykApi
from .coordinator import PstrykPricingCoordinator
from .cost_coordinator import PstrykEnergyCostCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Setting up Pstryk.pl integration")

    api_key = entry.data["api_key"]
    resolution = entry.data.get("resolution", "hour")
    days = entry.data.get("days", 2)

    session = ClientSession()
    api = PstrykApi(api_key, session)

    pricing_coordinator = PstrykPricingCoordinator(hass, api, resolution=resolution, days=days)
    cost_coordinator = PstrykEnergyCostCoordinator(hass, api, resolution=resolution, days=days)

    try:
        await pricing_coordinator.async_config_entry_first_refresh()
        await cost_coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.error("API initialization failed: %s", err)
        raise ConfigEntryNotReady(f"API unavailable: {err}")

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "coordinator": pricing_coordinator,
        "cost_coordinator": cost_coordinator
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok