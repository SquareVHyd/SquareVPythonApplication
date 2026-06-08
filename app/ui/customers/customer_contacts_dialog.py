from datetime import datetime
from PySide6.QtWidgets import (
QDialog,
QVBoxLayout,
QWidget,
QPushButton,
QTableWidget,
QTableWidgetItem,
QLineEdit,
QMessageBox,
QHBoxLayout,
QLabel,
    QHeaderView,
    QSplitter,
    QTextEdit,
    QDateTimeEdit
)

from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import Qt, QDateTime

from app.services.customer_contact_service import CustomerContactService
from app.services.customer_followup_service import CustomerFollowupService
from app.config.ui_state import UIStateManager
from app.ui.customers.customer_followups_dialog import CustomerFollowupForm


class CustomerContactsDialog(QDialog):

    def __init__(self, customer_id, parent=None, contact=None):
        super().__init__(parent)

        self.customer_id = customer_id
        self.service = CustomerContactService()
        self.followup_service = CustomerFollowupService()
        self.current_contact_id = None
        self.followups = []

        self.setWindowTitle("Customer Contacts & Follow-up Manager")
        self.resize(1200, 750)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # Main Header for Contacts
        header = QHBoxLayout()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search contacts...")

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setToolTip("Refresh contacts (Ctrl+R)")
        self.add_btn = QPushButton("➕ Add")
        self.add_btn.setToolTip("Add contact (Ctrl+N)")
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setToolTip("Edit selected contact (Ctrl+E)")
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setToolTip("Delete selected contact (Delete)")

        header.addWidget(self.search_box)
        header.addWidget(self.refresh_btn)
        header.addWidget(self.add_btn)
        header.addWidget(self.edit_btn)
        header.addWidget(self.delete_btn)

        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setObjectName("contactsTable")
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Contact Name", "Title", "Designation", "Mobile 1", "Mobile 2"]
        )
        h_header = self.table.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.Interactive)
        h_header.setStretchLastSection(True)
        h_header.setMinimumSectionSize(100)
        
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setStyleSheet(
            "QTableWidget { gridline-color: #e9ecef; border: 1px solid #d9d9d9; }"
            "QHeaderView::section { background-color: #f8f9fa; padding: 6px; border: 1px solid #d9d9d9; }"
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        # Followups Section
        followup_container = QWidget()
        followup_container.setObjectName("followupContainer")
        
        self.followup_table = QTableWidget()
        self.followup_table.setObjectName("followupTable")
        self.followup_table.setColumnCount(3)
        self.followup_table.setHorizontalHeaderLabels(
            ["Date", "Discussion", "Mode"]
        )
        self.followup_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.followup_table.horizontalHeader().setStretchLastSection(True)
        self.followup_table.setAlternatingRowColors(True)
        self.followup_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.followup_table.setSelectionMode(QTableWidget.SingleSelection)

        f_header_layout = QVBoxLayout()
        f_btn_layout = QHBoxLayout()
        self.add_f_btn = QPushButton("➕ Add Followup")
        self.edit_f_btn = QPushButton("✏️ Edit Followup")
        self.delete_f_btn = QPushButton("🗑️ Delete Followup")
        
        f_label = QLabel("<b>Follow-up History</b>")
        f_label.setStyleSheet("font-size: 14px; color: #1e293b;")
        
        f_btn_layout.addWidget(f_label)
        f_btn_layout.addStretch()
        f_btn_layout.addWidget(self.add_f_btn)
        f_btn_layout.addWidget(self.edit_f_btn)
        f_btn_layout.addWidget(self.delete_f_btn)

        f_header_layout.addLayout(f_btn_layout)
        f_header_layout.addWidget(self.followup_table)
        followup_container.setLayout(f_header_layout)

        # Splitter to show Contacts and Followups in the same window
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.table)
        self.splitter.addWidget(followup_container)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setHandleWidth(10)
        layout.addWidget(self.splitter)

        # Footer Action
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        close_btn = QPushButton("Close Manager")
        close_btn.setMinimumWidth(120)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        layout.addLayout(footer_layout)

        # Styling
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QSplitter::handle {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f1f5f9, stop:0.5 #cbd5e1, stop:1 #f1f5f9);
                border-left: 1px solid #94a3b8;
                border-right: 1px solid #94a3b8;
            }
            QTableWidget {
                border: 1px solid #e2e8f0;
                gridline-color: #f1f5f9;
                background-color: #ffffff;
                selection-background-color: #dbeafe;
                selection-color: #1e40af;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                color: #475569;
                font-weight: bold;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
            }
            QPushButton {
                padding: 6px 12px;
                border-radius: 4px;
            }
        """)

        # BUTTON EVENTS
        self.add_btn.clicked.connect(self.add_contact)
        self.edit_btn.clicked.connect(self.edit_contact)
        self.delete_btn.clicked.connect(self.delete_contact)
        self.refresh_btn.clicked.connect(self.load_contacts)
        self.search_box.textChanged.connect(self.search_contacts)
        
        self.add_f_btn.clicked.connect(self.add_followup)
        self.edit_f_btn.clicked.connect(self.edit_followup)
        self.delete_f_btn.clicked.connect(self.delete_followup)

        # Selection event to update followups in real-time
        self.table.itemSelectionChanged.connect(self.on_contact_selection_changed)

        # SHORTCUTS
        QShortcut(QKeySequence.Find, self, activated=self.search_box.setFocus)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.add_contact)
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self.edit_contact)
        QShortcut(QKeySequence.Delete, self, activated=self.delete_contact)
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.load_contacts)
        QShortcut(QKeySequence("F1"), self, activated=self.show_shortcuts)

        # Load data
        self.load_contacts()
        self._restore_state()

    def load_contacts(self):
        contacts = self.service.get_contacts_by_customer(self.customer_id)
        self.contacts = list(contacts)
        self.displayed_contacts = self.contacts
        self.table.setRowCount(0)
        self.populate_table(self.displayed_contacts)
        self.table.resizeColumnsToContents()
        self._apply_saved_column_widths()

    def _restore_state(self):
        state = UIStateManager.get_dialog_state(f"customer_contacts_{self.customer_id}")
        search_text = state.get("search_text", "")
        if search_text:
            self.search_box.blockSignals(True)
            self.search_box.setText(search_text)
            self.search_box.blockSignals(False)
            self.search_contacts()

    def _apply_saved_column_widths(self):
        state = UIStateManager.get_dialog_state(f"customer_contacts_{self.customer_id}")
        widths = state.get("column_widths", {})
        for col in range(self.table.columnCount()):
            width = widths.get(str(col))
            if width:
                self.table.setColumnWidth(col, int(width))

    def populate_table(self, contacts):
        self.table.setRowCount(len(contacts))
        for row_index, row in enumerate(contacts):
            self.table.setItem(row_index, 0, QTableWidgetItem(str(row[2] or "")))
            self.table.setItem(row_index, 1, QTableWidgetItem(str(row[3] or "")))
            self.table.setItem(row_index, 2, QTableWidgetItem(str(row[4] or "")))
            self.table.setItem(row_index, 3, QTableWidgetItem(str(row[5] or "")))
            self.table.setItem(row_index, 4, QTableWidgetItem(str(row[6] or "")))

    def search_contacts(self):
        keyword = self.search_box.text().strip().lower()
        if not keyword:
            self.displayed_contacts = self.contacts
            self.populate_table(self.displayed_contacts)
            return
        filtered = []
        for row in self.contacts:
            text = " ".join(str(x or "") for x in row).lower()
            if keyword in text:
                filtered.append(row)
        self.displayed_contacts = filtered
        self.populate_table(self.displayed_contacts)

    def on_contact_selection_changed(self):
        row = self.table.currentRow()
        if row < 0:
            self.current_contact_id = None
            self.followup_table.setRowCount(0)
            return
        
        contact = self.displayed_contacts[row]
        self.current_contact_id = contact[0]
        self.load_followups()

    def load_followups(self):
        if not self.current_contact_id:
            self.followup_table.setRowCount(0)
            return
        
        self.followups = list(self.followup_service.get_followups_by_contact_id(self.current_contact_id))
        self.followup_table.setRowCount(len(self.followups))
        for i, row in enumerate(self.followups):
            f_date = row[2]
            if isinstance(f_date, datetime):
                f_date = f_date.strftime("%Y-%m-%d %H:%M")
            self.followup_table.setItem(i, 0, QTableWidgetItem(str(f_date or "")))
            self.followup_table.setItem(i, 1, QTableWidgetItem(str(row[3] or "")))
            self.followup_table.setItem(i, 2, QTableWidgetItem(str(row[4] or "")))
        self.followup_table.resizeColumnsToContents()

    def add_followup(self):
        if not self.current_contact_id:
            QMessageBox.warning(self, "Select Contact", "Please select a contact first")
            return
        dialog = CustomerFollowupForm(self)
        if dialog.exec():
            data = dialog.get_data()
            self.followup_service.create_followup(
                self.current_contact_id, data["date_of_followup"],
                data["what_discussed"], data["mode_of_contact"]
            )
            self.load_followups()

    def edit_followup(self):
        row = self.followup_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select Followup", "Please select a followup to edit")
            return
        followup = self.followups[row]
        dialog = CustomerFollowupForm(self, followup)
        if dialog.exec():
            data = dialog.get_data()
            self.followup_service.update_followup(
                followup[0], data["date_of_followup"],
                data["what_discussed"], data["mode_of_contact"]
            )
            self.load_followups()

    def delete_followup(self):
        row = self.followup_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select Followup", "Please select a followup to delete")
            return
        followup = self.followups[row]
        if QMessageBox.question(self, "Delete", "Delete selected followup?") == QMessageBox.Yes:
            self.followup_service.delete_followup(followup[0])
            self.load_followups()

    def add_contact(self):
        # assumes a CustomerContactForm exists elsewhere in the project
        dialog = CustomerContactForm(self)
        if dialog.exec():
            data = dialog.get_data()
            self.service.create_contact(
                self.customer_id,
                data["name"],
                data["title"],
                data["designation"],
                data["mobile1"],
                data["mobile2"],
            )
            self.load_contacts()

    def edit_contact(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select contact", "Please select a contact to edit")
            return
        contact = self.displayed_contacts[row]
        dialog = CustomerContactForm(self, contact)
        if dialog.exec():
            data = dialog.get_data()
            self.service.update_contact(
                contact[0],
                data["name"],
                data["title"],
                data["designation"],
                data["mobile1"],
                data["mobile2"],
            )
            self.load_contacts()

    def delete_contact(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select contact", "Please select a contact to delete")
            return
        contact = self.displayed_contacts[row]
        confirm = QMessageBox.question(self, "Delete Contact", "Delete selected contact?")
        if confirm == QMessageBox.Yes:
            self.service.delete_contact(contact[0])
            self.load_contacts()

    def closeEvent(self, event):
        widths = {str(i): self.table.columnWidth(i) for i in range(self.table.columnCount())}
        UIStateManager.save_dialog_state(
            f"customer_contacts_{self.customer_id}",
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
Ctrl+N  Add Contact
Ctrl+E  Edit Contact
Delete  Delete Contact
Ctrl+R  Refresh
F1      Help
""",
        )
