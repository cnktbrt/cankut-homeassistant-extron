DOMAIN = "extron_virtual_devices"

CONF_HOST = "host"
CONF_PORT = "port"

DEFAULT_PORT = 5000
DEFAULT_NAME = "Extron IPL PRO S3"

PLATFORMS = ["switch", "select", "number", "button", "text"]

OUTPUT_OPTIONS = {
    "Projeksiyon HDMI 1": 1,
    "Projeksiyon HDMI 2": 2,
    "Projeksiyon VGA": 3,
    "Mutfak TV": 4,
    "Çağlar TV Mutfak": 5,
    "Salon TV": 6,
    "Ercan TV": 7,
    "Çağlar TV Salon": 8,
}

INPUT_OPTIONS = {
    "Uydu": 1,
    "HDMI 2": 2,
    "XBOX": 3,
    "Apple TV": 4,
    "Giriş 5": 5,
    "Giriş 6": 6,
    "Giriş 7": 7,
    "Giriş 8": 8,
}

AUDIO_OPTIONS = dict(INPUT_OPTIONS)
