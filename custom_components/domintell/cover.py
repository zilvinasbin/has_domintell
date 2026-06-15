"""
Support for Domintell covers.

For more details about this platform, please refer to the documentation at
https://github.com/shamanenas/has_domintell
"""
import logging

from homeassistant.components.cover import CoverEntity
from homeassistant.const import CONF_DEVICES

from .entity import DomintellEntity

_LOGGER = logging.getLogger(__name__)

DOM_TRV = 'TRV' # 4 - shutter controller


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up covers from a config entry."""
    hub = entry.runtime_data
    devices = entry.data.get(CONF_DEVICES, {}).get("cover", [])
    async_add_entities(DomintellCover(cover, hub) for cover in devices)


class DomintellCover(DomintellEntity, CoverEntity):
    """Representation of a Domintell Cover."""

    def __init__(self, cover, hub):
        """Initialize a Domintell cover."""
        super().__init__(cover, hub)
        self._is_opening = None
        self._is_closing = None

    def _on_message(self, message):
        if message.serialNumber == self._module:
            m = self._domintell.get_module(self._module)
            if m:
                self._is_opening = m.is_opening(self._channel)
                self._is_closing = m.is_closing(self._channel)
            self.schedule_update_ha_state()

    @property
    def is_opening(self):
        """Return true if the cover is opening."""
        return self._is_opening

    @property
    def is_closing(self):
        """Return true if the cover is closing."""
        return self._is_closing

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        return None

    def close_cover(self, **kwargs):
        """Instruct the cover to close."""
        m = self._domintell.get_module(self._module)
        if m:
            m.close_cover(self._channel)

    def open_cover(self, **kwargs):
        """Instruct the cover to open."""
        m = self._domintell.get_module(self._module)
        if m:
            m.open_cover(self._channel)

    def stop_cover(self, **kwargs):
        """Instruct the cover to stop."""
        m = self._domintell.get_module(self._module)
        if m:
            m.stop_cover(self._channel)
