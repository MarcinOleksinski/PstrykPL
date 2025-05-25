
# Poprawny handler dla options flow:


import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback
from .const import DOMAIN, CONF_METERS, CONF_TIMEZONE, CONF_ALERT_PRICE, CONF_ALERT_USAGE

class ICTPartnerDlaPstrykOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        data = {**self.config_entry.data, **self.config_entry.options}
        schema = vol.Schema({
            vol.Required(CONF_API_KEY, default=data.get(CONF_API_KEY, "")): str,
            vol.Optional(CONF_METERS, default=data.get(CONF_METERS, "main")): str,
            vol.Optional(CONF_TIMEZONE, default=data.get(CONF_TIMEZONE, "Europe/Warsaw")): str,
            vol.Optional(CONF_ALERT_PRICE, default=data.get(CONF_ALERT_PRICE, 1.0)): vol.Coerce(float),
            vol.Optional(CONF_ALERT_USAGE, default=data.get(CONF_ALERT_USAGE, 10.0)): vol.Coerce(float),
        })
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)


class ICTPartnerDlaPstrykConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ICTPartnerDlaPstrykOptionsFlow(config_entry)

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
