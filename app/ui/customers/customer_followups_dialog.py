from datetime import datetime

from PySide6.QtCore import QDateTime
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QDateTimeEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QHeaderView,
)

from app.services.customer_followup_service import CustomerFollowupService
from app.config.ui_state import UIStateManager


class CustomerFollowupsDialog(QDialog):

    def __init__(self, contact_id, contact_name=None, parent=None):
        super().__init__(parent)

        self.contact_id = contact_id
        self.contact_name = contact_name or str(contact_id)
        self.service = CustomerFollowupService()

        self.setWindowTitle(f"Followups - {self.contact_name}")
        self.resize(920, 420)

        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search followups...")

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setToolTip("Refresh followups (Ctrl+R)")
        self.add_btn = QPushButton("➕ Add")
        self.add_btn.setToolTip("Add followup (Ctrl+N)")
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setToolTip("Edit selected followup (Ctrl+E)")
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setToolTip("Delete selected followup (Delete)")

        header.addWidget(self.search_box)
        header.addWidget(self.refresh_btn)
        header.addWidget(self.add_btn)
        header.addWidget(self.edit_btn)
        header.addWidget(self.delete_btn)

        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(
            ["Date of Followup", "What Discussed", "Mode of Contact"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        header.setMinimumSectionSize(80)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setStyleSheet(
            "QTableWidget { gridline-color: #e9ecef; border: 1px solid #d9d9d9; }"
            "QHeaderView::section { background-color: #f8f9fa; padding: 6px; border: 1px solid #d9d9d9; }"
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.table)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.refresh_btn.clicked.connect(self.load_followups)
        self.add_btn.clicked.connect(self.add_followup)
        self.edit_btn.clicked.connect(self.edit_followup)
        self.delete_btn.clicked.connect(self.delete_followup)
        self.search_box.textChanged.connect(self.search_followups)

        QShortcut(QKeySequence.Find, self, activated=self.search_box.setFocus)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.add_followup)
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self.edit_followup)
        QShortcut(QKeySequence.Delete, self, activated=self.delete_followup)
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.load_followups)
        QShortcut(QKeySequence("F1"), self, activated=self.show_shortcuts)

        self.load_followups()
        self._restore_state()

    def load_followups(self):
        followups = self.service.get_followups_by_contact_id(self.contact_id)
        self.followups = list(followups)
        self.displayed_followups = self.followups
        self.table.setRowCount(0)
        self.populate_table(self.displayed_followups)
        self.table.resizeColumnsToContents()
        self._apply_saved_column_widths()

    def _restore_state(self):
        state = UIStateManager.get_dialog_state(f"customer_followups_{self.contact_id}")
        search_text = state.get("search_text", "")
        if search_text:
            self.search_box.blockSignals(True)
            self.search_box.setText(search_text)
            self.search_box.blockSignals(False)
            self.search_followups()

    def _apply_saved_column_widths(self):
        state = UIStateManager.get_dialog_state(f"customer_followups_{self.contact_id}")
        widths = state.get("column_widths", {})
        for col in range(self.table.columnCount()):
            width = widths.get(str(col))
            if width:
                self.table.setColumnWidth(col, int(width))

    def populate_table(self, followups):
        self.table.setRowCount(len(followups))
        for row_index, row in enumerate(followups):
            followup_date = row[2]
            if isinstance(followup_date, datetime):
                followup_date = followup_date.strftime("%Y-%m-%d %H:%M:%S")
            self.table.setItem(row_index, 0, QTableWidgetItem(str(followup_date or "")))
            self.table.setItem(row_index, 1, QTableWidgetItem(str(row[3] or "")))
            self.table.setItem(row_index, 2, QTableWidgetItem(str(row[4] or "")))

    def search_followups(self):
        keyword = self.search_box.text().strip().lower()
        if not keyword:
            self.displayed_followups = self.followups
            self.populate_table(self.displayed_followups)
            return

        filtered = []
        for row in self.followups:
            text = " ".join(str(x or "") for x in row).lower()
            if keyword in text:
                filtered.append(row)

        self.displayed_followups = filtered
        self.populate_table(self.displayed_followups)

    def add_followup(self):
        dialog = CustomerFollowupForm(self)
        if dialog.exec():
            data = dialog.get_data()
            self.service.create_followup(
                self.contact_id,
                data["date_of_followup"],
                data["what_discussed"],
                data["mode_of_contact"],
            )
            self.load_followups()

    def edit_followup(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select followup", "Please select a followup to edit")
            return

        followup = self.displayed_followups[row]
        dialog = CustomerFollowupForm(self, followup)
        if dialog.exec():
            data = dialog.get_data()
            self.service.update_followup(
                followup[0],
                data["date_of_followup"],
                data["what_discussed"],
                data["mode_of_contact"],
            )
            self.load_followups()

    def delete_followup(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select followup", "Please select a followup to delete")
            return

        followup = self.displayed_followups[row]
        confirm = QMessageBox.question(
            self,
            "Delete Followup",
            "Delete selected followup?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self.service.delete_followup(followup[0])
            self.load_followups()

    def closeEvent(self, event):
        widths = {str(i): self.table.columnWidth(i) for i in range(self.table.columnCount())}
        UIStateManager.save_dialog_state(
            f"customer_followups_{self.contact_id}",
            column_widths=widths,
            search_text=self.search_box.text(),
        )
        super().closeEvent(event)

    def show_shortcuts(self):
        QMessageBox.information(
            self,
            "Shortcuts",
            """
Ctrl+F  Search
Ctrl+N  Add Followup
Ctrl+E  Edit Followup
Delete  Delete Followup
Ctrl+R  Refresh
F1      Help
""",
        )


class CustomerFollowupForm(QDialog):

    def __init__(self, parent=None, followup=None):
        super().__init__(parent)

        self.setWindowTitle("Followup Details")
        self.resize(520, 360)

        layout = QVBoxLayout(self)

        self.date_input = QDateTimeEdit(QDateTime.currentDateTime())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd HH:mm:ss")

        self.what_discussed_input = QTextEdit()
        self.mode_input = QLineEdit()

        layout.addWidget(QLabel("Date of Followup"))
        layout.addWidget(self.date_input)
        layout.addWidget(QLabel("What Discussed"))
        layout.addWidget(self.what_discussed_input)
        layout.addWidget(QLabel("Mode of Contact"))
        layout.addWidget(self.mode_input)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        if followup:
            followup_date = followup[2]
            if isinstance(followup_date, datetime):
                self.date_input.setDateTime(QDateTime(followup_date))
            else:
                try:
                    self.date_input.setDateTime(QDateTime.fromString(
                        str(followup_date), "yyyy-MM-dd HH:mm:ss"
                    ))
                except Exception:
                    pass

            self.what_discussed_input.setPlainText(str(followup[3] or ""))
            self.mode_input.setText(str(followup[4] or ""))

    def get_data(self):
        date_time = self.date_input.dateTime()
        try:
            followup_date = date_time.toPython()
        except AttributeError:
            followup_date = date_time.toPyDateTime()

        return {
            "date_of_followup": followup_date,
            "what_discussed": self.what_discussed_input.toPlainText().strip(),
            "mode_of_contact": self.mode_input.text().strip(),
        }
