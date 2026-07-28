from __future__ import annotations
import asyncio
from collections.abc import Callable
from homeassistant.core import HomeAssistant
from .const import *

class ExtronHub:
    def __init__(self, hass: HomeAssistant, host: str, port: int, used_inputs: list[str], used_outputs: list[str], input_names: dict[str, str], output_names: dict[str, str]) -> None:
        self.hass, self.host, self.port = hass, host, port
        self.used_inputs, self.used_outputs = used_inputs, used_outputs
        self.input_names, self.output_names = input_names, output_names
        self.connected = False
        self.projector_is_on = None
        self.selected_output = used_outputs[0] if used_outputs else None
        self.matrix_routes = {}
        self._reader = self._writer = None
        self._connection_task = self._poll_task = None
        self._write_lock = asyncio.Lock()
        self._listeners: list[Callable[[], None]] = []
        self._stopping = False

    @property
    def output_options(self):
        return [self.output_names[n] for n in self.used_outputs if n in self.output_names]

    @property
    def input_options(self):
        return [self.input_names[n] for n in self.used_inputs if n in self.input_names]

    @property
    def selected_output_name(self):
        return self.output_names.get(self.selected_output) if self.selected_output else None

    @property
    def active_input_name(self):
        n = self.matrix_routes.get(self.selected_output) if self.selected_output else None
        return self.input_names.get(n) if n else None

    def output_number_from_name(self, name):
        return next((n for n in self.used_outputs if self.output_names.get(n) == name), None)

    def input_number_from_name(self, name):
        return next((n for n in self.used_inputs if self.input_names.get(n) == name), None)

    async def async_start(self):
        self._stopping = False
        self._connection_task = self.hass.async_create_task(self._connection_loop())
        self._poll_task = self.hass.async_create_task(self._poll_loop())

    async def async_stop(self):
        self._stopping = True
        for task in (self._connection_task, self._poll_task):
            if task:
                task.cancel()
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except (ConnectionError, OSError):
                pass
        for task in (self._connection_task, self._poll_task):
            if task:
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self.connected = False
        self._notify()

    def add_listener(self, listener):
        self._listeners.append(listener)
        def remove():
            if listener in self._listeners:
                self._listeners.remove(listener)
        return remove

    async def async_send(self, command: str) -> bool:
        if not self.connected or not self._writer or self._writer.is_closing():
            return False
        try:
            async with self._write_lock:
                self._writer.write((command.strip() + "\r\n").encode())
                await self._writer.drain()
            return True
        except (ConnectionError, OSError):
            return False

    async def async_request_projector_status(self):
        return await self.async_send(PROJECTOR_STATUS_COMMAND)

    async def async_select_output(self, n):
        if n not in self.used_outputs:
            return False
        self.selected_output = n
        self._notify()
        return await self.async_query_matrix_output(n)

    async def async_set_matrix_route(self, out_n, in_n):
        if out_n not in self.used_outputs or in_n not in self.used_inputs:
            return False
        return await self.async_send(f"{MATRIX_SET_PREFIX}:{out_n}:{in_n}")

    async def async_query_matrix_output(self, out_n):
        if out_n not in self.used_outputs:
            return False
        return await self.async_send(f"{MATRIX_QUERY_PREFIX}:{out_n}")

    async def _connection_loop(self):
        while not self._stopping:
            try:
                self._reader, self._writer = await asyncio.open_connection(self.host, self.port)
                self.connected = True
                self._notify()
                await self.async_request_projector_status()
                for out_n in self.used_outputs:
                    await self.async_query_matrix_output(out_n)
                    await asyncio.sleep(0.1)
                while not self._stopping:
                    raw = await self._reader.readline()
                    if not raw:
                        raise ConnectionError
                    msg = raw.decode(errors="ignore").strip()
                    if msg:
                        self._handle(msg)
            except asyncio.CancelledError:
                raise
            except (ConnectionError, OSError, asyncio.TimeoutError):
                pass
            finally:
                self.connected = False
                if self._writer:
                    self._writer.close()
                    try:
                        await self._writer.wait_closed()
                    except (ConnectionError, OSError):
                        pass
                self._reader = self._writer = None
                self._notify()
            if not self._stopping:
                await asyncio.sleep(RECONNECT_DELAY)

    async def _poll_loop(self):
        while not self._stopping:
            await asyncio.sleep(MATRIX_POLL_SECONDS)
            if self.connected and self.selected_output:
                await self.async_query_matrix_output(self.selected_output)

    def _handle(self, msg):
        if msg == PROJECTOR_STATE_ON:
            self.projector_is_on = True
            self._notify()
            return
        if msg == PROJECTOR_STATE_OFF:
            self.projector_is_on = False
            self._notify()
            return
        if msg.startswith(MATRIX_STATE_PREFIX + ":"):
            parts = msg.split(":")
            if len(parts) == 3:
                self.matrix_routes[parts[1]] = parts[2]
                self._notify()

    def _notify(self):
        for listener in list(self._listeners):
            listener()
