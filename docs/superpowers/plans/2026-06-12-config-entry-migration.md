# Domintell Config-Entry Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the Domintell custom integration from YAML configuration to config entries with automatic one-time YAML import, unique IDs, and device registry support.

**Architecture:** A `DomintellHub` class owns the sync `domintell.Controller` (login, reconnect, ping, shutdown) and is stored in `entry.runtime_data`. A config flow provides a `user` step (manual hub setup) and an `import` step (automatic YAML migration with a Repair issue). All five platforms switch to `async_setup_entry`, reading device lists from `entry.data["devices"]`. A shared `DomintellEntity` base class provides `unique_id`, `device_info`, and the message-subscription lifecycle so entity behavior is otherwise unchanged.

**Tech Stack:** Home Assistant 2026.5+ custom component, python-domintell==0.0.17 (sync library, wrapped in executor jobs), voluptuous.

**Spec:** `docs/superpowers/specs/2026-06-12-config-entry-migration-design.md`

**Testing note:** The spec explicitly defers automated tests to Phase 2 and the repo has no test harness, so tasks use `python3 -m py_compile` as a syntax gate plus a final manual verification checklist against a dev HA instance (Task 12). TDD steps are intentionally absent — this is a spec decision, not an oversight.

**Entity-ID preservation rule (applies to every platform task):** entity IDs today are name-derived slugs (no registry entries exist). Do NOT change any entity's name source (`device["name"]`) and do NOT set `_attr_has_entity_name`. The first boot after migration creates registry entries with the same name-derived IDs.

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `custom_components/domintell/const.py` | Modify | Domain constants, platform list, config keys |
| `custom_components/domintell/manifest.json` | Modify | Declare config flow, single instance, iot_class |
| `custom_components/domintell/strings.json` | Create | Config flow + repair issue text |
| `custom_components/domintell/translations/en.json` | Create | English translation (copy of strings.json) |
| `custom_components/domintell/hub.py` | Create | `DomintellHub`: controller lifecycle, executor-safe |
| `custom_components/domintell/entity.py` | Create | `DomintellEntity` base: unique_id, device_info, subscription |
| `custom_components/domintell/config_flow.py` | Create | `user` + `import` steps |
| `custom_components/domintell/__init__.py` | Rewrite | YAML import detection, repair issue, entry setup/unload |
| `custom_components/domintell/light.py` | Rewrite | Light + dimmer entities on new base |
| `custom_components/domintell/switch.py` | Rewrite | Switch entities on new base |
| `custom_components/domintell/binary_sensor.py` | Rewrite | Binary sensor entities on new base |
| `custom_components/domintell/climate.py` | Rewrite | Climate entities on new base + undefined-name fix |
| `custom_components/domintell/cover.py` | Rewrite | Cover entities on new base + syntax-error fix |
| `README.md` | Modify | UI setup + migration instructions |

---

### Task 1: Constants, manifest, and translations

**Files:**
- Modify: `custom_components/domintell/const.py`
- Modify: `custom_components/domintell/manifest.json`
- Create: `custom_components/domintell/strings.json`
- Create: `custom_components/domintell/translations/en.json`

- [ ] **Step 1: Replace `const.py` with:**

```python
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
```

Note: the old `CONF_BINARY_SENSOR`/`CONF_SENSOR`/`CONF_CLIMATE`/`CONF_SWITCH`/`CONF_LIGHT` constants are removed; their only consumer was the old `__init__.py` import line, which Task 5 rewrites. `VERSION` bumped because this is a behavior-visible release.

- [ ] **Step 2: Replace `manifest.json` with:**

```json
{
  "domain": "domintell",
  "name": "Domintell Integration",
  "version": "1.1.0",
  "documentation": "https://github.com/shamanenas/has_domintell",
  "config_flow": true,
  "single_config_entry": true,
  "iot_class": "local_push",
  "codeowners": ["@zilvinas"],
  "requirements": ["python-domintell==0.0.17"],
  "quality_scale": "silver"
}
```

