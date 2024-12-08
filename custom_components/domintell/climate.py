"""
Support for Domintell Climate control.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.domintell/
"""
import asyncio
import logging
import voluptuous as vol

from homeassistant.const import CONF_NAME, CONF_DEVICES import homeassistant.helpers.config_validation as cv
from homeassistant.components.climate import ( PLATFORM_SCHEMA, ClimateEntity )
from homeassistant.components.climate.const import (PRESET_AWAY, PRESET_NONE, PRESET_COMFORT, PRESET_HOME, ClimateEntityFeature, HVACMode)
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE

from .const import (DOMAIN)


SUPPORT_FLAGS = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE

DOM_ABSENCE = 1
DOM_AUTO = 2
DOM_COMFORT = 5
DOM_FROST = 6
DOM_MANUAL = 99

OP_ABSENCE = 'Absence'
OP_AUTO = 'Auto'
OP_COMFORT = 'Comfort'
OP_FROST = 'Frost'
OP_MANUAL = 'Manual'

# REQUIREMENTS = ['python-domintell==0.1.0']
# DEPENDENCIES = ['domintell']
# DOMAIN = 'domintell'

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(10)

DOM_TE1 = 'TE1' # 5 - relay controller
DOM_TE2 = 'TE2'


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [
        {
            vol.Optional('type', default=DOM_TE1): cv.string,
            vol.Required('module'): cv.string,
            vol.Optional('channel', default=1): cv.positive_int,
            vol.Required(CONF_NAME): cv.string,
            vol.Optional('force_update'): cv.string,
            vol.Optional('location'): cv.string,
        }
    ])
})

async def async_setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up Climate device."""
    domintell = hass.data[DOMAIN]
    add_devices(create_device(device, domintell) for device in config[CONF_DEVICES])

def create_device(device, domintell):
        module_type = device['type']
        return DomintellClimateDevice(device, domintell)

def operation_mode_str(mode):
    if mode == DOM_ABSENCE:
        return OP_ABSENCE
    elif mode == DOM_AUTO:
        return OP_AUTO
    elif mode == DOM_COMFORT:
        return OP_COMFORT
    elif mode == DOM_FROST:
        return OP_FROST
    elif mode == DOM_MANUAL:
        return OP_MANUAL
    return OP_AUTO


class DomintellClimateDevice(ClimateEntity):
    """Representation of a Domintell ClimateDevice."""

    def __init__(self, device, domintell):
        """Initialize the climate device."""
        self._device = device
        self._domintell = domintell
        self._name = device[CONF_NAME]
        self._module = device['module']
        self._channel = device['channel'] - 1 # we use 0 based index internally
        self._type = device['type']
        self._support_flags = SUPPORT_FLAGS

        self._unit_of_measurement = UnitOfTemperature.CELSIUS
        self._mode = DOM_AUTO

        self._current_temperature = None
        self._set_point_temperature = None
        self._range_temperature = None
        self._on = True

        dev = domintell.add_module(self._type, self._module)

    async def async_added_to_hass(self):
        """Add listener for Domintell messages on bus."""
        def _init_domintell():
            """Initialize Domintell on startup."""
            self._domintell.subscribe(self._on_message)
            self.get_status()

        await self.hass.async_add_job(_init_domintell)

    def _on_message(self, message):
        import domintell
        if message.serialNumber == self._module:
            m = self._domintell.get_module(self._module)
            if m:
                self._current_temperature = m.get_temperature()
                self._set_point_temperature = m.get_set_point()
                self._range = m.get_range()
                self._mode = m.get_mode()
            self.schedule_update_ha_state()

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._support_flags

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name
    
    @property
    def should_poll(self):
        """Disable polling."""
        return False

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._set_point_temperature

    @property
    def is_away_mode_on(self):
        """Return if away mode is on."""
        return self._mode == DOM_ABSENCE

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        return operation_mode_str(self._mode)

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return ['Auto', 'Comfort', 'Absence', 'Frost', 'Manual']

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self._set_point_temperature = kwargs.get(ATTR_TEMPERATURE)

            m = self._domintell.get_module(self._module)
            if m:
                m.set_temperature(self._set_point_temperature)

        self.schedule_update_ha_state()

    def set_hvac_mode(self, hvac_mode):
        m = self._domintell.get_module(self._module)
        if m:
            if hvac_mode == HVACMode.HEAT_COOL:
                m.set_automatic()
            elif operation_mode == HVACMode.OFF:
                m.set_frost()
        self.schedule_update_ha_state()

    def set_preset_mode(self, operation_mode):
        """Set new target operation mode."""
        m = self._domintell.get_module(self._module)
        if m:
            if operation_mode == PRESET_NONE:
                m.set_automatic()
            elif operation_mode == PRESET_COMFORT:
                m.set_comfort()
            elif operation_mode == PRESET_HOME:
                m.set_automatic()
            elif operation_mode == PRESET_AWAY:
                m.set_absence()
        self.schedule_update_ha_state()

    @property
    def preset_modes(sefl):
        return [PRESET_NONE, PRESET_COMFORT, PRESET_HOME, PRESET_AWAY]

    @property
    def preset_mode(self):
        if self._mode == DOM_ABSENCE:
            return PRESET_AWAY
        elif self._mode == DOM_COMFORT:
            return PRESET_COMFORT
        else:
            return PRESET_NONE    

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode.
        """
        if self._mode == DOM_ABSENCE:
            return HVACMode.OFF
        return HVACMode.HEAT_COOL

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes.
        Need to be a subset of HVAC_MODES.
        """
        return [HVACMode.HEAT_COOL, HVACMode.OFF]

    @property
    def is_on(self):
        """Return true if the light is on."""
        return True

    def get_status(self):
        """Retrieve current status."""
        m = self._domintell.get_module(self._module)
        if m:
            m.get_status()
