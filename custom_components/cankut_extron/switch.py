from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, PROJECTOR_ON_COMMAND, PROJECTOR_OFF_COMMAND

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([ProjectorSwitch(hass.data[DOMAIN][entry.entry_id])])

class ProjectorSwitch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_name = "Güç"
    _attr_icon = "mdi:projector"
    _attr_suggested_object_id = "projector_power"

    def __init__(self, hub):
        self._hub = hub
        self._remove = None
        self._attr_unique_id = f"{hub.host}_{hub.port}_epson_tw6100_power"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{hub.host}:{hub.port}:epson_tw6100")},
            name="Projeksiyon",
            manufacturer="Epson",
            model="TW6100",
            via_device=(DOMAIN, f"{hub.host}:{hub.port}"),
        )

    @property
    def available(self):
        return self._hub.connected

    @property
    def is_on(self):
        return self._hub.projector_is_on

    async def async_turn_on(self, **kwargs):
        if not await self._hub.async_send(PROJECTOR_ON_COMMAND):
            raise HomeAssistantError("Extron bağlantısı yok.")

    async def async_turn_off(self, **kwargs):
        if not await self._hub.async_send(PROJECTOR_OFF_COMMAND):
            raise HomeAssistantError("Extron bağlantısı yok.")

    async def async_added_to_hass(self):
        self._remove = self._hub.add_listener(self._update)
        await self._hub.async_request_projector_status()

    async def async_will_remove_from_hass(self):
        if self._remove:
            self._remove()

    @callback
    def _update(self):
        self.async_write_ha_state()
