"""Constants for Domintell"""
from homeassistant.const import Platform

# Base constants
DOMAIN = "domintell"
VERSION = "1.1.0"

# Platforms set up from a config entry
PLATFORMS = [
    Platform.LIGHT,
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.COVER,
]

# Configuration keys
CONF_PING_INTERVAL = "ping_interval"
DEFAULT_PING_INTERVAL = 60

# Default Domintell module type per platform (used by YAML import)
DEFAULT_MODULE_TYPES = {
    "light": "BIR",
    "switch": "TRP",
    "binary_sensor": "IS8",
    "climate": "TE1",
    "cover": "TRV",
}

# OTHER
DOMINTELL_MESSAGE = "domintell.message"

# Defaults
DEFAULT_NAME = DOMAIN
