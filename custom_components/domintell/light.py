"""
Support for Domintell lights.

For more details about this platform, please refer to the documentation at
https://github.com/shamanenas/has_domintell
"""
import logging

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.const import CONF_DEVICES

from .entity import DomintellEntity

_LOGGER = logging.getLogger(__name__)

DOM_BIR = 'BIR' # 8 - relay controller
DOM_TRP = 'DMR' # 5 - relay controller
DOM_DIM = 'DIM' # Dimmer controller
DOM_LED = 'LED' # LED controller


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Lights from a config entry."""
    hub = entry.runtime_data
    devices = entry.data.get(CONF_DEVICES, {}).get("light", [])
    async_add_entities(create_light(light, hub) for light in devices)


def create_light(light, hub):
    if light['type'] in [DOM_DIM]:
        return DomintellDimmerLight(light, hub)
    return DomintellLight(light, hub)


class DomintellLight(DomintellEntity, LightEntity):
    """Representation of a Domintell Light."""

    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, light, hub):
        """Initialize a Domintell light."""
        super().__init__(light, hub)
        self._state = False

    def _on_message(self, message):
        if message.serialNumber == self._module:
            m = self._domintell.get_module(self._module)
            if m:
                self._state = m.is_on(self._channel)
            self.schedule_update_ha_state()

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


class DomintellDimmerLight(DomintellLight):
    """Representation of a Domintell dimmer."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, light, hub):
        """Initialize a Domintell dimmer."""
        super().__init__(light, hub)
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

    def turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        m = self._domintell.get_module(self._module)
        if m:
            b = kwargs.get(ATTR_BRIGHTNESS, 255)
            b = int(b / 255 * 100)
            m.set_value(self._channel, b)
