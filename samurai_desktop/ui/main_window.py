from PySide6.QtWidgets import QMainWindow, QWidget, QLabel, QStackedWidget, QPushButton
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCursor
from pathlib import Path


class MainWindow(QMainWindow):
    def __init__(self, user_id: str):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Самурай")
        self.setStyleSheet("QMainWindow { background-color: #0d0d0d; }")

        # Минимальный размер — четверть экрана
        screen = self.screen().availableGeometry()
        min_w = screen.width() // 4
        min_h = screen.height() // 4
        self.setMinimumSize(min_w, min_h)
    
        self.stack = QStackedWidget(self)
        self.home_screen = HomeScreen(self)
        self.stack.addWidget(self.home_screen)
        self.stack.setCurrentWidget(self.home_screen)
    
        # Запускаем в нормальном окне, не полноэкранном
        self.show()
        self.showMaximized()
        QTimer.singleShot(150, self._after_show)

    def _after_show(self):
        self.stack.setGeometry(0, 0, self.width(), self.height())
        self.home_screen.reposition()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.stack.setGeometry(0, 0, self.width(), self.height())
        self.home_screen.reposition()

    def navigate_to(self, section: str):
        # Удаляем все экраны кроме home перед добавлением нового
        while self.stack.count() > 1:
            widget = self.stack.widget(self.stack.count() - 1)
            self.stack.removeWidget(widget)
            widget.deleteLater()
    
        if section == "bloom":
            self._show_placeholder("🌸 Цветение", "Раздел в разработке")
            return
        if section == "seed":
            from ui.seed.seed_screen import SeedScreen
            screen = SeedScreen(self)
            self.stack.addWidget(screen)
            self.stack.setCurrentWidget(screen)
            return
        if section == "sprout":
            from ui.sprout.sprout_screen import SproutScreen
            screen = SproutScreen(self)
            self.stack.addWidget(screen)
            self.stack.setCurrentWidget(screen)
            return
        if section == "tree":
            from ui.tree.tree_screen import TreeScreen
            screen = TreeScreen(self)
            self.stack.addWidget(screen)
            self.stack.setCurrentWidget(screen)
            return
    
    def go_back(self):
        if self.stack.count() > 1:
            widget = self.stack.widget(self.stack.count() - 1)
            self.stack.removeWidget(widget)
            widget.deleteLater()
        # Активируем текущий виджет
        current = self.stack.currentWidget()
        if current:
            current.activateWindow()
            current.setFocus()
    
    def go_home(self):
        while self.stack.count() > 1:
            widget = self.stack.widget(self.stack.count() - 1)
            self.stack.removeWidget(widget)
            widget.deleteLater()
        self.stack.setCurrentWidget(self.home_screen)

    def _show_placeholder(self, title: str, message: str):
        from ui.placeholder_screen import PlaceholderScreen
        screen = PlaceholderScreen(title, message, self)
        self.stack.addWidget(screen)
        self.stack.setCurrentWidget(screen)

    def go_home(self):
        # Удаляем все экраны кроме home_screen
        while self.stack.count() > 1:
            widget = self.stack.widget(self.stack.count() - 1)
            self.stack.removeWidget(widget)
            widget.deleteLater()
        self.stack.setCurrentWidget(self.home_screen)
    
    def go_back(self):
        if self.stack.count() > 1:
            widget = self.stack.widget(self.stack.count() - 1)
            self.stack.removeWidget(widget)
            widget.deleteLater()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.showMaximized()
        if event.key() == Qt.Key_F2:
            from ui.settings_dialog import SettingsDialog
            SettingsDialog(self).exec()


class HomeScreen(QWidget):
    ZONES = [
        ("tree",   0.0,  0.0,  1.0,  1.0),
        ("bloom",  0.25, 0.02, 0.50, 0.20),
        ("sprout", 0.22, 0.35, 0.56, 0.42),
        ("seed",   0.30, 0.68, 0.40, 0.26),
    ]

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setStyleSheet("background-color: #0d0d0d;")
        self.buttons = []
        self.btn_settings = None

        assets = Path(__file__).parent.parent / "assets"
        for section, rx, ry, rw, rh in self.ZONES:
            png_path = assets / f"{section}.png"
            btn = PngButton(section, str(png_path), main_window)
            btn.setParent(self)
            btn.props = (rx, ry, rw, rh)
            self.buttons.append(btn)

    def reposition(self):
        w = self.main_window.width()
        h = self.main_window.height()

        for btn in self.buttons:
            rx, ry, rw, rh = btn.props
            btn.setGeometry(int(rx * w), int(ry * h), int(rw * w), int(rh * h))
            btn.show()

        self.buttons[0].lower()
        for btn in self.buttons[1:]:
            btn.raise_()

        if self.btn_settings is None:
            self.btn_settings = QPushButton("⚙")
            self.btn_settings.setParent(self)
            self.btn_settings.setFixedSize(40, 40)
            self.btn_settings.setCursor(Qt.PointingHandCursor)
            self.btn_settings.setStyleSheet("""
                QPushButton {
                    background-color: #1a1a1a;
                    color: #888888;
                    border: 1px solid #333333;
                    border-radius: 20px;
                    font-size: 18px;
                }
                QPushButton:hover { color: #ffffff; border-color: #555; }
            """)
            self.btn_settings.clicked.connect(self._open_settings)

        self.btn_settings.move(w - 56, 16)
        self.btn_settings.show()
        self.btn_settings.raise_()

        if not hasattr(self, 'btn_tools'):
            self.btn_tools = QPushButton("🛠")
            self.btn_tools.setParent(self)
            self.btn_tools.setFixedSize(40, 40)
            self.btn_tools.setCursor(Qt.PointingHandCursor)
            self.btn_tools.setStyleSheet("""
                QPushButton {
                    background-color: #1a1a1a;
                    color: #888888;
                    border: 1px solid #333333;
                    border-radius: 20px;
                    font-size: 18px;
                }
                QPushButton:hover { color: #ffffff; border-color: #555; }
            """)
            self.btn_tools.clicked.connect(self._open_tools)
        
        self.btn_tools.move(w - 104, 16)
        self.btn_tools.show()
        self.btn_tools.raise_()

    def _open_settings(self):
        from ui.settings_dialog import SettingsDialog
        SettingsDialog(self.main_window).exec()

    def _open_tools(self):
        from ui.tools_screen import ToolsScreen
        screen = ToolsScreen(self.main_window)
        self.main_window.stack.addWidget(screen)
        self.main_window.stack.setCurrentWidget(screen)


class PngButton(QLabel):
    def __init__(self, section: str, png_path: str, main_window):
        super().__init__()
        self.section = section
        self.main_window = main_window
        self.png_path = png_path
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setScaledContents(False)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background: transparent; border: none;")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_pixmap()

    def _update_pixmap(self):
        from PySide6.QtGui import QPixmap
        px = QPixmap(self.png_path)
        if not px.isNull():
            scaled = px.scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.setPixmap(scaled)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.main_window.navigate_to(self.section)