
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback
from .const import DOMAIN, CONF_METERS, CONF_TIMEZONE, CONF_ALERT_PRICE, CONF_ALERT_USAGE

class ICTPartnerDlaPstrykOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        super().__init__()
        # Nie zapisuj config_entry do self.config_entry (deprecated)
        # Używaj przekazanego config_entry bezpośrednio w metodach

    async def async_step_init(self, user_input=None):
        errors = {}
        # Użyj self.config_entry przekazanego do konstruktora przez argument
        config_entry = self.options_flow.config_entry if hasattr(self, 'options_flow') and hasattr(self.options_flow, 'config_entry') else None
        if config_entry is None:
            # Fallback: spróbuj z user_input (przy pierwszej konfiguracji)
            data = user_input or {}
        else:
            data = {**config_entry.data, **config_entry.options}
        from .const import CONF_DEBUG
        schema = vol.Schema({
            vol.Required(CONF_API_KEY, default=data.get(CONF_API_KEY, "")): str,
            vol.Optional(CONF_METERS, default=data.get(CONF_METERS, "main")): str,
            vol.Optional(CONF_TIMEZONE, default=data.get(CONF_TIMEZONE, "Europe/Warsaw")): str,
            vol.Optional(CONF_ALERT_PRICE, default=data.get(CONF_ALERT_PRICE, 1.0)): vol.Coerce(float),
            vol.Optional(CONF_ALERT_USAGE, default=data.get(CONF_ALERT_USAGE, 10.0)): vol.Coerce(float),
            vol.Optional(CONF_DEBUG, default=data.get(CONF_DEBUG, False)): bool,
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
        from .const import CONF_DEBUG
        schema = vol.Schema({
            vol.Required(CONF_API_KEY): str,
            vol.Optional(CONF_METERS, default="main"): str,
            vol.Optional(CONF_TIMEZONE, default="Europe/Warsaw"): str,
            vol.Optional(CONF_ALERT_PRICE, default=1.0): vol.Coerce(float),
            vol.Optional(CONF_ALERT_USAGE, default=10.0): vol.Coerce(float),
            vol.Optional(CONF_DEBUG, default=False): bool,
        })
        if user_input is not None:
            return self.async_create_entry(title="ictpartnerdlapstrykpl", data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
