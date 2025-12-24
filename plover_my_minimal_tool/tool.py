from pathlib import Path

from plover.gui_qt.tool import Tool
from plover.oslayer.config import ASSETS_DIR

from plover_my_minimal_tool.extended_engine import ExtendedStenoEngine
from plover_my_minimal_tool.get_logger import get_logger
from plover_my_minimal_tool.signal import Signal

log = get_logger("Tool")


class Main(Tool):
    TITLE = "Connection Settings"
    ICON = str(Path(ASSETS_DIR) / "plover.png")
    ROLE = "connection_settings"

    _engine: ExtendedStenoEngine

    def __init__(self, engine: ExtendedStenoEngine):
        super().__init__(engine)
        log.info("Tool initialised")

        if hasattr(engine, "my_minimal_extension"):
            self.extension = engine.my_minimal_extension
            log.info("Tool successfully connected to Extension!")
        else:
            log.warning("Extension not found. Is the plugin enabled?")
        # Your GUI initialization here

        self.signals = [Signal("stroked", self), Signal("translated", self)]

        # Example: Connect to stroke signals
        for signal in self.signals:
            self._engine.hook_connect(signal.hook, signal.callback)

    def on_stroked(self, stroke):
        # Minimal example: just log strokes
        log.info(f"Stroke: {stroke}")

    def on_translated(self, old, new):
        if new:
            log.info(f"Translated: {new}")

    def closeEvent(self, event):  # noqa: N802
        for signal in self.signals:
            self._engine.hook_disconnect(signal.hook, signal.callback)
        super().closeEvent(event)
