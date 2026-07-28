from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_AVAILABLE, DATA_PROJECTOR_POWER, DOMAIN
from .coordinator import ExtronCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ExtronCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ProjectorPowerSwitch(coordinator, entry)])


class ProjectorPowerSwitch(CoordinatorEntity[ExtronCoordinator], SwitchEntity):
    _attr_has_entity_name = True
    _attr_name = "Güç"
    _attr_icon = "mdi:projector"

    def __init__(
        self,
        coordinator: ExtronCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_projector_power"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_projector")},
            name="Epson TW6100",
            manufacturer="Epson",
            model="TW6100",
            via_device=(DOMAIN, entry.entry_id),
        )

    @property
    def available(self) -> bool:
        return bool(self.coordinator.data[DATA_AVAILABLE])

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data[DATA_PROJECTOR_POWER]

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_send("PROJECTOR_ON")

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_send("PROJECTOR_OFF")