(The `"mqtt"` dependency is removed — nothing in the component uses MQTT. `quality_scale` lowercased to the valid enum value.)

- [ ] **Step 3: Create `strings.json`:**

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Connect to Domintell master",
        "description": "Enter the connection details of your DETH02 module.",
        "data": {
          "host": "Host (ip:port, default port 17481)",
          "password": "Password (use LOGIN if no password is set)",
          "ping_interval": "Ping interval in seconds (0 disables)"
        }
      }
    },
    "error": {
      "cannot_connect": "Failed to connect or log in. Check the host and password."
    },
    "abort": {
      "single_instance_allowed": "Already configured. Only a single Domintell hub is supported."
    }
  },
  "issues": {
    "deprecated_yaml": {
      "title": "Domintell YAML configuration is deprecated",
      "description": "Your Domintell YAML configuration was imported into a config entry and is no longer used. Remove the `domintell:` section and all `platform: domintell` entries (light, switch, binary_sensor, climate, cover) from configuration.yaml, then restart Home Assistant."
    }
  }
}
```

- [ ] **Step 4: Create `translations/en.json` with the exact same content as `strings.json`.**

- [ ] **Step 5: Verify JSON validity and Python syntax**

Run:
```bash
python3 -m json.tool custom_components/domintell/manifest.json > /dev/null \
  && python3 -m json.tool custom_components/domintell/strings.json > /dev/null \
  && python3 -m json.tool custom_components/domintell/translations/en.json > /dev/null \
  && python3 -m py_compile custom_components/domintell/const.py && echo OK
```
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add custom_components/domintell/const.py custom_components/domintell/manifest.json custom_components/domintell/strings.json custom_components/domintell/translations/en.json
git commit -m "feat: declare config flow in manifest, add constants and translations"
```

---

### Task 2: Hub wrapper

**Files:**
- Create: `custom_components/domintell/hub.py`

- [ ] **Step 1: Create `hub.py`:**

```python
"""Hub wrapper owning the Domintell controller and its session lifecycle."""
import logging
import threading

import domintell

_LOGGER = logging.getLogger(__name__)

CONNECT_TIMEOUT = 10  # seconds to wait for SessionOpenedMessage


class CannotConnect(Exception):
    """Failed to connect or log in to the Domintell master."""


class DomintellHub:
    """Owns the domintell.Controller: login, reconnect, ping, shutdown.

    The python-domintell library is synchronous; every method here that
    touches the network is blocking and must be called from an executor,
    never from the event loop. async_connect() does this for you.
    """

    def __init__(self, hass, host, password, ping_interval, entry_id=None):
        self._hass = hass
        self._host = host
        self._password = bytearray(ord(c) for c in password)
        self._ping_interval = ping_interval
        self.entry_id = entry_id
        self._controller = None
        self._session_opened = threading.Event()

    def _connect(self):
        """Connect and log in (blocking, runs in executor)."""
        self._controller = domintell.Controller(self._host)
        self._controller.subscribe(self._on_message)
        self._controller.login(self._password)
        if not self._session_opened.wait(CONNECT_TIMEOUT):
            self._controller.stop()
            self._controller = None
            raise CannotConnect(
                f"No session opened by {self._host} within {CONNECT_TIMEOUT}s"
            )

    async def async_connect(self):
        """Connect and log in without blocking the event loop."""
        await self._hass.async_add_executor_job(self._connect)

    def _on_message(self, message):
        """Handle session lifecycle messages (runs in the reader thread)."""
        if isinstance(message, domintell.SessionOpenedMessage):
            self._session_opened.set()
            if self._ping_interval > 0:
                self._controller.start_ping(self._ping_interval)
        elif isinstance(
            message,
            (domintell.SessionClosedMessage, domintell.SessionTimeoutMessage),
        ):
            # The DETH02 dropped us; re-login to restore the session.
            self._session_opened.clear()
            self._controller.login(self._password)

    # --- pass-throughs used by entities -----------------------------------

    def subscribe(self, callback):
        """Subscribe a callback to all controller messages."""
        self._controller.subscribe(callback)

    def add_module(self, module_type, serial_number):
        """Register a module with the controller."""
        return self._controller.add_module(module_type, serial_number)

    def get_module(self, serial_number):
        """Return a registered module or None."""
        return self._controller.get_module(serial_number)

    def stop(self):
        """Shut down the controller (blocking, run in executor)."""
        if self._controller is not None:
            self._controller.stop()
            self._controller = None
```

