from typing import TYPE_CHECKING

from plover_my_minimal_tool.get_logger import get_logger
from plover_my_minimal_tool.signal import Signal

if TYPE_CHECKING:
    from plover_my_minimal_tool.extended_engine import ExtendedStenoEngine

log = get_logger("Extension")


class Extension:
    engine: "ExtendedStenoEngine"

    def __init__(self, engine: "ExtendedStenoEngine"):
        self.engine = engine
        self.engine.my_minimal_extension = self

        self.signals = [Signal("stroked", self), Signal("translated", self)]

    def on_stroked(self, stroke):
        # Minimal example: just log strokes
        log.info(f"Stroke: {stroke}")

    def on_translated(self, old, new):
        if new:
            log.info(f"Translated: {new}")

    def start(self):
        log.info("Extension initialised")

        # Example: Connect to stroke signals
        for signal in self.signals:
            self.engine.hook_connect(signal.hook, signal.callback)

    def stop(self):
        for signal in self.signals:
            self.engine.hook_disconnect(signal.hook, signal.callback)
