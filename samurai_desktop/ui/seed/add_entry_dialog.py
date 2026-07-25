from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QComboBox
)
from PySide6.QtCore import Qt, Signal
from core.database import save_idea_entry
from core.models import IdeaEntry, ProjectType


class AddEntryDialog(QDialog):
    entry_added = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новая запись")
        self.setFixedSize(500, 360)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
            }
            QLabel {
                color: #aaaaaa;
                font-size: 13px;
            }
            QComboBox {
                background-color: #2e2e2e;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                color: #e8e8e8;
                font-size: 14px;
                padding: 8px 12px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #2e2e2e;
                color: #e8e8e8;
                selection-background-color: #534AB7;
            }
            QTextEdit {
                background-color: #2e2e2e;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                color: #e8e8e8;
                font-size: 14px;
                padding: 8px 12px;
            }
            QTextEdit:focus { border: 1px solid #534AB7; }
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        lbl_title = QLabel("Новая запись")
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 18px; font-weight: 500;")
        layout.addWidget(lbl_title)

        lbl_theme = QLabel("Раздел")
        layout.addWidget(lbl_theme)

        self.combo = QComboBox()
        self.combo.addItem("Идея: прога",       ProjectType.SOFTWARE)
        self.combo.addItem("Идея: производство", ProjectType.PRODUCTION)
        self.combo.addItem("Исследование",       ProjectType.RESEARCH)
        self.combo.setFixedHeight(44)
        layout.addWidget(self.combo)

        lbl_desc = QLabel("Описание")
        layout.addWidget(lbl_desc)

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Опишите вашу идею...")
        layout.addWidget(self.text_input)

        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("color: #E24B4A; font-size: 12px;")
        layout.addWidget(self.lbl_error)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Отмена")
        btn_cancel.setFixedHeight(40)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #2e2e2e; color: #aaaaaa;
                border: 1px solid #3a3a3a; border-radius: 8px; font-size: 14px;
            }
            QPushButton:hover { color: #ffffff; border-color: #555; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Отправить")
        btn_save.setFixedHeight(40)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #534AB7; color: #ffffff;
                border: none; border-radius: 8px; font-size: 14px;
            }
            QPushButton:hover { background-color: #6358c8; }
        """)
        btn_save.clicked.connect(self._on_save)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _on_save(self):
        description = self.text_input.toPlainText().strip()
        if not description:
            self.lbl_error.setText("Введите описание")
            return
    
        theme = self.combo.currentData()
        entry = IdeaEntry(
            project_id=None,
            theme=theme,
            description=description,
        )
        save_idea_entry(entry)
        self.entry_added.emit()
        self.accept()