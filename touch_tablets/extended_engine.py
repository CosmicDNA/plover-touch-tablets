from typing import TYPE_CHECKING

from plover.engine import StenoEngine

if TYPE_CHECKING:
    from touch_tablets.extension import Extension

from touch_tablets.signal import Signal


class ExtendedStenoEngine:
    my_minimal_extension: "Extension"
    signals: list[Signal]
    _engine: StenoEngine

    def __init__(self, engine: StenoEngine):
        self._engine = engine

    def __getattr__(self, name):
        """Wrapper around StenoEngine."""
        return getattr(self._engine, name)

    def disconnect_hooks(self, host: object):
        for signal in self.signals:
            self._engine.hook_disconnect(signal.hook, getattr(host, signal.callback))

    def connect_hooks(self, host: object):
        for signal in self.signals:
            self._engine.hook_connect(signal.hook, getattr(host, signal.callback))
