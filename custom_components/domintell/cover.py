"""
Support for Domintell covers.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/cover.domintell/
"""
import asyncio
import logging
import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.components.cover import ATTR_POSITION, CoverEntity, PLATFORM_SCHEMA
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_DEVICES, CONF_NAME, ATTR_ENTITY_ID, ATTR_STATE
import homeassistant.helpers.config_validation as cv

from .const import (DOMAIN)


# REQUIREMENTS = ['python-domintell==0.1.0']
# DEPENDENCIES = ['domintell']
# DOMAIN = 'domintell'

_LOGGER = logging.getLogger(__name__)


DOM_TRV = 'TRV' # 4 - shutter controller

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [
        {
            vol.Optional('type', default=DOM_TRV): cv.string,
            vol.Required('module'): cv.string,
            vol.Required('channel'): cv.positive_int,
            vol.Required(CONF_NAME): cv.string,
            vol.Optional('location'): cv.string
        }
    ])
})

async def async_setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up Covers."""
    domintell = hass.data[DOMAIN]
    # _LOGGER.warning('Creating covers =========================== ')
    add_devices(create_cover(cover, domintell) for cover in config[CONF_DEVICES])


def create_cover(cover, domintell):
        module_type = cover['type']
#        _LOGGER.warning('creating cover %s', cover[CONF_NAME])
        return DomintellCover(cover, domintell)

class DomintellCover(CoverEntity):
    """Representation of a Domintell Cover."""

    def __init__(self, cover, domintell):
        """Initialize a Domintell cover."""
        self._cover = cover
        self._domintell = domintell
        self._name = cover[CONF_NAME]
        self._module = cover['module']
        self._channel = cover['channel'] - 1 # we use 0 based index internally
        self._id = f"{self._module}-{self._channel}"
        self._type = cover['type']
        
        self._is_opening = None
        self._is_closing = None

        self._position = None
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
                self._is_opening = m.is_opening(self._channel)
                self._is_closing = m.is_closing(self._channel)
            self.schedule_update_ha_state()

    @property
    def device_info(self):
        return {
            "identifiers": {
                (DOMAIN, self._id)
            },
            "name": self._name,
            "manufacturer": 'Trump s.a.',
            "model": self._type,
            "via_device": (DOMAIN, self._domintell),
        }

    @property
    def unique_id(self):
        """Return the unique_id of this cover."""
        return self._id
    
    @property
    def name(self):
        """Return the display name of this cover."""
        return self._name
    
    @property
    def should_poll(self):
        """Disable polling."""
        return False

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

    def get_status(self):
        """Retrieve current status."""
        m = self._domintell.get_module(self._module)
        if m:
            m.get_status()

