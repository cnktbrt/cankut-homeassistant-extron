from __future__ import annotations
import asyncio, contextlib
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlowWithReload
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode, TextSelector, TextSelectorConfig
from .const import *

class CannotConnect(Exception):
    pass

async def _validate(host, port):
    writer = None
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), 5)
        writer.write(b"PING\r\n")
        await writer.drain()
        response = await asyncio.wait_for(reader.readline(), 5)
        if response.decode(errors="ignore").strip() != "PONG":
            raise CannotConnect
    except (ConnectionError, OSError, asyncio.TimeoutError) as err:
        raise CannotConnect from err
    finally:
        if writer:
            writer.close()
            with contextlib.suppress(ConnectionError, OSError):
                await writer.wait_closed()

class CankutExtronConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        return CankutExtronOptionsFlow()

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input:
            host, port = user_input[CONF_HOST].strip(), user_input[CONF_PORT]
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()
            try:
                await _validate(host, port)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=f"Extron IPL PRO S3 ({host})", data={CONF_HOST: host, CONF_PORT: port})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({
            vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
            vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
        }), errors=errors)

class CankutExtronOptionsFlow(OptionsFlowWithReload):
    def __init__(self):
        self._used_inputs = []
        self._used_outputs = []

    async def async_step_init(self, user_input=None):
        if user_input:
            self._used_inputs = sorted([str(x) for x in user_input[CONF_USED_INPUTS]], key=int)
            self._used_outputs = sorted([str(x) for x in user_input[CONF_USED_OUTPUTS]], key=int)
            return await self.async_step_names()
        opts = self.config_entry.options
        choices = [{"value": str(i), "label": str(i)} for i in range(1, 9)]
        return self.async_show_form(step_id="init", data_schema=vol.Schema({
            vol.Required(CONF_USED_INPUTS, default=list(opts.get(CONF_USED_INPUTS, DEFAULT_USED_INPUTS))): SelectSelector(SelectSelectorConfig(options=choices, multiple=True, mode=SelectSelectorMode.DROPDOWN)),
            vol.Required(CONF_USED_OUTPUTS, default=list(opts.get(CONF_USED_OUTPUTS, DEFAULT_USED_OUTPUTS))): SelectSelector(SelectSelectorConfig(options=choices, multiple=True, mode=SelectSelectorMode.DROPDOWN)),
        }))

    async def async_step_names(self, user_input=None):
        opts = self.config_entry.options
        old_in = dict(opts.get(CONF_INPUT_NAMES, DEFAULT_INPUT_NAMES))
        old_out = dict(opts.get(CONF_OUTPUT_NAMES, DEFAULT_OUTPUT_NAMES))
        if user_input:
            return self.async_create_entry(data={
                CONF_USED_INPUTS: self._used_inputs,
                CONF_USED_OUTPUTS: self._used_outputs,
                CONF_INPUT_NAMES: {n: user_input[f"input_{n}_name"].strip() or f"Input {n}" for n in self._used_inputs},
                CONF_OUTPUT_NAMES: {n: user_input[f"output_{n}_name"].strip() or f"Output {n}" for n in self._used_outputs},
            })
        fields = {}
        for n in self._used_inputs:
            fields[vol.Required(f"input_{n}_name", default=old_in.get(n, f"Input {n}"))] = TextSelector(TextSelectorConfig())
        for n in self._used_outputs:
            fields[vol.Required(f"output_{n}_name", default=old_out.get(n, f"Output {n}"))] = TextSelector(TextSelectorConfig())
        return self.async_show_form(step_id="names", data_schema=vol.Schema(fields))
