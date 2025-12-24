from pathlib import Path

from plover import log
from plover.engine import StenoEngine
from plover.gui_qt.tool import Tool
from plover.oslayer.config import ASSETS_DIR


class Main(Tool):
    TITLE = "Connection Settings"
    ICON = str(Path(ASSETS_DIR) / "plover.png")
    ROLE = "connection_settings"

    def __init__(self, engine: StenoEngine):
        super().__init__(engine)
        log.info("Tool initialised")
        # Your GUI initialization here

        # Example: Connect to stroke signals
        engine.hook_connect("stroked", self.on_stroke)
        engine.hook_connect("translated", self.on_translated)

    def on_stroke(self, stroke):
        # Minimal example: just log strokes
        log.info(f"From tool - Stroke: {stroke}")

    def on_translated(self, old, new):
        if new:
            log.info(f"From tool - Translated: {new}")
