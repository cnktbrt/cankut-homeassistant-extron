from extronlib.interface import EthernetServerInterfaceEx, SerialInterface
from extronlib.system import Timer
from extronlib import event
from extronlib.device import ProcessorDevice

# ============================================================
# DONANIM
# ============================================================

processor = ProcessorDevice("ProcessorAlias")

projector = SerialInterface(
    processor,
    "COM1",
    Baud=9600,
    Data=8,
    Parity="None",
    Stop=1,
    FlowControl="Off",
)

matrix = SerialInterface(
    processor,
    "COM2",
    Baud=115200,
    Data=8,
    Parity="None",
    Stop=1,
    FlowControl="Off",
)

server = EthernetServerInterfaceEx(5000, "TCP")

clients = []
client_buffers = {}
projector_buffer = ""
matrix_buffer = ""

last_projector_state = None
last_matrix_routes = {}
last_audio_input = None


# ============================================================
# TCP YARDIMCILARI
# ============================================================

def send_to_client(client, message):
    try:
        client.Send("{}\r\n".format(message))
        print("HA'YA GONDERILDI: {}".format(message))
    except Exception as error:
        print("HA GONDERME HATASI: {}".format(error))


def broadcast(message):
    for client in list(clients):
        send_to_client(client, message)


# ============================================================
# PROJEKSIYON
# ============================================================

def projector_on():
    print("EPSON KOMUTU: PWR ON")
    projector.Send("PWR ON\r")


def projector_off():
    print("EPSON KOMUTU: PWR OFF")
    projector.Send("PWR OFF\r")


def projector_status():
    print("EPSON STATUS SORGUSU: PWR?")
    projector.Send("PWR?\r")


def publish_projector_state(state):
    global last_projector_state

    if state not in ("ON", "OFF"):
        return

    last_projector_state = state
    broadcast("PROJECTOR_STATE:{}".format(state))


# ============================================================
# KRAMER VIDEO
# ============================================================

def matrix_query(output_number):
    command = "#VID? {}\r".format(output_number)
    print("KRAMER STATUS SORGUSU: {}".format(command.strip()))
    matrix.Send(command)


def matrix_set(output_number, input_number):
    command = "#AV {}>{}\r".format(input_number, output_number)
    print("KRAMER VIDEO KOMUTU: {}".format(command.strip()))
    matrix.Send(command)


def publish_matrix_route(output_number, input_number):
    last_matrix_routes[output_number] = input_number
    broadcast(
        "MATRIX_STATE:{}:{}".format(
            output_number,
            input_number,
        )
    )


# ============================================================
# KRAMER HARICI SES
# ============================================================

def matrix_audio_set(input_number):
    command = "#EXT-AUD 0,1,1,{}\r".format(input_number)
    print("KRAMER SES KOMUTU: {}".format(command.strip()))
    matrix.Send(command)


def matrix_audio_query():
    # Kramer cihazında sorgu sözdizimi firmware'e göre farklılık gösterebilir.
    # Önce mevcut EXT-AUD durumunu istemek için bu biçim denenir.
    command = "#EXT-AUD?\r"
    print("KRAMER SES STATUS SORGUSU: {}".format(command.strip()))
    matrix.Send(command)


def publish_audio_state(input_number):
    global last_audio_input

    last_audio_input = input_number
    broadcast("MATRIX_AUDIO_STATE:{}".format(input_number))


# ============================================================
# HOME ASSISTANT KOMUT PARSER
# ============================================================

def handle_ha_command(client, raw_command):
    command = raw_command.strip()
    upper_command = command.upper()

    if not upper_command:
        return

    print("HA KOMUTU: {}".format(upper_command))

    if upper_command == "PING":
        send_to_client(client, "PONG")
        return

    if upper_command == "PROJECTOR_ON":
        projector_on()
        send_to_client(client, "OK:PROJECTOR_ON")
        return

    if upper_command == "PROJECTOR_OFF":
        projector_off()
        send_to_client(client, "OK:PROJECTOR_OFF")
        return

    if upper_command == "PROJECTOR_STATUS":
        projector_status()

        if last_projector_state is not None:
            send_to_client(
                client,
                "PROJECTOR_STATE:{}".format(last_projector_state),
            )
        return

    if upper_command.startswith("MATRIX_QUERY:"):
        parts = upper_command.split(":")

        if len(parts) != 2 or not parts[1].isdigit():
            send_to_client(client, "ERROR:MATRIX_QUERY_FORMAT")
            return

        output_number = int(parts[1])

        if output_number < 1 or output_number > 8:
            send_to_client(client, "ERROR:MATRIX_OUTPUT_RANGE")
            return

        matrix_query(output_number)
        send_to_client(
            client,
            "OK:MATRIX_QUERY:{}".format(output_number),
        )
        return

    if upper_command.startswith("MATRIX_SET:"):
        parts = upper_command.split(":")

        if (
            len(parts) != 3
            or not parts[1].isdigit()
            or not parts[2].isdigit()
        ):
            send_to_client(client, "ERROR:MATRIX_SET_FORMAT")
            return

        output_number = int(parts[1])
        input_number = int(parts[2])

        if output_number < 1 or output_number > 8:
            send_to_client(client, "ERROR:MATRIX_OUTPUT_RANGE")
            return

        if input_number < 1 or input_number > 8:
            send_to_client(client, "ERROR:MATRIX_INPUT_RANGE")
            return

        matrix_set(output_number, input_number)
        send_to_client(
            client,
            "OK:MATRIX_SET:{}:{}".format(
                output_number,
                input_number,
            ),
        )
        return

    if upper_command.startswith("MATRIX_AUDIO:"):
        parts = upper_command.split(":")

        if len(parts) != 2 or not parts[1].isdigit():
            send_to_client(client, "ERROR:MATRIX_AUDIO_FORMAT")
            return

        input_number = int(parts[1])

        if input_number < 1 or input_number > 8:
            send_to_client(client, "ERROR:MATRIX_AUDIO_RANGE")
            return

        matrix_audio_set(input_number)
        send_to_client(
            client,
            "OK:MATRIX_AUDIO:{}".format(input_number),
        )
        return

    if upper_command == "MATRIX_AUDIO_QUERY":
        matrix_audio_query()

        if last_audio_input is not None:
            send_to_client(
                client,
                "MATRIX_AUDIO_STATE:{}".format(last_audio_input),
            )
        return

    send_to_client(client, "ERROR:UNKNOWN_COMMAND")


