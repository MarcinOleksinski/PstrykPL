"""Koordynator danych Pstryk.pl."""
from datetime import timedelta
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api import PstrykApi
from .const import DOMAIN, DEFAULT_RESOLUTION, DEFAULT_DAYS

_LOGGER = logging.getLogger(__name__)


class PstrykPricingCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api: PstrykApi):
        super().__init__(
            hass,
            _LOGGER,
            name="Pstryk Pricing Coordinator",
            update_interval=timedelta(minutes=5),
        )
        self.api = api

    async def _async_update_data(self):
        try:
            return await self.api.get_pricing(
                resolution=DEFAULT_RESOLUTION,
                days=DEFAULT_DAYS
            )
        except Exception as err:
            raise UpdateFailed(f"Update failed: {err}")