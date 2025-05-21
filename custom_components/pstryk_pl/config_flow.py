"""Config flow for Pstryk.pl integration."""

from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol

from .const import DOMAIN


class PstrykConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pstryk.pl."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial user step."""
        if user_input is not None:
            return self.async_create_entry(
                title="Pstryk.pl",
                data={"api_key": user_input["api_key"]},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("api_key"): str
            }),
            errors={},
        )