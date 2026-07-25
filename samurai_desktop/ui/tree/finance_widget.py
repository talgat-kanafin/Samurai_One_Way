import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from core.database import get_connection


class FinanceWidget(QWidget):
    def __init__(self, project_id: str, detail_screen):
        super().__init__()
        self.project_id = project_id
        self.detail_screen = detail_screen
        self.setStyleSheet("background: #111111;")
        self._build_ui()
        self.load()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Итоги сверху
        self.summary = SummaryWidget(self.project_id, self)
        root.addWidget(self.summary)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Дата", "Описание", "Доход", "Расход", "Баланс"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                border: none;
                color: #e8e8e8;
                font-size: 13px;
                gridline-color: #2a2a2a;
            }
            QHeaderView::section {
                background-color: #242424;
                color: #888888;
                border: none;
                border-bottom: 1px solid #2a2a2a;
                padding: 8px;
                font-size: 12px;
            }
            QTableWidget::item { padding: 6px; }
            QTableWidget::item:selected {
                background-color: #534AB733;
            }
        """)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.DoubleClicked)
        self.table.itemChanged.connect(self._on_cell_changed)
        root.addWidget(self.table)

        # Нижняя панель
        bottom = QWidget()
        bottom.setFixedHeight(52)
        bottom.setStyleSheet("background: #1a1a1a; border-top: 1px solid #2a2a2a;")
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(24, 0, 24, 0)

        btn_add = QPushButton("+ Добавить строку")
        btn_add.setFixedHeight(36)
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton {
                background: #534AB7; color: #fff;
                border: none; border-radius: 6px;
                padding: 0 16px; font-size: 13px;
            }
            QPushButton:hover { background: #6358c8; }
        """)
        btn_add.clicked.connect(self._add_row)

        btn_del = QPushButton("Удалить строку")
        btn_del.setFixedHeight(36)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet("""
            QPushButton {
                background: #2e2e2e; color: #aaa;
                border: 1px solid #3a3a3a; border-radius: 6px;
                padding: 0 16px; font-size: 13px;
            }
            QPushButton:hover { color: #fff; border-color: #D32F2F; }
        """)
        btn_del.clicked.connect(self._delete_row)

        bottom_layout.addWidget(btn_add)
        bottom_layout.addWidget(btn_del)
        bottom_layout.addStretch()
        root.addWidget(bottom)

    def load(self):
        with get_connection() as conn:
            tp = conn.execute(
                "SELECT finance_data FROM tree_projects WHERE project_id = ?",
                (self.project_id,)
            ).fetchone()

        data = json.loads(tp["finance_data"]) if tp and tp["finance_data"] else {}
        rows = data.get("rows", [])

        self.table.blockSignals(True)
        self.table.setRowCount(len(rows))

        for i, row in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(row.get("date", "")))
            self.table.setItem(i, 1, QTableWidgetItem(row.get("description", "")))
            self.table.setItem(i, 2, QTableWidgetItem(str(row.get("income", ""))))
            self.table.setItem(i, 3, QTableWidgetItem(str(row.get("expense", ""))))

            balance = row.get("balance", 0)
            bal_item = QTableWidgetItem(str(balance))
            bal_item.setFlags(bal_item.flags() & ~Qt.ItemIsEditable)
            if balance >= 0:
                bal_item.setForeground(QColor("#4caf50"))
            else:
                bal_item.setForeground(QColor("#E24B4A"))
            self.table.setItem(i, 4, bal_item)

        self.table.blockSignals(False)
        self.summary.update_summary()

    def _add_row(self):
        with get_connection() as conn:
            tp = conn.execute(
                "SELECT finance_data FROM tree_projects WHERE project_id = ?",
                (self.project_id,)
            ).fetchone()
        data = json.loads(tp["finance_data"]) if tp and tp["finance_data"] else {}
        rows = data.get("rows", [])
        rows.append({"date": "", "description": "", "income": 0, "expense": 0, "balance": 0})
        data["rows"] = rows
        self._save_data(data)
        self.load()

    def _delete_row(self):
        row = self.table.currentRow()
        if row < 0:
            return
        with get_connection() as conn:
            tp = conn.execute(
                "SELECT finance_data FROM tree_projects WHERE project_id = ?",
                (self.project_id,)
            ).fetchone()
        data = json.loads(tp["finance_data"]) if tp and tp["finance_data"] else {}
        rows = data.get("rows", [])
        if row < len(rows):
            rows.pop(row)
        data["rows"] = rows
        self._save_data(data)
        self.load()

    def _on_cell_changed(self, item):
        row = item.row()
        col = item.column()
        if col == 4:
            return

        with get_connection() as conn:
            tp = conn.execute(
                "SELECT finance_data FROM tree_projects WHERE project_id = ?",
                (self.project_id,)
            ).fetchone()
        data = json.loads(tp["finance_data"]) if tp and tp["finance_data"] else {}
        rows = data.get("rows", [])

        if row >= len(rows):
            return

        val = item.text().strip()
        if col == 0:
            rows[row]["date"] = val
        elif col == 1:
            rows[row]["description"] = val
        elif col == 2:
            try:
                rows[row]["income"] = float(val)
            except ValueError:
                rows[row]["income"] = 0
        elif col == 3:
            try:
                rows[row]["expense"] = float(val)
            except ValueError:
                rows[row]["expense"] = 0

        income = float(rows[row].get("income", 0) or 0)
        expense = float(rows[row].get("expense", 0) or 0)
        rows[row]["balance"] = income - expense

        data["rows"] = rows
        self._save_data(data)
        self.table.blockSignals(True)
        bal_item = QTableWidgetItem(str(rows[row]["balance"]))
        bal_item.setFlags(bal_item.flags() & ~Qt.ItemIsEditable)
        color = "#4caf50" if rows[row]["balance"] >= 0 else "#E24B4A"
        bal_item.setForeground(QColor(color))
        self.table.setItem(row, 4, bal_item)
        self.table.blockSignals(False)
        self.summary.update_summary()

    def _save_data(self, data: dict):
        with get_connection() as conn:
            conn.execute(
                "UPDATE tree_projects SET finance_data = ? WHERE project_id = ?",
                (json.dumps(data, ensure_ascii=False), self.project_id)
            )
            conn.commit()

    def check_stability(self):
        with get_connection() as conn:
            tp = conn.execute(
                "SELECT finance_data FROM tree_projects WHERE project_id = ?",
                (self.project_id,)
            ).fetchone()
        data = json.loads(tp["finance_data"]) if tp and tp["finance_data"] else {}
        rows = data.get("rows", [])
        if len(rows) < 3:
            return False
        last3 = rows[-3:]
        return all(float(r.get("balance", 0) or 0) > 0 for r in last3)


