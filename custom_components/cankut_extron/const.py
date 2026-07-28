from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from .const import *
from .hub import ExtronHub

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hub = ExtronHub(
        hass,
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        list(entry.options.get(CONF_USED_INPUTS, DEFAULT_USED_INPUTS)),
        list(entry.options.get(CONF_USED_OUTPUTS, DEFAULT_USED_OUTPUTS)),
        dict(entry.options.get(CONF_INPUT_NAMES, DEFAULT_INPUT_NAMES)),
        dict(entry.options.get(CONF_OUTPUT_NAMES, DEFAULT_OUTPUT_NAMES)),
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub
    dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, f"{hub.host}:{hub.port}")},
        name="Extron IPL PRO S3",
        manufacturer="Extron",
        model="IPL PRO S3",
    )
    await hub.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hub = hass.data[DOMAIN].pop(entry.entry_id)
        await hub.async_stop()
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
    return ok
