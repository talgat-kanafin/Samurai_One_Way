from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt


class PlaceholderScreen(QWidget):
    def __init__(self, title: str, message: str, main_window):
        super().__init__()
        self.main_window = main_window
        self.setStyleSheet("background-color: #1a1a1a;")
        self._build_ui(title, message)

    def _build_ui(self, title: str, message: str):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 32px; font-weight: 500;")
        layout.addWidget(lbl_title)

        lbl_msg = QLabel(message)
        lbl_msg.setAlignment(Qt.AlignCenter)
        lbl_msg.setStyleSheet("color: #888888; font-size: 16px;")
        layout.addWidget(lbl_msg)

        btn_back = QPushButton("← Назад")
        btn_back.setFixedSize(160, 44)
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: #2e2e2e;
                color: #cccccc;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                color: #ffffff;
            }
        """)
        btn_back.clicked.connect(self.main_window.go_back)
        layout.addWidget(btn_back, alignment=Qt.AlignCenter)