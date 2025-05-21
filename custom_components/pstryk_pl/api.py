"""API client for Pstryk.pl."""
import asyncio
import aiohttp
import async_timeout

BASE_URL = "https://api.pstryk.pl"


class PstrykApi:
    def __init__(self, api_key: str, session: aiohttp.ClientSession):
        self.api_key = api_key
        self.session = session

    async def test_connection(self) -> bool:
        """Send test request to verify API key."""
        url = f"{BASE_URL}/integrations/pricing/"
        headers = {"Authorization": f"{self.api_key}"}

        params = {
            "window_start": "2025-05-20T10:00:00Z",
            "window_end": "2025-05-20T11:00:00Z",
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
                    raise CannotConnect
        except asyncio.TimeoutError:
            raise CannotConnect
        except aiohttp.ClientError:
            raise CannotConnect


class CannotConnect(Exception):
    """Error to indicate we cannot connect to Pstryk.pl."""


class InvalidAuth(Exception):
    """Error to indicate API key is invalid."""