from PySide6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QScrollArea
)
from PySide6.QtCore import Qt
from ui.widgets.circle_button import CircleButton
from core.database import get_idea_entries


class IdeaScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setStyleSheet("background-color: #111111;")
        self._build_ui()
        self.load_entries()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Левая — Программная
        self.left_panel = SidePanel("Программная", "#0f1a0f")
        # Центр — ИДЕЯ
        center = CenterLabel("ИДЕЯ")
        # Правая — Производственная
        self.right_panel = SidePanel("Производственная", "#1a0f0f")

        root.addWidget(self.left_panel, 1)
        root.addWidget(center, 0)
        root.addWidget(self.right_panel, 1)

    def load_entries(self):
        self.left_panel.clear_circles()
        self.right_panel.clear_circles()

        prog = get_idea_entries("software")
        prod = get_idea_entries("production")
    
        # Сортируем — активные сверху, зелёные снизу
        def sort_key(row):
            return 1 if row["color"] == "green" else 0
    
        prog_sorted = sorted(prog, key=sort_key)
        prod_sorted = sorted(prod, key=sort_key)
    
        for row in prog_sorted:
            dt = row["date_received"][:10]
            parts = dt.split("-")
            label = f"{parts[2]}.{parts[1]}\n{parts[0]}"
            btn = CircleButton(row["id"], label, row["color"])
            if row["color"] == "green":
                btn.setEnabled(False)
                btn.setToolTip("Отправлено в Росток — только просмотр")
            else:
                btn.clicked.connect(self._open_chat)
            self.left_panel.add_circle(btn)
    
        for row in prod_sorted:
            dt = row["date_received"][:10]
            parts = dt.split("-")
            label = f"{parts[2]}.{parts[1]}\n{parts[0]}"
            btn = CircleButton(row["id"], label, row["color"])
            if row["color"] == "green":
                btn.setEnabled(False)
                btn.setToolTip("Отправлено в Росток — только просмотр")
            else:
                btn.clicked.connect(self._open_chat)
            self.right_panel.add_circle(btn)

    def _open_chat(self, entry_id: str):
        from core.database import get_connection
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM idea_entries WHERE id = ?", (entry_id,)
            ).fetchone()
        if not row:
            return
        from ui.seed.idea_card import IdeaCard
        screen = IdeaCard(
            entry_id=entry_id,
            theme=row["theme"],
            main_window=self.main_window
        )
        screen.confirmed.connect(lambda _: self.load_entries())
        self.main_window.stack.addWidget(screen)
        self.main_window.stack.setCurrentWidget(screen)


class SidePanel(QWidget):
    def __init__(self, title: str, bg: str):
        super().__init__()
        self.setStyleSheet(f"background-color: {bg};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        lbl = QLabel(title)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #888888; font-size: 13px; font-weight: 500;")
        layout.addWidget(lbl)

        # Область с кружками
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.flow = FlowLayout(self.container)
        scroll.setWidget(self.container)
        layout.addWidget(scroll)

    def add_circle(self, btn: CircleButton):
        self.flow.addWidget(btn)

    def clear_circles(self):
        while self.flow.count():
            item = self.flow.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class CenterLabel(QWidget):
    def __init__(self, text: str):
        super().__init__()
        self.setFixedWidth(120)
        self.setStyleSheet("background-color: #111111;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setFixedSize(90, 90)
        lbl.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                color: #e8e8e8;
                font-size: 13px;
                font-weight: 500;
                border-radius: 45px;
                border: 2px solid #444444;
            }
        """)
        layout.addWidget(lbl)


class FlowLayout(QVBoxLayout):
    """Простой вертикальный поток кружков по 3 в ряд."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSpacing(8)
        self.setContentsMargins(8, 8, 8, 8)
        self.setAlignment(Qt.AlignTop)
        self._row = None
        self._row_count = 0

    def addWidget(self, widget):
        if self._row is None or self._row_count >= 3:
            self._row = QHBoxLayout()
            self._row.setSpacing(8)
            self._row.setAlignment(Qt.AlignLeft)
            super().addLayout(self._row)
            self._row_count = 0
        self._row.addWidget(widget)
        self._row_count += 1

    def clear(self):
        self._row = None
        self._row_count = 0