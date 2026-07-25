from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget
)
from PySide6.QtCore import Qt
from ui.sprout.mvp_screen import MVPScreen


class SproutScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setStyleSheet("background-color: #111111;")
        self._build_ui()

    def _refresh(self):
        self.mvp_screen.load_projects()
        if hasattr(self, 'eco_screen'):
            self.eco_screen.load_entries()

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
    
        lbl_title = QLabel("🌿 Росток")
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 18px; font-weight: 500;")
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()
    
        self.btn_mvp = self._tab_btn("МВП", True)
        self.btn_eco = self._tab_btn("ЭКОСИСТЕМА", False)
        self.btn_mvp.clicked.connect(lambda: self._switch(0))
        self.btn_eco.clicked.connect(lambda: self._switch(1))
        top_layout.addWidget(self.btn_mvp)
        top_layout.addSpacing(8)
        top_layout.addWidget(self.btn_eco)
        top_layout.addSpacing(8)
    
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
    
        root.addWidget(top)
    
        self.stack = QStackedWidget()
        self.mvp_screen = MVPScreen(self.main_window)
        self.stack.addWidget(self.mvp_screen)
    
        from ui.sprout.eco_screen import EcoScreen
        self.eco_screen = EcoScreen(self.main_window)
        self.stack.addWidget(self.eco_screen)
    
        root.addWidget(self.stack)

    def _tab_btn(self, text: str, active: bool) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(32)
        btn.setCursor(Qt.PointingHandCursor)
        self._style_tab(btn, active)
        return btn

    def _style_tab(self, btn, active):
        if active:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #534AB7; color: #ffffff;
                    border: none; border-radius: 6px;
                    padding: 0 16px; font-size: 13px; font-weight: 500;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent; color: #888888;
                    border: 1px solid #333333; border-radius: 6px;
                    padding: 0 16px; font-size: 13px;
                }
                QPushButton:hover { color: #cccccc; border-color: #555; }
            """)

    def _switch(self, index):
        self.stack.setCurrentIndex(index)
        self._style_tab(self.btn_mvp, index == 0)
        self._style_tab(self.btn_eco, index == 1)