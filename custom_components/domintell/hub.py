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
