from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea
)
from PySide6.QtCore import Qt
from ui.widgets.circle_button import CircleButton
from core.database import get_idea_entries


class ResearchScreen(QWidget):
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
    
        # Центральный лейбл
        top = QWidget()
        top.setFixedHeight(160)
        top.setStyleSheet("background-color: #111111;")
        top_layout = QHBoxLayout(top)
        top_layout.setAlignment(Qt.AlignCenter)
    
        lbl = QLabel("ИССЛЕДОВАНИЕ")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setFixedSize(130, 130)
        lbl.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                color: #e8e8e8;
                font-size: 12px;
                font-weight: 500;
                border-radius: 65px;
                border: 2px solid #444444;
            }
        """)
        top_layout.addWidget(lbl)
        root.addWidget(top)
    
        # Кружки
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
    
        self.container = QWidget()
        self.container.setStyleSheet("background-color: #111111;")
        self.flow = ResearchFlow(self.container)
        scroll.setWidget(self.container)
        root.addWidget(scroll)

    def load_entries(self):
        if not hasattr(self, 'flow'):
            return

        # Очищаем все строки в flow layout
        while self.flow.count():
            item = self.flow.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
        
        # Сбрасываем состояние flow
        self.flow._row = None
        self.flow._row_count = 0
    
        rows = get_idea_entries("research")
    
        def sort_key(row):
            return 1 if row["color"] == "green" else 0
    
        rows_sorted = sorted(rows, key=sort_key)
    
        for row in rows_sorted:
            dt = row["date_received"][:10]
            parts = dt.split("-")
            label = f"{parts[2]}.{parts[1]}\n{parts[0]}"
            btn = CircleButton(row["id"], label, row["color"])
            if row["color"] == "green":
                btn.setEnabled(False)
                btn.setToolTip("Отправлено — только просмотр")
            else:
                btn.clicked.connect(self._open_chat)
            self.flow.addWidget(btn)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _open_chat(self, entry_id: str):
        from ui.seed.research_card import ResearchCard
        screen = ResearchCard(
            entry_id=entry_id,
            main_window=self.main_window
        )
        screen.confirmed.connect(lambda _: self.load_entries())
        self.main_window.stack.addWidget(screen)
        self.main_window.stack.setCurrentWidget(screen)


class ResearchFlow(QVBoxLayout):
    """Кружки по 4 в ряд."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSpacing(8)
        self.setContentsMargins(16, 8, 16, 8)
        self.setAlignment(Qt.AlignTop)
        self._row = None
        self._row_count = 0

    def addWidget(self, widget):
        if self._row is None or self._row_count >= 4:
            self._row = QHBoxLayout()
            self._row.setSpacing(8)
            self._row.setAlignment(Qt.AlignLeft)
            super().addLayout(self._row)
            self._row_count = 0
        self._row.addWidget(widget)
        self._row_count += 1
        widget.show()