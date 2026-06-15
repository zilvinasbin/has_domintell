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
