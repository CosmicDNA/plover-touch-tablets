from plover.gui_qt.tool import Tool
from plover.engine import StenoEngine

class Main(Tool):
    TITLE = 'My Minimal Tool'
    ICON = ''  # e.g., ':/my_minimal_tool/icon.png' if you have resources
    ROLE = 'my_minimal_tool'

    def __init__(self, engine: StenoEngine):
        super().__init__(engine)
        # Your GUI initialization here

        # Example: Connect to stroke signals
        engine.hook_connect("stroked", self.on_stroke)
        engine.hook_connect("translated", self.on_translated)

    def on_stroke(self, stroke):
        # Minimal example: just log strokes
        print(f"Stroke: {stroke}")

    def on_translated(self, old, new):
        if new:
            print(f"Translated: {new}")