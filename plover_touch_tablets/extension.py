import json
import threading
import time
from collections.abc import Callable
from importlib.metadata import metadata
from typing import Any

from jsonpickle import encode
from nacl_middleware import MailBox
from plover.engine import StenoEngine
from plover.gui_qt.paper_tape import TapeModel
from plover.steno import Stroke
from websocket import WebSocketApp

from plover_touch_tablets.client_config import ClientConfig
from plover_touch_tablets.config import BASE_WORKER_FQDN, WORKER_PROTOCOL
from plover_touch_tablets.extended_engine import ExtendedStenoEngine
from plover_touch_tablets.get_logger import get_logger
from plover_touch_tablets.lookup import lookup
from plover_touch_tablets.signal import Signal

log = get_logger("Extension")

SERVER_CONFIG_FILE = "plover_websocket_server_config.json"


class Extension:
    engine: ExtendedStenoEngine
    _tape_model: TapeModel
    _ws: WebSocketApp | None

    def __init__(self, engine: StenoEngine):
        self.engine = ExtendedStenoEngine(engine)
        engine.my_minimal_extension = self

        self.engine.signals = [Signal("stroked"), Signal("translated")]
        self._config = ClientConfig(SERVER_CONFIG_FILE)
        self.mail_boxes: dict[int, MailBox] = {}

        self._tape_model = TapeModel()
        self._tape_model.reset()

        # ----- Idle keep‑alive attributes -----
        self._ws = None
        self._keep_alive_timer = None
        self._last_sent_time = 0.0
        self._idle_threshold = 30.0

    # ---------- Idle timer management ----------
    def _send_ping(self):
        """Send a ping if the connection is still open."""
        if not self._ws or not self._ws.sock or not self._ws.sock.connected:
            log.warning("⚠️ Cannot send ping – WebSocket not connected")
            return

        try:
            self._ws.send(json.dumps({"type": "ping"}))
            log.info("✅ Sent idle keep‑alive ping")
            # No need to call _update_last_sent() – it's already called by wrapped_send
        except Exception:
            log.exception("❌ Failed to send ping")

    def _update_last_sent(self):
        """Record that we just sent a message."""
        self._last_sent_time = time.time()

    def _start_keep_alive(self):
        """Start the keep-alive loop."""
        self._stop_keep_alive()
        self._keep_alive_loop()

    def _stop_keep_alive(self):
        """Stop the keep-alive loop."""
        if self._keep_alive_timer:
            self._keep_alive_timer.cancel()
            self._keep_alive_timer = None
            log.debug("🛑 Keep-alive timer stopped")

    def _keep_alive_loop(self):
        """Check if we need to send a ping, and schedule the next check."""
        if not self._ws:
            return

        now = time.time()
        delta = now - self._last_sent_time

        if delta >= self._idle_threshold:
            self._send_ping()
            next_delay = self._idle_threshold
        else:
            # Minimum sleep guard
            next_delay = max(0.1, self._idle_threshold - delta)

        self._keep_alive_timer = threading.Timer(next_delay, self._keep_alive_loop)
        self._keep_alive_timer.daemon = True
        self._keep_alive_timer.start()

    # ---------- Original extension methods ----------
    def on_stroked(self, stroke: Stroke):
        log.info(f"Stroke: {stroke}")

    def on_translated(self, old, new):
        if new:
            log.info(f"Translated: {new}")

    def start(self):
        log.info("Extension initialised")
        self.engine.connect_hooks(self)

    def stop(self):
        self.engine.disconnect_hooks(self)

    def _handle_tablet_connected(
        self,
        ws: WebSocketApp,
        tablet_id: int,
        public_key: str,
        on_tablet_connected: Callable[[str], None] | None,
        new_tablet_token: str | None,
    ):
        log.debug(f"Private key: {self._config.private_key} and public key: {public_key}")
        if public_key:
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
        if on_tablet_connected and new_tablet_token:
            on_tablet_connected(new_tablet_token)

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

    def connect_websocket(self, connection_string: str, on_tablet_connected: Callable[[str], None] | None = None):
        def on_message(ws: WebSocketApp, message: Any):
            if isinstance(message, str):
                message: dict = json.loads(message)
            log.debug(f"Received: {message}")
            msg_type = message.get("type")
            if msg_type == "tablet_connected":
                tablet_id = message.get("id")
                public_key = message.get("publicKey")
                new_tablet_token = message.get("newTabletToken")
                self._handle_tablet_connected(ws, tablet_id, public_key, on_tablet_connected, new_tablet_token)
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

        def on_error(ws: WebSocketApp, error: Exception):
            log.exception(f"Error: {error}")

        def on_close(ws: WebSocketApp, close_status_code, close_msg):
            log.info("🔌 WebSocket CLOSED – stopping idle timer")
            self._stop_keep_alive()
            self._ws = None

        def on_open(ws: WebSocketApp):
            log.info("🔌 WebSocket OPENED – starting idle timer")
            self._ws = ws

            original_send = ws.send

            def wrapped_send(message: bytes | str, opcode=None):
                # Only pass opcode if it was explicitly provided
                result = original_send(message) if opcode is None else original_send(message, opcode)
                self._update_last_sent()  # track this outgoing message
                return result

            ws.send = wrapped_send
            self._update_last_sent()
            self._start_keep_alive()

        meta = metadata("plover-touch-tablets")
        header = {
            "User-Agent": f"{meta['Name']}/{meta['Version']}",
            "Origin": f"{WORKER_PROTOCOL}//{BASE_WORKER_FQDN}",
            "X-Public-Key": self._config.public_key,
        }
        log.info(header)
        ws = WebSocketApp(
            connection_string,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            header=header,
        )
        ws.run_forever(reconnect=5)
