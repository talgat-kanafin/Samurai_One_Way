from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QCheckBox, QInputDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from core.database import get_mvp_tasks, save_mvp_task
from core.models import MVPTask, TaskStatus, TestMark


class MVPCard(QWidget):
    def __init__(self, project_id: str, main_window):
        super().__init__()
        self.project_id = project_id
        self.main_window = main_window
        self.setStyleSheet("background-color: #111111;")
        self._build_ui()
        self.load_tasks()

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

        self.lbl_title = QLabel("МВП — Проект")
        self.lbl_title.setStyleSheet("color: #e8e8e8; font-size: 16px; font-weight: 500;")
        top_layout.addWidget(self.lbl_title)
        top_layout.addStretch()
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

        # Вкладки
        tabs = QWidget()
        tabs.setFixedHeight(44)
        tabs.setStyleSheet("background-color: #1a1a1a;")
        tabs_layout = QHBoxLayout(tabs)
        tabs_layout.setContentsMargins(16, 6, 16, 6)
        tabs_layout.setSpacing(8)

        self.btn_work = self._tab_btn("В работе", True)
        self.btn_test = self._tab_btn("Тест", False)
        self.btn_work.clicked.connect(lambda: self._switch_tab(0))
        self.btn_test.clicked.connect(lambda: self._switch_tab(1))
        tabs_layout.addWidget(self.btn_work)
        tabs_layout.addWidget(self.btn_test)
        tabs_layout.addStretch()
        root.addWidget(tabs)

        # Контент
        from PySide6.QtWidgets import QStackedWidget
        self.tab_stack = QStackedWidget()

        # Кнопка отправки в тест
        btn_to_test = QPushButton("→ Отправить в Тестирование")
        btn_to_test.setFixedHeight(40)
        btn_to_test.setCursor(Qt.PointingHandCursor)
        btn_to_test.setStyleSheet("""
            QPushButton {
                background-color: #1a2a3a; color: #aaaaff;
                border: 1px solid #333366;
                font-size: 13px; font-weight: 500;
            }
            QPushButton:hover { background-color: #252545; }
        """)
        btn_to_test.clicked.connect(self._send_checked_to_test)
        root.addWidget(btn_to_test)

        # Вкладка "В работе"
        self.work_widget = WorkWidget(self.project_id, self)
        self.tab_stack.addWidget(self.work_widget)

        # Вкладка "Тест"
        self.test_widget = TestWidget(self.project_id, self)
        self.tab_stack.addWidget(self.test_widget)

        root.addWidget(self.tab_stack)

        # Кнопка ЗАПУСК
        self.btn_launch = QPushButton("🚀 ЗАПУСК")
        self.btn_launch.setFixedHeight(52)
        self.btn_launch.setCursor(Qt.PointingHandCursor)
        self.btn_launch.setVisible(False)
        self.btn_launch.setStyleSheet("""
            QPushButton {
                background-color: #388E3C; color: #ffffff;
                border: none; font-size: 16px; font-weight: 500;
            }
            QPushButton:hover { background-color: #4caf50; }
        """)
        self.btn_launch.clicked.connect(self._on_launch)
        root.addWidget(self.btn_launch)

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
                    background-color: #534AB7; color: #fff;
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
        self._style_tab(self.btn_work, index == 0)
        self._style_tab(self.btn_test, index == 1)
        self.check_launch_visible()

    def load_tasks(self):
        self.work_widget.load()
        self.test_widget.load()
        self.check_launch_visible()

    def check_launch_visible(self):
        tasks = get_mvp_tasks(self.project_id)
        work_tasks = [t for t in tasks if t["status"] == "in_work"]
        test_tasks = [t for t in tasks if t["status"] == "in_test"]
        all_done = all(
            t["test_mark"] in ("green", "blue") for t in test_tasks
        ) if test_tasks else False
        self.btn_launch.setVisible(
            len(work_tasks) == 0 and len(test_tasks) > 0 and all_done
        )

    def _on_launch(self):
        name, ok = QInputDialog.getText(
            self, "Запуск проекта", "Введите название проекта:"
        )
        if ok and name.strip():
            self._launch_project(name.strip())

    def _launch_project(self, name: str):
        from core.database import save_project, get_connection
        from core.models import Project, ProjectType, ProjectStatus
        import json
        from datetime import datetime

        with get_connection() as conn:
            proj = conn.execute(
                "SELECT * FROM projects WHERE id = ?", (self.project_id,)
            ).fetchone()

        project_type = ProjectType(proj["project_type"]) if proj else ProjectType.SOFTWARE

        with get_connection() as conn:
            conn.execute(
                "UPDATE projects SET title = ?, status = ?, date_launched = ? WHERE id = ?",
                (name, ProjectStatus.TREE.value, datetime.now().isoformat(), self.project_id)
            )
            conn.commit()

        from ui.placeholder_screen import PlaceholderScreen
        screen = PlaceholderScreen(
            f"🚀 {name}",
            "Проект запущен и перемещён в Дерево/Запуск ПРОД",
            self.main_window
        )
        from core.project_files import log_to_project
        from datetime import datetime
        log_to_project(
            name,
            "ПЕРЕХОД: РОСТОК → ДЕРЕВО",
            f"Дата запуска: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        self.main_window.stack.addWidget(screen)
        self.main_window.stack.setCurrentWidget(screen)

    def _go_back(self):
        self.main_window.stack.setCurrentIndex(
            self.main_window.stack.count() - 2
        )

    def _send_checked_to_test(self):
        from core.database import get_connection
        # Берём все отмеченные задачи из вкладки "В работе"
        moved = 0
        for i in range(self.work_widget.tasks_layout.count() - 1):
            item = self.work_widget.tasks_layout.itemAt(i)
            if not item or not item.widget():
                continue
            row = item.widget()
            if isinstance(row, TaskRow) and row.checkbox.isChecked():
                with get_connection() as conn:
                    conn.execute(
                        "UPDATE mvp_tasks SET status = ? WHERE id = ?",
                        (TaskStatus.IN_TEST.value, row.task_id)
                    )
                    conn.commit()
                moved += 1

        if moved == 0:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Нет задач", "Отметьте хотя бы одну задачу галочкой.")
            return

        self.work_widget.load()
        self.test_widget.load()
        self._switch_tab(1)
        self.check_launch_visible()

    def _show_info(self):
        import os
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QScrollArea
        from core.database import get_connection
        from core.project_files import get_project_log_path, create_project_folder
    
        with get_connection() as conn:
            proj = conn.execute(
                "SELECT * FROM projects WHERE id = ?", (self.project_id,)
            ).fetchone()
    
        if not proj:
            return
    
        project_name = proj["title"] or "Без названия"
    
        dialog = QDialog(self)
        dialog.setWindowTitle("Информация о проекте")
        dialog.setFixedSize(600, 480)
        dialog.setStyleSheet("QDialog { background: #1a1a1a; }")
    
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
    
        lbl_title = QLabel(f"Проект: {project_name}")
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 16px; font-weight: 500;")
        layout.addWidget(lbl_title)
    
        # Статус и даты
        date_created = proj["date_created"][:10] if proj["date_created"] else ""
        date_launched = proj["date_launched"][:10] if proj["date_launched"] else "—"
        lbl_dates = QLabel(f"Создан: {date_created}  |  Запущен: {date_launched}  |  Статус: {proj['status']}")
        lbl_dates.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(lbl_dates)
    
        # Путь к папке
        folder = create_project_folder(project_name)
        lbl_path = QLabel(f"📁 {folder}")
        lbl_path.setStyleSheet("color: #534AB7; font-size: 12px;")
        lbl_path.setWordWrap(True)
        lbl_path.setCursor(Qt.PointingHandCursor)
        lbl_path.mousePressEvent = lambda e: os.startfile(str(folder))
        layout.addWidget(lbl_path)
    
        # Лог
        lbl_log_title = QLabel("📋 История:")
        lbl_log_title.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(lbl_log_title)
    
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #2a2a2a; background: #111111; }")
    
        log_path = get_project_log_path(project_name)
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
    
        btn_row = QHBoxLayout()
    
        btn_open = QPushButton("📁 Открыть папку")
        btn_open.setFixedHeight(38)
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.setStyleSheet("""
            QPushButton {
                background: #2a2a2a; color: #ccc;
                border: 1px solid #333; border-radius: 8px; font-size: 13px;
            }
            QPushButton:hover { border-color: #555; color: #fff; }
        """)
        btn_open.clicked.connect(lambda: os.startfile(str(folder)))
        btn_row.addWidget(btn_open)
    
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
        btn_row.addWidget(btn_close)
    
        layout.addLayout(btn_row)
        dialog.exec()


class WorkWidget(QWidget):
    def __init__(self, project_id: str, card):
        super().__init__()
        self.project_id = project_id
        self.card = card
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
        self.tasks_layout = QVBoxLayout(self.container)
        self.tasks_layout.setContentsMargins(24, 12, 24, 12)
        self.tasks_layout.setSpacing(4)
        self.tasks_layout.addStretch()

        scroll.setWidget(self.container)
        root.addWidget(scroll)

        # Кнопка добавить задачу
        btn_add = QPushButton("+ Добавить задачу")
        btn_add.setFixedHeight(44)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #1e1e1e; color: #888888;
                border: 1px dashed #333333; font-size: 14px;
            }
            QPushButton:hover { color: #ffffff; border-color: #555; }
        """)
        btn_add.clicked.connect(self._add_task)
        root.addWidget(btn_add)

    def load(self):
        while self.tasks_layout.count() > 1:
            item = self.tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tasks = get_mvp_tasks(self.project_id)
        work_tasks = [t for t in tasks if t["status"] == "in_work"]

        for task in work_tasks:
            row = TaskRow(task, self)
            self.tasks_layout.insertWidget(
                self.tasks_layout.count() - 1, row
            )

    def _add_task(self):
        tasks = get_mvp_tasks(self.project_id)
        order = len(tasks)
        task = MVPTask(
            project_id=self.project_id,
            title="Новая задача",
            order=order
        )
        save_mvp_task(task)
        self.load()
        self.card.check_launch_visible()


class TaskRow(QFrame):
    def __init__(self, task_data, work_widget: WorkWidget):
        super().__init__()
        self.task_id = task_data["id"]
        self.work_widget = work_widget
        self.project_id = task_data["project_id"]
        self.is_subtask = task_data["parent_task_id"] is not None
        self.setStyleSheet("background: transparent;")
        self.setFixedHeight(44)
        self._build_ui(task_data)

    def _build_ui(self, task_data):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(self.is_subtask * 24, 0, 0, 0)
        layout.setSpacing(8)

        self.checkbox = QCheckBox()
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 18px; height: 18px;
                border: 2px solid #444; border-radius: 4px;
                background: #2a2a2a;
            }
            QCheckBox::indicator:checked {
                background: #388E3C; border-color: #388E3C;
            }
        """)
        self.checkbox.stateChanged.connect(self._on_check)
        layout.addWidget(self.checkbox)

        self.title_edit = QLineEdit(task_data["title"])
        self.title_edit.setStyleSheet("""
            QLineEdit {
                background: transparent; border: none;
                color: #e8e8e8; font-size: 14px;
            }
            QLineEdit:focus {
                border-bottom: 1px solid #534AB7;
            }
        """)
        self.title_edit.editingFinished.connect(self._save_title)
        layout.addWidget(self.title_edit)

    def _save_title(self):
        from core.database import get_connection
        with get_connection() as conn:
            conn.execute(
                "UPDATE mvp_tasks SET title = ? WHERE id = ?",
                (self.title_edit.text(), self.task_id)
            )
            conn.commit()

    def _on_check(self, state):
        if state == Qt.Checked:
            from core.database import get_connection
            with get_connection() as conn:
                conn.execute(
                    "UPDATE mvp_tasks SET status = ? WHERE id = ?",
                    (TaskStatus.IN_TEST.value, self.task_id)
                )
                conn.commit()
            # Даём время Qt обработать событие
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self._refresh_parent)
    
    def _refresh_parent(self):
        self.work_widget.load()
        self.work_widget.card.test_widget.load()
        self.work_widget.card._switch_tab(1)  # Переключаем на вкладку Тест
        self.work_widget.card.check_launch_visible()


