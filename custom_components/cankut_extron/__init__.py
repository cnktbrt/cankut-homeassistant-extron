"""Cankut Extron integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, PLATFORMS
from .hub import ExtronHub


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up Cankut Extron from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    hub = ExtronHub(hass, host, port)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, f"{host}:{port}")},
        name="Extron IPL PRO S3",
        manufacturer="Extron",
        model="IPL PRO S3",
    )

    await hub.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload a Cankut Extron config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unloaded:
        hub: ExtronHub = hass.data[DOMAIN].pop(entry.entry_id)
        await hub.async_stop()

        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

    return unloaded
