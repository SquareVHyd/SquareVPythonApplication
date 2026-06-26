from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit,
    QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import QDate

class POCustomerForm(QDialog):
    def __init__(self, po_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PO Customer Details" if po_data else "Add PO Customer")
        self.setMinimumWidth(400)
        self.po_data = po_data
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.po_no_input = QLineEdit()
        
        self.po_date_input = QDateEdit()
        self.po_date_input.setCalendarPopup(True)
        self.po_date_input.setDisplayFormat("yyyy-MM-dd")
        self.po_date_input.setDate(QDate.currentDate())

        if self.po_data:
            self.po_no_input.setText(self.po_data.get("PO_No", ""))
            if self.po_data.get("PO_Date"):
                # Handle different date formats or types
                date_val = self.po_data.get("PO_Date")
                if isinstance(date_val, str):
                    self.po_date_input.setDate(QDate.fromString(date_val, "yyyy-MM-dd"))
                else:
                    # assuming datetime.date
                    self.po_date_input.setDate(QDate(date_val.year, date_val.month, date_val.day))

        form_layout.addRow("PO Number:", self.po_no_input)
        form_layout.addRow("PO Date:", self.po_date_input)

        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def validate_and_accept(self):
        if not self.po_no_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "PO Number is required.")
            return
        self.accept()

    def get_data(self):
        return {
            "po_no": self.po_no_input.text().strip(),
            "po_date": self.po_date_input.date().toString("yyyy-MM-dd")
        }
