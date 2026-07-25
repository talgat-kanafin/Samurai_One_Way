from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget
)
from PySide6.QtCore import Qt
from ui.seed.idea_screen import IdeaScreen
from ui.seed.research_screen import ResearchScreen


class SeedScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setStyleSheet("background-color: #111111;")
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Верхняя панель ──
        top_bar = QWidget()
        top_bar.setFixedHeight(56)
        top_bar.setStyleSheet("background-color: #1a1a1a; border-bottom: 1px solid #2a2a2a;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 0, 16, 0)

        btn_back = QPushButton("← Назад")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #aaaaaa;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover { color: #ffffff; }
        """)
        btn_back.clicked.connect(self.main_window.go_home)
        top_layout.addWidget(btn_back)
        top_layout.addStretch()

        lbl_title = QLabel("🌱 Семя")
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 18px; font-weight: 500;")
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()

        # Переключатель вкладок
        self.btn_idea = self._tab_btn("ИДЕЯ", active=True)
        self.btn_research = self._tab_btn("ИССЛЕДОВАНИЯ", active=False)
        self.btn_idea.clicked.connect(lambda: self._switch(0))
        self.btn_research.clicked.connect(lambda: self._switch(1))
        top_layout.addWidget(self.btn_idea)
        top_layout.addSpacing(8)
        top_layout.addWidget(self.btn_research)

        top_layout.addSpacing(16)

        btn_add = QPushButton("+ Запись")
        btn_add.setFixedHeight(32)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #388E3C; color: #ffffff;
                border: none; border-radius: 6px;
                padding: 0 16px; font-size: 13px;
            }
            QPushButton:hover { background-color: #4caf50; }
        """)
        btn_add.clicked.connect(self._add_entry)
        top_layout.addWidget(btn_add)

        root.addWidget(top_bar)

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
        btn_refresh.clicked.connect(self.refresh)
        top_layout.addWidget(btn_refresh)

        # ── Стек экранов ──
        self.stack = QStackedWidget()
        self.idea_screen = IdeaScreen(self.main_window)
        self.research_screen = ResearchScreen(self.main_window)
        self.stack.addWidget(self.idea_screen)
        self.stack.addWidget(self.research_screen)
        root.addWidget(self.stack)

    def _tab_btn(self, text: str, active: bool) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(32)
        self._style_tab(btn, active)
        return btn

    def _style_tab(self, btn: QPushButton, active: bool):
        if active:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #534AB7;
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    padding: 0 16px;
                    font-size: 13px;
                    font-weight: 500;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #888888;
                    border: 1px solid #333333;
                    border-radius: 6px;
                    padding: 0 16px;
                    font-size: 13px;
                }
                QPushButton:hover { color: #cccccc; border-color: #555555; }
            """)

    def _switch(self, index: int):
        self.stack.setCurrentIndex(index)
        self._style_tab(self.btn_idea, index == 0)
        self._style_tab(self.btn_research, index == 1)

    def refresh(self):
        self.idea_screen.load_entries()
        if hasattr(self, 'research_screen') and self.research_screen is not None:
            self.research_screen.load_entries()

    def _add_entry(self):
        from ui.seed.add_entry_dialog import AddEntryDialog
        dialog = AddEntryDialog(self)
        dialog.entry_added.connect(self.refresh)
        dialog.exec()