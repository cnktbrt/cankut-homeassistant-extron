from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_AVAILABLE, DOMAIN
from .coordinator import ExtronCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ExtronCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            MatrixVolumeDownButton(coordinator, entry),
            MatrixVolumeUpButton(coordinator, entry),
        ]
    )


class MatrixButtonBase(CoordinatorEntity[ExtronCoordinator], ButtonEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ExtronCoordinator,
        entry: ConfigEntry,
        suffix: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{suffix}"
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


class MatrixVolumeDownButton(MatrixButtonBase):
    _attr_name = "Ses Kıs"
    _attr_icon = "mdi:volume-minus"

    def __init__(self, coordinator: ExtronCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "matrix_volume_down")

    async def async_press(self) -> None:
        await self.coordinator.async_volume_down()


class MatrixVolumeUpButton(MatrixButtonBase):
    _attr_name = "Ses Aç"
    _attr_icon = "mdi:volume-plus"

    def __init__(self, coordinator: ExtronCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "matrix_volume_up")

    async def async_press(self) -> None:
        await self.coordinator.async_volume_up()