class TestWidget(QWidget):
    def __init__(self, project_id: str, card):
        super().__init__()
        self.project_id = project_id
        self.card = card
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
        self.tasks_layout = QVBoxLayout(self.container)
        self.tasks_layout.setContentsMargins(24, 12, 24, 12)
        self.tasks_layout.setSpacing(4)
        self.tasks_layout.addStretch()

        scroll.setWidget(self.container)
        root.addWidget(scroll)

    def load(self):
        while self.tasks_layout.count() > 1:
            item = self.tasks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tasks = get_mvp_tasks(self.project_id)
        test_tasks = [t for t in tasks if t["status"] == "in_test"]

        for task in test_tasks:
            row = TestRow(task, self)
            self.tasks_layout.insertWidget(
                self.tasks_layout.count() - 1, row
            )


class TestRow(QFrame):
    def __init__(self, task_data, test_widget: TestWidget):
        super().__init__()
        self.task_id = task_data["id"]
        self.test_widget = test_widget
        self.current_mark = task_data["test_mark"]
        self.setFixedHeight(52)
        self._build_ui(task_data)
        self._apply_style()

    def _build_ui(self, task_data):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        self.lbl_title = QLabel(task_data["title"])
        self.lbl_title.setStyleSheet("color: #e8e8e8; font-size: 14px;")
        layout.addWidget(self.lbl_title)
        layout.addStretch()

        # Три кнопки статуса
        self.btn_green = self._mark_btn("✓", "#388E3C", "green")
        self.btn_red   = self._mark_btn("✗", "#D32F2F", "red")
        self.btn_blue  = self._mark_btn("◈", "#1565C0", "blue")

        layout.addWidget(self.btn_green)
        layout.addWidget(self.btn_red)
        layout.addWidget(self.btn_blue)

    def _mark_btn(self, text, color, mark):
        btn = QPushButton(text)
        btn.setFixedSize(36, 36)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color}33;
                color: {color};
                border: 1px solid {color}66;
                border-radius: 6px;
                font-size: 16px;
            }}
            QPushButton:hover {{ background-color: {color}66; }}
        """)
        btn.clicked.connect(lambda: self._set_mark(mark))
        return btn

    def _set_mark(self, mark: str):
        self.current_mark = mark
        from core.database import get_connection
        with get_connection() as conn:
            conn.execute(
                "UPDATE mvp_tasks SET test_mark = ? WHERE id = ?",
                (mark, self.task_id)
            )
            conn.commit()
        self._apply_style()
        self.test_widget.card.check_launch_visible()

    def _apply_style(self):
        if self.current_mark == "red":
            self.setStyleSheet("""
                QFrame {
                    background-color: #2a1010;
                    border: 1px solid #D32F2F;
                    border-radius: 8px;
                }
            """)
        elif self.current_mark == "green":
            self.setStyleSheet("""
                QFrame {
                    background-color: #102a10;
                    border: 1px solid #388E3C;
                    border-radius: 8px;
                }
            """)
        elif self.current_mark == "blue":
            self.setStyleSheet("""
                QFrame {
                    background-color: #10102a;
                    border: 1px solid #1565C0;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #1e1e1e;
                    border: 1px solid #2a2a2a;
                    border-radius: 8px;
                }
            """)

    def contextMenuEvent(self, event):
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e1e; border: 1px solid #333;
                border-radius: 6px; color: #e8e8e8; font-size: 13px;
            }
            QMenu::item { padding: 8px 20px; }
            QMenu::item:selected { background-color: #2a2a2a; }
        """)
        action_delete = menu.addAction("🗑 Удалить задачу")
        action = menu.exec(event.globalPos())
        if action == action_delete:
            from core.database import get_connection
            with get_connection() as conn:
                conn.execute("DELETE FROM mvp_tasks WHERE id = ?", (self.task_id,))
                conn.commit()
            self.work_widget.load()
            self.work_widget.card.check_launch_visible()