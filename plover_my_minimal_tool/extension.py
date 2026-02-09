import json
from collections.abc import Callable
from importlib.metadata import metadata
from typing import Any

from jsonpickle import encode
from nacl_middleware import MailBox
from plover.engine import StenoEngine
from plover.gui_qt.paper_tape import TapeModel
from plover.steno import Stroke
from websocket import WebSocketApp

from plover_my_minimal_tool.client_config import ClientConfig
from plover_my_minimal_tool.config import BASE_WORKER_FQDN, WORKER_PROTOCOL
from plover_my_minimal_tool.extended_engine import ExtendedStenoEngine
from plover_my_minimal_tool.get_logger import get_logger
from plover_my_minimal_tool.lookup import lookup
from plover_my_minimal_tool.signal import Signal

log = get_logger("Extension")

SERVER_CONFIG_FILE = "plover_websocket_server_config.json"


class Extension:
    engine: ExtendedStenoEngine
    _tape_model: TapeModel

    def __init__(self, engine: StenoEngine):
        self.engine = ExtendedStenoEngine(engine)
        engine.my_minimal_extension = self

        self.engine.signals = [Signal("stroked"), Signal("translated")]
        self._config = ClientConfig(SERVER_CONFIG_FILE)  # reload the configuration when the server is restarted
        self.mail_boxes: dict[int, MailBox] = {}

        self._tape_model = TapeModel()
        self._tape_model.reset()

    def on_stroked(self, stroke: Stroke):
        # Minimal example: just log strokes
        log.info(f"Stroke: {stroke}")

    def on_translated(self, old, new):
        if new:
            log.info(f"Translated: {new}")

    def start(self):
        log.info("Extension initialised")

        # Example: Connect to stroke signals
        self.engine.connect_hooks(self)

    def stop(self):
        self.engine.disconnect_hooks(self)

    def _handle_tablet_connected(self, ws: WebSocketApp, tablet_id: int, public_key: str, on_tablet_connected: Callable[[], None] | None):
        log.debug(f"Private key: {self._config.private_key} and public key: {public_key}")
        self.mail_boxes[tablet_id] = MailBox(self._config.private_key, public_key)
        ws.send(
            json.dumps(
                {
                    "to": {"type": "tablet", "id": tablet_id},
                    "payload": {
                        "message": "Here is my the public key for you to privately communicate with me...",
                        "public_key": self._config.public_key,
                    },
                }
            )
        )
        if on_tablet_connected:
            on_tablet_connected()

    def _handle_stroke(self, ws: WebSocketApp, tablet_id: int, tablet_mail_box: MailBox, steno_keys: list):
        try:
            stroke = Stroke(steno_keys)
            stroke_json = encode(stroke, unpicklable=False)
            paper = self._tape_model._paper_format(stroke)

            data = {
                "keys": stroke.steno_keys,
                "stroked": stroke_json,
                "rtfcre": stroke.rtfcre,
                "paper": paper,
            }
            message = {"on_stroked": data}

            ws.send(
                json.dumps(
                    {
                        "to": {"type": "tablet", "id": tablet_id},
                        "payload": tablet_mail_box.box(message),
                    }
                )
            )

            self.engine._engine._machine_stroke_callback(steno_keys)
        except Exception:
            log.exception("Failed to process stroke")

    def _handle_lookup(self, ws: WebSocketApp, tablet_id: int, tablet_mail_box: MailBox, text_to_lookup: str):
        try:
            steno_options_per_word = lookup(self.engine._engine, text_to_lookup)
            ws.send(
                json.dumps(
                    {
                        "to": {"type": "tablet", "id": tablet_id},
                        "payload": tablet_mail_box.box({"lookup": steno_options_per_word}),
                    }
                )
            )
        except Exception:
            log.exception("Failed to process lookup request")

    def connect_websocket(self, connection_string: str, on_tablet_connected: Callable[[], None] | None = None):
        def on_message(ws: WebSocketApp, message: Any):
            if isinstance(message, str):
                message: dict = json.loads(message)
            log.debug(f"Received: {message}")
            msg_type = message.get("type")
            if msg_type == "tablet_connected":
                tablet_id = message.get("id")
                public_key = message.get("publicKey")
                self._handle_tablet_connected(ws, tablet_id, public_key, on_tablet_connected)
                return

            from_data: dict = message.get("from")
            if from_data and from_data.get("type") == "tablet":
                payload = message.get("payload")
                tablet_id = from_data.get("id")
                tablet_mail_box = self.mail_boxes.get(tablet_id)
                decrypted_payload = tablet_mail_box.unbox(payload)

                if "stroke" in decrypted_payload:
                    steno_keys = decrypted_payload["stroke"]
                    if isinstance(steno_keys, list):
                        self._handle_stroke(ws, tablet_id, tablet_mail_box, steno_keys)

                if "lookup" in decrypted_payload:
                    text_to_lookup = decrypted_payload["lookup"]
                    log.debug(f"Lookup request for: {text_to_lookup}")
                    if isinstance(text_to_lookup, str):
                        self._handle_lookup(ws, tablet_id, tablet_mail_box, text_to_lookup)

        def on_error(ws, error: Exception):
            log.exception(f"Error: {error}")

        def on_close(ws, close_status_code, close_msg):
            log.info("Closed")

        def on_open(ws):
            log.info("Opened")

        meta = metadata("plover-my-minimal-tool")
        header = {
            "User-Agent": f"{meta['Name']}/{meta['Version']}",
            "Origin": f"{WORKER_PROTOCOL}//{BASE_WORKER_FQDN}",
            "X-Public-Key": self._config.public_key,
        }
        log.info(header)
        ws = WebSocketApp(connection_string, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close, header=header)
        ws.run_forever(reconnect=5)