- [ ] **Step 2: Verify syntax**

Run: `python3 -m py_compile custom_components/domintell/hub.py && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add custom_components/domintell/hub.py
git commit -m "feat: add DomintellHub wrapper for controller lifecycle"
```

---

### Task 3: Shared entity base class

**Files:**
- Create: `custom_components/domintell/entity.py`

- [ ] **Step 1: Create `entity.py`:**

```python
"""Base entity for Domintell devices."""
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN


class DomintellEntity(Entity):
    """Common behavior for all Domintell entities.

    Subclasses must implement _on_message(message); it runs in the
    controller's reader thread, so update state via
    schedule_update_ha_state(), never async APIs.
    """

    _attr_should_poll = False

    def __init__(self, device, hub):
        """Initialize from a device config dict and the hub."""
        self._domintell = hub
        self._attr_name = device["name"]
        self._module = device["module"]
        self._channel = device["channel"] - 1  # we use 0 based index internally
        self._type = device["type"]
        self._attr_unique_id = f"{self._module}-{self._channel}"
        hub.add_module(self._type, self._module)

    @property
    def device_info(self) -> DeviceInfo:
        """One HA device per Domintell module, linked to the hub device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._module)},
            name=f"Domintell {self._type} {self._module}",
            manufacturer="Domintell",
            model=self._type,
            via_device=(DOMAIN, self._domintell.entry_id),
        )

    async def async_added_to_hass(self):
        """Subscribe to controller messages and request initial status."""
        def _subscribe():
            self._domintell.subscribe(self._on_message)
            self.get_status()

        await self.hass.async_add_executor_job(_subscribe)

    def get_status(self):
        """Request current status from the module."""
        m = self._domintell.get_module(self._module)
        if m:
            m.get_status()

    def _on_message(self, message):
        """Handle a controller message. Subclasses must override."""
        raise NotImplementedError
```

- [ ] **Step 2: Verify syntax**

Run: `python3 -m py_compile custom_components/domintell/entity.py && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add custom_components/domintell/entity.py
git commit -m "feat: add DomintellEntity base with unique_id and device registry support"
```

---

### Task 4: Config flow

**Files:**
- Create: `custom_components/domintell/config_flow.py`

- [ ] **Step 1: Create `config_flow.py`:**

```python
"""Config flow for the Domintell integration."""
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_DEVICES, CONF_HOST, CONF_PASSWORD

from .const import CONF_PING_INTERVAL, DEFAULT_PING_INTERVAL, DOMAIN
from .hub import CannotConnect, DomintellHub

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_PING_INTERVAL, default=DEFAULT_PING_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=0)
        ),
    }
)


class DomintellConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the Domintell config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Manual setup: ask for connection details and validate them."""
        errors = {}
        if user_input is not None:
            hub = DomintellHub(
                self.hass,
                user_input[CONF_HOST],
                user_input[CONF_PASSWORD],
                ping_interval=0,
            )
            try:
                await hub.async_connect()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                await self.hass.async_add_executor_job(hub.stop)
                return self.async_create_entry(
                    title=f"Domintell ({user_input[CONF_HOST]})",
                    data={**user_input, CONF_DEVICES: {}},
                )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_import(self, import_data):
        """Import hub settings and device lists from configuration.yaml.

        No connection validation: the YAML config is known-working, and a
        transient failure here would strand the migration.
        """
        return self.async_create_entry(
            title=f"Domintell ({import_data[CONF_HOST]})",
            data=import_data,
        )
```

