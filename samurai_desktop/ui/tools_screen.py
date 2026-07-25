from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QDialog, QLineEdit, QComboBox,
    QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from core.tools_manager import (
    load_tools, add_tool, delete_tool, update_tool,
    get_chrome_profiles, open_tool
)


class ToolsScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setStyleSheet("background-color: #111111;")
        self._build_ui()
        self.load_tools()

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
            QPushButton { background: transparent; color: #aaaaaa; border: none; font-size: 14px; }
            QPushButton:hover { color: #ffffff; }
        """)
        btn_back.clicked.connect(self.main_window.go_back)
        top_layout.addWidget(btn_back)
        top_layout.addStretch()

        lbl_title = QLabel("🛠 Инструменты")
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 18px; font-weight: 500;")
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()

        btn_add = QPushButton("+ Добавить")
        btn_add.setFixedHeight(34)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #534AB7; color: #fff;
                border: none; border-radius: 6px; padding: 0 16px; font-size: 13px;
            }
            QPushButton:hover { background-color: #6358c8; }
        """)
        btn_add.clicked.connect(self._add_tool)
        top_layout.addWidget(btn_add)
        root.addWidget(top)

        # Список инструментов
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

    def load_tools(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tools = load_tools()

        if not tools:
            lbl = QLabel("Нет инструментов. Нажмите «+ Добавить».")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #555555; font-size: 14px;")
            self.list_layout.insertWidget(0, lbl)
            return

        for tool in tools:
            card = ToolCard(tool, self)
            self.list_layout.insertWidget(self.list_layout.count() - 1, card)

    def _add_tool(self):
        dialog = ToolDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            if data["name"] and data["url"]:
                add_tool(
                    name=data["name"],
                    url=data["url"],
                    profile=data["profile"],
                    account_label=data["account_label"],
                    prompt=data["prompt"]
                )
                self.load_tools()


class ToolCard(QFrame):
    def __init__(self, tool: dict, tools_screen):
        super().__init__()
        self.tool = tool
        self.tools_screen = tools_screen
        self.setFixedHeight(72)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #2a2a2a;
                border-radius: 10px;
            }
            QFrame:hover { border-color: #534AB7; }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 16, 0)
        layout.setSpacing(12)

        # Иконка
        lbl_icon = QLabel("🔗")
        lbl_icon.setStyleSheet("font-size: 20px;")
        lbl_icon.setFixedWidth(32)
        layout.addWidget(lbl_icon)

        # Название и аккаунт
        info = QVBoxLayout()
        info.setSpacing(3)

        lbl_name = QLabel(tool.get("name", ""))
        lbl_name.setStyleSheet("color: #e8e8e8; font-size: 14px; font-weight: 500;")
        info.addWidget(lbl_name)

        account_label = tool.get("account_label", "")
        url = tool.get("url", "")
        sub = account_label if account_label else url[:50]
        lbl_sub = QLabel(sub)
        lbl_sub.setStyleSheet("color: #555555; font-size: 12px;")
        info.addWidget(lbl_sub)

        layout.addLayout(info)
        layout.addStretch()

        # Профиль Chrome
        profile = tool.get("profile", "")
        if profile:
            lbl_profile = QLabel(f"👤 {profile}")
            lbl_profile.setStyleSheet("color: #534AB7; font-size: 11px;")
            layout.addWidget(lbl_profile)

        # Кнопка открыть
        btn_open = QPushButton("Открыть →")
        btn_open.setFixedHeight(34)
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.setStyleSheet("""
            QPushButton {
                background-color: #534AB7; color: #fff;
                border: none; border-radius: 6px;
                padding: 0 14px; font-size: 13px;
            }
            QPushButton:hover { background-color: #6358c8; }
        """)
        btn_open.clicked.connect(self._open)
        layout.addWidget(btn_open)

        prompt = tool.get("prompt", "")
        if prompt:
            btn_prompt = QPushButton("Промпт")
            btn_prompt.setFixedHeight(34)
            btn_prompt.setCursor(Qt.PointingHandCursor)
            btn_prompt.setStyleSheet("""
                QPushButton {
                    background-color: #1a2a1a; color: #aaffaa;
                    border: 1px solid #336633; border-radius: 6px;
                    padding: 0 14px; font-size: 13px;
                }
                QPushButton:hover { background-color: #253525; }
            """)
            btn_prompt.clicked.connect(lambda: self._copy_prompt(prompt))
            layout.addWidget(btn_prompt)

        # Кнопка редактировать
        btn_edit = QPushButton("✏")
        btn_edit.setFixedSize(34, 34)
        btn_edit.setCursor(Qt.PointingHandCursor)
        btn_edit.setStyleSheet("""
            QPushButton { background: #2a2a2a; color: #888; border: 1px solid #333; border-radius: 6px; font-size: 14px; }
            QPushButton:hover { color: #fff; border-color: #555; }
        """)
        btn_edit.clicked.connect(self._edit)
        layout.addWidget(btn_edit)

        # Кнопка удалить
        btn_del = QPushButton("×")
        btn_del.setFixedSize(34, 34)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet("""
            QPushButton { background: #2a2a2a; color: #888; border: 1px solid #333; border-radius: 6px; font-size: 16px; }
            QPushButton:hover { color: #E24B4A; border-color: #E24B4A; }
        """)
        btn_del.clicked.connect(self._delete)
        layout.addWidget(btn_del)

    def _open(self):
        open_tool(self.tool.get("url", ""), self.tool.get("profile", ""))

    def _edit(self):
        dialog = ToolDialog(tool=self.tool, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            update_tool(
                self.tool["id"],
                name=data["name"],
                url=data["url"],
                profile=data["profile"],
                account_label=data["account_label"],
                prompt=data["prompt"]
            )
            self.tools_screen.load_tools()

    def _delete(self):
        delete_tool(self.tool["id"])
        self.tools_screen.load_tools()

    def _copy_prompt(self, prompt: str):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(prompt)
        self.btn_open.setText("Скопировано ✓")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self.btn_open.setText("Открыть →"))


class ToolDialog(QDialog):
    def __init__(self, tool: dict = None, parent=None):
        super().__init__(parent)
        self.tool = tool
        self.profiles = get_chrome_profiles()
        self.setWindowTitle("Инструмент" if tool else "Новый инструмент")
        self.setFixedSize(520, 360)
        self.setStyleSheet("""
            QDialog { background: #1a1a1a; }
            QLabel { color: #aaaaaa; font-size: 13px; }
            QLineEdit, QComboBox {
                background: #2e2e2e; border: 1px solid #3a3a3a;
                border-radius: 8px; color: #e8e8e8;
                font-size: 13px; padding: 0 10px; height: 38px;
            }
            QLineEdit:focus, QComboBox:focus { border-color: #534AB7; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: #2e2e2e; color: #e8e8e8;
                selection-background-color: #534AB7;
            }
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        lbl_title = QLabel("Инструмент" if self.tool else "Новый инструмент")
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 16px; font-weight: 500;")
        layout.addWidget(lbl_title)

        layout.addWidget(QLabel("Название"))
        self.input_name = QLineEdit(self.tool.get("name", "") if self.tool else "")
        self.input_name.setPlaceholderText("Например: Claude — проект A")
        layout.addWidget(self.input_name)

        layout.addWidget(QLabel("URL"))
        self.input_url = QLineEdit(self.tool.get("url", "") if self.tool else "")
        self.input_url.setPlaceholderText("https://claude.ai")
        layout.addWidget(self.input_url)

        layout.addWidget(QLabel("Метка аккаунта (необязательно)"))
        self.input_label = QLineEdit(self.tool.get("account_label", "") if self.tool else "")
        self.input_label.setPlaceholderText("Например: Аккаунт 1 / Рабочий")
        layout.addWidget(self.input_label)

        layout.addWidget(QLabel("Промпт (необязательно)"))
        self.input_prompt = QTextEdit(self.tool.get("prompt", "") if self.tool else "")
        self.input_prompt.setPlaceholderText("Вставьте промпт который будет копироваться одной кнопкой...")
        self.input_prompt.setFixedHeight(80)
        self.input_prompt.setStyleSheet("""
            QTextEdit {
                background: #2e2e2e; border: 1px solid #3a3a3a;
                border-radius: 8px; color: #e8e8e8;
                font-size: 13px; padding: 8px;
            }
            QTextEdit:focus { border-color: #534AB7; }
        """)
        layout.addWidget(self.input_prompt)

        layout.addWidget(QLabel("Профиль Chrome"))
        self.combo_profile = QComboBox()
        self.combo_profile.addItem("— Без профиля —", "")

        current_profile = self.tool.get("profile", "") if self.tool else ""
        selected_index = 0

        for i, p in enumerate(self.profiles):
            self.combo_profile.addItem(p["label"], p["dir"])
            if p["dir"] == current_profile:
                selected_index = i + 1

        self.combo_profile.setCurrentIndex(selected_index)
        layout.addWidget(self.combo_profile)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Отмена")
        btn_cancel.setFixedHeight(38)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("QPushButton { background: #2a2a2a; color: #aaa; border: 1px solid #333; border-radius: 8px; }")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Сохранить")
        btn_save.setFixedHeight(38)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton { background: #534AB7; color: #fff; border: none; border-radius: 8px; font-size: 13px; }
            QPushButton:hover { background: #6358c8; }
        """)
        btn_save.clicked.connect(self.accept)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def get_data(self) -> dict:
        return {
            "name": self.input_name.text().strip(),
            "url": self.input_url.text().strip(),
            "account_label": self.input_label.text().strip(),
            "profile": self.combo_profile.currentData() or "",
            "prompt": self.input_prompt.toPlainText().strip()
        }