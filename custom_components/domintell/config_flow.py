"""Config flow for the Domintell integration."""
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_DEVICES, CONF_HOST, CONF_PASSWORD

from .const import CONF_PING_INTERVAL, DEFAULT_PING_INTERVAL, DOMAIN
from .hub import CannotConnect, DomintellHub

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_PING_INTERVAL, default=DEFAULT_PING_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=0)
        ),
    }
)


class DomintellConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the Domintell config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Manual setup: ask for connection details and validate them."""
        errors = {}
        if user_input is not None:
            hub = DomintellHub(
                self.hass,
                user_input[CONF_HOST],
                user_input[CONF_PASSWORD],
                ping_interval=0,
            )
            try:
                await hub.async_connect()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                await self.hass.async_add_executor_job(hub.stop)
                return self.async_create_entry(
                    title=f"Domintell ({user_input[CONF_HOST]})",
                    data={**user_input, CONF_DEVICES: {}},
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_import(self, import_data):
        """Import hub settings and device lists from configuration.yaml.

        No connection validation: the YAML config is known-working, and a
        transient failure here would strand the migration.
        """
        return self.async_create_entry(
            title=f"Domintell ({import_data[CONF_HOST]})",
            data=import_data,
        )