class SummaryWidget(QFrame):
    def __init__(self, project_id: str, finance_widget):
        super().__init__()
        self.project_id = project_id
        self.finance_widget = finance_widget
        self.setFixedHeight(80)
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-bottom: 1px solid #2a2a2a;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(32)

        self.lbl_income = self._stat("Общий доход", "0")
        self.lbl_expense = self._stat("Общий расход", "0")
        self.lbl_balance = self._stat("Баланс", "0")
        self.lbl_stability = QLabel("")
        self.lbl_stability.setStyleSheet("color: #388E3C; font-size: 13px; font-weight: 500;")

        layout.addLayout(self.lbl_income[0])
        layout.addLayout(self.lbl_expense[0])
        layout.addLayout(self.lbl_balance[0])
        layout.addStretch()
        layout.addWidget(self.lbl_stability)

    def _stat(self, title, value):
        col = QVBoxLayout()
        col.setSpacing(2)
        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("color: #666; font-size: 11px;")
        lbl_v = QLabel(value)
        lbl_v.setStyleSheet("color: #e8e8e8; font-size: 16px; font-weight: 500;")
        col.addWidget(lbl_t)
        col.addWidget(lbl_v)
        return col, lbl_v

    def update_summary(self):
        with get_connection() as conn:
            tp = conn.execute(
                "SELECT finance_data, stability_achieved FROM tree_projects WHERE project_id = ?",
                (self.project_id,)
            ).fetchone()

        data = json.loads(tp["finance_data"]) if tp and tp["finance_data"] else {}
        rows = data.get("rows", [])

        total_income = sum(float(r.get("income", 0) or 0) for r in rows)
        total_expense = sum(float(r.get("expense", 0) or 0) for r in rows)
        total_balance = total_income - total_expense

        self.lbl_income[1].setText(f"{total_income:,.0f}")
        self.lbl_expense[1].setText(f"{total_expense:,.0f}")

        color = "#4caf50" if total_balance >= 0 else "#E24B4A"
        self.lbl_balance[1].setStyleSheet(
            f"color: {color}; font-size: 16px; font-weight: 500;"
        )
        self.lbl_balance[1].setText(f"{total_balance:,.0f}")

        # Проверка стабильности
        if not tp["stability_achieved"] and self.finance_widget.check_stability():
            with get_connection() as conn:
                conn.execute(
                    "UPDATE tree_projects SET stability_achieved = 1 WHERE project_id = ?",
                    (self.project_id,)
                )
                conn.commit()
            self.lbl_stability.setText("✓ Стабильность достигнута!")
            self.finance_widget.detail_screen.notify_stability()
        elif tp["stability_achieved"]:
            self.lbl_stability.setText("✓ Стабильность достигнута!")