class  CustomerContactForm(QDialog):

    def __init__(self, parent=None, contact=None):
        super().__init__(parent)

        self.setWindowTitle("Contact Details")
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        self.name_input = QLineEdit()
        self.title_input = QLineEdit()
        self.designation_input = QLineEdit()
        self.mobile1_input = QLineEdit()
        self.mobile2_input = QLineEdit()

        layout.addWidget(QLabel("Name"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Title"))
        layout.addWidget(self.title_input)
        layout.addWidget(QLabel("Designation"))
        layout.addWidget(self.designation_input)
        layout.addWidget(QLabel("Mobile 1"))
        layout.addWidget(self.mobile1_input)
        layout.addWidget(QLabel("Mobile 2"))
        layout.addWidget(self.mobile2_input)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        if contact:
            self.name_input.setText(str(contact[2] or ""))
            self.title_input.setText(str(contact[3] or ""))
            self.designation_input.setText(str(contact[4] or ""))
            self.mobile1_input.setText(str(contact[5] or ""))
            self.mobile2_input.setText(str(contact[6] or ""))

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "title": self.title_input.text().strip(),
            "designation": self.designation_input.text().strip(),
            "mobile1": self.mobile1_input.text().strip(),
            "mobile2": self.mobile2_input.text().strip(),
        }
