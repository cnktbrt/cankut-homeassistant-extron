from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
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
        [KramerCodeSendText(coordinator, entry.entry_id)]
    )


class KramerCodeSendText(ExtronEntity, TextEntity):
    _attr_name = "Kramer VS-88H2A Code Send"
    _attr_unique_id = "kramer_vs_88h2a_code_send"
    _attr_icon = "mdi:console-line"
    _attr_mode = TextMode.TEXT
    _attr_native_min = 1
    _attr_native_max = 255
    _attr_pattern = r"^#[^\r\n]+$"

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator, entry_id)
        self._value = "#"

    @property
    def native_value(self) -> str:
        return self._value

    async def async_set_value(self, value: str) -> None:
        command = value.strip()

        if not command:
            return

        # Tek kutudan birden fazla komut gönderilmesini engelle.
        command = command.replace("\r", "").replace("\n", "")

        if not command.startswith("#"):
            raise ValueError("Kramer komutu # ile başlamalıdır")

        await self.coordinator.async_send(
            "MATRIX_RAW:{}".format(command)
        )

        self._value = command
        self.async_write_ha_state()
