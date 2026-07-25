import json
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTextEdit, QLineEdit, QDialog,
    QDateTimeEdit, QMessageBox, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QTimer, QDateTime
from core.database import get_connection


class EcoReleaseCard(QWidget):
    def __init__(self, project_id: str, main_window, release_screen):
        super().__init__()
        self.project_id = project_id
        self.main_window = main_window
        self.release_screen = release_screen
        self.setStyleSheet("background-color: #111111;")

        with get_connection() as conn:
            self.project = conn.execute(
                "SELECT * FROM eco_release_projects WHERE id = ?", (project_id,)
            ).fetchone()

        if not self.project:
            return

        self._build_ui()

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
            QPushButton { background: transparent; color: #aaaaaa; border: none; font-size: 14px; }
            QPushButton:hover { color: #ffffff; }
        """)
        btn_back.clicked.connect(self._go_back)
        top_layout.addWidget(btn_back)
        top_layout.addStretch()

        desc = self.project["description"] or ""
        title = desc[:40] + "..." if len(desc) > 40 else desc
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 15px; font-weight: 500;")
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()

        self.lbl_saved = QLabel("✓ Сохранено")
        self.lbl_saved.setStyleSheet("color: #388E3C; font-size: 12px;")
        self.lbl_saved.setVisible(False)
        top_layout.addWidget(self.lbl_saved)
        root.addWidget(top)

        # Описание + дата запуска
        info_bar = QWidget()
        info_bar.setFixedHeight(80)
        info_bar.setStyleSheet("background-color: #1a1a1a; border-bottom: 1px solid #2a2a2a;")
        info_layout = QHBoxLayout(info_bar)
        info_layout.setContentsMargins(24, 0, 24, 0)
        info_layout.setSpacing(16)

        # Краткое описание
        desc_col = QVBoxLayout()
        desc_col.setSpacing(2)
        lbl_d = QLabel("Краткое описание")
        lbl_d.setStyleSheet("color: #666666; font-size: 11px;")
        desc_col.addWidget(lbl_d)

        self.input_desc = QLineEdit(self.project["description"] or "")
        self.input_desc.setPlaceholderText("Введите краткое описание...")
        self.input_desc.setStyleSheet("""
            QLineEdit {
                background: #2a2a2a; border: 1px solid #333;
                border-radius: 6px; color: #e8e8e8;
                font-size: 13px; padding: 0 10px; height: 34px;
            }
            QLineEdit:focus { border-color: #388E3C; }
        """)
        self.input_desc.setFixedHeight(34)
        self.input_desc.textChanged.connect(self._schedule_autosave)
        desc_col.addWidget(self.input_desc)
        info_layout.addLayout(desc_col, 2)

        # Дата запуска
        date_col = QVBoxLayout()
        date_col.setSpacing(2)
        lbl_launched = QLabel("Дата запуска")
        lbl_launched.setStyleSheet("color: #666666; font-size: 11px;")
        date_col.addWidget(lbl_launched)

        self.input_launched = QLineEdit(self.project["date_launched"] or "")
        self.input_launched.setPlaceholderText("дд.мм.гггг")
        self.input_launched.setFixedHeight(34)
        self.input_launched.setStyleSheet("""
            QLineEdit {
                background: #2a2a2a; border: 1px solid #333;
                border-radius: 6px; color: #e8e8e8;
                font-size: 13px; padding: 0 10px;
            }
            QLineEdit:focus { border-color: #388E3C; }
        """)
        self.input_launched.textChanged.connect(self._schedule_autosave)
        date_col.addWidget(self.input_launched)
        info_layout.addLayout(date_col, 1)

        root.addWidget(info_bar)

        # Вкладки
        tabs = QWidget()
        tabs.setFixedHeight(44)
        tabs.setStyleSheet("background: #1a1a1a; border-bottom: 1px solid #2a2a2a;")
        tabs_layout = QHBoxLayout(tabs)
        tabs_layout.setContentsMargins(16, 6, 16, 6)
        tabs_layout.setSpacing(8)

        self.btn_plan = self._tab_btn("Чек-лист план", True)
        self.btn_notes = self._tab_btn("Записи", False)
        self.btn_plan.clicked.connect(lambda: self._switch_tab(0))
        self.btn_notes.clicked.connect(lambda: self._switch_tab(1))
        tabs_layout.addWidget(self.btn_plan)
        tabs_layout.addWidget(self.btn_notes)
        tabs_layout.addStretch()
        root.addWidget(tabs)

        # Стек вкладок
        self.tab_stack = QStackedWidget()

        checklist_data = []
        try:
            checklist_data = json.loads(self.project["checklist"] or "[]")
        except Exception:
            pass

        self.plan_widget = ReleasePlanWidget(checklist_data, self.project_id, self)
        self.tab_stack.addWidget(self.plan_widget)

        notes_data = []
        try:
            notes_data = json.loads(self.project["notes"] or "[]")
        except Exception:
            pass

        self.notes_widget = ReleaseNotesWidget(notes_data, self.project_id, self)
        self.tab_stack.addWidget(self.notes_widget)

        root.addWidget(self.tab_stack)

        # Автосохранение
        self.autosave_timer = QTimer()
        self.autosave_timer.setInterval(3000)
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.timeout.connect(self._autosave)

    def _tab_btn(self, text, active):
        btn = QPushButton(text)
        btn.setFixedHeight(32)
        btn.setCursor(Qt.PointingHandCursor)
        self._style_tab(btn, active)
        return btn

    def _style_tab(self, btn, active):
        if active:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #388E3C; color: #fff;
                    border: none; border-radius: 6px;
                    padding: 0 16px; font-size: 13px;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent; color: #888;
                    border: 1px solid #333; border-radius: 6px;
                    padding: 0 16px; font-size: 13px;
                }
                QPushButton:hover { color: #ccc; border-color: #555; }
            """)

    def _switch_tab(self, index):
        self.tab_stack.setCurrentIndex(index)
        self._style_tab(self.btn_plan, index == 0)
        self._style_tab(self.btn_notes, index == 1)

    def _schedule_autosave(self):
        self.autosave_timer.start()

    def _autosave(self):
        try:
            with get_connection() as conn:
                conn.execute("""
                    UPDATE eco_release_projects
                    SET description = ?, date_launched = ?
                    WHERE id = ?
                """, (
                    self.input_desc.text().strip(),
                    self.input_launched.text().strip(),
                    self.project_id
                ))
                conn.commit()
            if hasattr(self, 'lbl_saved') and self.lbl_saved is not None:
                self.lbl_saved.setVisible(True)
                QTimer.singleShot(2000, self._hide_saved)
        except RuntimeError:
            pass

    def _hide_saved(self):
        try:
            if hasattr(self, 'lbl_saved'):
                self.lbl_saved.setVisible(False)
        except RuntimeError:
            pass

    def save_checklist(self, items: list):
        with get_connection() as conn:
            conn.execute(
                "UPDATE eco_release_projects SET checklist = ? WHERE id = ?",
                (json.dumps(items, ensure_ascii=False), self.project_id)
            )
            conn.commit()

    def save_notes(self, notes: list):
        with get_connection() as conn:
            conn.execute(
                "UPDATE eco_release_projects SET notes = ? WHERE id = ?",
                (json.dumps(notes, ensure_ascii=False), self.project_id)
            )
            conn.commit()

    def _go_back(self):
        if hasattr(self, 'autosave_timer'):
            self.autosave_timer.stop()
        self._autosave()
        self.release_screen.load_projects()
        self.main_window.go_back()


class ReleasePlanWidget(QWidget):
    def __init__(self, checklist_data: list, project_id: str, card):
        super().__init__()
        self.project_id = project_id
        self.card = card
        self.items = checklist_data
        self.setStyleSheet("background: #111111;")
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #111111; }")

        self.container = QWidget()
        self.container.setStyleSheet("background: #111111;")
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(40, 16, 40, 16)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch()

        scroll.setWidget(self.container)
        root.addWidget(scroll)

        self._load_items()

    def _load_items(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, item in enumerate(self.items):
            row = PlanRow(item, i, self)
            self.list_layout.insertWidget(self.list_layout.count() - 1, row)

    def toggle_item(self, index: int, done: bool):
        if index < len(self.items):
            if isinstance(self.items[index], dict):
                self.items[index]["done"] = done
            else:
                self.items[index] = {"title": str(self.items[index]), "done": done}
            self.card.save_checklist(self.items)


class PlanRow(QFrame):
    def __init__(self, item, index: int, plan_widget):
        super().__init__()
        self.index = index
        self.plan_widget = plan_widget
        self.setFixedHeight(40)

        title = item.get("title", str(item)) if isinstance(item, dict) else str(item)
        done = item.get("done", False) if isinstance(item, dict) else False

        self.setStyleSheet("""
            QFrame { background: #1e1e1e; border-radius: 6px; }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)

        from PySide6.QtWidgets import QCheckBox
        self.cb = QCheckBox()
        self.cb.setChecked(done)
        self.cb.setStyleSheet("""
            QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #444; border-radius: 4px; background: #2a2a2a; }
            QCheckBox::indicator:checked { background: #388E3C; border-color: #388E3C; }
        """)
        self.cb.stateChanged.connect(lambda s: self.plan_widget.toggle_item(self.index, s == Qt.Checked))
        layout.addWidget(self.cb)

        lbl = QLabel(title)
        color = "#666666" if done else "#e8e8e8"
        lbl.setStyleSheet(f"color: {color}; font-size: 13px;")
        layout.addWidget(lbl)
        layout.addStretch()


class ReleaseNotesWidget(QWidget):
    def __init__(self, notes_data: list, project_id: str, card):
        super().__init__()
        self.project_id = project_id
        self.card = card
        self.notes = notes_data
        self.setStyleSheet("background: #111111;")
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # Кнопки добавить
        btn_bar = QWidget()
        btn_bar.setFixedHeight(52)
        btn_bar.setStyleSheet("background: #1a1a1a; border-bottom: 1px solid #2a2a2a;")
        btn_layout = QHBoxLayout(btn_bar)
        btn_layout.setContentsMargins(24, 0, 24, 0)
        btn_layout.setSpacing(8)
        btn_layout.addStretch()

        btn_add_note = QPushButton("+ Запись")
        btn_add_note.setFixedHeight(34)
        btn_add_note.setCursor(Qt.PointingHandCursor)
        btn_add_note.setStyleSheet("""
            QPushButton {
                background: #2a2a2a; color: #cccccc;
                border: 1px solid #333; border-radius: 6px; padding: 0 14px; font-size: 13px;
            }
            QPushButton:hover { border-color: #555; color: #fff; }
        """)
        btn_add_note.clicked.connect(self._add_note_simple)
        btn_layout.addWidget(btn_add_note)

        btn_add_reminder = QPushButton("+ Заметка с напоминанием")
        btn_add_reminder.setFixedHeight(34)
        btn_add_reminder.setCursor(Qt.PointingHandCursor)
        btn_add_reminder.setStyleSheet("""
            QPushButton {
                background: #1a2a1a; color: #aaffaa;
                border: 1px solid #336633; border-radius: 6px; padding: 0 14px; font-size: 13px;
            }
            QPushButton:hover { background: #253525; }
        """)
        btn_add_reminder.clicked.connect(self._add_note_reminder)
        btn_layout.addWidget(btn_add_reminder)
        root.addWidget(btn_bar)

        # Список записей
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #111111; }")

        self.container = QWidget()
        self.container.setStyleSheet("background: #111111;")
        self.notes_layout = QVBoxLayout(self.container)
        self.notes_layout.setContentsMargins(40, 16, 40, 16)
        self.notes_layout.setSpacing(8)
        self.notes_layout.addStretch()

        scroll.setWidget(self.container)
        root.addWidget(scroll)

        self._load_notes()

    def _load_notes(self):
        while self.notes_layout.count() > 1:
            item = self.notes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, note in enumerate(self.notes):
            card = NoteCard(note, i, self)
            self.notes_layout.insertWidget(self.notes_layout.count() - 1, card)

    def _add_note_simple(self):
        dialog = SimpleNoteDialog(self)
        if dialog.exec():
            text = dialog.get_text()
            if text:
                self.notes.insert(0, {
                    "type": "note",
                    "text": text,
                    "date": datetime.now().strftime("%d.%m.%Y %H:%M")
                })
                self.card.save_notes(self.notes)
                self._load_notes()

    def _add_note_reminder(self):
        dialog = ReminderNoteDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data:
                self.notes.insert(0, data)
                self.card.save_notes(self.notes)
                self._load_notes()

    def delete_note(self, index: int):
        if index < len(self.notes):
            self.notes.pop(index)
            self.card.save_notes(self.notes)
            self._load_notes()


class NoteCard(QFrame):
    def __init__(self, note: dict, index: int, notes_widget):
        super().__init__()
        self.index = index
        self.notes_widget = notes_widget
        is_reminder = note.get("type") == "reminder"

        if is_reminder:
            self.setStyleSheet("""
                QFrame { background: #1a2a1a; border: 1px solid #388E3C; border-radius: 8px; }
            """)
        else:
            self.setStyleSheet("""
                QFrame { background: #1e1e1e; border: 1px solid #2a2a2a; border-radius: 8px; }
            """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        # Заголовок строки
        top_row = QHBoxLayout()

        if is_reminder:
            lbl_type = QLabel("📅 Заметка")
            lbl_type.setStyleSheet("color: #4caf50; font-size: 11px; font-weight: 500;")
            top_row.addWidget(lbl_type)

            title = note.get("title", "")
            if title:
                lbl_title = QLabel(title)
                lbl_title.setStyleSheet("color: #e8e8e8; font-size: 13px; font-weight: 500;")
                top_row.addWidget(lbl_title)

            remind_dt = note.get("remind_at", "")
            if remind_dt:
                lbl_remind = QLabel(f"⏰ {remind_dt}")
                lbl_remind.setStyleSheet("color: #FBC02D; font-size: 11px;")
                top_row.addWidget(lbl_remind)
        else:
            lbl_type = QLabel("📝 Запись")
            lbl_type.setStyleSheet("color: #888888; font-size: 11px;")
            top_row.addWidget(lbl_type)

        top_row.addStretch()

        lbl_date = QLabel(note.get("date", ""))
        lbl_date.setStyleSheet("color: #555555; font-size: 11px;")
        top_row.addWidget(lbl_date)

        btn_del = QPushButton("×")
        btn_del.setFixedSize(20, 20)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet("""
            QPushButton { background: transparent; color: #555; border: none; font-size: 16px; }
            QPushButton:hover { color: #E24B4A; }
        """)
        btn_del.clicked.connect(lambda: self.notes_widget.delete_note(self.index))
        top_row.addWidget(btn_del)
        layout.addLayout(top_row)

        lbl_text = QLabel(note.get("text", ""))
        lbl_text.setWordWrap(True)
        lbl_text.setStyleSheet("color: #cccccc; font-size: 13px;")
        layout.addWidget(lbl_text)


class SimpleNoteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новая запись")
        self.setFixedSize(480, 260)
        self.setStyleSheet("QDialog { background: #1a1a1a; } QLabel { color: #aaa; font-size: 13px; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        lbl = QLabel("Текст записи")
        lbl.setStyleSheet("color: #e8e8e8; font-size: 15px;")
        layout.addWidget(lbl)

        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background: #2a2a2a; border: 1px solid #333;
                border-radius: 8px; color: #e8e8e8; font-size: 14px; padding: 8px;
            }
            QTextEdit:focus { border-color: #388E3C; }
        """)
        layout.addWidget(self.text_edit)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Отмена")
        btn_cancel.setFixedHeight(38)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("QPushButton { background: #2a2a2a; color: #aaa; border: 1px solid #333; border-radius: 8px; }")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Сохранить")
        btn_save.setFixedHeight(38)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("QPushButton { background: #388E3C; color: #fff; border: none; border-radius: 8px; font-size: 13px; } QPushButton:hover { background: #4caf50; }")
        btn_save.clicked.connect(self.accept)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def get_text(self) -> str:
        return self.text_edit.toPlainText().strip()


class ReminderNoteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новая заметка с напоминанием")
        self.setFixedSize(480, 340)
        self.setStyleSheet("QDialog { background: #1a1a1a; } QLabel { color: #aaa; font-size: 13px; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)

        lbl = QLabel("Заметка с напоминанием")
        lbl.setStyleSheet("color: #e8e8e8; font-size: 15px;")
        layout.addWidget(lbl)

        layout.addWidget(QLabel("Название"))
        self.input_title = QLineEdit()
        self.input_title.setFixedHeight(38)
        self.input_title.setStyleSheet("""
            QLineEdit { background: #2a2a2a; border: 1px solid #333; border-radius: 8px; color: #e8e8e8; font-size: 13px; padding: 0 10px; }
            QLineEdit:focus { border-color: #388E3C; }
        """)
        layout.addWidget(self.input_title)

        layout.addWidget(QLabel("Описание"))
        self.text_edit = QTextEdit()
        self.text_edit.setFixedHeight(80)
        self.text_edit.setStyleSheet("""
            QTextEdit { background: #2a2a2a; border: 1px solid #333; border-radius: 8px; color: #e8e8e8; font-size: 13px; padding: 6px; }
            QTextEdit:focus { border-color: #388E3C; }
        """)
        layout.addWidget(self.text_edit)

        layout.addWidget(QLabel("Дата и время напоминания"))
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.datetime_edit.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.datetime_edit.setFixedHeight(38)
        self.datetime_edit.setStyleSheet("""
            QDateTimeEdit { background: #2a2a2a; border: 1px solid #333; border-radius: 8px; color: #e8e8e8; font-size: 13px; padding: 0 10px; }
            QDateTimeEdit:focus { border-color: #388E3C; }
        """)
        layout.addWidget(self.datetime_edit)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Отмена")
        btn_cancel.setFixedHeight(38)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("QPushButton { background: #2a2a2a; color: #aaa; border: 1px solid #333; border-radius: 8px; }")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Сохранить")
        btn_save.setFixedHeight(38)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("QPushButton { background: #388E3C; color: #fff; border: none; border-radius: 8px; font-size: 13px; } QPushButton:hover { background: #4caf50; }")
        btn_save.clicked.connect(self.accept)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def get_data(self) -> dict:
        title = self.input_title.text().strip()
        text = self.text_edit.toPlainText().strip()
        if not title and not text:
            return None
        return {
            "type": "reminder",
            "title": title,
            "text": text,
            "remind_at": self.datetime_edit.dateTime().toString("dd.MM.yyyy HH:mm"),
            "date": datetime.now().strftime("%d.%m.%Y %H:%M")
        }