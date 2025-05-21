"""Pstryk.pl Integration Initialization."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.discovery import async_load_platform

DOMAIN = "pstryk_pl"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Basic setup - for YAML based setup (if needed)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup entry from UI (if config_flow will be used later)."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload integration."""
    return await hass.config_entries.async_forward_entry_unload(entry, "sensor")