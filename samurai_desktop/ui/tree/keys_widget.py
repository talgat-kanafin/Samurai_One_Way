import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QDialog,
    QLineEdit, QTextEdit
)
from PySide6.QtCore import Qt
from core.database import get_connection


class KeysWidget(QWidget):
    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        self.setStyleSheet("background: #111111;")
        self._build_ui()
        self.load()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # Кнопка добавить
        top = QWidget()
        top.setFixedHeight(52)
        top.setStyleSheet("background: #1a1a1a; border-bottom: 1px solid #2a2a2a;")
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(24, 0, 24, 0)
        top_layout.addStretch()

        btn_add = QPushButton("+ Добавить")
        btn_add.setFixedHeight(34)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #534AB7; color: #fff;
                border: none; border-radius: 6px;
                padding: 0 16px; font-size: 13px;
            }
            QPushButton:hover { background-color: #6358c8; }
        """)
        btn_add.clicked.connect(self._add_item)
        top_layout.addWidget(btn_add)
        root.addWidget(top)

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

        with get_connection() as conn:
            tp = conn.execute(
                "SELECT keys_tools FROM tree_projects WHERE project_id = ?",
                (self.project_id,)
            ).fetchone()

        items = json.loads(tp["keys_tools"]) if tp and tp["keys_tools"] else []

        for i, item in enumerate(items):
            row = KeyRow(item, i, self.project_id, self)
            self.list_layout.insertWidget(self.list_layout.count() - 1, row)

    def _add_item(self):
        dialog = KeyDialog(self)
        if dialog.exec():
            title, desc = dialog.get_values()
            if title:
                with get_connection() as conn:
                    tp = conn.execute(
                        "SELECT keys_tools FROM tree_projects WHERE project_id = ?",
                        (self.project_id,)
                    ).fetchone()
                    items = json.loads(tp["keys_tools"]) if tp and tp["keys_tools"] else []
                    items.append({"title": title, "description": desc})
                    conn.execute(
                        "UPDATE tree_projects SET keys_tools = ? WHERE project_id = ?",
                        (json.dumps(items, ensure_ascii=False), self.project_id)
                    )
                    conn.commit()
                self.load()


class KeyRow(QFrame):
    def __init__(self, item: dict, index: int, project_id: str, parent_widget):
        super().__init__()
        self.index = index
        self.project_id = project_id
        self.parent_widget = parent_widget
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(52)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #2a2a2a;
                border-radius: 8px;
            }
            QFrame:hover { border-color: #534AB7; }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)

        lbl = QLabel(item.get("title", ""))
        lbl.setStyleSheet("color: #e8e8e8; font-size: 14px;")
        layout.addWidget(lbl)
        layout.addStretch()

        lbl_arrow = QLabel("→")
        lbl_arrow.setStyleSheet("color: #444; font-size: 16px;")
        layout.addWidget(lbl_arrow)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            with get_connection() as conn:
                tp = conn.execute(
                    "SELECT keys_tools FROM tree_projects WHERE project_id = ?",
                    (self.project_id,)
                ).fetchone()
            items = json.loads(tp["keys_tools"]) if tp and tp["keys_tools"] else []
            if self.index < len(items):
                item = items[self.index]
                dialog = KeyDialog(self.parent_widget, item["title"], item.get("description", ""))
                if dialog.exec():
                    title, desc = dialog.get_values()
                    items[self.index] = {"title": title, "description": desc}
                    with get_connection() as conn:
                        conn.execute(
                            "UPDATE tree_projects SET keys_tools = ? WHERE project_id = ?",
                            (json.dumps(items, ensure_ascii=False), self.project_id)
                        )
                        conn.commit()
                    self.parent_widget.load()

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
        action_delete = menu.addAction("🗑 Удалить")
        action = menu.exec(event.globalPos())
        if action == action_delete:
            with get_connection() as conn:
                tp = conn.execute(
                    "SELECT keys_tools FROM tree_projects WHERE project_id = ?",
                    (self.project_id,)
                ).fetchone()
            import json
            items = json.loads(tp["keys_tools"]) if tp and tp["keys_tools"] else []
            if self.index < len(items):
                items.pop(self.index)
                with get_connection() as conn:
                    conn.execute(
                        "UPDATE tree_projects SET keys_tools = ? WHERE project_id = ?",
                        (json.dumps(items, ensure_ascii=False), self.project_id)
                    )
                    conn.commit()
            self.parent_widget.load()


class KeyDialog(QDialog):
    def __init__(self, parent=None, title="", description=""):
        super().__init__(parent)
        self.setWindowTitle("Ключ / Инструмент")
        self.setFixedSize(480, 300)
        self.setStyleSheet("""
            QDialog { background: #1a1a1a; }
            QLabel { color: #aaaaaa; font-size: 13px; }
            QLineEdit, QTextEdit {
                background: #2e2e2e; border: 1px solid #3a3a3a;
                border-radius: 8px; color: #e8e8e8; font-size: 14px;
                padding: 8px 12px;
            }
            QLineEdit:focus, QTextEdit:focus { border-color: #534AB7; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Заголовок"))
        self.input_title = QLineEdit(title)
        self.input_title.setFixedHeight(40)
        layout.addWidget(self.input_title)

        layout.addWidget(QLabel("Описание"))
        self.input_desc = QTextEdit(description)
        layout.addWidget(self.input_desc)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Отмена")
        btn_cancel.setFixedHeight(38)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: #2e2e2e; color: #aaa;
                border: 1px solid #3a3a3a; border-radius: 8px; font-size: 13px;
            }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Сохранить")
        btn_save.setFixedHeight(38)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton {
                background: #534AB7; color: #fff;
                border: none; border-radius: 8px; font-size: 13px;
            }
            QPushButton:hover { background: #6358c8; }
        """)
        btn_save.clicked.connect(self.accept)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def get_values(self):
        return (
            self.input_title.text().strip(),
            self.input_desc.toPlainText().strip()
        )