"""
Support for Domintell Bimnary Sensor.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.domintell/
"""
import asyncio
import logging
import voluptuous as vol

from homeassistant.const import CONF_NAME, CONF_DEVICES
from homeassistant.components.binary_sensor import BinarySensorDevice
from homeassistant.components.binary_sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv

from .const import (DOMAIN)


# REQUIREMENTS = ['python-domintell==0.1.0']
# DEPENDENCIES = ['domintell']
# DOMAIN = 'domintell'

_LOGGER = logging.getLogger(__name__)

_LOGGER.debug('entered Sensor $$$$$$$$$$$$$$')


DOM_IS8 = 'IS8' # 8 inputs DI sensor
DOM_IS4 = 'IS4' # 4 inputs DI sensor
DOM_BU4 = 'BU4' # 4 inputs button block
DOM_DET = 'DET' # movement detector (1 DI)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [
        {
            vol.Optional('type', default=DOM_IS8): cv.string,
            vol.Required('module'): cv.string,
            vol.Required('channel'): cv.positive_int,
            vol.Required(CONF_NAME): cv.string,
            vol.Optional('location'): cv.string,
            vol.Optional('device_class'): cv.string,

        }
    ])
})

async def async_setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up switch."""
    domintell = hass.data[DOMAIN]
    add_devices(create_sensor(sensor, domintell) for sensor in config[CONF_DEVICES])


def create_sensor(sensor, domintell):
        module_type = sensor['type']
        return DomintellBinarySensor(sensor, domintell)

class DomintellBinarySensor(BinarySensorDevice):
    """Representation of a Domintell Binary sensor."""

    def __init__(self, sensor, domintell):
        """Initialize a Domintell sensoe/buttom."""
        self._sensor = sensor
        self._domintell = domintell
        self._name = sensor[CONF_NAME]
        self._module = sensor['module']
        self._channel = sensor['channel'] - 1 # we use 0 based index internally
        self._type = sensor['type']
        self._state = False

        dev = domintell.add_module(self._type, self._module)

    @asyncio.coroutine
    def async_added_to_hass(self):
        """Add listener for Domintell messages on bus."""
        
        def _init_domintell():
            """Initialize Domintell on startup."""
            self._domintell.subscribe(self._on_message)
            self.get_status()

        yield from self.hass.async_add_job(_init_domintell)

    def _on_message(self, message):
        import domintell
        if message.serialNumber == self._module:
            m = self._domintell.get_module(self._module)
            if m:
                self._state = m.is_on(self._channel)
            print(message.to_json())
            self.schedule_update_ha_state()

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name
    
    @property
    def should_poll(self):
        """Disable polling."""
        return False

    @property
    def is_on(self):
        """Return true if the light is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        m = self._domintell.get_module(self._module)
        if m:
            m.turn_on(self._channel)

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        m = self._domintell.get_module(self._module)
        if m:
            m.turn_off(self._channel)

    def get_status(self):
        """Retrieve current status."""
        m = self._domintell.get_module(self._module)
        if m:
            m.get_status()
