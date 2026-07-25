from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget
)
from PySide6.QtCore import Qt
from core.database import get_connection


class TreeProjectDetail(QWidget):
    def __init__(self, project_id: str, main_window):
        super().__init__()
        self.project_id = project_id
        self.main_window = main_window
        self.setStyleSheet("background: #111111;")
        self._ensure_tree_project()
        self._build_ui()

    def _ensure_tree_project(self):
        with get_connection() as conn:
            exists = conn.execute(
                "SELECT 1 FROM tree_projects WHERE project_id = ?",
                (self.project_id,)
            ).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO tree_projects (project_id) VALUES (?)",
                    (self.project_id,)
                )
                conn.commit()

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

        with get_connection() as conn:
            proj = conn.execute(
                "SELECT title FROM projects WHERE id = ?",
                (self.project_id,)
            ).fetchone()
        title = proj["title"] if proj else "Проект"

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 16px; font-weight: 500;")
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()

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

        # Кнопка ЭКО (показывается при стабильности)
        self.btn_eco = QPushButton("🌿 ЭКО")
        self.btn_eco.setFixedHeight(32)
        self.btn_eco.setCursor(Qt.PointingHandCursor)
        self.btn_eco.setStyleSheet("""
            QPushButton {
                background-color: #1a3a1a; color: #4caf50;
                border: 1px solid #388E3C; border-radius: 6px;
                padding: 0 16px; font-size: 13px;
            }
            QPushButton:hover { background-color: #2a4a2a; }
        """)
        self.btn_eco.clicked.connect(self._on_eco)
        self.btn_eco.setVisible(False)
        top_layout.addWidget(self.btn_eco)

        root.addWidget(top)

        # Вкладки
        tabs = QWidget()
        tabs.setFixedHeight(44)
        tabs.setStyleSheet("background: #1a1a1a;")
        tabs_layout = QHBoxLayout(tabs)
        tabs_layout.setContentsMargins(16, 6, 16, 6)
        tabs_layout.setSpacing(8)

        self.btn_checklist = self._tab_btn("Чек-лист", True)
        self.btn_keys = self._tab_btn("Ключи/инструменты", False)
        self.btn_finance = self._tab_btn("Финансы", False)
        self.btn_checklist.clicked.connect(lambda: self._switch(0))
        self.btn_keys.clicked.connect(lambda: self._switch(1))
        self.btn_finance.clicked.connect(lambda: self._switch(2))

        tabs_layout.addWidget(self.btn_checklist)
        tabs_layout.addWidget(self.btn_keys)
        tabs_layout.addWidget(self.btn_finance)
        tabs_layout.addStretch()
        root.addWidget(tabs)

        # Стек вкладок
        self.tab_stack = QStackedWidget()

        from ui.tree.keys_widget import KeysWidget
        from ui.tree.finance_widget import FinanceWidget

        self.checklist_widget = ChecklistWidget(self.project_id)
        self.keys_widget = KeysWidget(self.project_id)
        self.finance_widget = FinanceWidget(self.project_id, self)

        self.tab_stack.addWidget(self.checklist_widget)
        self.tab_stack.addWidget(self.keys_widget)
        self.tab_stack.addWidget(self.finance_widget)

        root.addWidget(self.tab_stack)
        self._check_stability()

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

    def _switch(self, index):
        self.tab_stack.setCurrentIndex(index)
        self._style_tab(self.btn_checklist, index == 0)
        self._style_tab(self.btn_keys, index == 1)
        self._style_tab(self.btn_finance, index == 2)

    def _check_stability(self):
        with get_connection() as conn:
            tp = conn.execute(
                "SELECT stability_achieved FROM tree_projects WHERE project_id = ?",
                (self.project_id,)
            ).fetchone()
        if tp and tp["stability_achieved"]:
            self.btn_eco.setVisible(True)

    def notify_stability(self):
        self.btn_eco.setVisible(True)

    def _on_eco(self):
        from ui.placeholder_screen import PlaceholderScreen
        screen = PlaceholderScreen(
            "🌿 Экосистема",
            "Запрос отправлен в Росток/ЭКОСИСТЕМА",
            self.main_window
        )
        self.main_window.stack.addWidget(screen)
        self.main_window.stack.setCurrentWidget(screen)

    def _go_back(self):
        self.main_window.stack.setCurrentIndex(
            self.main_window.stack.count() - 2
        )

    def _show_info(self):
        import os
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QScrollArea
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
    
        date_created = proj["date_created"][:10] if proj["date_created"] else ""
        date_launched = proj["date_launched"][:10] if proj["date_launched"] else "—"
        lbl_dates = QLabel(f"Создан: {date_created}  |  Запущен: {date_launched}  |  Статус: {proj['status']}")
        lbl_dates.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(lbl_dates)
    
        folder = create_project_folder(project_name)
        lbl_path = QLabel(f"📁 {folder}")
        lbl_path.setStyleSheet("color: #534AB7; font-size: 12px;")
        lbl_path.setWordWrap(True)
        lbl_path.setCursor(Qt.PointingHandCursor)
        lbl_path.mousePressEvent = lambda e: os.startfile(str(folder))
        layout.addWidget(lbl_path)
    
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


