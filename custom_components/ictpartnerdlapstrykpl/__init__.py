"""
ictpartnerdlapstrykpl Home Assistant Integration
"""

import logging


from homeassistant.const import Platform
from homeassistant.config_entries import ConfigEntryNotReady
from .sensor import PstrykDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ictpartnerdlapstrykpl"
PLATFORMS = [Platform.SENSOR]

async def async_setup(hass, config):
    """Set up the integration via configuration.yaml (not used)."""
    return True

async def async_setup_entry(hass, entry):
    """Set up integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}
    # Spróbuj odświeżyć dane z API przed forwardowaniem platform
    try:
        coordinator = PstrykDataUpdateCoordinator(hass, entry.data.get("api_key"))
        await coordinator.async_setup_timezone()
        await coordinator.async_config_entry_first_refresh()
        hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator
    except Exception as exc:
        raise ConfigEntryNotReady from exc
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
