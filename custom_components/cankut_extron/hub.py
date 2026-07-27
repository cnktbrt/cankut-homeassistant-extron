"""TCP communication hub for the Cankut Extron integration."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from homeassistant.core import HomeAssistant

from .const import (
    PROJECTOR_STATE_OFF,
    PROJECTOR_STATE_ON,
    PROJECTOR_STATUS_COMMAND,
    RECONNECT_DELAY,
)

_LOGGER = logging.getLogger(__name__)


class ExtronHub:
    """Maintain the TCP connection between Home Assistant and Extron."""

    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
        self.hass = hass
        self.host = host
        self.port = port

        self.connected = False
        self.projector_is_on: bool | None = None

        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._connection_task: asyncio.Task | None = None
        self._write_lock = asyncio.Lock()
        self._listeners: list[Callable[[], None]] = []
        self._stopping = False

    async def async_start(self) -> None:
        """Start the persistent TCP connection task."""
        if self._connection_task is not None:
            return

        self._stopping = False
        self._connection_task = self.hass.async_create_task(
            self._connection_loop()
        )

    async def async_stop(self) -> None:
        """Stop the TCP connection task."""
        self._stopping = True

        if self._writer is not None:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except (ConnectionError, OSError):
                pass

        if self._connection_task is not None:
            self._connection_task.cancel()
            try:
                await self._connection_task
            except asyncio.CancelledError:
                pass
            self._connection_task = None

        self._reader = None
        self._writer = None
        self.connected = False
        self._notify_listeners()

    def add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register an entity update listener."""
        self._listeners.append(listener)

        def remove_listener() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return remove_listener

    async def async_send(self, command: str) -> bool:
        """Send one line to Extron."""
        writer = self._writer

        if not self.connected or writer is None or writer.is_closing():
            _LOGGER.warning("Extron bağlantısı yok; komut gönderilemedi: %s", command)
            return False

        try:
            async with self._write_lock:
                writer.write((command.strip() + "\r\n").encode("utf-8"))
                await writer.drain()
            return True
        except (ConnectionError, OSError) as err:
            _LOGGER.warning("Extron komutu gönderilemedi: %s", err)
            return False

    async def async_request_projector_status(self) -> bool:
        """Ask Extron for the current projector power state."""
        return await self.async_send(PROJECTOR_STATUS_COMMAND)

    async def _connection_loop(self) -> None:
        """Reconnect automatically and process incoming status messages."""
        while not self._stopping:
            try:
                _LOGGER.info(
                    "Extron cihazına bağlanılıyor: %s:%s", self.host, self.port
                )

                self._reader, self._writer = await asyncio.open_connection(
                    self.host,
                    self.port,
                )

                self.connected = True
                self._notify_listeners()
                _LOGGER.info("Extron bağlantısı kuruldu")

                await self.async_request_projector_status()

                while not self._stopping:
                    line_bytes = await self._reader.readline()

                    if not line_bytes:
                        raise ConnectionError("Extron TCP bağlantıyı kapattı")

                    message = line_bytes.decode(
                        "utf-8", errors="ignore"
                    ).strip()

                    if message:
                        self._handle_message(message)

            except asyncio.CancelledError:
                raise
            except (ConnectionError, OSError, asyncio.TimeoutError) as err:
                if not self._stopping:
                    _LOGGER.warning("Extron bağlantı hatası: %s", err)
            finally:
                self.connected = False

                if self._writer is not None:
                    self._writer.close()
                    try:
                        await self._writer.wait_closed()
                    except (ConnectionError, OSError):
                        pass

                self._reader = None
                self._writer = None
                self._notify_listeners()

            if not self._stopping:
                await asyncio.sleep(RECONNECT_DELAY)

    def _handle_message(self, message: str) -> None:
        """Interpret messages sent by Extron."""
        if message == PROJECTOR_STATE_ON:
            if self.projector_is_on is not True:
                self.projector_is_on = True
                self._notify_listeners()
            return

        if message == PROJECTOR_STATE_OFF:
            if self.projector_is_on is not False:
                self.projector_is_on = False
                self._notify_listeners()
            return

        _LOGGER.debug("Extron mesajı: %s", message)

    def _notify_listeners(self) -> None:
        """Notify all Home Assistant entities."""
        for listener in list(self._listeners):
            listener()
