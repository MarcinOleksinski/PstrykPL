"""Konfiguracja integracji Pstryk.pl przez UI."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN
from .api import PstrykApi, CannotConnect, InvalidAuth
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)


class PstrykConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            api_key = user_input["api_key"]
            session = aiohttp.ClientSession()

            try:
                api = PstrykApi(api_key, session)
                await api.test_connection()

                return self.async_create_entry(
                    title="Pstryk.pl",
                    data={"api_key": api_key},
                )

            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception as e:
                _LOGGER.exception("Unknown error during config flow")
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