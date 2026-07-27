"""Switch platform for the Epson projector connected to Extron."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    PROJECTOR_OFF_COMMAND,
    PROJECTOR_ON_COMMAND,
)
from .hub import ExtronHub


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the projector switch."""
    hub: ExtronHub = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [ExtronProjectorSwitch(hub)],
        update_before_add=False,
    )


class ExtronProjectorSwitch(SwitchEntity):
    """Epson TW6100 projector power switch."""

    _attr_has_entity_name = True
    _attr_name = "Güç"
    _attr_icon = "mdi:projector"

    def __init__(self, hub: ExtronHub) -> None:
        self._hub = hub
        self._attr_unique_id = (
            f"{hub.host}_{hub.port}_epson_tw6100_power"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    f"{hub.host}:{hub.port}:epson_tw6100",
                )
            },
            name="Projeksiyon",
            manufacturer="Epson",
            model="TW6100",
            via_device=(DOMAIN, f"{hub.host}:{hub.port}"),
        )
        self._remove_listener = None

    @property
    def available(self) -> bool:
        """Return whether the Extron TCP connection is active."""
        return self._hub.connected

    @property
    def is_on(self) -> bool | None:
        """Return the actual state reported by the projector."""
        return self._hub.projector_is_on

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the projector on."""
        sent = await self._hub.async_send(PROJECTOR_ON_COMMAND)

        if not sent:
            raise HomeAssistantError(
                "Extron bağlantısı olmadığı için projeksiyon açılamadı."
            )

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the projector off."""
        sent = await self._hub.async_send(PROJECTOR_OFF_COMMAND)

        if not sent:
            raise HomeAssistantError(
                "Extron bağlantısı olmadığı için projeksiyon kapatılamadı."
            )

    async def async_added_to_hass(self) -> None:
        """Subscribe to Extron state changes."""
        self._remove_listener = self._hub.add_listener(
            self._handle_hub_update
        )
        await self._hub.async_request_projector_status()

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe when the entity is removed."""
        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None

    @callback
    def _handle_hub_update(self) -> None:
        """Write the latest Extron state into Home Assistant."""
        self.async_write_ha_state()
