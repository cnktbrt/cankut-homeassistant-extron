"""Config flow for the Cankut Extron integration."""

from __future__ import annotations

import asyncio
import contextlib

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from .const import DEFAULT_HOST, DEFAULT_PORT, DOMAIN


class CannotConnect(Exception):
    """Raised when Home Assistant cannot connect to Extron."""


async def _validate_connection(host: str, port: int) -> None:
    """Connect to Extron and verify the TCP protocol with PING/PONG."""
    writer = None

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=5,
        )

        writer.write(b"PING\r\n")
        await writer.drain()

        response = await asyncio.wait_for(
            reader.readline(),
            timeout=5,
        )

        if response.decode("utf-8", errors="ignore").strip() != "PONG":
            raise CannotConnect

    except (ConnectionError, OSError, asyncio.TimeoutError) as err:
        raise CannotConnect from err
    finally:
        if writer is not None:
            writer.close()
            with contextlib.suppress(ConnectionError, OSError):
                await writer.wait_closed()


class CankutExtronConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle the Cankut Extron configuration flow."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> FlowResult:
        """Handle configuration started by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]

            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

            try:
                await _validate_connection(host, port)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"Extron IPL PRO S3 ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_HOST,
                    default=(
                        user_input.get(CONF_HOST, DEFAULT_HOST)
                        if user_input
                        else DEFAULT_HOST
                    ),
                ): str,
                vol.Required(
                    CONF_PORT,
                    default=(
                        user_input.get(CONF_PORT, DEFAULT_PORT)
                        if user_input
                        else DEFAULT_PORT
                    ),
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=1, max=65535),
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
