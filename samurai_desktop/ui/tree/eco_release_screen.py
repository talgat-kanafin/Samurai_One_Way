import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPolygon, QColor, QPen, QFont
from PySide6.QtCore import QPoint, QRect
from core.database import get_connection


class EcoReleaseScreen(QWidget):
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

        # Верхняя панель без кнопки назад — навигация через TreeScreen
        top = QWidget()
        top.setFixedHeight(56)
        top.setStyleSheet("background-color: #1a1a1a; border-bottom: 1px solid #2a2a2a;")
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(16, 0, 16, 0)
        top_layout.addStretch()
        
        lbl_title = QLabel("ЭКО Релиз")
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 18px; font-weight: 500;")
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()
        root.addWidget(top)

        # Пирамида с глазом
        pyramid = PyramidImageWidget()
        pyramid.setFixedHeight(200)
        root.addWidget(pyramid)

        # Список проектов
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

    def load_projects(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

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
            rows = conn.execute(
                "SELECT * FROM eco_release_projects ORDER BY date_received DESC"
            ).fetchall()

        if not rows:
            lbl_empty = QLabel("Нет проектов в ЭКО Релиз")
            lbl_empty.setAlignment(Qt.AlignCenter)
            lbl_empty.setStyleSheet("color: #555555; font-size: 15px;")
            self.list_layout.insertWidget(0, lbl_empty)
            return

        for row in rows:
            card = EcoReleaseProjectCard(row, self.main_window, self)
            self.list_layout.insertWidget(self.list_layout.count() - 1, card)


class PyramidImageWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #111111;")
        self.setFixedHeight(200)

    def paintEvent(self, event):
        from PySide6.QtGui import QPixmap
        from pathlib import Path
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        png_path = Path(__file__).parent.parent.parent / "assets" / "eco_release.png"
        px = QPixmap(str(png_path))

        if not px.isNull():
            scaled = px.scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        painter.end()


class EcoReleaseProjectCard(QFrame):
    def __init__(self, row, main_window, release_screen):
        super().__init__()
        self.project_id = row["id"]
        self.main_window = main_window
        self.release_screen = release_screen
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(72)
        self.setStyleSheet("""
            QFrame {
                background-color: #1a2a1a;
                border: 1px solid #2a3a2a;
                border-radius: 10px;
            }
            QFrame:hover { border-color: #388E3C; }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)

        info = QVBoxLayout()
        info.setSpacing(3)

        desc = row["description"] or "Без названия"
        title = desc[:50] + "..." if len(desc) > 50 else desc
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 14px; font-weight: 500;")
        info.addWidget(lbl_title)

        date_str = row["date_received"][:10] if row["date_received"] else ""
        launched = row["date_launched"]
        date_info = f"Поступил: {date_str}"
        if launched:
            date_info += f"  |  Запущен: {launched[:10]}"
        lbl_date = QLabel(date_info)
        lbl_date.setStyleSheet("color: #555555; font-size: 11px;")
        info.addWidget(lbl_date)

        layout.addLayout(info)
        layout.addStretch()

        lbl_arrow = QLabel("→")
        lbl_arrow.setStyleSheet("color: #388E3C; font-size: 18px;")
        layout.addWidget(lbl_arrow)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            from ui.tree.eco_release_card import EcoReleaseCard
            screen = EcoReleaseCard(self.project_id, self.main_window, self.release_screen)
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
            self.release_screen.load_projects()
        elif action == action_delete:
            msg = QMessageBox(self)
            msg.setWindowTitle("Удалить")
            msg.setText("Удалить проект из ЭКО Релиз?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setStyleSheet("QMessageBox { background: #1a1a1a; } QLabel { color: #e8e8e8; }")
            if msg.exec() == QMessageBox.Yes:
                from core.database import get_connection
                with get_connection() as conn:
                    conn.execute("DELETE FROM eco_release_projects WHERE id = ?", (self.project_id,))
                    conn.commit()
                self.release_screen.load_projects()
                self.hide()
                self.deleteLater()