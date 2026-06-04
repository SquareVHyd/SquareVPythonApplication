from PySide6.QtWidgets import (
QDialog,
QVBoxLayout,
QPushButton,
QTableWidget,
QTableWidgetItem,
QLineEdit,
QMessageBox,
QHBoxLayout,
QLabel,
    QHeaderView,
)

from PySide6.QtGui import (
    QShortcut,
    QKeySequence,
)

from app.services.customer_contact_service import CustomerContactService
from app.config.ui_state import UIStateManager
from app.ui.customers.customer_followups_dialog import CustomerFollowupsDialog


class CustomerContactsDialog(QDialog):

    def __init__(self, customer_id, parent=None, contact=None):
        super().__init__(parent)

        self.customer_id = customer_id
        self.service = CustomerContactService()

        self.setWindowTitle(f"Customer Contacts - Customer {customer_id}")
        self.resize(900, 400)

        layout = QVBoxLayout(self)

        # Header
        header = QHBoxLayout()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search contacts...")

        self.refresh_btn = QPushButton("Refresh")
        self.add_btn = QPushButton("Add")
        self.edit_btn = QPushButton("Edit")
        self.delete_btn = QPushButton("Delete")
        self.followups_btn = QPushButton("Followups")

        header.addWidget(self.search_box)
        header.addWidget(self.refresh_btn)
        header.addWidget(self.add_btn)
        header.addWidget(self.edit_btn)
        header.addWidget(self.delete_btn)
        header.addWidget(self.followups_btn)

        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Contact Name", "Title", "Designation", "Mobile 1", "Mobile 2"]
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

        # BUTTON EVENTS
        self.add_btn.clicked.connect(self.add_contact)
        self.edit_btn.clicked.connect(self.edit_contact)
        self.delete_btn.clicked.connect(self.delete_contact)
        self.followups_btn.clicked.connect(self.open_followups)
        self.refresh_btn.clicked.connect(self.load_contacts)
        self.search_box.textChanged.connect(self.search_contacts)

        # SHORTCUTS
        QShortcut(QKeySequence.Find, self, activated=self.search_box.setFocus)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.add_contact)
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self.edit_contact)
        QShortcut(QKeySequence.Delete, self, activated=self.delete_contact)
        QShortcut(QKeySequence("Ctrl+U"), self, activated=self.open_followups)
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

    def open_followups(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select contact", "Please select a contact to view followups")
            return

        contact = self.displayed_contacts[row]
        dialog = CustomerFollowupsDialog(
            contact[0],
            contact_name=str(contact[2] or ""),
            parent=self,
        )
        dialog.exec()

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
Ctrl+U  View Followups
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
