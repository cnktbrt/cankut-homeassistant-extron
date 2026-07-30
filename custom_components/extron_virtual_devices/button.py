from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import ExtronEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            KramerVolumeUpButton(coordinator, entry.entry_id),
            KramerVolumeDownButton(coordinator, entry.entry_id),
        ]
    )


class KramerVolumeUpButton(ExtronEntity, ButtonEntity):
    _attr_name = "Kramer VS-88H2A Ses Aç"
    _attr_unique_id = "kramer_vs_88h2a_volume_up"
    _attr_icon = "mdi:volume-plus"

    async def async_press(self) -> None:
        await self.coordinator.async_send("MATRIX_VOLUME_UP")


class KramerVolumeDownButton(ExtronEntity, ButtonEntity):
    _attr_name = "Kramer VS-88H2A Ses Kıs"
    _attr_unique_id = "kramer_vs_88h2a_volume_down"
    _attr_icon = "mdi:volume-minus"

    async def async_press(self) -> None:
        await self.coordinator.async_send("MATRIX_VOLUME_DOWN")
