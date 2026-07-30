from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    AUDIO_OPTIONS,
    DOMAIN,
    INPUT_OPTIONS,
    OUTPUT_OPTIONS,
)
from .entity import ExtronEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            KramerOutputSelect(coordinator, entry.entry_id),
            KramerInputSelect(coordinator, entry.entry_id),
            KramerAudioInputSelect(coordinator, entry.entry_id),
        ]
    )


def _name_from_number(options: dict[str, int], number: int | None):
    if number is None:
        return None

    for name, value in options.items():
        if value == number:
            return name

    return None


class KramerOutputSelect(ExtronEntity, SelectEntity):
    _attr_name = "Kramer VS-88H2A Seçili Çıkış"
    _attr_unique_id = "kramer_vs_88h2a_selected_output"
    _attr_icon = "mdi:video-output"

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator, entry_id)
        self._attr_options = list(OUTPUT_OPTIONS)

    @property
    def current_option(self):
        return _name_from_number(
            OUTPUT_OPTIONS,
            self.coordinator.data.get("selected_output"),
        )

    async def async_select_option(self, option: str) -> None:
        output_number = OUTPUT_OPTIONS[option]
        self.coordinator.select_output(output_number)
        await self.coordinator.async_send(
            f"MATRIX_QUERY:{output_number}"
        )


class KramerInputSelect(ExtronEntity, SelectEntity):
    _attr_name = "Kramer VS-88H2A Aktif Giriş"
    _attr_unique_id = "kramer_vs_88h2a_active_input"
    _attr_icon = "mdi:video-input-hdmi"

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator, entry_id)
        self._attr_options = list(INPUT_OPTIONS)

    @property
    def current_option(self):
        output_number = self.coordinator.data.get("selected_output")
        input_number = self.coordinator.data["routes"].get(output_number)
        return _name_from_number(INPUT_OPTIONS, input_number)

    async def async_select_option(self, option: str) -> None:
        output_number = self.coordinator.data.get("selected_output", 1)
        input_number = INPUT_OPTIONS[option]

        await self.coordinator.async_send(
            f"MATRIX_SET:{output_number}:{input_number}"
        )


class KramerAudioInputSelect(ExtronEntity, SelectEntity):
    _attr_name = "Kramer VS-88H2A Aktif Ses"
    _attr_unique_id = "kramer_vs_88h2a_active_audio"
    _attr_icon = "mdi:audio-input-rca"

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator, entry_id)
        self._attr_options = list(AUDIO_OPTIONS)

    @property
    def current_option(self):
        return _name_from_number(
            AUDIO_OPTIONS,
            self.coordinator.data.get("audio_input"),
        )

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_send(
            f"MATRIX_AUDIO:{AUDIO_OPTIONS[option]}"
        )
