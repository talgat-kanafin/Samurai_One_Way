from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt
from core.auth import verify_user, register_user, needs_registration


class AuthWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Самурай — Вход")
        self.setFixedSize(440, 400)
        self._center_window()
        self._build_ui()

    def _center_window(self):
        screen = self.screen().availableGeometry()
        self.move(
            (screen.width() - 440) // 2,
            (screen.height() - 400) // 2
        )

    def _build_ui(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1a1a1a;
            }
            QFrame#card {
                background-color: #242424;
                border: 1px solid #333333;
                border-radius: 12px;
            }
            QLabel#title {
                color: #e8e8e8;
                font-size: 22px;
                font-weight: 500;
            }
            QLabel#subtitle {
                color: #888888;
                font-size: 13px;
            }
            QLabel#field_label {
                color: #aaaaaa;
                font-size: 13px;
                padding: 0px;
                margin: 0px;
            }
            QLineEdit {
                background-color: #2e2e2e;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                color: #e8e8e8;
                font-size: 14px;
                padding: 10px 14px;
            }
            QLineEdit:focus {
                border: 1px solid #534AB7;
            }
            QPushButton#btn_main {
                background-color: #534AB7;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                padding: 12px;
            }
            QPushButton#btn_main:hover {
                background-color: #6358c8;
            }
            QPushButton#btn_main:pressed {
                background-color: #3c348f;
            }
            QLabel#error_label {
                color: #E24B4A;
                font-size: 12px;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)

        outer = QVBoxLayout(central)
        outer.setContentsMargins(40, 40, 40, 40)
        outer.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("card")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(8)

        # Заголовок
        title = QLabel("侍  Самурай")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(2)

        # Подзаголовок
        mode_text = "Первый запуск — создайте аккаунт" if needs_registration() else "Добро пожаловать"
        subtitle = QLabel(mode_text)
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(16)

        # Логин
        lbl_login = QLabel("Логин")
        lbl_login.setObjectName("field_label")
        layout.addWidget(lbl_login)

        layout.addSpacing(4)

        self.input_login = QLineEdit()
        self.input_login.setPlaceholderText("Введите логин")
        self.input_login.setFixedHeight(44)
        layout.addWidget(self.input_login)

        layout.addSpacing(12)

        # Пароль
        lbl_pass = QLabel("Пароль")
        lbl_pass.setObjectName("field_label")
        layout.addWidget(lbl_pass)

        layout.addSpacing(4)

        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Введите пароль")
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_password.setFixedHeight(44)
        self.input_password.returnPressed.connect(self._on_submit)
        layout.addWidget(self.input_password)

        layout.addSpacing(8)

        # Ошибка
        self.error_label = QLabel("")
        self.error_label.setObjectName("error_label")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setFixedHeight(16)
        layout.addWidget(self.error_label)

        layout.addSpacing(8)

        # Кнопка
        btn_text = "Создать аккаунт" if needs_registration() else "Войти"
        self.btn_submit = QPushButton(btn_text)
        self.btn_submit.setObjectName("btn_main")
        self.btn_submit.setFixedHeight(46)
        self.btn_submit.setCursor(Qt.PointingHandCursor)
        self.btn_submit.clicked.connect(self._on_submit)
        layout.addWidget(self.btn_submit)

        outer.addWidget(card)

    def _on_submit(self):
        login = self.input_login.text().strip()
        password = self.input_password.text()

        if not login or not password:
            self.error_label.setText("Заполните все поля")
            return

        if needs_registration():
            ok, result = register_user(login, password)
            if ok:
                self._open_main(result)
            else:
                self.error_label.setText(result)
        else:
            ok, user_id = verify_user(login, password)
            if ok:
                self._open_main(user_id)
            else:
                self.error_label.setText("Неверный логин или пароль")

    def _open_main(self, user_id: str):
        from ui.main_window import MainWindow
        self.main_window = MainWindow(user_id)
        self.main_window.show()
        self.close()