Note on errors: the library does not distinguish a wrong password from an unreachable host (both end in no `SessionOpenedMessage`), so the user step reports `cannot_connect` for both. The spec's `invalid_auth` mapping is not implementable with python-domintell 0.0.17 — this is the documented deviation.

- [ ] **Step 2: Verify syntax**

Run: `python3 -m py_compile custom_components/domintell/config_flow.py && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add custom_components/domintell/config_flow.py
git commit -m "feat: add config flow with user and import steps"
```

---

### Task 5: Integration setup rewrite

**Files:**
- Rewrite: `custom_components/domintell/__init__.py`

- [ ] **Step 1: Replace `__init__.py` with:**

```python
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
```

Notes:
- `hass.data[DOMAIN]` is gone; the hub lives in `entry.runtime_data`.
- While the legacy YAML is still present, HA will log an error per leftover `platform: domintell` entry (the platforms no longer support YAML setup). This is expected and goes away when the user removes the YAML, as the repair issue instructs.
- Optional YAML keys that HA core no longer uses (`location`, `path`, `force_update`, `device_class`) are intentionally dropped by the import: `location`/`path` were never used, and `force_update`/`device_class` were read by no code path.

- [ ] **Step 2: Verify syntax**

Run: `python3 -m py_compile custom_components/domintell/__init__.py && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add custom_components/domintell/__init__.py
git commit -m "feat: config entry setup with automatic YAML import and repair issue"
```

---

### Task 6: Light platform

**Files:**
- Rewrite: `custom_components/domintell/light.py`

- [ ] **Step 1: Replace `light.py` with:**

```python
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
```

Changes vs. old file: `PLATFORM_SCHEMA`/`async_setup_platform` replaced by `async_setup_entry`; common init/subscription/name/should_poll moved to `DomintellEntity`; color-mode properties became `_attr_` class attributes; the unused `self._is_dimmer` lookup is dropped. `_on_message`, `is_on`, `turn_on`, `turn_off`, and brightness math are unchanged.

- [ ] **Step 2: Verify syntax**

Run: `python3 -m py_compile custom_components/domintell/light.py && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add custom_components/domintell/light.py
git commit -m "feat: migrate light platform to config entry setup"
```

---

### Task 7: Switch platform

**Files:**
- Rewrite: `custom_components/domintell/switch.py`

- [ ] **Step 1: Replace `switch.py` with:**

```python
"""
Support for Domintell trip switch.

For more details about this platform, please refer to the documentation at
https://github.com/shamanenas/has_domintell
"""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_DEVICES

from .entity import DomintellEntity

_LOGGER = logging.getLogger(__name__)

DOM_TRP = 'TRP' # 5 - relay controller


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up switches from a config entry."""
    hub = entry.runtime_data
    devices = entry.data.get(CONF_DEVICES, {}).get("switch", [])
    async_add_entities(DomintellSwitch(switch, hub) for switch in devices)


class DomintellSwitch(DomintellEntity, SwitchEntity):
    """Representation of a Domintell Switch."""

    def __init__(self, switch, hub):
        """Initialize a Domintell switch."""
        super().__init__(switch, hub)
        self._state = False

    def _on_message(self, message):
        if message.serialNumber == self._module:
            m = self._domintell.get_module(self._module)
            if m:
                self._state = m.is_on(self._channel)
            self.schedule_update_ha_state()

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Instruct the switch to turn on."""
        m = self._domintell.get_module(self._module)
        if m:
            m.turn_on(self._channel)

    def turn_off(self, **kwargs):
        """Instruct the switch to turn off."""
        m = self._domintell.get_module(self._module)
        if m:
            m.turn_off(self._channel)
```

Changes vs. old file: same mechanical migration as light. The stray `print(message.to_json())` and the module-level `_LOGGER.setLevel(10)` are dropped.

