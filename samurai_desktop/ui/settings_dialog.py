import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFileDialog, QFrame
)
from PySide6.QtCore import Qt
from config import SYNC_FOLDER
from pathlib import Path


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки синхронизации")
        self.setFixedSize(540, 380)
        self.setStyleSheet("""
            QDialog { background: #1a1a1a; }
            QLabel { color: #aaaaaa; font-size: 13px; }
            QLineEdit {
                background: #2e2e2e; border: 1px solid #3a3a3a;
                border-radius: 8px; color: #e8e8e8;
                font-size: 13px; padding: 8px 12px;
            }
            QLineEdit:focus { border-color: #534AB7; }
            QFrame#divider {
                background: #2a2a2a;
                max-height: 1px;
            }
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        lbl_title = QLabel("Настройки синхронизации")
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 18px; font-weight: 500;")
        layout.addWidget(lbl_title)

        # Текущая папка входящих
        layout.addWidget(QLabel("Папка входящих файлов (с телефона):"))

        path_row = QHBoxLayout()
        self.input_path = QLineEdit(str(SYNC_FOLDER))
        self.input_path.setReadOnly(True)
        self.input_path.setFixedHeight(40)
        path_row.addWidget(self.input_path)

        btn_open = QPushButton("Открыть")
        btn_open.setFixedSize(80, 40)
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.setStyleSheet("""
            QPushButton {
                background: #2e2e2e; color: #ccc;
                border: 1px solid #3a3a3a; border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover { border-color: #555; color: #fff; }
        """)
        btn_open.clicked.connect(self._open_folder)
        path_row.addWidget(btn_open)
        layout.addLayout(path_row)

        # Инструкция по SMB
        divider = QFrame()
        divider.setObjectName("divider")
        layout.addWidget(divider)

        lbl_inst = QLabel("Как настроить синхронизацию с телефоном:")
        lbl_inst.setStyleSheet("color: #e8e8e8; font-size: 13px; font-weight: 500;")
        layout.addWidget(lbl_inst)

        steps = [
            "1. Нажмите «Открыть папку» — это папка куда телефон будет отправлять файлы",
            "2. Кликните правой кнопкой на папку → Свойства → Общий доступ",
            "3. Нажмите «Поделиться» и дайте доступ",
            "4. Запомните сетевой путь (\\\\ИМЯ_ПК\\incoming)",
            "5. В мобильном приложении введите этот путь",
        ]
        for step in steps:
            lbl = QLabel(step)
            lbl.setStyleSheet("color: #888888; font-size: 12px;")
            lbl.setWordWrap(True)
            layout.addWidget(lbl)

        layout.addStretch()

        # Имя компьютера
        import socket
        pc_name = socket.gethostname()
        lbl_pc = QLabel(f"Имя компьютера: {pc_name}")
        lbl_pc.setStyleSheet("color: #534AB7; font-size: 13px;")
        layout.addWidget(lbl_pc)

        btn_sync = QPushButton("Синхронизировать")
        btn_sync.setFixedHeight(40)
        btn_sync.setCursor(Qt.PointingHandCursor)
        btn_sync.setStyleSheet("""
            QPushButton {
                background: #534AB7; color: #fff;
                border: none; border-radius: 8px; font-size: 14px;
            }
            QPushButton:hover { background: #6358c8; }
        """)
        btn_sync.clicked.connect(self._sync_now)
        layout.addWidget(btn_sync)
        
        btn_close = QPushButton("Закрыть")
        btn_close.setFixedHeight(40)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background: #2a2a2a; color: #aaa;
                border: 1px solid #333; border-radius: 8px; font-size: 14px;
            }
            QPushButton:hover { color: #fff; border-color: #555; }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def _open_folder(self):
        os.startfile(str(SYNC_FOLDER))

    def _sync_now(self):
        import json
        from pathlib import Path
        from core.database import save_idea_entry
        from core.models import IdeaEntry, ProjectType, EntryColor
    
        THEME_MAP = {
            "Идея: прога":        ProjectType.SOFTWARE,
            "Идея: производство": ProjectType.PRODUCTION,
            "Исследование":       ProjectType.RESEARCH,
        }
    
        folder = SYNC_FOLDER
        files = list(folder.glob("*.json"))
    
        if not files:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Синхронизация", "Нет новых файлов в папке.")
            return
    
        imported = 0
        errors = 0
        archive = folder / "archive"
        archive.mkdir(exist_ok=True)
    
        for path in files:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
    
                theme_str = data.get("theme", "")
                description = data.get("description", "")
    
                if not theme_str or not description:
                    errors += 1
                    continue
    
                project_type = THEME_MAP.get(theme_str)
                if not project_type:
                    errors += 1
                    continue
    
                entry = IdeaEntry(
                    project_id=None,
                    theme=project_type,
                    description=description,
                    color=EntryColor.RED,
                    phase=0,
                )
                save_idea_entry(entry)
                path.rename(archive / path.name)
                imported += 1
    
            except Exception as e:
                print(f"[sync] Ошибка: {path.name}: {e}")
                errors += 1
    
        from PySide6.QtWidgets import QMessageBox
        msg = f"Импортировано: {imported}"
        if errors:
            msg += f"\nОшибок: {errors}"
        QMessageBox.information(self, "Синхронизация завершена", msg)