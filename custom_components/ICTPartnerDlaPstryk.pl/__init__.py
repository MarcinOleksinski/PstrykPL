"""
ICTPartnerDlaPstryk.pl Home Assistant Integration
"""

import logging

from homeassistant.const import Platform

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
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
