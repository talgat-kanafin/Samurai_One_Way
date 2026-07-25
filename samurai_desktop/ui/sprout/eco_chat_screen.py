import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QScrollArea, QFrame,
    QDialog, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from core.database import get_connection, get_chat_session, save_chat_session
from core.models import ChatSession, EcoEntry, EcoType
from ai.client import send_message
from datetime import datetime


class AIWorker(QThread):
    finished = Signal(dict)

    def __init__(self, prompt_id, message, history, phase):
        super().__init__()
        self.prompt_id = prompt_id
        self.message = message
        self.history = history
        self.phase = phase

    def run(self):
        result = send_message(
            prompt_id=self.prompt_id,
            user_message=self.message,
            history=self.history,
            phase=self.phase
        )
        self.finished.emit(result)


class EcoChatScreen(QWidget):
    def __init__(self, entry_id: str, main_window):
        super().__init__()
        self.entry_id = entry_id
        self.main_window = main_window
        self.phase = 0
        self.messages = []
        self.revision_used = False
        self.is_complete = False
        self.prompt_id = "eco_new"
        self.worker = None

        self.setStyleSheet("background-color: #111111;")
        self._load_entry()
        self._build_ui()
        self._load_or_start()

    def _load_entry(self):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM eco_entries WHERE id = ?", (self.entry_id,)
            ).fetchone()
        self.entry = row
        if row:
            self.prompt_id = "eco_integration" if row["entry_type"] == "integration" else "eco_new"

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Верхняя панель
        top = QWidget()
        top.setFixedHeight(56)
        top.setStyleSheet("background-color: #1a1a1a; border-bottom: 1px solid #2a2a2a;")
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(16, 0, 16, 0)

        btn_back = QPushButton("← Назад")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet("""
            QPushButton {
                background: transparent; color: #aaaaaa;
                border: none; font-size: 14px;
            }
            QPushButton:hover { color: #ffffff; }
        """)
        btn_back.clicked.connect(self._go_back)
        top_layout.addWidget(btn_back)
        top_layout.addStretch()

        entry_type = self.entry["entry_type"] if self.entry else "new"
        type_str = "Интеграция" if entry_type == "integration" else "Новый проект"
        lbl_title = QLabel(f"Экосистема — {type_str}")
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 16px; font-weight: 500;")
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()

        self.lbl_phase = QLabel("Фаза 0 из 5")
        self.lbl_phase.setStyleSheet("color: #888888; font-size: 13px;")
        top_layout.addWidget(self.lbl_phase)

        root.addWidget(top)

        # Сообщения
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #111111; }")
        self.scroll = scroll

        self.messages_widget = QWidget()
        self.messages_widget.setStyleSheet("background: #111111;")
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(24, 16, 24, 16)
        self.messages_layout.setSpacing(12)
        self.messages_layout.addStretch()

        scroll.setWidget(self.messages_widget)
        root.addWidget(scroll)

        # Нижняя панель
        bottom = QWidget()
        bottom.setStyleSheet("background-color: #1a1a1a; border-top: 1px solid #2a2a2a;")
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(16, 12, 16, 12)
        bottom_layout.setSpacing(8)

        self.input = QTextEdit()
        self.input.setFixedHeight(80)
        self.input.setPlaceholderText("Введите сообщение...")
        self.input.setStyleSheet("""
            QTextEdit {
                background-color: #2e2e2e; border: 1px solid #3a3a3a;
                border-radius: 8px; color: #e8e8e8;
                font-size: 14px; padding: 8px 12px;
            }
            QTextEdit:focus { border-color: #388E3C; }
        """)
        bottom_layout.addWidget(self.input)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_send = QPushButton("Отправить")
        self.btn_send.setFixedHeight(40)
        self.btn_send.setCursor(Qt.PointingHandCursor)
        self.btn_send.setStyleSheet("""
            QPushButton {
                background-color: #388E3C; color: #fff;
                border: none; border-radius: 8px; font-size: 14px;
            }
            QPushButton:hover { background-color: #4caf50; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.btn_send.clicked.connect(self._on_send)

        self.btn_revision = QPushButton("Доработка")
        self.btn_revision.setFixedHeight(40)
        self.btn_revision.setCursor(Qt.PointingHandCursor)
        self.btn_revision.setVisible(False)
        self.btn_revision.setStyleSheet("""
            QPushButton {
                background-color: #7a5c00; color: #fff;
                border: none; border-radius: 8px; font-size: 14px;
            }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.btn_revision.clicked.connect(self._on_revision)

        self.btn_confirm = QPushButton("✓ Под реализацию")
        self.btn_confirm.setFixedHeight(40)
        self.btn_confirm.setCursor(Qt.PointingHandCursor)
        self.btn_confirm.setVisible(False)
        self.btn_confirm.setStyleSheet("""
            QPushButton {
                background-color: #388E3C; color: #fff;
                border: none; border-radius: 8px; font-size: 14px;
            }
            QPushButton:hover { background-color: #4caf50; }
        """)
        self.btn_confirm.clicked.connect(self._on_confirm)

        btn_row.addWidget(self.btn_send)
        btn_row.addWidget(self.btn_revision)
        btn_row.addWidget(self.btn_confirm)
        bottom_layout.addLayout(btn_row)
        root.addWidget(bottom)

    def _load_or_start(self):
        row = get_chat_session(self.entry_id)
        if row:
            self.phase = row["phase"]
            self.messages = json.loads(row["messages"])
            self.revision_used = bool(row["revision_used"])
            self.is_complete = bool(row["is_complete"])
            for msg in self.messages:
                self._add_bubble(msg["text"], msg["role"] == "user")
            self._update_ui_state()
        else:
            self._start_phase_1()

    def _start_phase_1(self):
        self.phase = 1
        desc = self.entry["description"] if self.entry else ""
        self._add_bubble(desc, is_user=True)
        self.messages.append({"role": "user", "text": desc})
        self._save_session()
        self._call_ai(desc)

    def _call_ai(self, user_text: str):
        self.btn_send.setEnabled(False)
        self.btn_send.setText("ИИ думает...")
        history = self.messages[:-1]
        self.worker = AIWorker(self.prompt_id, user_text, history, self.phase)
        self.worker.finished.connect(self._on_ai_response)
        self.worker.start()

    def _on_ai_response(self, result: dict):
        self.btn_send.setEnabled(True)
        self.btn_send.setText("Отправить")

        if not result["success"]:
            self._add_bubble(f"Ошибка: {result['error']}", is_user=False, is_error=True)
            return

        text = result["text"]
        self.messages.append({"role": "assistant", "text": text})
        self._add_bubble(text, is_user=False)
        self._save_session()

        if self.phase >= 5:
            self.is_complete = True
            self._save_session()
            self._update_ui_state()
        else:
            self.lbl_phase.setText(f"Фаза {self.phase} из 5")

    def _on_send(self):
        text = self.input.toPlainText().strip()
        if not text:
            return
        self.input.clear()
        self.phase = min(self.phase + 1, 5)
        self.messages.append({"role": "user", "text": text})
        self._add_bubble(text, is_user=True)
        self._save_session()
        self._call_ai(text)

    def _on_revision(self):
        if self.revision_used:
            return
        self.revision_used = True
        self.btn_revision.setEnabled(False)
        text = self.input.toPlainText().strip() or "Прошу доработать"
        self.input.clear()
        self.messages.append({"role": "user", "text": text})
        self._add_bubble(text, is_user=True)
        self._save_session()
        self._call_ai(text)

    def _on_confirm(self):
        with get_connection() as conn:
            last_ai = next(
                (m["text"] for m in reversed(self.messages) if m["role"] == "assistant"),
                ""
            )
            conn.execute(
                "UPDATE eco_entries SET result = ? WHERE id = ?",
                (last_ai[:500], self.entry_id)
            )
            conn.commit()
        self._go_back()

    def _update_ui_state(self):
        self.lbl_phase.setText(f"Фаза {self.phase} из 5")
        if self.is_complete:
            self.btn_send.setVisible(False)
            self.btn_revision.setVisible(not self.revision_used)
            self.btn_confirm.setVisible(True)
            self.input.setReadOnly(self.revision_used)
        if self.revision_used:
            self.btn_revision.setVisible(False)

    def _add_bubble(self, text: str, is_user: bool, is_error: bool = False):
        from ui.seed.chat_screen import MessageBubble
        bubble = MessageBubble(text, is_user, is_error)
        self.messages_layout.insertWidget(
            self.messages_layout.count() - 1, bubble
        )
        QThread.msleep(50)
        self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        )

    def _save_session(self):
        session = ChatSession(
            entry_id=self.entry_id,
            prompt_id=self.prompt_id,
            phase=self.phase,
            messages=self.messages,
            is_complete=self.is_complete,
            revision_used=self.revision_used,
        )
        row = get_chat_session(self.entry_id)
        if row:
            session.id = row["id"]
        save_chat_session(session)

    def _go_back(self):
        self.main_window.stack.setCurrentIndex(
            self.main_window.stack.count() - 2
        )


