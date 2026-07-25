import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTextEdit, QLineEdit, QFileDialog,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from core.database import get_connection, save_to_archive
from core.project_files import (
    copy_file_to_project, get_project_files, log_to_project
)
from datetime import datetime


ECO_PROJECT_PREFIX = "eco_"


def _get_eco_project_name(entry_id: str) -> str:
    return f"{ECO_PROJECT_PREFIX}{entry_id[:8]}"


class EcoCard(QWidget):
    confirmed = Signal(str)

    def __init__(self, entry_id: str, main_window):
        super().__init__()
        self.entry_id = entry_id
        self.main_window = main_window
        self.setStyleSheet("background-color: #111111;")
        self.project_name = _get_eco_project_name(entry_id)

        with get_connection() as conn:
            self.entry = conn.execute(
                "SELECT * FROM eco_entries WHERE id = ?", (entry_id,)
            ).fetchone()

        if not self.entry:
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

        entry_type = self.entry["entry_type"]
        type_str = "Интеграция" if entry_type == "integration" else "Новый проект"
        lbl_title = QLabel(f"Экосистема — {type_str}")
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 15px; font-weight: 500;")
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()

        self.lbl_saved = QLabel("✓ Сохранено")
        self.lbl_saved.setStyleSheet("color: #388E3C; font-size: 12px;")
        self.lbl_saved.setVisible(False)
        top_layout.addWidget(self.lbl_saved)
        top_layout.addSpacing(12)

        btn_send = QPushButton("✓ Отправить в ЭКО Релиз")
        btn_send.setFixedHeight(34)
        btn_send.setCursor(Qt.PointingHandCursor)
        btn_send.setStyleSheet("""
            QPushButton {
                background-color: #388E3C; color: #fff;
                border: none; border-radius: 6px; padding: 0 16px; font-size: 13px;
            }
            QPushButton:hover { background-color: #4caf50; }
        """)
        btn_send.clicked.connect(self._on_send)
        top_layout.addWidget(btn_send)
        root.addWidget(top)

        # Карточка описания
        card_top = QFrame()
        card_top.setFixedHeight(100)
        card_top.setStyleSheet("background-color: #1a1a1a; border-bottom: 1px solid #2a2a2a;")
        card_top_layout = QVBoxLayout(card_top)
        card_top_layout.setContentsMargins(24, 10, 24, 10)

        lbl_desc_title = QLabel("Исходный запрос")
        lbl_desc_title.setStyleSheet("color: #666666; font-size: 11px;")
        card_top_layout.addWidget(lbl_desc_title)

        desc = self.entry["description"] or ""
        lbl_desc = QLabel(desc[:200] + "..." if len(desc) > 200 else desc)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #e8e8e8; font-size: 14px;")
        card_top_layout.addWidget(lbl_desc)
        root.addWidget(card_top)

        # Нижние две карточки
        bottom_row = QWidget()
        bottom_layout = QHBoxLayout(bottom_row)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(1)

        self.files_card = EcoFilesCard(self.project_name, self)
        bottom_layout.addWidget(self.files_card, 1)

        saved_checklist = []
        try:
            saved_checklist = json.loads(self.entry["result"] or "[]")
            if not isinstance(saved_checklist, list):
                saved_checklist = []
        except Exception:
            pass

        self.checklist_card = EcoChecklistCard(saved_checklist, self)
        self.checklist_card.changed.connect(self._autosave)
        bottom_layout.addWidget(self.checklist_card, 1)

        root.addWidget(bottom_row, 1)

        self.autosave_timer = QTimer()
        self.autosave_timer.setInterval(3000)
        self.autosave_timer.timeout.connect(self._autosave)
        self.autosave_timer.start()

    def _autosave(self):
        if not hasattr(self, 'checklist_card'):
            return
        tasks = self.checklist_card.get_tasks()
        with get_connection() as conn:
            conn.execute(
                "UPDATE eco_entries SET result = ? WHERE id = ?",
                (json.dumps(tasks, ensure_ascii=False), self.entry_id)
            )
            conn.commit()
        try:
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

    def _on_send(self):
        tasks = self.checklist_card.get_tasks()
        if not tasks:
            QMessageBox.warning(self, "Чек-лист пуст", "Добавьте хотя бы один пункт плана.")
            return

        self._autosave()

        # Создаём запись в ЭКО Релиз
        with get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS eco_release_projects (
                    id TEXT PRIMARY KEY,
                    eco_entry_id TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    checklist TEXT NOT NULL DEFAULT '[]',
                    notes TEXT NOT NULL DEFAULT '[]',
                    date_received TEXT NOT NULL,
                    date_launched TEXT DEFAULT ''
                )
            """)
            import uuid
            release_id = str(uuid.uuid4())
            conn.execute("""
                INSERT INTO eco_release_projects
                (id, eco_entry_id, description, checklist, notes, date_received)
                VALUES (?, ?, ?, ?, '[]', ?)
            """, (
                release_id,
                self.entry_id,
                self.entry["description"],
                json.dumps(tasks, ensure_ascii=False),
                datetime.now().isoformat()
            ))
            conn.commit()

        log_to_project(
            self.project_name,
            "ЭКОСИСТЕМА → ЭКО РЕЛИЗ — Чек-лист план",
            "\n".join(f"- {t}" for t in tasks)
        )

        if hasattr(self, 'autosave_timer'):
            self.autosave_timer.stop()

        self.confirmed.emit(self.entry_id)
        self._go_back()

    def _go_back(self):
        if hasattr(self, 'autosave_timer'):
            self.autosave_timer.stop()
        self._autosave()
        self.main_window.go_back()


class EcoFilesCard(QFrame):
    def __init__(self, project_name: str, parent=None):
        super().__init__(parent)
        self.project_name = project_name
        self.setStyleSheet("QFrame { background-color: #161616; border-right: 1px solid #2a2a2a; }")
        self._build_ui()
        self.refresh_files()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        lbl = QLabel("Файлы")
        lbl.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(lbl)

        btn_add = QPushButton("+ Добавить файл")
        btn_add.setFixedHeight(36)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #1a2a1a; color: #aaffaa;
                border: 1px solid #336633; border-radius: 6px; font-size: 13px;
            }
            QPushButton:hover { background-color: #253525; }
        """)
        btn_add.clicked.connect(self._add_file)
        layout.addWidget(btn_add)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.list_widget = QWidget()
        self.list_widget.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(4)
        self.list_layout.addStretch()

        scroll.setWidget(self.list_widget)
        layout.addWidget(scroll)

    def _add_file(self):
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QFileDialog
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setWindowTitle("Выберите файлы")
        if dialog.exec():
            paths = dialog.selectedFiles()
            for path in paths:
                copy_file_to_project(self.project_name, path)
            self.refresh_files()
        QTimer.singleShot(200, self._restore_focus)
    
    def _restore_focus(self):
        main = self.window()
        if main:
            main.activateWindow()
            main.raise_()
            main.setFocus()

    def refresh_files(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        files = get_project_files(self.project_name)
        for f in files:
            row = QWidget()
            row.setFixedHeight(32)
            row.setStyleSheet("background: #1e1e1e; border-radius: 4px;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 0, 8, 0)

            lbl = QLabel(f["name"])
            lbl.setStyleSheet("color: #cccccc; font-size: 12px;")
            row_layout.addWidget(lbl)
            row_layout.addStretch()

            size_str = f"{f['size'] // 1024}KB" if f['size'] > 1024 else f"{f['size']}B"
            lbl_size = QLabel(size_str)
            lbl_size.setStyleSheet("color: #555555; font-size: 11px;")
            row_layout.addWidget(lbl_size)

            self.list_layout.insertWidget(self.list_layout.count() - 1, row)


class EcoChecklistCard(QFrame):
    changed = Signal()

    def __init__(self, saved_tasks: list = None, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QFrame { background-color: #161616; }")
        self._build_ui()

        if saved_tasks:
            for task in saved_tasks:
                if task:
                    self._add_task_row(task)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        lbl = QLabel("Чек-лист план")
        lbl.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(lbl)

        input_row = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Новый пункт плана...")
        self.task_input.setFixedHeight(34)
        self.task_input.setStyleSheet("""
            QLineEdit {
                background: #2a2a2a; border: 1px solid #333;
                border-radius: 6px; color: #e8e8e8;
                font-size: 13px; padding: 0 10px;
            }
            QLineEdit:focus { border-color: #388E3C; }
        """)
        self.task_input.returnPressed.connect(self._add_task)
        input_row.addWidget(self.task_input)

        btn_add = QPushButton("+")
        btn_add.setFixedSize(34, 34)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton { background: #388E3C; color: #fff; border: none; border-radius: 6px; font-size: 18px; }
            QPushButton:hover { background: #4caf50; }
        """)
        btn_add.clicked.connect(self._add_task)
        input_row.addWidget(btn_add)
        layout.addLayout(input_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.tasks_widget = QWidget()
        self.tasks_widget.setStyleSheet("background: transparent;")
        self.tasks_layout = QVBoxLayout(self.tasks_widget)
        self.tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.tasks_layout.setSpacing(4)
        self.tasks_layout.addStretch()

        scroll.setWidget(self.tasks_widget)
        layout.addWidget(scroll)

    def _add_task(self):
        text = self.task_input.text().strip()
        if not text:
            return
        self.task_input.clear()
        self._add_task_row(text)
        self.changed.emit()

    def _add_task_row(self, text: str):
        from ui.seed.idea_card import TaskRow
        row = TaskRow(text, self)
        row.deleted.connect(lambda: self.changed.emit())
        self.tasks_layout.insertWidget(self.tasks_layout.count() - 1, row)

    def get_tasks(self) -> list:
        tasks = []
        from ui.seed.idea_card import TaskRow
        for i in range(self.tasks_layout.count() - 1):
            item = self.tasks_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), TaskRow):
                tasks.append(item.widget().get_text())
        return tasks