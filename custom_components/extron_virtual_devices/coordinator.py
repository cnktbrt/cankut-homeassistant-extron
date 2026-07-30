from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class ExtronCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Extron Virtual Devices",
        )
        self.host = host
        self.port = port

        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._connection_task: asyncio.Task | None = None
        self._send_lock = asyncio.Lock()
        self._stopping = False

        self.data = {
            "available": False,
            "projector_power": None,
            "selected_output": 1,
            "routes": {},
            "audio_input": None,
            "volume": None,
            "mute": None,
        }

    async def async_start(self) -> None:
        self._stopping = False
        self._connection_task = self.hass.async_create_task(
            self._connection_loop()
        )

    async def async_stop(self) -> None:
        self._stopping = True

        if self._connection_task is not None:
            self._connection_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._connection_task

        await self._close_connection()

    async def _connection_loop(self) -> None:
        delays = (2, 5, 10, 30, 60)
        delay_index = 0

        while not self._stopping:
            try:
                self._reader, self._writer = await asyncio.open_connection(
                    self.host,
                    self.port,
                )

                delay_index = 0
                self._set_value("available", True)
                _LOGGER.info(
                    "Extron TCP bağlantısı kuruldu: %s:%s",
                    self.host,
                    self.port,
                )

                await self._initial_sync()
                await self._read_loop()

            except asyncio.CancelledError:
                raise
            except Exception as error:
                _LOGGER.warning("Extron bağlantı hatası: %s", error)
            finally:
                await self._close_connection()
                self._set_value("available", False)

            if self._stopping:
                break

            delay = delays[min(delay_index, len(delays) - 1)]
            delay_index += 1
            await asyncio.sleep(delay)

    async def _read_loop(self) -> None:
        assert self._reader is not None

        while not self._stopping:
            raw = await self._reader.readline()

            if not raw:
                raise ConnectionError("Extron TCP bağlantısı kapandı")

            line = raw.decode("utf-8", errors="ignore").strip()

            if line:
                self._handle_line(line)

    async def _initial_sync(self) -> None:
        await self.async_send("PING")
        await self.async_send("PROJECTOR_STATUS")

        for output_number in range(1, 9):
            await self.async_send(f"MATRIX_QUERY:{output_number}")

        await self.async_send("MATRIX_AUDIO_QUERY")
        await self.async_send("MATRIX_VOLUME_QUERY")

    async def async_send(self, command: str) -> None:
        async with self._send_lock:
            writer = self._writer

            if writer is None or writer.is_closing():
                raise ConnectionError("Extron TCP bağlantısı hazır değil")

            writer.write(f"{command}\r\n".encode("utf-8"))
            await writer.drain()
            _LOGGER.debug("Extron'a gönderildi: %s", command)

    def select_output(self, output_number: int) -> None:
        self._set_value("selected_output", output_number)

        route = self.data["routes"].get(output_number)
        if route is not None:
            self.async_set_updated_data({**self.data})

    def _set_value(self, key: str, value: Any) -> None:
        new_data = {**self.data, key: value}
        self.async_set_updated_data(new_data)

    def _handle_line(self, line: str) -> None:
        upper = line.upper()
        _LOGGER.debug("Extron'dan geldi: %s", upper)

        if upper == "PROJECTOR_STATE:ON":
            self._set_value("projector_power", True)
            return

        if upper == "PROJECTOR_STATE:OFF":
            self._set_value("projector_power", False)
            return

        if upper.startswith("MATRIX_STATE:"):
            parts = upper.split(":")

            if (
                len(parts) == 3
                and parts[1].isdigit()
                and parts[2].isdigit()
            ):
                output_number = int(parts[1])
                input_number = int(parts[2])
                routes = dict(self.data["routes"])
                routes[output_number] = input_number
                self._set_value("routes", routes)
            return

        if upper.startswith("MATRIX_AUDIO_STATE:"):
            value = upper.rsplit(":", 1)[-1]

            if value.isdigit():
                self._set_value("audio_input", int(value))
            return

        if upper.startswith("MATRIX_VOLUME_STATE:"):
            value = upper.rsplit(":", 1)[-1]

            if value.isdigit():
                level = int(value)

                if 0 <= level <= 100:
                    new_data = {
                        **self.data,
                        "volume": level,
                        "mute": level == 0,
                    }
                    self.async_set_updated_data(new_data)
            return

        if upper == "MATRIX_MUTE_STATE:ON":
            self._set_value("mute", True)
            return

        if upper == "MATRIX_MUTE_STATE:OFF":
            self._set_value("mute", False)
            return

        if upper.startswith("ERROR:"):
            _LOGGER.warning("Extron hata cevabı: %s", line)

    async def _close_connection(self) -> None:
        writer = self._writer
        self._reader = None
        self._writer = None

        if writer is not None:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()
