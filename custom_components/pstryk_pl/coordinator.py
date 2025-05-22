from datetime import timedelta
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api import PstrykApi
from .const import DOMAIN, DEFAULT_RESOLUTION, DEFAULT_DAYS

_LOGGER = logging.getLogger(__name__)


class PstrykPricingCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api: PstrykApi, resolution: str = DEFAULT_RESOLUTION, days: int = DEFAULT_DAYS):
        super().__init__(
            hass,
            _LOGGER,
            name="PstrykPricingCoordinator",
            update_interval=timedelta(minutes=5),
        )
        self.api = api
        self.resolution = resolution
        self.days = days

    async def _async_update_data(self):
        try:
            return await self.api.get_pricing(self.resolution, self.days)
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}")