class EcoAddDialog(QDialog):
    entry_added = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новый запрос в Экосистему")
        self.setFixedSize(500, 340)
        self.setStyleSheet("""
            QDialog { background: #1a1a1a; }
            QLabel { color: #aaaaaa; font-size: 13px; }
            QComboBox, QTextEdit {
                background: #2e2e2e; border: 1px solid #3a3a3a;
                border-radius: 8px; color: #e8e8e8;
                font-size: 14px; padding: 8px 12px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: #2e2e2e; color: #e8e8e8;
                selection-background-color: #534AB7;
            }
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)

        lbl_title = QLabel("Новый запрос")
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 18px; font-weight: 500;")
        layout.addWidget(lbl_title)

        layout.addWidget(QLabel("Тип"))
        self.combo = QComboBox()
        self.combo.addItem("Новый проект", "new")
        self.combo.addItem("Интеграция с существующим", "integration")
        self.combo.setFixedHeight(44)
        layout.addWidget(self.combo)

        layout.addWidget(QLabel("Описание запроса"))
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Опишите запрос...")
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
                background: #2e2e2e; color: #aaa;
                border: 1px solid #3a3a3a; border-radius: 8px;
            }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Отправить")
        btn_save.setFixedHeight(40)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton {
                background: #388E3C; color: #fff;
                border: none; border-radius: 8px; font-size: 14px;
            }
            QPushButton:hover { background: #4caf50; }
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

        entry_type = self.combo.currentData()
        with get_connection() as conn:
            import uuid
            entry_id = str(uuid.uuid4())
            conn.execute("""
                INSERT INTO eco_entries
                (id, description, date_received, entry_type, result)
                VALUES (?, ?, ?, ?, '')
            """, (
                entry_id,
                description,
                datetime.now().isoformat(),
                entry_type
            ))
            conn.commit()

        self.entry_added.emit()
        self.accept()