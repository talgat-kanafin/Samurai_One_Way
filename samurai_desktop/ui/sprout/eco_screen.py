from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame
)
from PySide6.QtCore import Qt
from core.database import get_connection
from datetime import datetime


class EcoScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setStyleSheet("background-color: #111111;")
        self._build_ui()
        self.load_entries()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Центральный треугольник
        top = QWidget()
        top.setFixedHeight(160)
        top.setStyleSheet("background-color: #111111;")
        top_layout = QHBoxLayout(top)
        top_layout.setAlignment(Qt.AlignCenter)

        center = TriangleLabel("ЭКОСИСТЕМА")
        top_layout.addWidget(center)

        # Кнопка добавить вручную
        btn_add = QPushButton("+")
        btn_add.setFixedSize(40, 40)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #1a2a1a;
                color: #4caf50;
                border: 1px solid #388E3C;
                border-radius: 20px;
                font-size: 20px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #2a3a2a; }
        """)
        btn_add.clicked.connect(self._add_entry)
        top_layout.addWidget(btn_add)

        root.addWidget(top)

        # Список треугольников
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #111111; }")

        self.container = QWidget()
        self.container.setStyleSheet("background: #111111;")
        self.flow_layout = QVBoxLayout(self.container)
        self.flow_layout.setContentsMargins(40, 8, 40, 8)
        self.flow_layout.setSpacing(8)
        self.flow_layout.addStretch()

        scroll.setWidget(self.container)
        root.addWidget(scroll)

    def load_entries(self):
        while self.flow_layout.count() > 1:
            item = self.flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM eco_entries ORDER BY date_received DESC"
            ).fetchall()

        for row in rows:
            card = EcoCard(row, self.main_window, self)
            self.flow_layout.insertWidget(
                self.flow_layout.count() - 1, card
            )

    def _add_entry(self):
        from ui.sprout.eco_chat_screen import EcoAddDialog
        dialog = EcoAddDialog(self)
        dialog.entry_added.connect(self.load_entries)
        dialog.exec()


class TriangleLabel(QWidget):
    def __init__(self, text: str):
        super().__init__()
        self.text = text
        self.setFixedSize(120, 120)

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QPolygon, QColor, QFont, QPen
        from PySide6.QtCore import QPoint
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        points = QPolygon([
            QPoint(60, 10),
            QPoint(110, 105),
            QPoint(10, 105),
        ])
        painter.setBrush(QColor("#2a2a2a"))
        painter.setPen(QPen(QColor("#444444"), 2))
        painter.drawPolygon(points)

        painter.setPen(QColor("#e8e8e8"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Medium))
        from PySide6.QtCore import QRect
        painter.drawText(QRect(10, 60, 100, 40), Qt.AlignCenter, self.text)
        painter.end()


class EcoCard(QFrame):
    def __init__(self, row, main_window, eco_screen):
        super().__init__()
        self.entry_id = row["id"]
        self.main_window = main_window
        self.eco_screen = eco_screen
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(72)

        entry_type = row["entry_type"]
        is_complete = bool(row["result"])

        if is_complete:
            border_color = "#388E3C"
            bg_color = "#0f2a0f"
        elif entry_type == "integration":
            border_color = "#1565C0"
            bg_color = "#0f0f2a"
        else:
            border_color = "#534AB7"
            bg_color = "#1a1a2a"

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
            QFrame:hover {{ border-width: 2px; }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)

        info = QVBoxLayout()
        info.setSpacing(2)

        desc = row["description"] or ""
        lbl_desc = QLabel(desc[:60] + "..." if len(desc) > 60 else desc)
        lbl_desc.setStyleSheet("color: #e8e8e8; font-size: 13px;")
        info.addWidget(lbl_desc)

        date_str = row["date_received"][:10] if row["date_received"] else ""
        type_str = "Интеграция" if entry_type == "integration" else "Новый проект"
        lbl_meta = QLabel(f"{date_str}  ·  {type_str}")
        lbl_meta.setStyleSheet("color: #555555; font-size: 11px;")
        info.addWidget(lbl_meta)

        layout.addLayout(info)
        layout.addStretch()

        status = QLabel("✓ Завершён" if is_complete else "В процессе")
        status.setStyleSheet(
            "color: #388E3C; font-size: 12px;" if is_complete
            else "color: #888888; font-size: 12px;"
        )
        layout.addWidget(status)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            from ui.sprout.eco_card import EcoCard as EcoCardScreen
            screen = EcoCardScreen(self.entry_id, self.main_window)
            screen.confirmed.connect(lambda _: self.eco_screen.load_entries())
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
        action_delete = menu.addAction("🗑 Удалить")
        action = menu.exec(event.globalPos())
        if action == action_refresh:
            self.eco_screen.load_entries()
        elif action == action_delete:
            msg = QMessageBox(self)
            msg.setWindowTitle("Удалить")
            msg.setText("Удалить запись экосистемы?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setStyleSheet("QMessageBox { background: #1a1a1a; } QLabel { color: #e8e8e8; }")
            if msg.exec() == QMessageBox.Yes:
                from core.database import get_connection
                with get_connection() as conn:
                    conn.execute("DELETE FROM eco_entries WHERE id = ?", (self.entry_id,))
                    conn.commit()
                self.eco_screen.load_entries()
                self.hide()
                self.deleteLater()