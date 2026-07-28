from __future__ import annotations

import asyncio
import socket
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from .const import DEFAULT_PORT, DOMAIN


async def _test_connection(host: str, port: int) -> bool:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=5,
        )
        writer.write(b"PING\r\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return True
    except (OSError, asyncio.TimeoutError, socket.gaierror):
        return False


class ExtronVirtualDevicesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

            if await _test_connection(host, port):
                return self.async_create_entry(
                    title="Extron IPL PRO S3",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                    },
                )

            errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default="192.168.4.74"): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
