import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTextEdit, QDialog, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from core.database import (
    get_idea_entry, save_to_archive, find_similar_in_archive,
    update_idea_entry_color, update_idea_entry_project,
    delete_idea_entry, save_idea_entry
)
from core.models import IdeaEntry, ProjectType, EntryColor
from core.project_files import log_to_project
from datetime import datetime


class ResearchCard(QWidget):
    confirmed = Signal(str)

    def __init__(self, entry_id: str, main_window):
        super().__init__()
        self.entry_id = entry_id
        self.main_window = main_window
        self.setStyleSheet("background-color: #111111;")

        self.entry = get_idea_entry(entry_id)
        if not self.entry:
            return

        similar = find_similar_in_archive(
            self.entry["description"], "research"
        )
        if similar:
            self._show_similar_dialog(similar[0])
        else:
            self._build_ui()

    def _show_similar_dialog(self, match: dict):
        from ui.seed.idea_card import SimilarDialog
        dialog = SimilarDialog(
            current_desc=self.entry["description"],
            archive_entry=match["entry"],
            similarity=match["similarity"],
            parent=self
        )
        result = dialog.exec()
        if result == QDialog.Accepted:
            self._build_ui()
        else:
            delete_idea_entry(self.entry_id)
            self._go_back()

    def _build_ui(self):
        update_idea_entry_color(self.entry_id, EntryColor.YELLOW.value)

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
        btn_back.clicked.connect(self._go_back)
        top_layout.addWidget(btn_back)
        top_layout.addStretch()

        lbl_title = QLabel("Исследование")
        lbl_title.setStyleSheet("color: #e8e8e8; font-size: 15px; font-weight: 500;")
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()

        self.lbl_saved = QLabel("✓ Сохранено")
        self.lbl_saved.setStyleSheet("color: #388E3C; font-size: 12px;")
        self.lbl_saved.setVisible(False)
        top_layout.addWidget(self.lbl_saved)
        top_layout.addSpacing(12)

        root.addWidget(top)

        # Карточка исходной записи
        card_source = QFrame()
        card_source.setFixedHeight(100)
        card_source.setStyleSheet("background-color: #1a1a1a; border-bottom: 1px solid #2a2a2a;")
        source_layout = QVBoxLayout(card_source)
        source_layout.setContentsMargins(24, 10, 24, 10)

        lbl_source_title = QLabel("Исходная запись")
        lbl_source_title.setStyleSheet("color: #666666; font-size: 11px;")
        source_layout.addWidget(lbl_source_title)

        desc = self.entry["description"] if self.entry else ""
        lbl_desc = QLabel(desc[:200] + "..." if len(desc) > 200 else desc)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #e8e8e8; font-size: 14px;")
        source_layout.addWidget(lbl_desc)
        root.addWidget(card_source)

        # Средняя часть — три колонки
        middle = QWidget()
        middle_layout = QHBoxLayout(middle)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(1)

        # Левая — описание
        card_desc = QFrame()
        card_desc.setStyleSheet("background-color: #161616; border-right: 1px solid #2a2a2a;")
        desc_layout = QVBoxLayout(card_desc)
        desc_layout.setContentsMargins(16, 12, 16, 12)
        desc_layout.setSpacing(8)

        lbl_desc_title = QLabel("Описание исследования")
        lbl_desc_title.setStyleSheet("color: #888888; font-size: 12px;")
        desc_layout.addWidget(lbl_desc_title)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Введите описание исследования...")
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e; border: 1px solid #2a2a2a;
                border-radius: 8px; color: #e8e8e8;
                font-size: 14px; padding: 10px;
            }
            QTextEdit:focus { border-color: #534AB7; }
        """)

        saved = self.entry["checklist"] if self.entry else "{}"
        try:
            saved_data = json.loads(saved)
            if isinstance(saved_data, dict) and "research_text" in saved_data:
                self.text_edit.setPlainText(saved_data["research_text"])
        except Exception:
            pass

        self.text_edit.textChanged.connect(self._on_text_changed)
        desc_layout.addWidget(self.text_edit)
        middle_layout.addWidget(card_desc, 2)

        # Средняя — Исследовать
        card_research = QFrame()
        card_research.setStyleSheet("background-color: #0f1a2a; border-right: 1px solid #2a2a2a;")
        research_layout = QVBoxLayout(card_research)
        research_layout.setContentsMargins(16, 12, 16, 12)
        research_layout.setSpacing(8)

        lbl_r = QLabel("Исследовать")
        lbl_r.setStyleSheet("color: #888888; font-size: 12px;")
        research_layout.addWidget(lbl_r)

        self.research_edit = QTextEdit()
        self.research_edit.setPlaceholderText("Источники, данные, ссылки...")
        self.research_edit.setStyleSheet("""
            QTextEdit {
                background-color: #111a2a; border: 1px solid #1a2a3a;
                border-radius: 8px; color: #aaccff;
                font-size: 13px; padding: 8px;
            }
            QTextEdit:focus { border-color: #1565C0; }
        """)

        try:
            if isinstance(saved_data, dict) and "research_notes" in saved_data:
                self.research_edit.setPlainText(saved_data["research_notes"])
        except Exception:
            pass

        self.research_edit.textChanged.connect(self._on_text_changed)
        research_layout.addWidget(self.research_edit)
        middle_layout.addWidget(card_research, 1)

        # Правая — Реализуемо
        card_feasible = QFrame()
        card_feasible.setStyleSheet("background-color: #0f2a0f;")
        feasible_layout = QVBoxLayout(card_feasible)
        feasible_layout.setContentsMargins(16, 12, 16, 12)
        feasible_layout.setSpacing(8)

        lbl_f = QLabel("Реализуемо")
        lbl_f.setStyleSheet("color: #888888; font-size: 12px;")
        feasible_layout.addWidget(lbl_f)

        self.feasible_edit = QTextEdit()
        self.feasible_edit.setPlaceholderText("Оценка реализуемости...")
        self.feasible_edit.setStyleSheet("""
            QTextEdit {
                background-color: #112a11; border: 1px solid #1a3a1a;
                border-radius: 8px; color: #aaffaa;
                font-size: 13px; padding: 8px;
            }
            QTextEdit:focus { border-color: #388E3C; }
        """)

        try:
            if isinstance(saved_data, dict) and "feasibility_notes" in saved_data:
                self.feasible_edit.setPlainText(saved_data["feasibility_notes"])
        except Exception:
            pass

        self.feasible_edit.textChanged.connect(self._on_text_changed)
        feasible_layout.addWidget(self.feasible_edit)
        middle_layout.addWidget(card_feasible, 1)

        root.addWidget(middle, 1)

        # Нижняя панель
        bottom = QWidget()
        bottom.setFixedHeight(60)
        bottom.setStyleSheet("background-color: #1a1a1a; border-top: 1px solid #2a2a2a;")
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(24, 0, 24, 0)
        bottom_layout.addStretch()

        lbl_send = QLabel("Отправить в:")
        lbl_send.setStyleSheet("color: #888888; font-size: 13px;")
        bottom_layout.addWidget(lbl_send)
        bottom_layout.addSpacing(12)

        btn_prog = QPushButton("💻 Программная")
        btn_prog.setFixedHeight(36)
        btn_prog.setCursor(Qt.PointingHandCursor)
        btn_prog.setStyleSheet("""
            QPushButton {
                background-color: #1a1a2e; color: #aaaaff;
                border: 1px solid #333366; border-radius: 6px; padding: 0 16px; font-size: 13px;
            }
            QPushButton:hover { background-color: #252540; }
        """)
        btn_prog.clicked.connect(lambda: self._send_to("software"))
        bottom_layout.addWidget(btn_prog)

        btn_prod = QPushButton("🏭 Производственная")
        btn_prod.setFixedHeight(36)
        btn_prod.setCursor(Qt.PointingHandCursor)
        btn_prod.setStyleSheet("""
            QPushButton {
                background-color: #1a2e1a; color: #aaffaa;
                border: 1px solid #336633; border-radius: 6px; padding: 0 16px; font-size: 13px;
            }
            QPushButton:hover { background-color: #253525; }
        """)
        btn_prod.clicked.connect(lambda: self._send_to("production"))
        bottom_layout.addWidget(btn_prod)

        root.addWidget(bottom)

        self.autosave_timer = QTimer()
        self.autosave_timer.setInterval(3000)
        self.autosave_timer.timeout.connect(self._autosave)
        self.autosave_timer.start()

    def _on_text_changed(self):
        if hasattr(self, 'autosave_timer'):
            self.autosave_timer.start()

    def _autosave(self):
        if not hasattr(self, 'text_edit'):
            return
        from core.database import update_idea_entry_checklist
        update_idea_entry_checklist(self.entry_id, {
            "research_text": self.text_edit.toPlainText(),
            "research_notes": self.research_edit.toPlainText() if hasattr(self, 'research_edit') else "",
            "feasibility_notes": self.feasible_edit.toPlainText() if hasattr(self, 'feasible_edit') else ""
        })
        self.lbl_saved.setVisible(True)
        QTimer.singleShot(2000, self._hide_saved)

    def _send_to(self, theme: str):
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Пусто", "Введите описание исследования.")
            return

        # Создаём новую запись в ИДЕЯ
        new_entry = IdeaEntry(
            project_id=None,
            theme=ProjectType(theme),
            description=text,
            color=EntryColor.RED,
            phase=0
        )
        save_idea_entry(new_entry)

        # Логируем
        log_to_project(
            f"research_{self.entry_id[:8]}",
            f"ИССЛЕДОВАНИЕ → {theme.upper()}",
            text
        )

        # Архивируем исходную запись
        save_to_archive(dict(self.entry))
        update_idea_entry_color(self.entry_id, EntryColor.GREEN.value)

        if hasattr(self, 'autosave_timer'):
            self.autosave_timer.stop()

        self.confirmed.emit(self.entry_id)
        self._go_back()

    def _go_back(self):
        if hasattr(self, 'autosave_timer'):
            self.autosave_timer.stop()
        self._autosave()
        self.main_window.go_back()

    def _hide_saved(self):
        try:
            if hasattr(self, 'lbl_saved') and self.lbl_saved is not None:
                self.lbl_saved.setVisible(False)
        except RuntimeError:
            pass