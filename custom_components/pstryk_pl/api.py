"""API klient do Pstryk.pl."""
import asyncio
import aiohttp
import async_timeout
from datetime import datetime, timedelta, timezone

BASE_URL = "https://api.pstryk.pl"


class PstrykApi:
    def __init__(self, api_key: str, session: aiohttp.ClientSession):
        self.api_key = api_key
        self.session = session

    async def test_connection(self) -> bool:
        """Testuje poprawność API key."""
        url = f"{BASE_URL}/integrations/pricing/"
        headers = {"Authorization": self.api_key}

        now = datetime.now(timezone.utc)
        params = {
            "window_start": (now - timedelta(hours=1)).isoformat(),
            "window_end": now.isoformat(),
            "resolution": "hour"
        }

        try:
            async with async_timeout.timeout(10):
                response = await self.session.get(url, headers=headers, params=params)
                if response.status == 200:
                    return True
                elif response.status in (401, 403):
                    raise InvalidAuth
                else:
                    raise CannotConnect(f"Unexpected response: {response.status}")
        except asyncio.TimeoutError:
            raise CannotConnect("Timeout")
        except aiohttp.ClientError as e:
            raise CannotConnect(str(e))

    async def get_pricing(self, resolution="hour", days=1) -> dict:
        """Pobiera dane o cenach energii."""
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days)

        url = f"{BASE_URL}/integrations/pricing/"
        headers = {"Authorization": self.api_key}
        params = {
            "window_start": start.isoformat(),
            "window_end": now.isoformat(),
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
    """Błąd połączenia z API."""


class InvalidAuth(Exception):
    """Błąd uwierzytelnienia."""