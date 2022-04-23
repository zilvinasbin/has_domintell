"""
Support for Domintell lights.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.domintell/
"""
import asyncio
import logging
import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.components.light import ATTR_BRIGHTNESS, LightEntity, PLATFORM_SCHEMA, SUPPORT_BRIGHTNESS
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_DEVICES, CONF_NAME
import homeassistant.helpers.config_validation as cv

from .const import (DOMAIN)


# REQUIREMENTS = ['python-domintell==0.1.0']
# DEPENDENCIES = ['domintell']
# DOMAIN = 'domintell'

_LOGGER = logging.getLogger(__name__)


DOM_BIR = 'BIR' # 8 - relay controller
DOM_TRP = 'DMR' # 5 - relay controller
DOM_DIM = 'DIM' # Dimmer controller
DOM_LED = 'LED' # LED controller

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [
        {
            vol.Optional('type', default=DOM_BIR): cv.string,
            vol.Required('module'): cv.string,
            vol.Required('channel'): cv.positive_int,
            vol.Required(CONF_NAME): cv.string,
            vol.Optional('location'): cv.string
        }
    ])
})

async def async_setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up Lights."""
    domintell = hass.data[DOMAIN]
    # _LOGGER.warning('Creating lights =========================== ')
    add_devices(create_light(light, domintell) for light in config[CONF_DEVICES])


def create_light(light, domintell):
        module_type = light['type']
        # _LOGGER.warning('creating light %s', light[CONF_NAME])
        if  module_type in [DOM_DIM]:
            return DomintellDimmerLight(light, domintell)
        return DomintellLight(light, domintell)

class DomintellLight(LightEntity):
    """Representation of a Domintell Light."""

    def __init__(self, light, domintell):
        """Initialize a Domintell light."""
        self._light = light
        self._domintell = domintell
        self._name = light[CONF_NAME]
        self._module = light['module']
        self._channel = light['channel'] - 1 # we use 0 based index internally
        self._type = light['type']
        self._state = False

        self._brightness = None
        dev = domintell.add_module(self._type, self._module)
        self._is_dimmer = dev.is_dimmer()

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

class DomintellDimmerLight(DomintellLight):

    def __init__(self, light, domintell):
        """ Initialize domintell dimmer"""
        DomintellLight.__init__(self, light, domintell)
        self._brightness = 0

    def _on_message(self, message):
        if message.serialNumber == self._module:
            m = self._domintell.get_module(self._module)
            if m:
                self._state = m.is_on(self._channel)
                self._brightness = m.get_value(self._channel)
            self.schedule_update_ha_state()

    @property
    def brightness(self):
        return int(self._brightness * 255 / 100)

    @property
    def supported_features(self):
        return SUPPORT_BRIGHTNESS

    def turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        m = self._domintell.get_module(self._module)
        if m:
            b = kwargs.get(ATTR_BRIGHTNESS, 255)
            b = int(b / 255 * 100)
            m.set_value(self._channel, b)
