import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback
from .const import DOMAIN, CONF_API_KEY, CONF_METERS, CONF_TIMEZONE, CONF_ALERT_PRICE, CONF_ALERT_USAGE

class ICTPartnerDlaPstrykConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ictpartnerdlapstrykpl."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        errors = {}
        schema = vol.Schema({
            vol.Required(CONF_API_KEY): str,
            vol.Optional(CONF_METERS, default="main"): str,
            vol.Optional(CONF_TIMEZONE, default="Europe/Warsaw"): str,
            vol.Optional(CONF_ALERT_PRICE, default=1.0): vol.Coerce(float),
            vol.Optional(CONF_ALERT_USAGE, default=10.0): vol.Coerce(float),
        })
        if user_input is not None:
            # Validate API key, meters, etc. (optionally, do a test request here)
            return self.async_create_entry(title="ictpartnerdlapstrykpl", data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
