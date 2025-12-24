from pathlib import Path

from plover.engine import StenoEngine
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

    def __init__(self, engine: StenoEngine):
        super().__init__(engine)
        self._engine = ExtendedStenoEngine(engine)
        log.info("Tool initialised")

        if hasattr(engine, "my_minimal_extension"):
            self.extension = self._engine.my_minimal_extension
            log.info("Tool successfully connected to Extension!")
        else:
            log.warning("Extension not found. Is the plugin enabled?")
        # Your GUI initialization here

        self._engine.signals = [Signal("stroked"), Signal("translated")]

        # Example: Connect to stroke signals
        self._engine.connect_hooks(self)

    def on_stroked(self, stroke):
        # Minimal example: just log strokes
        log.info(f"Stroke: {stroke}")

    def on_translated(self, old, new):
        if new:
            log.info(f"Translated: {new}")

    def closeEvent(self, event):  # noqa: N802
        self._engine.disconnect_hooks(self)
        super().closeEvent(event)
