import asyncio
import aiohttp
import async_timeout
from datetime import datetime, timedelta, timezone

BASE_URL = "https://api.pstryk.pl"


class PstrykApi:
    def __init__(self, api_key: str, session: aiohttp.ClientSession):
        self.api_key = api_key
        self.session = session

    async def get_pricing(self, resolution: str = "hour", days: int = 1) -> dict:
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(days=days)
        window_end = now

        url = f"{BASE_URL}/integrations/pricing/"
        headers = {"Authorization": self.api_key}
        params = {
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "resolution": resolution
        }

        try:
            async with async_timeout.timeout(15):
                response = await self.session.get(url, headers=headers, params=params)
                if response.status == 200:
                    return await response.json()
                raise CannotConnect(f"Status: {response.status}")
        except asyncio.TimeoutError:
            raise CannotConnect("Timeout")
        except aiohttp.ClientError as e:
            raise CannotConnect(str(e))


class CannotConnect(Exception):
    """API connection error."""
    pass