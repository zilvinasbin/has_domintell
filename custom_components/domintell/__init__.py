"""
Support for Domintell platform.

For more details about this platform, please refer to the documentation at
https://github.com/shamanenas/has_domintell
"""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_DEVICES,
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PLATFORM,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_PING_INTERVAL,
    DEFAULT_MODULE_TYPES,
    DEFAULT_PING_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .hub import CannotConnect, DomintellHub

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(
                    CONF_PING_INTERVAL, default=DEFAULT_PING_INTERVAL
                ): cv.positive_int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def _collect_yaml_devices(config: ConfigType) -> dict:
    """Collect `platform: domintell` device lists from legacy YAML config."""
    devices = {}
    for platform in PLATFORMS:
        platform_key = str(platform)
        entries = []
        for platform_config in config.get(platform_key, []):
            if platform_config.get(CONF_PLATFORM) != DOMAIN:
                continue
            for device in platform_config.get(CONF_DEVICES, []):
                if "module" not in device or CONF_NAME not in device:
                    _LOGGER.warning(
                        "Skipping malformed %s device entry during import: %s",
                        platform_key,
                        device,
                    )
                    continue
                entries.append(
                    {
                        "type": device.get(
                            "type", DEFAULT_MODULE_TYPES[platform_key]
                        ),
                        "module": device["module"],
                        "channel": device.get("channel", 1),
                        "name": device[CONF_NAME],
                    }
                )
        if entries:
            devices[platform_key] = entries
    return devices


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Detect legacy YAML configuration and import it once."""
    if DOMAIN not in config:
        return True

    ir.async_create_issue(
        hass,
        DOMAIN,
        "deprecated_yaml",
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="deprecated_yaml",
    )

    if hass.config_entries.async_entries(DOMAIN):
        # Already migrated; the YAML is ignored (issue above reminds the user).
        return True

    hub_conf = config[DOMAIN]
    import_data = {
        CONF_HOST: hub_conf[CONF_HOST],
        CONF_PASSWORD: hub_conf[CONF_PASSWORD],
        CONF_PING_INTERVAL: hub_conf.get(CONF_PING_INTERVAL, DEFAULT_PING_INTERVAL),
        CONF_DEVICES: _collect_yaml_devices(config),
    }
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=import_data
        )
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Domintell from a config entry."""
    hub = DomintellHub(
        hass,
        entry.data[CONF_HOST],
        entry.data[CONF_PASSWORD],
        entry.data.get(CONF_PING_INTERVAL, DEFAULT_PING_INTERVAL),
        entry_id=entry.entry_id,
    )
    try:
        await hub.async_connect()
    except CannotConnect as err:
        raise ConfigEntryNotReady(str(err)) from err

    entry.runtime_data = hub

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer="Domintell",
        name=f"Domintell master ({entry.data[CONF_HOST]})",
    )

    async def _async_stop(event):
        await hass.async_add_executor_job(hub.stop)

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_stop)
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Domintell config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await hass.async_add_executor_job(entry.runtime_data.stop)
    return unload_ok