# ============================================================
# TCP OLAYLARI
# ============================================================

@event(server, "Connected")
def client_connected(client, state):
    if client not in clients:
        clients.append(client)

    client_buffers[client] = ""

    print("CLIENT BAGLANDI: {}".format(client.IPAddress))

    if last_projector_state is not None:
        send_to_client(
            client,
            "PROJECTOR_STATE:{}".format(last_projector_state),
        )

    if last_audio_input is not None:
        send_to_client(
            client,
            "MATRIX_AUDIO_STATE:{}".format(last_audio_input),
        )


@event(server, "Disconnected")
def client_disconnected(client, state):
    if client in clients:
        clients.remove(client)

    if client in client_buffers:
        del client_buffers[client]

    print("CLIENT AYRILDI")


@event(server, "ReceiveData")
def client_receive(client, data):
    text = client_buffers.get(client, "")
    text += data.decode("utf-8", errors="ignore")

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")

    client_buffers[client] = lines.pop()

    for line in lines:
        if line.strip():
            handle_ha_command(client, line)


# ============================================================
# EPSON FEEDBACK
# ============================================================

@event(projector, "ReceiveData")
def projector_receive(interface, data):
    global projector_buffer

    projector_buffer += data.decode("utf-8", errors="ignore")
    projector_buffer = projector_buffer.replace("\r\n", "\n")
    projector_buffer = projector_buffer.replace("\r", "\n")

    lines = projector_buffer.split("\n")
    projector_buffer = lines.pop()

    for line in lines:
        response = line.strip().upper()

        if not response:
            continue

        print("EPSON GELEN: {}".format(response))

        if "PWR=01" in response:
            publish_projector_state("ON")
        elif "PWR=00" in response:
            publish_projector_state("OFF")


# ============================================================
# KRAMER FEEDBACK
# ============================================================

def parse_kramer_line(response):
    upper_response = response.strip().upper()

    if not upper_response:
        return

    print("KRAMER GELEN: {}".format(upper_response))

    # Örnek:
    # ~01@VID 5>2
    # ~01@AV 5>2
    if "@VID " in upper_response or "@AV " in upper_response:
        route_text = upper_response.split(" ", 1)[1]

        if ">" in route_text:
            input_text, output_text = route_text.split(">", 1)

            input_text = "".join(
                character for character in input_text if character.isdigit()
            )
            output_text = "".join(
                character for character in output_text if character.isdigit()
            )

            if input_text and output_text:
                publish_matrix_route(
                    int(output_text),
                    int(input_text),
                )
        return

    # Örnek:
    # ~01@EXT-AUD 0,1,1,4
    if "@EXT-AUD " in upper_response:
        values_text = upper_response.split("@EXT-AUD ", 1)[1]
        values = [value.strip() for value in values_text.split(",")]

        if len(values) >= 4:
            input_text = "".join(
                character
                for character in values[3]
                if character.isdigit()
            )

            if input_text:
                input_number = int(input_text)

                if 1 <= input_number <= 8:
                    publish_audio_state(input_number)
        return


@event(matrix, "ReceiveData")
def matrix_receive(interface, data):
    global matrix_buffer

    matrix_buffer += data.decode("utf-8", errors="ignore")
    matrix_buffer = matrix_buffer.replace("\r\n", "\n")
    matrix_buffer = matrix_buffer.replace("\r", "\n")

    lines = matrix_buffer.split("\n")
    matrix_buffer = lines.pop()

    for line in lines:
        parse_kramer_line(line)


# ============================================================
# PERIYODIK DURUM SORGULARI
# ============================================================

def poll_devices(timer, count):
    projector_status()

    # Seçili output HA tarafından ayrıca sorgulanır.
    # Burada 1-8 bütün video rotalarını senkron tutuyoruz.
    for output_number in range(1, 9):
        matrix_query(output_number)

    matrix_audio_query()


poll_timer = Timer(10, poll_devices)

server.StartListen()

print("TCP SERVER DINLEMEDE: PORT 5000")
print("EPSON COM1: 9600 8N1")
print("KRAMER COM2: 115200 8N1")
