"""
Support for Domintell platform.

From Home Assistant version 0.104.0

For more details about this platform, please refer to the documentation at
https://github.com/shamanenas/has_domintell
"""
import time
import logging
import voluptuous as vol
import threading

import homeassistant.helpers.config_validation as cv
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, CONF_HOST, CONF_PORT, CONF_PASSWORD

from .const import (
    CONF_BINARY_SENSOR,
    CONF_SENSOR,
    CONF_CLIMATE,
    CONF_SWITCH,
    CONF_LIGHT,
    VERSION,
    DOMAIN,
    DOMINTELL_MESSAGE
)

# REQUIREMENTS = ['python-domintell==0.0.10']

_LOGGER = logging.getLogger(__name__)


CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PASSWORD):cv.string,
        vol.Optional('ping_interval', default=60): cv.positive_int
    })
}, extra=vol.ALLOW_EXTRA)

def setup(hass, config):
    """Set up the Domintell platform."""

    _LOGGER.info("SETUP DOMINTELL")

    import domintell

    host = config[DOMAIN].get(CONF_HOST)
    ping_interval = config[DOMAIN].get('ping_interval')
    pswd = bytearray()
    for c in config[DOMAIN].get(CONF_PASSWORD):
        pswd.append(ord(c))

    _LOGGER.debug(host)
    _LOGGER.debug(pswd)

    controller = domintell.Controller(host)

    def _on_message(message):
        _LOGGER.debug(message)
        if isinstance(message, domintell.SessionOpenedMessage):
            # we are good to go start pinger
            if ping_interval > 0:
                controller.start_ping(ping_interval)
        elif isinstance(message, domintell.SessionClosedMessage):
            # we were disconnected by the DETH02, try to reconnect
            controller.login(pswd)
        elif isinstance(message, domintell.SessionTimeoutMessage):
            # we were disconnected by the DETH02, try to reconnect
            controller.login(pswd)

    controller.subscribe(_on_message)
    hass.data[DOMAIN] = controller

    controller.login(pswd)
    _LOGGER.debug("login")
    time.sleep(2)

    def stop_domintell(event):
        """Disconnect."""
        _LOGGER.warning("Shutting down ")
        controller.stop()

    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, stop_domintell)
    return True
