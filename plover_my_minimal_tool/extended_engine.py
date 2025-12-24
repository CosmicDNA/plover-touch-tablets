from typing import TYPE_CHECKING

from plover.engine import StenoEngine

if TYPE_CHECKING:
    from plover_my_minimal_tool.extension import Extension


class ExtendedStenoEngine(StenoEngine):
    my_minimal_extension: "Extension"

    def __init__(self, config, controller, keyboard_emulation):
        super().__init__(config, controller, keyboard_emulation)
