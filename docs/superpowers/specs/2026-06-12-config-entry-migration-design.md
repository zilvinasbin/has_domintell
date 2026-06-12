# Domintell Config-Entry Migration — Design (Phase 1)

**Date:** 2026-06-12
**Status:** Draft — awaiting approval
**Target:** Home Assistant 2026.5+

## Goal

Migrate the Domintell custom integration from YAML configuration to config
entries, so the hub connection and all device definitions live in Home
Assistant's storage (`.storage`) and are managed via the UI. Existing
installations migrate automatically with identical entity IDs.

## Decisions made

| Decision | Choice |
|---|---|
| Device source after migration | Hybrid: one-time YAML import now, APPINFO discovery in Phase 2 |
| Import trigger | Automatic on first restart after upgrade, with a Repair issue prompting YAML removal |
| Scope | Config entry + unique IDs + device registry + hub wrapper; entity behavior unchanged; options flow and discovery deferred to Phase 2 |

## Architecture

```
configuration.yaml (legacy, one-time read)
        │  async_setup → import flow
        ▼
ConfigEntry.data {host, password, ping_interval, devices:{light:[...], switch:[...], ...}}
        │  async_setup_entry
        ▼
DomintellHub (hub.py) ── owns domintell.Controller, login/reconnect/ping/stop
        │  entry.runtime_data, forward_entry_setups
        ▼
Platforms (light, switch, binary_sensor, climate, cover)
        │  async_setup_entry reads entry.data["devices"][platform]
        ▼
Entities (unchanged logic) + unique_id + DeviceInfo
```

## Components

### 1. `config_flow.py` (new)

- `async_step_user`: form with `host` (`ip:port` string), `password`,
  `ping_interval` (positive int, default 60). Validates by constructing a
  controller and attempting login with a timeout; maps failures to
  `cannot_connect` / `invalid_auth` form errors. Creates an entry with an
  empty `devices` dict (devices arrive via Phase 2 discovery or future
  options flow; manual setup on a clean install yields hub-only until then).
- `async_step_import`: accepts the merged YAML payload from `async_setup`
  and creates the entry without interaction. No connection validation on
  import (the YAML config is known-working; validation failure would strand
  the migration).
- Single instance enforced via `single_config_entry: true` in the manifest.

### 2. `__init__.py` (rewrite)

- `async_setup(hass, config)`: legacy-YAML detector only. If `domintell:`
  is present in the YAML config:
  - Collect hub settings from `config[DOMAIN]`.
  - Collect device lists by scanning `config[<platform>]` for entries with
    `platform: domintell` across light, switch, binary_sensor, climate,
    cover.
  - If no config entry exists, start an import flow with the merged payload.
  - Raise a Repair issue (`deprecated_yaml`) telling the user the YAML has
    been imported and can be removed.
- `async_setup_entry(hass, entry)`: create `DomintellHub`, connect (raises
  `ConfigEntryNotReady` on failure), store it in `entry.runtime_data`,
  forward to the five platforms, register `EVENT_HOMEASSISTANT_STOP`
  shutdown listener.
- `async_unload_entry`: unload platforms, stop the hub.

### 3. `hub.py` (new)

`DomintellHub` wraps `domintell.Controller`:

- `async_connect()`: runs login in the executor, then waits for
  `SessionOpenedMessage` with a timeout (replaces the current blocking
  `time.sleep(2)`). On timeout/failure raises an exception that
  `async_setup_entry` converts to `ConfigEntryNotReady`.
- Message handling: keeps the existing behavior — start pinger on
  `SessionOpenedMessage` (if `ping_interval > 0`), re-login on
  `SessionClosedMessage` / `SessionTimeoutMessage`.
- `subscribe(cb)` / `add_module(type, serial)` / `get_module(serial)`
  pass-throughs for entities.
- `stop()`: controller shutdown.
- All sync library calls from the event loop go through
  `hass.async_add_executor_job`.

### 4. Platform files (5 × mechanical change)

Replace `PLATFORM_SCHEMA` + `async_setup_platform` with:

```python
async def async_setup_entry(hass, entry, async_add_entities):
    hub = entry.runtime_data
    devices = entry.data["devices"].get(<platform>, [])
    async_add_entities(create_<x>(d, hub) for d in devices)
```

Entity classes gain exactly three things; message-callback logic stays:

- `_attr_unique_id = f"{module}-{channel}"` (matches cover's existing
  scheme; channel is the 0-based internal index, as cover does today).
- `device_info`: one HA device per Domintell module —
  `identifiers={(DOMAIN, module)}`, `model=type`,
  `manufacturer="Domintell"`, `via_device=(DOMAIN, entry.entry_id)`.
  The hub itself is registered as a device.
- `async_added_to_hass`: deprecated `hass.async_add_job` replaced with
  `hass.async_add_executor_job` (subscribe + get_status are sync calls).

**Entity ID preservation:** entities currently have no unique_id and are not
in the entity registry; their entity IDs are name-derived slugs. On first
boot after migration, registry entries are created with the same
name-derived IDs, so automations and dashboards keep working provided names
are unchanged. This is an explicit verification step.

### 5. Targeted fixes (in files already being touched)

- `cover.py:71`: `async_added_to_hass` lacks `async` but contains `await` —
  a syntax error; the cover platform cannot load today. Fix the signature.
- `climate.py:185`: `operation_mode` is undefined inside `set_hvac_mode`
  (should be `hvac_mode`).
- `manifest.json`: add `"config_flow": true`, `"single_config_entry": true`,
  `"iot_class": "local_push"`; remove unused `"mqtt"` dependency; keep
  `python-domintell==0.0.17` requirement.
- Add `strings.json` + `translations/en.json` covering the user step,
  errors, and the repair issue text.

## Error handling

- Config flow (user step): connection/login failure → form error, no entry.
- Setup: hub connect failure → `ConfigEntryNotReady` (HA retries with
  backoff).
- Runtime: session closed/timeout → hub re-logins (existing behavior).
- Import: malformed device entries are skipped with a warning log rather
  than failing the whole import.

## Testing (manual, against dev HA instance)

1. Upgrade path: start with existing YAML → entry auto-created, repair
   issue shown, all entities present with **identical entity IDs**.
2. Remove YAML, restart → integration loads from storage alone.
3. Reload entry from UI → entities come back.
4. Clean instance: add via UI with valid and invalid host/password.
5. Devices visible in device registry, grouped per module under the hub.

## Out of scope (Phase 2)

- APPINFO bus discovery (`controller.scan()`) to auto-create devices.
- Options flow for adding/editing devices in the UI.
- Async rewrite of the python-domintell boundary.
- Automated tests.
