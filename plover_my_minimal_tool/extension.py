from plover.engine import StenoEngine

from plover_my_minimal_tool.extended_engine import ExtendedStenoEngine
from plover_my_minimal_tool.get_logger import get_logger
from plover_my_minimal_tool.signal import Signal

log = get_logger("Extension")


class Extension:
    engine: "ExtendedStenoEngine"

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
