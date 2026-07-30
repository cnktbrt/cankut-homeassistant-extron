from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_AVAILABLE, DATA_VOLUME_LEVEL, DOMAIN
from .coordinator import ExtronCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ExtronCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MatrixVolumeNumber(coordinator, entry)])


class MatrixVolumeNumber(CoordinatorEntity[ExtronCoordinator], NumberEntity):
    _attr_has_entity_name = True
    _attr_name = "Ses Seviyesi"
    _attr_icon = "mdi:tune-vertical"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: ExtronCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_matrix_volume"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_matrix")},
            name="Kramer VS-88H2A",
            manufacturer="Kramer",
            model="VS-88H2A",
            via_device=(DOMAIN, entry.entry_id),
        )

    @property
    def available(self) -> bool:
        return bool(self.coordinator.data[DATA_AVAILABLE])

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data[DATA_VOLUME_LEVEL]

    async def async_set_native_value(self, value: float) -> None:
        level = max(0, min(100, round(value)))
        await self.coordinator.async_set_volume(level)
