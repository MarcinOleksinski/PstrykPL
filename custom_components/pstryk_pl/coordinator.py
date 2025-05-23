from datetime import timedelta, datetime, timezone
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api import PstrykApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PstrykPricingCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api: PstrykApi):
        super().__init__(
            hass,
            _LOGGER,
            name="Pstryk Pricing Coordinator",
            update_interval=timedelta(minutes=10),
        )
        self.api = api

    async def _async_update_data(self):
        try:
            now = datetime.now(timezone.utc)
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=2)
            return await self.api.get_pricing(resolution="hour", window_start=start, window_end=end)
        except Exception as err:
            raise UpdateFailed(f"Error fetching pricing: {err}")