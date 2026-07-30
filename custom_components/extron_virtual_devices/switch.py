from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
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
            EpsonProjectorSwitch(coordinator, entry.entry_id),
            KramerMuteSwitch(coordinator, entry.entry_id),
        ]
    )


class EpsonProjectorSwitch(ExtronEntity, SwitchEntity):
    _attr_name = "Epson TW6100 Güç"
    _attr_unique_id = "epson_tw6100_power"
    _attr_icon = "mdi:projector"

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get("projector_power")

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_send("PROJECTOR_ON")

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_send("PROJECTOR_OFF")


class KramerMuteSwitch(ExtronEntity, SwitchEntity):
    _attr_name = "Kramer VS-88H2A Ses Mute"
    _attr_unique_id = "kramer_vs_88h2a_audio_mute"
    _attr_icon = "mdi:volume-mute"

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get("mute")

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_send("MATRIX_MUTE_ON")

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_send("MATRIX_MUTE_OFF")
