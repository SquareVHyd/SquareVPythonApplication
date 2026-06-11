from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QPushButton, QComboBox, QDateEdit, 
    QDialogButtonBox, QLabel, QMessageBox, QInputDialog
)
from PySide6.QtCore import QDate, Qt
from app.services.quotation_service import QuotationService

class QuickCustomerDialog(QDialog):
    """Simple dialog to quickly add a customer."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Customer")
        layout = QFormLayout(self)
        self.name_input = QLineEdit()
        layout.addRow("Customer Name:", self.name_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_name(self):
        return self.name_input.text().strip()

class QuotationForm(QDialog):
    """Form for adding or editing a Quotation record."""
    
    def __init__(self, parent=None, quotation_data=None):
        super().__init__(parent)
        self.service = QuotationService()
        self.quotation_data = quotation_data
        self.setWindowTitle("Edit Quotation" if quotation_data else "New Quotation")
        self.resize(500, 450)
        
        self.setup_ui()
        self.load_customers()
        
        if quotation_data:
            self.fill_data(quotation_data)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Customer Dropdown + Add Button
        cust_layout = QHBoxLayout()
        self.customer_combo = QComboBox()
        self.add_customer_btn = QPushButton("+")
        self.add_customer_btn.setFixedWidth(30)
        self.add_customer_btn.setToolTip("Add new customer")
        self.add_customer_btn.clicked.connect(self._quick_add_customer)
        
        cust_layout.addWidget(self.customer_combo, 1)
        cust_layout.addWidget(self.add_customer_btn)
        form_layout.addRow("Customer:", cust_layout)

        self.ref_no_input = QLineEdit()
        form_layout.addRow("Ref No:", self.ref_no_input)

        self.req_date_input = QDateEdit(calendarPopup=True)
        self.req_date_input.setDate(QDate.currentDate())
        form_layout.addRow("Req. Date:", self.req_date_input)

        self.quote_date_input = QDateEdit(calendarPopup=True)
        self.quote_date_input.setDate(QDate.currentDate())
        form_layout.addRow("Quote Date:", self.quote_date_input)

        self.subject_input = QLineEdit()
        form_layout.addRow("Subject:", self.subject_input)

        self.project_input = QLineEdit()
        form_layout.addRow("Project:", self.project_input)

        self.contact_input = QLineEdit()
        form_layout.addRow("Contact Person:", self.contact_input)

        self.prepared_by_input = QLineEdit()
        form_layout.addRow("Prepared By:", self.prepared_by_input)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Draft", "Sent", "Pending", "Approved", "Revised", "Cancelled"])
        form_layout.addRow("Status:", self.status_combo)

        layout.addLayout(form_layout)

        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def load_customers(self):
        """Populates the customer dropdown from the service."""
        self.customer_combo.clear()
        # Assuming service has a get_all_customers returning (id, name)
        try:
            customers = self.service.get_all_customers()
            for cid, name in customers:
                self.customer_combo.addItem(name, cid)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error loading customers: {e}")

    def _quick_add_customer(self):
        """Opens a small dialog to add a customer on the fly."""
        dialog = QuickCustomerDialog(self)
        if dialog.exec() == QDialog.Accepted:
            name = dialog.get_name()
            if name:
                try:
                    # Implementation depends on your service layer
                    new_id = self.service.create_customer_quick(name)
                    self.load_customers()
                    index = self.customer_combo.findData(new_id)
                    if index >= 0:
                        self.customer_combo.setCurrentIndex(index)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to add customer: {e}")

    def fill_data(self, data):
        index = self.customer_combo.findData(data["customer_id"])
        if index >= 0: self.customer_combo.setCurrentIndex(index)
        
        self.ref_no_input.setText(data.get("ref_no", ""))
        self.req_date_input.setDate(QDate.fromString(data["req_date"], Qt.ISODate) if data.get("req_date") else QDate.currentDate())
        self.quote_date_input.setDate(QDate.fromString(data["quote_date"], Qt.ISODate) if data.get("quote_date") else QDate.currentDate())
        self.subject_input.setText(data.get("subject", ""))
        self.project_input.setText(data.get("project", ""))
        self.contact_input.setText(data.get("contact", ""))
        self.prepared_by_input.setText(data.get("prepared_by", ""))
        self.status_combo.setCurrentText(data.get("status", "Draft"))

    def get_data(self):
        return {
            "customer_id": self.customer_combo.currentData(),
            "ref_no": self.ref_no_input.text().strip(),
            "req_date": self.req_date_input.date().toString(Qt.ISODate),
            "quote_date": self.quote_date_input.date().toString(Qt.ISODate),
            "subject": self.subject_input.text().strip(),
            "project": self.project_input.text().strip(),
            "contact": self.contact_input.text().strip(),
            "prepared_by": self.prepared_by_input.text().strip(),
            "status": self.status_combo.currentText()
        }

    def validate_and_accept(self):
        if self.customer_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Validation", "Please select a customer.")
            return
        self.accept()
