from plover import log
from plover.engine import StenoEngine


class Extension:
    engine: StenoEngine

    def __init__(self, engine: StenoEngine):
        self.engine = engine

    def on_stroke(self, stroke):
        # Minimal example: just log strokes
        log.info(f"From extension - Stroke: {stroke}")

    def on_translated(self, old, new):
        if new:
            log.info(f"From extension - Translated: {new}")

    def start(self):
        log.info("Extension initialised")

        # Example: Connect to stroke signals
        self.engine.hook_connect("stroked", self.on_stroke)
        self.engine.hook_connect("translated", self.on_translated)
