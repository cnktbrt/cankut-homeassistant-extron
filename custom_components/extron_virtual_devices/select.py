from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_ACTIVE_AUDIO,
    DATA_ACTIVE_INPUT,
    DATA_AVAILABLE,
    DATA_SELECTED_OUTPUT,
    DOMAIN,
    INPUT_OPTIONS,
    OUTPUT_OPTIONS,
)
from .coordinator import ExtronCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ExtronCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            MatrixSelectedOutputSelect(coordinator, entry),
            MatrixActiveInputSelect(coordinator, entry),
            MatrixActiveAudioSelect(coordinator, entry),
        ]
    )


class MatrixSelectBase(CoordinatorEntity[ExtronCoordinator], SelectEntity):
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


class MatrixSelectedOutputSelect(MatrixSelectBase):
    _attr_name = "Seçili Çıkış"
    _attr_icon = "mdi:video-output"
    _attr_options = OUTPUT_OPTIONS

    def __init__(
        self,
        coordinator: ExtronCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry, "selected_output")

    @property
    def current_option(self) -> str | None:
        return self.coordinator.data[DATA_SELECTED_OUTPUT]

    async def async_select_option(self, option: str) -> None:
        self.coordinator.select_output(option)
        await self.coordinator.async_query_selected_output()


class MatrixActiveInputSelect(MatrixSelectBase):
    _attr_name = "Aktif Giriş"
    _attr_icon = "mdi:video-input-hdmi"
    _attr_options = INPUT_OPTIONS

    def __init__(
        self,
        coordinator: ExtronCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry, "active_input")

    @property
    def current_option(self) -> str | None:
        return self.coordinator.data[DATA_ACTIVE_INPUT]

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_video_input(option)


class MatrixActiveAudioSelect(MatrixSelectBase):
    _attr_name = "Aktif Ses"
    _attr_icon = "mdi:volume-high"
    _attr_options = INPUT_OPTIONS

    def __init__(
        self,
        coordinator: ExtronCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry, "active_audio")

    @property
    def current_option(self) -> str | None:
        return self.coordinator.data[DATA_ACTIVE_AUDIO]

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_audio_input(option)