class ChecklistWidget(QWidget):
    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        self.setStyleSheet("background: #111111;")
        self._build_ui()
        self.load()

    def _build_ui(self):
        from PySide6.QtWidgets import QScrollArea
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

    def load(self):
        import json
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
        with get_connection() as conn:
            tp = conn.execute(
                "SELECT checklists FROM tree_projects WHERE project_id = ?",
                (self.project_id,)
            ).fetchone()
    
        if not tp:
            # Создаём запись если нет
            with get_connection() as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO tree_projects (project_id) VALUES (?)",
                    (self.project_id,)
                )
                conn.commit()
            # Берём задачи из МВП и добавляем в чек-лист
            from core.database import get_mvp_tasks
            tasks = get_mvp_tasks(self.project_id)
            items = [{"title": t["title"], "done": False} for t in tasks]
            with get_connection() as conn:
                conn.execute(
                    "UPDATE tree_projects SET checklists = ? WHERE project_id = ?",
                    (json.dumps(items, ensure_ascii=False), self.project_id)
                )
                conn.commit()
        else:
            items = json.loads(tp["checklists"]) if tp["checklists"] else []
    
            # Если пусто — пробуем заполнить из МВП задач
            if not items:
                from core.database import get_mvp_tasks
                tasks = get_mvp_tasks(self.project_id)
                items = [{"title": t["title"], "done": False} for t in tasks]
                if items:
                    with get_connection() as conn:
                        conn.execute(
                            "UPDATE tree_projects SET checklists = ? WHERE project_id = ?",
                            (json.dumps(items, ensure_ascii=False), self.project_id)
                        )
                        conn.commit()
    
        # Кнопка добавить пункт
        btn_add = QPushButton("+ Добавить пункт")
        btn_add.setFixedHeight(36)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton {
                background: #1e1e1e; color: #888;
                border: 1px dashed #333; font-size: 13px;
            }
            QPushButton:hover { color: #fff; border-color: #555; }
        """)
        btn_add.clicked.connect(self._add_item)
        self.list_layout.insertWidget(0, btn_add)
    
        if not items:
            lbl = QLabel("Нет задач в чек-листе")
            lbl.setStyleSheet("color: #555555; font-size: 14px;")
            lbl.setAlignment(Qt.AlignCenter)
            self.list_layout.insertWidget(1, lbl)
            return
    
        for i, item in enumerate(items):
            row = ChecklistRow(item, i, self.project_id, self)
            self.list_layout.insertWidget(
                self.list_layout.count() - 1, row
            )
    
    def _add_item(self):
        import json
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "Новый пункт", "Введите пункт чек-листа:")
        if ok and text.strip():
            with get_connection() as conn:
                tp = conn.execute(
                    "SELECT checklists FROM tree_projects WHERE project_id = ?",
                    (self.project_id,)
                ).fetchone()
                items = json.loads(tp["checklists"]) if tp and tp["checklists"] else []
                items.append({"title": text.strip(), "done": False})
                conn.execute(
                    "UPDATE tree_projects SET checklists = ? WHERE project_id = ?",
                    (json.dumps(items, ensure_ascii=False), self.project_id)
                )
                conn.commit()
            self.load()


class ChecklistRow(QWidget):
    def __init__(self, item: dict, index: int, project_id: str, parent_widget):
        super().__init__()
        self.index = index
        self.project_id = project_id
        self.parent_widget = parent_widget
        self.setFixedHeight(44)
        self._build_ui(item)

    def _build_ui(self, item):
        from PySide6.QtWidgets import QCheckBox
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        cb = QCheckBox()
        cb.setChecked(item.get("done", False))
        cb.setStyleSheet("""
            QCheckBox::indicator {
                width: 18px; height: 18px;
                border: 2px solid #444; border-radius: 4px;
                background: #2a2a2a;
            }
            QCheckBox::indicator:checked {
                background: #388E3C; border-color: #388E3C;
            }
        """)
        cb.stateChanged.connect(lambda s: self._toggle(s))
        layout.addWidget(cb)

        lbl = QLabel(item.get("title", ""))
        color = "#666666" if item.get("done") else "#e8e8e8"
        lbl.setStyleSheet(f"color: {color}; font-size: 14px;")
        layout.addWidget(lbl)
        layout.addStretch()

    def _toggle(self, state):
        import json
        with get_connection() as conn:
            tp = conn.execute(
                "SELECT checklists FROM tree_projects WHERE project_id = ?",
                (self.project_id,)
            ).fetchone()
            items = json.loads(tp["checklists"]) if tp and tp["checklists"] else []
            if self.index < len(items):
                if isinstance(items[self.index], dict):
                    items[self.index]["done"] = (state == Qt.Checked)
                else:
                    items[self.index] = {
                        "title": str(items[self.index]),
                        "done": (state == Qt.Checked)
                    }
            conn.execute(
                "UPDATE tree_projects SET checklists = ? WHERE project_id = ?",
                (json.dumps(items, ensure_ascii=False), self.project_id)
            )
            conn.commit()