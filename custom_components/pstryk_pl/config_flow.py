"""Config flow for Pstryk.pl integration."""

from homeassistant import config_entries
import voluptuous as vol
import logging
import aiohttp

from .const import DOMAIN
from .api import PstrykApi, CannotConnect, InvalidAuth

_LOGGER = logging.getLogger(__name__)


class PstrykConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Pstryk.pl."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            api_key = user_input.get("api_key")
            session = aiohttp.ClientSession()

            try:
                client = PstrykApi(api_key, session)
                await client.test_connection()

                return self.async_create_entry(
                    title="Pstryk.pl",
                    data={"api_key": api_key},
                )
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception as e:
                _LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "unknown"
            finally:
                await session.close()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("api_key"): str
            }),
            errors=errors,
        )