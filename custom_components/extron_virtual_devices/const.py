DOMAIN = "extron_virtual_devices"

CONF_HOST = "host"
CONF_PORT = "port"

DEFAULT_PORT = 5000

PLATFORMS = ["switch", "select", "number", "button", "text"]

DATA_PROJECTOR_POWER = "projector_power"
DATA_SELECTED_OUTPUT = "selected_output"
DATA_ACTIVE_INPUT = "active_input"
DATA_ACTIVE_AUDIO = "active_audio"
DATA_VOLUME_LEVEL = "volume_level"
DATA_MUTE_STATE = "mute_state"
DATA_CODE_SEND = "code_send"
DATA_AVAILABLE = "available"

OUTPUT_OPTIONS = [f"Output {number}" for number in range(1, 9)]
INPUT_OPTIONS = [f"Input {number}" for number in range(1, 9)]