- [ ] **Step 2: Verify syntax**

Run: `python3 -m py_compile custom_components/domintell/switch.py && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add custom_components/domintell/switch.py
git commit -m "feat: migrate switch platform to config entry setup"
```

---

### Task 8: Binary sensor platform

**Files:**
- Rewrite: `custom_components/domintell/binary_sensor.py`

- [ ] **Step 1: Replace `binary_sensor.py` with:**

```python
"""
Support for Domintell binary sensors.

For more details about this platform, please refer to the documentation at
https://github.com/shamanenas/has_domintell
"""
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import CONF_DEVICES

from .entity import DomintellEntity

_LOGGER = logging.getLogger(__name__)

DOM_IS8 = 'IS8' # 8 inputs DI sensor
DOM_IS4 = 'IS4' # 4 inputs DI sensor
DOM_BU4 = 'BU4' # 4 inputs button block
DOM_DET = 'DET' # movement detector (1 DI)

DOM_VAR = 'VAR' # Binary variable (only binary implemented)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up binary sensors from a config entry."""
    hub = entry.runtime_data
    devices = entry.data.get(CONF_DEVICES, {}).get("binary_sensor", [])
    async_add_entities(DomintellBinarySensor(sensor, hub) for sensor in devices)


class DomintellBinarySensor(DomintellEntity, BinarySensorEntity):
    """Representation of a Domintell binary sensor."""

    def __init__(self, sensor, hub):
        """Initialize a Domintell sensor/button."""
        super().__init__(sensor, hub)
        self._state = False

    def _on_message(self, message):
        if message.serialNumber == self._module:
            m = self._domintell.get_module(self._module)
            if m:
                self._state = m.is_on(self._channel)
            self.schedule_update_ha_state()

    @property
    def is_on(self):
        """Return true if the sensor is on."""
        return self._state
```

Changes vs. old file: same mechanical migration; the `turn_on`/`turn_off` methods are removed (dead code — binary sensors expose no such services) and the stray `print` is dropped.

- [ ] **Step 2: Verify syntax**

Run: `python3 -m py_compile custom_components/domintell/binary_sensor.py && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add custom_components/domintell/binary_sensor.py
git commit -m "feat: migrate binary_sensor platform to config entry setup"
```

---

### Task 9: Climate platform (+ undefined-name fix)

**Files:**
- Rewrite: `custom_components/domintell/climate.py`

- [ ] **Step 1: Replace `climate.py` with:**

```python
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
```

Changes vs. old file: same mechanical migration, plus the spec's bug fix — `set_hvac_mode` referenced an undefined `operation_mode`; it now uses `hvac_mode`. Also removed: dead code that referenced nothing (`operation_mode_str`/`current_operation`/`operation_list` — string operation modes were replaced by HVAC/preset modes in HA years ago; `is_away_mode_on`, `is_on`, the unused `self._range_temperature`/`self._on` attributes, and the `sefl` typo'd `preset_modes` property which is now a class attribute).

- [ ] **Step 2: Verify syntax**

Run: `python3 -m py_compile custom_components/domintell/climate.py && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add custom_components/domintell/climate.py
git commit -m "feat: migrate climate platform to config entry setup, fix set_hvac_mode NameError"
```

---

### Task 10: Cover platform (+ syntax-error fix)

**Files:**
- Rewrite: `custom_components/domintell/cover.py`

- [ ] **Step 1: Replace `cover.py` with:**

```python
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
```

Changes vs. old file: fixes the syntax error (`async_added_to_hass` lacked `async` but contained `await` — the platform could not load at all; the base class now provides a correct implementation). The old hand-rolled `_id`/`unique_id`/`device_info` are replaced by the base class — the unique_id format `f"{module}-{channel}"` (0-based channel) is **identical** to the old `self._id`, so any registry entries that did exist are preserved. The base `device_info` also fixes the old broken `via_device=(DOMAIN, self._domintell)` (a controller object is not a valid identifier).

