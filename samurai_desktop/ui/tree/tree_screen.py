from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame
)
from PySide6.QtCore import Qt
from core.database import get_all_projects
from ui.tree.eco_release_screen import EcoReleaseScreen


class TreeScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setStyleSheet("background-color: #111111;")
        self._build_ui()
        self.load_projects()

    def _refresh(self):
        self.prod_widget.load()
        if hasattr(self, 'eco_widget'):
            self.eco_widget.load_projects()

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
        btn_back.clicked.connect(self.main_window.go_back)
        top_layout.addWidget(btn_back)
        top_layout.addStretch()

        lbl_title = QLabel("🌳 Дерево")
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 18px; font-weight: 500;")
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()

        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedSize(32, 32)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background: transparent; color: #888888;
                border: 1px solid #333; border-radius: 6px; font-size: 14px;
            }
            QPushButton:hover { color: #ffffff; border-color: #555; }
        """)
        btn_refresh.clicked.connect(self._refresh)
        top_layout.addWidget(btn_refresh)

        self.btn_prod = self._tab_btn("Запуск ПРОД", True)
        self.btn_eco = self._tab_btn("ЭКО Релиз", False)
        self.btn_prod.clicked.connect(lambda: self._switch(0))
        self.btn_eco.clicked.connect(lambda: self._switch(1))
        top_layout.addWidget(self.btn_prod)
        top_layout.addSpacing(8)
        top_layout.addWidget(self.btn_eco)
        root.addWidget(top)

        from PySide6.QtWidgets import QStackedWidget
        self.stack = QStackedWidget()

        # Запуск ПРОД
        self.prod_widget = ProdWidget(self.main_window)
        self.stack.addWidget(self.prod_widget)

        # ЭКО Релиз — заглушка
        self.eco_widget = EcoReleaseScreen(self.main_window)
        # Скрываем верхнюю панель EcoReleaseScreen так как TreeScreen уже имеет свою
        self.eco_widget.findChild(QWidget, "top_bar_eco") 
        self.stack.addWidget(self.eco_widget)


        root.addWidget(self.stack)

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
                    padding: 0 16px; font-size: 13px; font-weight: 500;
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
        self.stack.setCurrentIndex(index)
        self._style_tab(self.btn_prod, index == 0)
        self._style_tab(self.btn_eco, index == 1)

    def load_projects(self):
        self.prod_widget.load()


class ProdWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
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
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch()

        scroll.setWidget(self.container)
        root.addWidget(scroll)

    def load(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        projects = get_all_projects()
        tree_projects = [p for p in projects if p["status"] == "tree"]

        # Стабильные — вверху
        stable = []
        normal = []
        for p in tree_projects:
            from core.database import get_connection
            with get_connection() as conn:
                tp = conn.execute(
                    "SELECT stability_achieved FROM tree_projects WHERE project_id = ?",
                    (p["id"],)
                ).fetchone()
            if tp and tp["stability_achieved"]:
                stable.append(p)
            else:
                normal.append(p)

        for p in stable + normal:
            card = TreeProjectCard(p, self.main_window)
            self.list_layout.insertWidget(self.list_layout.count() - 1, card)


class TreeProjectCard(QFrame):
    def __init__(self, project, main_window):
        super().__init__()
        self.project_id = project["id"]
        self.main_window = main_window
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(80)

        # Проверяем стабильность
        from core.database import get_connection
        with get_connection() as conn:
            tp = conn.execute(
                "SELECT stability_achieved FROM tree_projects WHERE project_id = ?",
                (project["id"],)
            ).fetchone()
        is_stable = tp and tp["stability_achieved"]

        if is_stable:
            self.setStyleSheet("""
                QFrame {
                    background-color: #0f2a0f;
                    border: 1px solid #388E3C;
                    border-radius: 10px;
                }
                QFrame:hover { border: 2px solid #4caf50; }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #1e1e1e;
                    border: 1px solid #2a2a2a;
                    border-radius: 10px;
                }
                QFrame:hover { border: 1px solid #534AB7; }
            """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)

        info = QVBoxLayout()
        info.setSpacing(4)

        lbl_title = QLabel(project["title"] or "Без названия")
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 15px; font-weight: 500;")
        info.addWidget(lbl_title)

        desc = project["description"] or ""
        if desc:
            lbl_desc = QLabel(desc[:80] + "..." if len(desc) > 80 else desc)
            lbl_desc.setStyleSheet("color: #666666; font-size: 12px;")
            info.addWidget(lbl_desc)

        date_str = project["date_launched"][:10] if project["date_launched"] else project["date_created"][:10]
        lbl_date = QLabel(f"Запущен: {date_str}")
        lbl_date.setStyleSheet("color: #555555; font-size: 11px;")
        info.addWidget(lbl_date)

        layout.addLayout(info)
        layout.addStretch()

        if is_stable:
            lbl_stable = QLabel("✓ Стабильность")
            lbl_stable.setStyleSheet("color: #388E3C; font-size: 12px;")
            layout.addWidget(lbl_stable)

        lbl_arrow = QLabel("→")
        lbl_arrow.setStyleSheet("color: #444; font-size: 18px;")
        layout.addWidget(lbl_arrow)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            from ui.tree.project_card import TreeProjectDetail
            screen = TreeProjectDetail(self.project_id, self.main_window)
            self.main_window.stack.addWidget(screen)
            self.main_window.stack.setCurrentWidget(screen)

    def contextMenuEvent(self, event):
        from PySide6.QtWidgets import QMenu, QMessageBox
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e1e; border: 1px solid #333;
                border-radius: 6px; color: #e8e8e8; font-size: 13px;
            }
            QMenu::item { padding: 8px 20px; }
            QMenu::item:selected { background-color: #2a2a2a; }
        """)
        action_refresh = menu.addAction("🔄 Обновить")
        action_delete = menu.addAction("🗑 Удалить проект")
        action = menu.exec(event.globalPos())
        if action == action_refresh:
            from ui.tree.project_card import TreeProjectDetail
            screen = TreeProjectDetail(self.project_id, self.main_window)
            self.main_window.stack.addWidget(screen)
            self.main_window.stack.setCurrentWidget(screen)
        elif action == action_delete:
            msg = QMessageBox(self)
            msg.setWindowTitle("Удалить")
            msg.setText("Удалить проект из Дерева?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setStyleSheet("QMessageBox { background: #1a1a1a; } QLabel { color: #e8e8e8; }")
            if msg.exec() == QMessageBox.Yes:
                from core.database import get_connection
                with get_connection() as conn:
                    conn.execute("DELETE FROM tree_projects WHERE project_id = ?", (self.project_id,))
                    conn.execute("DELETE FROM projects WHERE id = ?", (self.project_id,))
                    conn.commit()
                self.hide()
                self.deleteLater()