from __future__ import annotations

from homeassistant.components.number import (
    NumberEntity,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
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
        [KramerVolumeNumber(coordinator, entry.entry_id)]
    )


class KramerVolumeNumber(ExtronEntity, NumberEntity):
    _attr_name = "Kramer VS-88H2A Ses Seviyesi"
    _attr_unique_id = "kramer_vs_88h2a_volume"
    _attr_icon = "mdi:volume-high"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("volume")

    async def async_set_native_value(self, value: float) -> None:
        level = max(0, min(100, round(value)))
        await self.coordinator.async_send(
            f"MATRIX_VOLUME_SET:{level}"
        )
