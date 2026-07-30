from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DATA_ACTIVE_AUDIO,
    DATA_ACTIVE_INPUT,
    DATA_AVAILABLE,
    DATA_CODE_SEND,
    DATA_HDCP_MODE,
    DATA_MUTE_STATE,
    DATA_PROJECTOR_POWER,
    DATA_SELECTED_OUTPUT,
    DATA_VOLUME_LEVEL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ExtronCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )
        self.host = entry.data[CONF_HOST]
        self.port = entry.data[CONF_PORT]

        self.data = {
            DATA_AVAILABLE: False,
            DATA_PROJECTOR_POWER: None,
            DATA_SELECTED_OUTPUT: "Output 1",
            DATA_ACTIVE_INPUT: None,
            DATA_ACTIVE_AUDIO: None,
            DATA_VOLUME_LEVEL: None,
            DATA_MUTE_STATE: None,
            DATA_CODE_SEND: "",
            DATA_HDCP_MODE: None,
        }

        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._runner_task: asyncio.Task | None = None
        self._stopping = False
        self._write_lock = asyncio.Lock()

    async def async_start(self) -> None:
        self._stopping = False
        self._runner_task = self.hass.async_create_task(self._connection_loop())

    async def async_stop(self) -> None:
        self._stopping = True

        if self._runner_task:
            self._runner_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._runner_task
            self._runner_task = None

        await self._close_connection()

    async def _connection_loop(self) -> None:
        retry_delay = 2

        while not self._stopping:
            try:
                _LOGGER.info(
                    "Extron bağlantısı kuruluyor: %s:%s",
                    self.host,
                    self.port,
                )
                self._reader, self._writer = await asyncio.open_connection(
                    self.host,
                    self.port,
                )

                retry_delay = 2
                self._set_value(DATA_AVAILABLE, True)

                await self.async_send("PING")
                await self.async_send("PROJECTOR_STATUS")
                await self.async_send("MATRIX_QUERY:1")
                await self.async_send("MATRIX_AUDIO_QUERY")
                await self.async_send("MATRIX_VOLUME_QUERY")
                await self.async_send("MATRIX_HDCP_QUERY")

                while not self._stopping:
                    raw_line = await self._reader.readline()
                    if not raw_line:
                        raise ConnectionError("Extron TCP bağlantısı kapandı")

                    line = raw_line.decode("utf-8", errors="ignore").strip()
                    if line:
                        self._handle_line(line)

            except asyncio.CancelledError:
                raise
            except Exception as err:
                _LOGGER.warning("Extron bağlantı hatası: %s", err)
            finally:
                self._set_value(DATA_AVAILABLE, False)
                await self._close_connection()

            if not self._stopping:
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)

    async def _close_connection(self) -> None:
        writer = self._writer
        self._reader = None
        self._writer = None

        if writer is not None:
            writer.close()
            with suppress(Exception):
                await writer.wait_closed()

    async def async_send(self, command: str) -> None:
        async with self._write_lock:
            if self._writer is None or self._writer.is_closing():
                raise ConnectionError("Extron bağlantısı kullanılamıyor")

            payload = f"{command.strip()}\r\n".encode("utf-8")
            self._writer.write(payload)
            await self._writer.drain()
            _LOGGER.debug("Extron'a gönderildi: %s", command)

    def select_output(self, option: str) -> None:
        self._set_value(DATA_SELECTED_OUTPUT, option)

    async def async_query_selected_output(self) -> None:
        output_number = self._option_number(self.data[DATA_SELECTED_OUTPUT])
        await self.async_send(f"MATRIX_QUERY:{output_number}")

    async def async_set_video_input(self, option: str) -> None:
        output_number = self._option_number(self.data[DATA_SELECTED_OUTPUT])
        input_number = self._option_number(option)
        await self.async_send(f"MATRIX_SET:{output_number}:{input_number}")

    async def async_set_audio_input(self, option: str) -> None:
        input_number = self._option_number(option)
        await self.async_send(f"MATRIX_AUDIO:{input_number}")

    async def async_set_volume(self, level: int) -> None:
        await self.async_send(f"MATRIX_VOLUME_SET:{level}")

    async def async_volume_up(self) -> None:
        await self.async_send("MATRIX_VOLUME_UP")

    async def async_volume_down(self) -> None:
        await self.async_send("MATRIX_VOLUME_DOWN")

    async def async_mute_on(self) -> None:
        await self.async_send("MATRIX_MUTE_ON")

    async def async_mute_off(self) -> None:
        await self.async_send("MATRIX_MUTE_OFF")

    async def async_hdcp_on(self) -> None:
        await self.async_send("MATRIX_HDCP_ON")

    async def async_hdcp_off(self) -> None:
        await self.async_send("MATRIX_HDCP_OFF")

    async def async_send_raw_matrix_code(self, command: str) -> None:
        clean_command = command.strip().replace("\r", "").replace("\n", "")

        if not clean_command.startswith("#"):
            raise ValueError("Kramer komutu # ile başlamalıdır")

        self._set_value(DATA_CODE_SEND, clean_command)
        await self.async_send(f"MATRIX_RAW:{clean_command}")

    @staticmethod
    def _option_number(option: str) -> int:
        return int(option.rsplit(" ", 1)[1])

    def _handle_line(self, line: str) -> None:
        normalized = line.strip().upper()
        _LOGGER.debug("Extron'dan alındı: %s", normalized)

        if normalized in {"PONG", "OK:PING"}:
            self._set_value(DATA_AVAILABLE, True)
            return

        if normalized == "PROJECTOR_STATE:ON":
            self._set_value(DATA_PROJECTOR_POWER, True)
            return

        if normalized == "PROJECTOR_STATE:OFF":
            self._set_value(DATA_PROJECTOR_POWER, False)
            return

        if normalized.startswith("MATRIX_STATE:"):
            parts = normalized.split(":")
            if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
                output_number = int(parts[1])
                input_number = int(parts[2])

                selected_output = self._option_number(
                    self.data[DATA_SELECTED_OUTPUT]
                )
                if output_number == selected_output:
                    self._set_value(
                        DATA_ACTIVE_INPUT,
                        f"Input {input_number}",
                    )
            return

        if normalized.startswith("MATRIX_AUDIO_STATE:"):
            parts = normalized.split(":")
            if len(parts) == 2 and parts[1].isdigit():
                self._set_value(
                    DATA_ACTIVE_AUDIO,
                    f"Input {int(parts[1])}",
                )
            return

        if normalized.startswith("MATRIX_VOLUME_STATE:"):
            parts = normalized.split(":")
            if len(parts) == 2 and parts[1].isdigit():
                level = int(parts[1])
                if 0 <= level <= 100:
                    updated = dict(self.data)
                    updated[DATA_VOLUME_LEVEL] = level
                    updated[DATA_MUTE_STATE] = level == 0
                    self.async_set_updated_data(updated)
            return

        if normalized == "MATRIX_MUTE_STATE:ON":
            self._set_value(DATA_MUTE_STATE, True)
            return

        if normalized == "MATRIX_MUTE_STATE:OFF":
            self._set_value(DATA_MUTE_STATE, False)
            return

        if normalized == "MATRIX_HDCP_STATE:ON":
            self._set_value(DATA_HDCP_MODE, True)
            return

        if normalized == "MATRIX_HDCP_STATE:OFF":
            self._set_value(DATA_HDCP_MODE, False)
            return

    def _set_value(self, key: str, value) -> None:
        if self.data.get(key) == value:
            return

        updated = dict(self.data)
        updated[key] = value
        self.async_set_updated_data(updated)
