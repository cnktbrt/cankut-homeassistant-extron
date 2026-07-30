from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ExtronCoordinator


class ExtronEntity(CoordinatorEntity[ExtronCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: ExtronCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Extron IPL PRO S3",
            manufacturer="Extron",
            model="IPL PRO S3",
        )

    @property
    def available(self) -> bool:
        return bool(self.coordinator.data.get("available"))
