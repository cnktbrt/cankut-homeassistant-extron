from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_AVAILABLE, DATA_CODE_SEND, DOMAIN
from .coordinator import ExtronCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ExtronCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MatrixCodeSendText(coordinator, entry)])


class MatrixCodeSendText(CoordinatorEntity[ExtronCoordinator], TextEntity):
    _attr_has_entity_name = True
    _attr_name = "Code Send"
    _attr_icon = "mdi:console"
    _attr_mode = TextMode.TEXT
    _attr_native_min = 1
    _attr_native_max = 255
    _attr_pattern = r"^#.*"

    def __init__(
        self,
        coordinator: ExtronCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_matrix_code_send"
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
    def native_value(self) -> str:
        return self.coordinator.data[DATA_CODE_SEND]

    async def async_set_value(self, value: str) -> None:
        await self.coordinator.async_send_raw_matrix_code(value)
