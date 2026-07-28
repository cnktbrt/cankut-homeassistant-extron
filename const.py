from homeassistant.components.select import SelectEntity
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    if hub.used_inputs and hub.used_outputs:
        async_add_entities([MatrixOutputSelect(hub), MatrixInputSelect(hub)])

class MatrixBase:
    _attr_has_entity_name = True
    def __init__(self, hub):
        self._hub = hub
        self._remove = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{hub.host}:{hub.port}:kramer_vs88h2a")},
            name="Kramer VS-88H2A",
            manufacturer="Kramer",
            model="VS-88H2A",
            via_device=(DOMAIN, f"{hub.host}:{hub.port}"),
        )
    @property
    def available(self):
        return self._hub.connected
    async def async_added_to_hass(self):
        self._remove = self._hub.add_listener(self._update)
    async def async_will_remove_from_hass(self):
        if self._remove:
            self._remove()
    @callback
    def _update(self):
        self.async_write_ha_state()

class MatrixOutputSelect(MatrixBase, SelectEntity):
    _attr_name = "Seçili Çıkış"
    _attr_icon = "mdi:video-output"
    _attr_suggested_object_id = "matrix_selected_output"
    def __init__(self, hub):
        super().__init__(hub)
        self._attr_unique_id = f"{hub.host}_{hub.port}_matrix_selected_output"
    @property
    def options(self):
        return self._hub.output_options
    @property
    def current_option(self):
        return self._hub.selected_output_name
    async def async_select_option(self, option):
        n = self._hub.output_number_from_name(option)
        if n is None or not await self._hub.async_select_output(n):
            raise HomeAssistantError("Matrix çıkışı seçilemedi.")

class MatrixInputSelect(MatrixBase, SelectEntity):
    _attr_name = "Aktif Giriş"
    _attr_icon = "mdi:video-input-hdmi"
    _attr_suggested_object_id = "matrix_active_input"
    def __init__(self, hub):
        super().__init__(hub)
        self._attr_unique_id = f"{hub.host}_{hub.port}_matrix_active_input"
    @property
    def options(self):
        return self._hub.input_options
    @property
    def current_option(self):
        return self._hub.active_input_name
    async def async_select_option(self, option):
        out_n = self._hub.selected_output
        in_n = self._hub.input_number_from_name(option)
        if not out_n:
            raise HomeAssistantError("Önce output seçin.")
        if in_n is None or not await self._hub.async_set_matrix_route(out_n, in_n):
            raise HomeAssistantError("Matrix komutu gönderilemedi.")