- [ ] **Step 2: Verify syntax**

Run: `python3 -m py_compile custom_components/domintell/cover.py && echo OK`
Expected: `OK`

- [ ] **Step 3: Compile-check the whole component**

Run: `python3 -m py_compile custom_components/domintell/*.py && echo ALL_OK`
Expected: `ALL_OK`

- [ ] **Step 4: Commit**

```bash
git add custom_components/domintell/cover.py
git commit -m "feat: migrate cover platform to config entry setup, fix async syntax error"
```

---

### Task 11: README update

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace the "Installation" and "Configuration" sections (README.md lines 6–27) with:**

```markdown
# Installation
1. Copy contents of the *custom_components* folder to your home assistants' */config/custom_components*
1. Restart Home Assistant
1. Go to **Settings → Devices & Services → Add Integration** and search for **Domintell**
1. Enter the DETH02 host (`ip:port`, default port 17481) and password

**Note:** You should not need to install python-domintell manually, it will be installed automatically

# Migrating from YAML

Starting with version 1.1.0 the integration is configured via the UI and
stores its configuration in Home Assistant's storage. If you have an
existing YAML configuration (`domintell:` plus `platform: domintell`
entries), it is **imported automatically** on the first restart after
upgrading — your hub settings and all device definitions are copied into a
config entry, and entity IDs are preserved.

After the import, a Repair issue will remind you to delete the `domintell:`
section and all `platform: domintell` entries from `configuration.yaml`,
then restart. The legacy YAML reference below is kept only for users who
have not migrated yet.

**Notes:**
* Please specify UDP port for deth02 module. Default port is 17481. If port number is omited Serial connection will be used instead.
* If your DETH02 has no password set, put 'LOGIN' instead of password.
```

Keep the rest of the README (the per-platform YAML examples) under a new heading `# Legacy YAML reference (pre-1.1.0)` so existing users can still map their old config, and update the "Supported Home Assistant versions" section to list `2026.5`.

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: document UI setup and YAML migration in README"
```

---

### Task 12: Manual verification on dev HA instance

No files. This task validates the migration end-to-end per the spec's testing section. Run against a Home Assistant 2026.5+ dev instance with the component installed.

- [ ] **Step 1: Upgrade path.** Start HA with the existing YAML config (hub + device lists) and the new component version. Verify:
  - A Domintell config entry appears under Settings → Devices & Services (no user interaction).
  - A repair issue "Domintell YAML configuration is deprecated" appears under Settings → Repairs.
  - **Every entity from before the upgrade exists with the identical entity_id** (compare Developer Tools → States against a pre-upgrade export). This is the critical check — automations and dashboards depend on it.
  - Entities respond: toggle a light, watch a binary sensor react to a physical button.

- [ ] **Step 2: YAML removal.** Delete the `domintell:` section and all `platform: domintell` entries from configuration.yaml. Restart. Verify all entities are still present and working, and the repair issue no longer reappears (it may need manual dismissal once).

- [ ] **Step 3: Reload.** From the integration page, reload the entry. Verify entities come back and respond.

- [ ] **Step 4: Device registry.** Verify each Domintell module appears as a device (named `Domintell <TYPE> <MODULE>`) with its channel entities attached, linked via the hub device.

- [ ] **Step 5: Clean install.** On a fresh HA instance (or after deleting the entry), add the integration via the UI:
  - Wrong host/password → form shows "Failed to connect or log in."
  - Correct host/password → entry created (hub-only, no devices — expected in Phase 1).
  - Adding a second instance is blocked (single instance).

- [ ] **Step 6: Restart resilience.** Restart HA with the Domintell master unreachable (e.g., unplug it). Verify the entry shows "Retrying setup" rather than failing permanently, and recovers when the master is back.

- [ ] **Step 7: Commit any fixes found, then finish the branch** (use superpowers:finishing-a-development-branch).
