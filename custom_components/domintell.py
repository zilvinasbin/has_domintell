"""
Support for Domintell platform.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/domintell/
"""
import time
import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, CONF_HOST, CONF_PORT, CONF_PASSWORD

REQUIREMENTS = ['python-domintell==0.0.5']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'domintell'

DOMINTELL_MESSAGE = 'domintell.message'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PASSWORD):cv.string
    })
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Set up the Domintell platform."""
    import domintell
    host = config[DOMAIN].get(CONF_HOST)
    controller = domintell.Controller(host)
    hass.data[DOMAIN] = controller

    p = bytearray()
    for c in config[DOMAIN].get(CONF_PASSWORD):
        p.append(ord(c))

    controller.login(p)
    time.sleep(10)

    def stop_domintell(event):
        """Disconnect."""
        _LOGGER.debug("Shutting down ")
        controller.stop()

    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, stop_domintell)
    return True
