from importlib.metadata import metadata

from plover.engine import StenoEngine
from websocket import WebSocketApp

from plover_my_minimal_tool.config import BASE_WORKER_URL, PROTOCOL
from plover_my_minimal_tool.extended_engine import ExtendedStenoEngine
from plover_my_minimal_tool.get_logger import get_logger
from plover_my_minimal_tool.signal import Signal

log = get_logger("Extension")


class Extension:
    engine: ExtendedStenoEngine

    def __init__(self, engine: StenoEngine):
        self.engine = ExtendedStenoEngine(engine)
        engine.my_minimal_extension = self

        self.engine.signals = [Signal("stroked"), Signal("translated")]

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

    def connect_websocket(self, connection_string):
        log.info(f"Connecting to websocket: {connection_string}")

        def on_message(ws, message):
            log.info(f"Received: {message}")

        def on_error(ws, error):
            log.error(f"Error: {error}")

        def on_close(ws, close_status_code, close_msg):
            log.info("Closed")

        def on_open(ws):
            log.info("Opened")

        meta = metadata("plover-my-minimal-tool")
        header = {"User-Agent": f"{meta['Name']}/{meta['Version']}", "Origin": f"{PROTOCOL}://{BASE_WORKER_URL}"}
        log.info(header)
        ws = WebSocketApp(connection_string, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close, header=header)
        ws.run_forever(reconnect=5)
