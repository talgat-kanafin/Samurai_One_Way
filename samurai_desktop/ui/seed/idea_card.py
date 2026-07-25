import json
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QFileDialog,
    QCheckBox, QInputDialog, QMessageBox, QDialog
)
from PySide6.QtCore import Qt, Signal, QTimer
from core.database import (
    get_connection, get_idea_entry, save_to_archive,
    find_similar_in_archive, update_idea_entry_color,
    update_idea_entry_project, update_idea_entry_checklist,
    delete_idea_entry, save_mvp_task
)
from core.models import MVPTask, EntryColor
from core.project_files import (
    create_project_folder, log_to_project,
    copy_file_to_project, get_project_files, save_project_meta
)
from datetime import datetime


class IdeaCard(QWidget):
    confirmed = Signal(str)

    def __init__(self, entry_id: str, theme: str, main_window):
        super().__init__()
        self.entry_id = entry_id
        self.theme = theme
        self.main_window = main_window
        self.setStyleSheet("background-color: #111111;")

        self.entry = get_idea_entry(entry_id)
        if not self.entry:
            return

        self.project_name = self.entry["project_name"] or ""

        if self.project_name:
            # Уже есть название — сразу открываем карточки
            self._build_cards()
        else:
            # Проверяем похожие
            similar = find_similar_in_archive(
                self.entry["description"],
                self.entry["theme"]
            )
            if similar:
                self._show_similar_dialog(similar[0])
            else:
                self._ask_project_name()

    def _show_similar_dialog(self, match: dict):
        dialog = SimilarDialog(
            current_desc=self.entry["description"],
            archive_entry=match["entry"],
            similarity=match["similarity"],
            parent=self
        )
        result = dialog.exec()
        if result == QDialog.Accepted:
            self._ask_project_name()
        else:
            delete_idea_entry(self.entry_id)
            self._go_back()

    def _ask_project_name(self):
        name, ok = QInputDialog.getText(
            self, "Название проекта",
            "Введите название проекта:"
        )
        if ok and name.strip():
            self.project_name = name.strip()
            update_idea_entry_project(self.entry_id, self.project_name)
            create_project_folder(self.project_name)
            save_project_meta(self.project_name, {
                "name": self.project_name,
                "theme": self.theme,
                "entry_id": self.entry_id,
                "date_created": datetime.now().isoformat()
            })
            log_to_project(
                self.project_name,
                "СЕМЯ — Исходная запись",
                self.entry["description"]
            )
            update_idea_entry_color(self.entry_id, EntryColor.YELLOW.value)
            self._build_cards()
        elif ok:
            self._ask_project_name()
        else:
            self._go_back()

    def _build_cards(self):
        for child in self.findChildren(QWidget):
            child.deleteLater()

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

        theme_names = {"software": "Программная", "production": "Производственная"}
        lbl_title = QLabel(f"{theme_names.get(self.theme, self.theme)} — {self.project_name}")
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 15px; font-weight: 500;")
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()

        # Индикатор автосохранения
        self.lbl_saved = QLabel("✓ Сохранено")
        self.lbl_saved.setStyleSheet("color: #388E3C; font-size: 12px;")
        self.lbl_saved.setVisible(False)
        top_layout.addWidget(self.lbl_saved)
        top_layout.addSpacing(12)

        btn_confirm = QPushButton("✓ Отправить в Росток")
        btn_confirm.setFixedHeight(34)
        btn_confirm.setCursor(Qt.PointingHandCursor)
        btn_confirm.setStyleSheet("""
            QPushButton {
                background-color: #388E3C; color: #fff;
                border: none; border-radius: 6px; padding: 0 16px; font-size: 13px;
            }
            QPushButton:hover { background-color: #4caf50; }
        """)
        btn_confirm.clicked.connect(self._on_confirm)
        top_layout.addWidget(btn_confirm)
        root.addWidget(top)

        btn_info = QPushButton("ℹ")
        btn_info.setFixedSize(34, 34)
        btn_info.setCursor(Qt.PointingHandCursor)
        btn_info.setStyleSheet("""
            QPushButton {
                background: #2a2a2a; color: #888;
                border: 1px solid #333; border-radius: 6px; font-size: 16px;
            }
            QPushButton:hover { color: #fff; border-color: #555; }
        """)
        btn_info.clicked.connect(self._show_info)
        top_layout.addWidget(btn_info)

        # Карточка записи
        card_top = QFrame()
        card_top.setFixedHeight(100)
        card_top.setStyleSheet("background-color: #1a1a1a; border-bottom: 1px solid #2a2a2a;")
        card_top_layout = QVBoxLayout(card_top)
        card_top_layout.setContentsMargins(24, 10, 24, 10)

        lbl_desc_title = QLabel("Исходная запись")
        lbl_desc_title.setStyleSheet("color: #666666; font-size: 11px;")
        card_top_layout.addWidget(lbl_desc_title)

        desc = self.entry["description"] if self.entry else ""
        lbl_desc = QLabel(desc[:200] + "..." if len(desc) > 200 else desc)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #e8e8e8; font-size: 14px;")
        card_top_layout.addWidget(lbl_desc)
        root.addWidget(card_top)

        # Нижние карточки
        bottom_row = QWidget()
        bottom_layout = QHBoxLayout(bottom_row)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(1)

        self.files_card = FilesCard(self.project_name, self)
        bottom_layout.addWidget(self.files_card, 1)

        # Загружаем сохранённый чек-лист
        saved_checklist = []
        try:
            saved_checklist = json.loads(self.entry["checklist"] or "[]")
        except Exception:
            pass

        self.checklist_card = ChecklistCard(saved_checklist, self)
        self.checklist_card.changed.connect(self._autosave)
        bottom_layout.addWidget(self.checklist_card, 1)

        root.addWidget(bottom_row, 1)

        # Таймер автосохранения — каждые 3 секунды
        self.autosave_timer = QTimer()
        self.autosave_timer.setInterval(3000)
        self.autosave_timer.timeout.connect(self._autosave)
        self.autosave_timer.start()

    def _autosave(self):
        if not hasattr(self, 'checklist_card'):
            return
        tasks = self.checklist_card.get_tasks()
        update_idea_entry_checklist(self.entry_id, tasks)
        if hasattr(self, 'lbl_saved') and self.lbl_saved is not None:
            try:
                self.lbl_saved.setVisible(True)
                QTimer.singleShot(2000, self._hide_saved_label)
            except RuntimeError:
                pass

    def _hide_saved_label(self):
        try:
            if hasattr(self, 'lbl_saved') and self.lbl_saved is not None:
                self.lbl_saved.setVisible(False)
        except RuntimeError:
            pass

    def _on_confirm(self):
        tasks = self.checklist_card.get_tasks()
        if not tasks:
            QMessageBox.warning(self, "Чек-лист пуст", "Добавьте хотя бы одну задачу.")
            return

        from core.database import save_project
        from core.models import Project, ProjectType, ProjectStatus

        with get_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM projects WHERE title = ?", (self.project_name,)
            ).fetchone()

        if existing:
            project_id = existing["id"]
        else:
            project_type = ProjectType.SOFTWARE if self.theme == "software" else ProjectType.PRODUCTION
            project = Project(
                title=self.project_name,
                project_type=project_type,
                status=ProjectStatus.SPROUT
            )
            save_project(project)
            project_id = project.id

        for i, task_title in enumerate(tasks):
            task = MVPTask(
                project_id=project_id,
                title=task_title,
                order=i
            )
            save_mvp_task(task)

        log_to_project(
            self.project_name,
            "СЕМЯ → РОСТОК — Чек-лист задач",
            "\n".join(f"- {t}" for t in tasks)
        )

        save_to_archive(dict(self.entry))
        update_idea_entry_color(self.entry_id, EntryColor.GREEN.value)

        with get_connection() as conn:
            conn.execute(
                "UPDATE idea_entries SET project_id = ? WHERE id = ?",
                (project_id, self.entry_id)
            )
            conn.commit()

        if hasattr(self, 'autosave_timer'):
            self.autosave_timer.stop()

        self.confirmed.emit(self.entry_id)
        log_to_project(
            self.project_name,
            "ПЕРЕХОД: СЕМЯ → РОСТОК",
            f"Дата перехода: {datetime.now().strftime('%d.%m.%Y %H:%M')}\nЗадач создано: {len(tasks)}"
        )
        self._go_back()

    def _go_back(self):
        if hasattr(self, 'autosave_timer'):
            self.autosave_timer.stop()
        self._autosave()
        self.main_window.go_back()

    def _show_info(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QScrollArea, QWidget
        from core.project_files import get_project_log_path, create_project_folder
        from pathlib import Path
        import os

        dialog = QDialog(self)
        dialog.setWindowTitle("Информация о проекте")
        dialog.setFixedSize(600, 480)
        dialog.setStyleSheet("QDialog { background: #1a1a1a; }")

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        lbl_title = QLabel(f"Проект: {self.project_name}")
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 16px; font-weight: 500;")
        layout.addWidget(lbl_title)

        # Путь к папке
        folder = create_project_folder(self.project_name)
        lbl_path = QLabel(f"📁 Путь: {folder}")
        lbl_path.setStyleSheet("color: #534AB7; font-size: 12px;")
        lbl_path.setWordWrap(True)
        lbl_path.setCursor(Qt.PointingHandCursor)
        lbl_path.mousePressEvent = lambda e: os.startfile(str(folder))
        layout.addWidget(lbl_path)

        # Лог файл
        log_path = get_project_log_path(self.project_name)
        lbl_log_title = QLabel("📋 История изменений:")
        lbl_log_title.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(lbl_log_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #2a2a2a; background: #111111; }")

        log_content = ""
        if log_path.exists():
            try:
                log_content = log_path.read_text(encoding="utf-8")
            except Exception:
                log_content = "Не удалось прочитать лог"
        else:
            log_content = "История пуста"

        lbl_log = QLabel(log_content)
        lbl_log.setStyleSheet("color: #cccccc; font-size: 12px; padding: 10px;")
        lbl_log.setWordWrap(True)
        lbl_log.setAlignment(Qt.AlignTop)
        scroll.setWidget(lbl_log)
        layout.addWidget(scroll)

        btn_open_folder = QPushButton("📁 Открыть папку проекта")
        btn_open_folder.setFixedHeight(38)
        btn_open_folder.setCursor(Qt.PointingHandCursor)
        btn_open_folder.setStyleSheet("""
            QPushButton {
                background: #2a2a2a; color: #ccc;
                border: 1px solid #333; border-radius: 8px; font-size: 13px;
            }
            QPushButton:hover { border-color: #555; color: #fff; }
        """)
        btn_open_folder.clicked.connect(lambda: os.startfile(str(folder)))
        layout.addWidget(btn_open_folder)

        btn_close = QPushButton("Закрыть")
        btn_close.setFixedHeight(38)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background: #534AB7; color: #fff;
                border: none; border-radius: 8px; font-size: 13px;
            }
            QPushButton:hover { background: #6358c8; }
        """)
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)

        dialog.exec()


class FilesCard(QFrame):
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

        lbl = QLabel("Файлы проекта")
        lbl.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(lbl)

        btn_add = QPushButton("+ Добавить файл")
        btn_add.setFixedHeight(36)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #1e1e2e; color: #aaaaff;
                border: 1px solid #333366; border-radius: 6px; font-size: 13px;
            }
            QPushButton:hover { background-color: #252540; }
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
        dialog.setOption(QFileDialog.DontUseNativeDialog, False)
        if dialog.exec():
            paths = dialog.selectedFiles()
            for path in paths:
                copy_file_to_project(self.project_name, path)
            self.refresh_files()
        QTimer.singleShot(200, self._restore_focus)
    
    def _restore_focus(self):
        from PySide6.QtWidgets import QApplication
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


class ChecklistCard(QFrame):
    changed = Signal()

    def __init__(self, saved_tasks: list = None, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QFrame { background-color: #161616; }")
        self._build_ui()

        # Загружаем сохранённые задачи
        if saved_tasks:
            for task in saved_tasks:
                if task:
                    self._add_task_row(task)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        lbl = QLabel("Чек-лист задач")
        lbl.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(lbl)

        input_row = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Новая задача...")
        self.task_input.setFixedHeight(34)
        self.task_input.setStyleSheet("""
            QLineEdit {
                background: #2a2a2a; border: 1px solid #333;
                border-radius: 6px; color: #e8e8e8;
                font-size: 13px; padding: 0 10px;
            }
            QLineEdit:focus { border-color: #534AB7; }
        """)
        self.task_input.returnPressed.connect(self._add_task)
        input_row.addWidget(self.task_input)

        btn_add = QPushButton("+")
        btn_add.setFixedSize(34, 34)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton { background: #534AB7; color: #fff; border: none; border-radius: 6px; font-size: 18px; }
            QPushButton:hover { background: #6358c8; }
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
        row = TaskRow(text, self)
        row.deleted.connect(lambda: self.changed.emit())
        self.tasks_layout.insertWidget(self.tasks_layout.count() - 1, row)

    def get_tasks(self) -> list:
        tasks = []
        for i in range(self.tasks_layout.count() - 1):
            item = self.tasks_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), TaskRow):
                tasks.append(item.widget().get_text())
        return tasks


class TaskRow(QFrame):
    deleted = Signal()

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setStyleSheet("QFrame { background: #1e1e1e; border-radius: 4px; }")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)

        self.lbl = QLabel(text)
        self.lbl.setStyleSheet("color: #e8e8e8; font-size: 13px;")
        layout.addWidget(self.lbl)
        layout.addStretch()

        btn_del = QPushButton("×")
        btn_del.setFixedSize(20, 20)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet("""
            QPushButton { background: transparent; color: #555; border: none; font-size: 16px; }
            QPushButton:hover { color: #E24B4A; }
        """)
        btn_del.clicked.connect(self._delete)
        layout.addWidget(btn_del)

    def _delete(self):
        self.deleted.emit()
        self.deleteLater()

    def get_text(self) -> str:
        return self.lbl.text()


class SimilarDialog(QDialog):
    def __init__(self, current_desc: str, archive_entry, similarity: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Похожая запись найдена")
        self.setFixedSize(600, 380)
        self.setStyleSheet("QDialog { background: #1a1a1a; }")
        self._build_ui(current_desc, archive_entry, similarity)

    def _build_ui(self, current_desc, archive_entry, similarity):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        lbl_title = QLabel(f"Найдена похожая запись (схожесть: {similarity}%)")
        lbl_title.setStyleSheet("color: #FBC02D; font-size: 15px; font-weight: 500;")
        layout.addWidget(lbl_title)

        cards_row = QHBoxLayout()
        cards_row.addWidget(self._make_card("Текущая запись", current_desc, "#1a1a2a"))

        date_archived = archive_entry["date_archived"][:10] if archive_entry.get("date_archived") else ""
        project_name = archive_entry.get("project_name", "")
        subtitle = f"Архив: {date_archived}" + (f" | {project_name}" if project_name else "")
        cards_row.addWidget(self._make_card(subtitle, archive_entry["description"], "#1a2a1a"))
        layout.addLayout(cards_row)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_delete = QPushButton("Удалить текущую")
        btn_delete.setFixedHeight(42)
        btn_delete.setCursor(Qt.PointingHandCursor)
        btn_delete.setStyleSheet("""
            QPushButton { background: #2a1a1a; color: #E24B4A; border: 1px solid #E24B4A; border-radius: 8px; font-size: 14px; }
            QPushButton:hover { background: #3a1a1a; }
        """)
        btn_delete.clicked.connect(self.reject)

        btn_create = QPushButton("Создать новый проект")
        btn_create.setFixedHeight(42)
        btn_create.setCursor(Qt.PointingHandCursor)
        btn_create.setStyleSheet("""
            QPushButton { background: #534AB7; color: #fff; border: none; border-radius: 8px; font-size: 14px; }
            QPushButton:hover { background: #6358c8; }
        """)
        btn_create.clicked.connect(self.accept)

        btn_row.addWidget(btn_delete)
        btn_row.addWidget(btn_create)
        layout.addLayout(btn_row)

    def _make_card(self, title: str, desc: str, bg: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background: {bg}; border-radius: 8px; border: 1px solid #333; }}")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("color: #888888; font-size: 11px;")
        card_layout.addWidget(lbl_t)

        lbl_d = QLabel(desc[:200] + "..." if len(desc) > 200 else desc)
        lbl_d.setWordWrap(True)
        lbl_d.setStyleSheet("color: #e8e8e8; font-size: 13px;")
        card_layout.addWidget(lbl_d)
        card_layout.addStretch()
        return card