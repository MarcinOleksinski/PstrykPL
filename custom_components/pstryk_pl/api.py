async def test_connection(self) -> bool:
    """Send test request to verify API key."""
    url = f"{BASE_URL}/integrations/pricing/"
    headers = {"Authorization": self.api_key}

    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    window_start = now.replace(minute=0, second=0, microsecond=0)
    window_end = window_start + timedelta(hours=1)

    params = {
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "resolution": "hour"
    }

    try:
        async with async_timeout.timeout(10):
            response = await self.session.get(url, headers=headers, params=params)
            if response.status == 200:
                return True
            elif response.status in (401, 403):
                raise InvalidAuth
            elif response.status == 400:
                text = await response.text()
                raise CannotConnect(f"400 Bad Request: {text}")
            else:
                raise CannotConnect(f"Unexpected status: {response.status}")
    except asyncio.TimeoutError:
        raise CannotConnect("Timeout")
    except aiohttp.ClientError as e:
        raise CannotConnect(str(e))