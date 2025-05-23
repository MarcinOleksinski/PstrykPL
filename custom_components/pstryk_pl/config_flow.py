import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import logging
from .const import DOMAIN
from .api import PstrykApi, CannotConnect, InvalidAuth
import aiohttp

_LOGGER = logging.getLogger(__name__)

RESOLUTIONS = ["hour", "day", "month"]

class PstrykConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        schema = vol.Schema({
            vol.Required("api_key"): str,
            vol.Optional("resolution", default="hour"): vol.In(RESOLUTIONS),
            vol.Optional("days", default=2): vol.All(vol.Coerce(int), vol.Range(min=1, max=31))
        })

        if user_input is not None:
            api_key = user_input["api_key"]
            session = aiohttp.ClientSession()
            try:
                api = PstrykApi(api_key, session)
                await api.test_connection()
                return self.async_create_entry(
                    title="Pstryk.pl",
                    data=user_input
                )
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unknown error")
                errors["base"] = "unknown"
            finally:
                await session.close()

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors
        )