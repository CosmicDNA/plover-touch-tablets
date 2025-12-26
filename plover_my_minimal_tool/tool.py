import threading
from io import BytesIO
from pathlib import Path

import qrcode
import requests
from plover.engine import StenoEngine
from plover.gui_qt.tool import Tool
from plover.oslayer.config import ASSETS_DIR
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout

from plover_my_minimal_tool.extended_engine import ExtendedStenoEngine
from plover_my_minimal_tool.get_logger import get_logger

log = get_logger("Tool")


class Main(Tool):
    TITLE = "Connection Settings"
    ICON = str(Path(ASSETS_DIR) / "plover.png")
    ROLE = "connection_settings"

    _engine: ExtendedStenoEngine
    qr: "QRCode"

    def __init__(self, engine: StenoEngine):
        super().__init__(engine)
        self._engine = ExtendedStenoEngine(engine)
        log.info("Tool initialised")

        self.qr = QRCode(self)

        if not hasattr(engine, "my_minimal_extension"):
            log.warning("Extension not found. Is the plugin enabled?")
            return

        self.extension = self._engine.my_minimal_extension
        log.info("Tool successfully connected to Extension!")

        self.thread_0 = threading.Thread(target=process_data, args=(self,), daemon=True)
        self.thread_0.start()

    def closeEvent(self, event):  # noqa: N802
        super().closeEvent(event)


def process_data(main_tool: Main):
    try:
        res = requests.post("https://relay.stenography.cosmicdna.co.uk/session/initiate", timeout=10)
        response: dict = res.json()
    except Exception:
        log.exception("Request failed")
    else:
        protocol, sessionId, pcConnectionToken, tabletConnectionToken = response.values()
        tokens = [pcConnectionToken, tabletConnectionToken]

        connection_strings = [f"{protocol}://relay.stenography.cosmicdna.co.uk/session/{sessionId}/connect?token={token}" for token in tokens]

        log.info(f"Pc connection string is {connection_strings[0]}")
        log.info(f"Tablet connection string is {connection_strings[1]}")

        if main_tool:
            main_tool.qr.qr_ready.emit(connection_strings[1])


class QRCode(QObject):
    qr_label: QLabel
    qr_ready = Signal(str)

    def __init__(self, tool: Main) -> None:
        super().__init__()
        self.tool = tool
        self.qr_label = QLabel("Generating QR Code...")
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = QVBoxLayout()
        layout.addWidget(self.qr_label)
        tool.setLayout(layout)
        self.qr_ready.connect(self.update_qr_code)

    def update_qr_code(self, connection_string):
        img = qrcode.make(connection_string)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qimage = QImage.fromData(buffer.getvalue())
        self.qr_label.setPixmap(QPixmap.fromImage(qimage))
