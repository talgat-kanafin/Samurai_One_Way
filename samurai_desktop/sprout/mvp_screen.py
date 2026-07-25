from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame
)
from PySide6.QtCore import Qt
from core.database import get_all_projects


class MVPScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setStyleSheet("background-color: #111111;")
        self._build_ui()
        self.load_projects()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Центральный квадрат МВП
        top = QWidget()
        top.setFixedHeight(140)
        top.setStyleSheet("background-color: #111111;")
        top_layout = QHBoxLayout(top)
        top_layout.setAlignment(Qt.AlignCenter)

        center = QLabel("МВП")
        center.setFixedSize(100, 100)
        center.setAlignment(Qt.AlignCenter)
        center.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                color: #e8e8e8;
                font-size: 16px;
                font-weight: 500;
                border: 2px solid #444444;
                border-radius: 8px;
            }
        """)
        top_layout.addWidget(center)
        root.addWidget(top)

        # Список проектов
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #111111; }")

        self.container = QWidget()
        self.container.setStyleSheet("background: #111111;")
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(40, 8, 40, 8)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch()

        scroll.setWidget(self.container)
        root.addWidget(scroll)

    def load_projects(self):
        # Очищаем список
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        projects = get_all_projects()
        sprout_projects = [p for p in projects if p["status"] == "sprout"]

        for i, project in enumerate(sprout_projects, 1):
            card = ProjectCard(i, project, self.main_window)
            self.list_layout.insertWidget(self.list_layout.count() - 1, card)


class ProjectCard(QFrame):
    def __init__(self, number: int, project, main_window):
        super().__init__()
        self.project_id = project["id"]
        self.main_window = main_window
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(72)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #2a2a2a;
                border-radius: 10px;
            }
            QFrame:hover {
                border: 1px solid #534AB7;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)

        # Номер
        lbl_num = QLabel(f"#{number}")
        lbl_num.setFixedWidth(40)
        lbl_num.setStyleSheet("color: #534AB7; font-size: 16px; font-weight: 500;")
        layout.addWidget(lbl_num)

        # Название и дата
        info = QVBoxLayout()
        info.setSpacing(2)

        lbl_title = QLabel(project["title"] or f"Проект #{number}")
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 14px; font-weight: 500;")
        info.addWidget(lbl_title)

        date_str = project["date_created"][:10] if project["date_created"] else ""
        lbl_date = QLabel(date_str)
        lbl_date.setStyleSheet("color: #666666; font-size: 12px;")
        info.addWidget(lbl_date)

        layout.addLayout(info)
        layout.addStretch()

        lbl_arrow = QLabel("→")
        lbl_arrow.setStyleSheet("color: #444444; font-size: 18px;")
        layout.addWidget(lbl_arrow)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            from ui.sprout.mvp_card import MVPCard
            screen = MVPCard(self.project_id, self.main_window)
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
            from ui.sprout.mvp_card import MVPCard
            screen = MVPCard(self.project_id, self.main_window)
            self.main_window.stack.addWidget(screen)
            self.main_window.stack.setCurrentWidget(screen)
        elif action == action_delete:
            msg = QMessageBox(self)
            msg.setWindowTitle("Удалить")
            msg.setText("Удалить проект и все его задачи?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setStyleSheet("QMessageBox { background: #1a1a1a; } QLabel { color: #e8e8e8; }")
            if msg.exec() == QMessageBox.Yes:
                from core.database import get_connection
                with get_connection() as conn:
                    conn.execute("DELETE FROM mvp_tasks WHERE project_id = ?", (self.project_id,))
                    conn.execute("DELETE FROM projects WHERE id = ?", (self.project_id,))
                    conn.commit()
                self.hide()
                self.deleteLater()