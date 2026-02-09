import threading
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

import qrcode
import requests
from plover.engine import StenoEngine
from plover.gui_qt.tool import Tool
from plover.oslayer.config import ASSETS_DIR
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout

from touch_tablets.config import (
    APP_URL,
    BASE_WORKER_FQDN,
    CONNECT_SLUG,
    INITIATE_SLUG,
    JOIN_SLUG,
    RELAY_PARAM,
    SESSION_SLUG,
    TOKEN_PARAM,
    WORKER_PROTOCOL,
)
from touch_tablets.encoding import encode_raw_url
from touch_tablets.extended_engine import ExtendedStenoEngine
from touch_tablets.get_logger import get_logger

if TYPE_CHECKING:
    from touch_tablets.extension import Extension

log = get_logger("Tool")


class Main(Tool):
    TITLE = "Tablet QR"
    ICON = str(Path(ASSETS_DIR) / "plover.png")
    ROLE = "connection_settings"

    _engine: ExtendedStenoEngine
    qr: "QRCode"
    extension: "Extension"
    tablet_connected = Signal(str)
    session_id: str

    def __init__(self, engine: StenoEngine):
        super().__init__(engine)
        self.tablet_connected.connect(self.on_tablet_connected)
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

    def on_tablet_connected(self, new_token: str):
        ws_protocol = WORKER_PROTOCOL.replace("http", "ws")
        tablet_connection_string = f"{ws_protocol}//{BASE_WORKER_FQDN}/{SESSION_SLUG}/{self.session_id}/{JOIN_SLUG}?{TOKEN_PARAM}={new_token}"
        log.info(f"Tablet connection string is {tablet_connection_string}")
        final_qr_url = f"{APP_URL}/?{RELAY_PARAM}={encode_raw_url(tablet_connection_string)}"
        log.info(final_qr_url)
        self.qr.qr_ready.emit(final_qr_url)


def process_data(main_tool: Main):
    try:
        res = requests.post(f"{WORKER_PROTOCOL}//{BASE_WORKER_FQDN}/{SESSION_SLUG}/{INITIATE_SLUG}", timeout=10)
        response: dict = res.json()
    except Exception:
        log.exception("Request failed")
    else:
        # protocol = response["protocol"]
        sessionId = response["sessionId"]
        pcConnectionToken = response["pcConnectionToken"]
        tabletConnectionToken = response["tabletConnectionToken"]
        connection_infos = [
            (pcConnectionToken, CONNECT_SLUG, WORKER_PROTOCOL, BASE_WORKER_FQDN),
            (tabletConnectionToken, JOIN_SLUG, WORKER_PROTOCOL, BASE_WORKER_FQDN),
        ]

        connection_strings = [
            f"{connection_info[2].replace('http', 'ws')}//{connection_info[3]}/{SESSION_SLUG}/{sessionId}/{connection_info[1]}?{TOKEN_PARAM}={
                connection_info[0]
            }"
            for connection_info in connection_infos
        ]

        log.info(f"Pc connection string is {connection_strings[0]}")

        tablet_connection_string = connection_strings[1]
        log.info(f"Tablet connection string is {tablet_connection_string}")

        final_qr_url = f"{APP_URL}/?{RELAY_PARAM}={encode_raw_url(tablet_connection_string)}"

        log.info(final_qr_url)

        if main_tool:
            main_tool.session_id = sessionId
            main_tool.qr.qr_ready.emit(final_qr_url)
            main_tool.extension.connect_websocket(connection_strings[0], on_tablet_connected=main_tool.tablet_connected.emit)


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
