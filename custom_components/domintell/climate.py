"""
Support for Domintell climate control.

For more details about this platform, please refer to the documentation at
https://github.com/shamanenas/has_domintell
"""
import logging

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    PRESET_AWAY,
    PRESET_COMFORT,
    PRESET_HOME,
    PRESET_NONE,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, CONF_DEVICES, UnitOfTemperature

from .entity import DomintellEntity

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = (
    ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
)

DOM_ABSENCE = 1
DOM_AUTO = 2
DOM_COMFORT = 5
DOM_FROST = 6
DOM_MANUAL = 99

DOM_TE1 = 'TE1'
DOM_TE2 = 'TE2'


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up climate devices from a config entry."""
    hub = entry.runtime_data
    devices = entry.data.get(CONF_DEVICES, {}).get("climate", [])
    async_add_entities(DomintellClimateDevice(device, hub) for device in devices)


class DomintellClimateDevice(DomintellEntity, ClimateEntity):
    """Representation of a Domintell climate device."""

    _attr_supported_features = SUPPORT_FLAGS
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT_COOL, HVACMode.OFF]
    _attr_preset_modes = [PRESET_NONE, PRESET_COMFORT, PRESET_HOME, PRESET_AWAY]

    def __init__(self, device, hub):
        """Initialize the climate device."""
        super().__init__(device, hub)
        self._mode = DOM_AUTO
        self._current_temperature = None
        self._set_point_temperature = None

    def _on_message(self, message):
        if message.serialNumber == self._module:
            m = self._domintell.get_module(self._module)
            if m:
                self._current_temperature = m.get_temperature()
                self._set_point_temperature = m.get_set_point()
                self._mode = m.get_mode()
            self.schedule_update_ha_state()

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._set_point_temperature

    def set_temperature(self, **kwargs):
        """Set new target temperatures."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self._set_point_temperature = kwargs.get(ATTR_TEMPERATURE)
            m = self._domintell.get_module(self._module)
            if m:
                m.set_temperature(self._set_point_temperature)
        self.schedule_update_ha_state()

    def set_hvac_mode(self, hvac_mode):
        """Set new HVAC mode."""
        m = self._domintell.get_module(self._module)
        if m:
            if hvac_mode == HVACMode.HEAT_COOL:
                m.set_automatic()
            elif hvac_mode == HVACMode.OFF:
                m.set_frost()
        self.schedule_update_ha_state()

    def set_preset_mode(self, preset_mode):
        """Set new target preset mode."""
        m = self._domintell.get_module(self._module)
        if m:
            if preset_mode == PRESET_NONE:
                m.set_automatic()
            elif preset_mode == PRESET_COMFORT:
                m.set_comfort()
            elif preset_mode == PRESET_HOME:
                m.set_automatic()
            elif preset_mode == PRESET_AWAY:
                m.set_absence()
        self.schedule_update_ha_state()

    @property
    def preset_mode(self):
        if self._mode == DOM_ABSENCE:
            return PRESET_AWAY
        if self._mode == DOM_COMFORT:
            return PRESET_COMFORT
        return PRESET_NONE

    @property
    def hvac_mode(self):
        """Return current HVAC mode."""
        if self._mode == DOM_ABSENCE:
            return HVACMode.OFF
        return HVACMode.HEAT_COOL
