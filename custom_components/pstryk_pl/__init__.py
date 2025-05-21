"""Pstryk.pl Integration Initialization."""

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up from configuration.yaml (not used here)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up integration from UI."""
    api_key = entry.data.get("api_key")
    _LOGGER.info(f"🔐 Loaded Pstryk API key: {api_key}")

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of config entry."""
    return await hass.config_entries.async_forward_entry_unload(entry, "sensor")