import logging
from datetime import datetime, timedelta, timezone
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api import PstrykApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PstrykEnergyCostCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api: PstrykApi, resolution: str, days: int):
        super().__init__(
            hass,
            _LOGGER,
            name="Pstryk Energy Cost Coordinator",
            update_interval=timedelta(minutes=15),
        )
        self.api = api
        self.resolution = resolution
        self.days = days

    async def _async_update_data(self):
        try:
            now = datetime.now(timezone.utc)
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=self.days)
            return await self.api.get_energy_cost(start, end, resolution=self.resolution)
        except Exception as err:
            raise UpdateFailed(f"Error fetching energy cost data: {err}")