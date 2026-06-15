"""
Support for Domintell trip switch.

For more details about this platform, please refer to the documentation at
https://github.com/shamanenas/has_domintell
"""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_DEVICES

from .entity import DomintellEntity

_LOGGER = logging.getLogger(__name__)

DOM_TRP = 'TRP' # 5 - relay controller


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up switches from a config entry."""
    hub = entry.runtime_data
    devices = entry.data.get(CONF_DEVICES, {}).get("switch", [])
    async_add_entities(DomintellSwitch(switch, hub) for switch in devices)


class DomintellSwitch(DomintellEntity, SwitchEntity):
    """Representation of a Domintell Switch."""

    def __init__(self, switch, hub):
        """Initialize a Domintell switch."""
        super().__init__(switch, hub)
        self._state = False

    def _on_message(self, message):
        if message.serialNumber == self._module:
            m = self._domintell.get_module(self._module)
            if m:
                self._state = m.is_on(self._channel)
            self.schedule_update_ha_state()

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Instruct the switch to turn on."""
        m = self._domintell.get_module(self._module)
        if m:
            m.turn_on(self._channel)

    def turn_off(self, **kwargs):
        """Instruct the switch to turn off."""
        m = self._domintell.get_module(self._module)
        if m:
            m.turn_off(self._channel)
