import json
from collections.abc import Callable
from importlib.metadata import metadata
from typing import Any

from nacl_middleware import MailBox
from plover.engine import StenoEngine
from websocket import WebSocketApp

from plover_my_minimal_tool.client_config import ClientConfig
from plover_my_minimal_tool.config import BASE_WORKER_URL, PROTOCOL
from plover_my_minimal_tool.extended_engine import ExtendedStenoEngine
from plover_my_minimal_tool.get_logger import get_logger
from plover_my_minimal_tool.signal import Signal

log = get_logger("Extension")

SERVER_CONFIG_FILE = "plover_websocket_server_config.json"


class Extension:
    engine: ExtendedStenoEngine

    def __init__(self, engine: StenoEngine):
        self.engine = ExtendedStenoEngine(engine)
        engine.my_minimal_extension = self

        self.engine.signals = [Signal("stroked"), Signal("translated")]
        self._config = ClientConfig(SERVER_CONFIG_FILE)  # reload the configuration when the server is restarted
        self.mail_boxes: dict[int, MailBox] = {}

    def on_stroked(self, stroke):
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

    def connect_websocket(self, connection_string: str, on_tablet_connected: Callable[[], None] | None = None):
        # mail_box = MailBox(self._config.private_key, "tablet_public_key")

        def on_message(ws: WebSocketApp, message: Any):
            if isinstance(message, str):
                message: dict = json.loads(message)
            log.debug(f"Received: {message}")
            msg_type = message.get("type")
            if msg_type == "tablet_connected":
                tablet_id = message.get("id")
                public_key = message.get("publicKey")
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
                return

            from_data: dict = message.get("from")
            log.debug(f"From is {from_data}")
            if from_data and from_data.get("type") == "tablet":
                payload = message.get("payload")
                log.debug(f"Payload is: {payload}")
                tablet_id = from_data.get("id")
                log.debug(f"Tablet ID is: {tablet_id}")
                # decrypted_payload = self.mail_boxes[tablet_id].unbox(payload)

        def on_error(ws, error: Exception):
            log.exception(f"Error: {error}")

        def on_close(ws, close_status_code, close_msg):
            log.info("Closed")

        def on_open(ws):
            log.info("Opened")

        meta = metadata("plover-my-minimal-tool")
        header = {
            "User-Agent": f"{meta['Name']}/{meta['Version']}",
            "Origin": f"{PROTOCOL}//{BASE_WORKER_URL}",
            "X-Public-Key": self._config.public_key,
        }
        log.info(header)
        ws = WebSocketApp(connection_string, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close, header=header)
        ws.run_forever(reconnect=5)
