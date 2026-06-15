"""
Support for Domintell binary sensors.

For more details about this platform, please refer to the documentation at
https://github.com/shamanenas/has_domintell
"""
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import CONF_DEVICES

from .entity import DomintellEntity

_LOGGER = logging.getLogger(__name__)

DOM_IS8 = 'IS8' # 8 inputs DI sensor
DOM_IS4 = 'IS4' # 4 inputs DI sensor
DOM_BU4 = 'BU4' # 4 inputs button block
DOM_DET = 'DET' # movement detector (1 DI)

DOM_VAR = 'VAR' # Binary variable (only binary implemented)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up binary sensors from a config entry."""
    hub = entry.runtime_data
    devices = entry.data.get(CONF_DEVICES, {}).get("binary_sensor", [])
    async_add_entities(DomintellBinarySensor(sensor, hub) for sensor in devices)


class DomintellBinarySensor(DomintellEntity, BinarySensorEntity):
    """Representation of a Domintell binary sensor."""

    def __init__(self, sensor, hub):
        """Initialize a Domintell sensor/button."""
        super().__init__(sensor, hub)
        self._state = False

    def _on_message(self, message):
        if message.serialNumber == self._module:
            m = self._domintell.get_module(self._module)
            if m:
                self._state = m.is_on(self._channel)
            self.schedule_update_ha_state()

    @property
    def is_on(self):
        """Return true if the sensor is on."""
        return self._state
