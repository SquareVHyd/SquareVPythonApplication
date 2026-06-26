from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QMessageBox, QDoubleSpinBox, QSpinBox
)

class POItemForm(QDialog):
    def __init__(self, item_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit PO Item" if item_data else "Add PO Item")
        self.setMinimumWidth(400)
        self.item_data = item_data
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.desc_input = QLineEdit()
        
        self.qty_input = QDoubleSpinBox()
        self.qty_input.setRange(0, 999999)
        self.qty_input.setDecimals(2)
        
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 999999999)
        self.price_input.setDecimals(2)
        
        self.warranty_input = QDoubleSpinBox()
        self.warranty_input.setRange(0, 100)
        self.warranty_input.setDecimals(2)
        self.warranty_input.setSuffix(" Years")

        if self.item_data:
            self.desc_input.setText(self.item_data.get("Description", ""))
            self.qty_input.setValue(float(self.item_data.get("Qty", 0)))
            self.price_input.setValue(float(self.item_data.get("Price", 0)))
            self.warranty_input.setValue(float(self.item_data.get("Warranty", 0)))

        form_layout.addRow("Description:", self.desc_input)
        form_layout.addRow("Quantity:", self.qty_input)
        form_layout.addRow("Unit Price:", self.price_input)
        form_layout.addRow("Warranty:", self.warranty_input)

        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def validate_and_accept(self):
        if not self.desc_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Description is required.")
            return
        self.accept()

    def get_data(self):
        return {
            "description": self.desc_input.text().strip(),
            "qty": self.qty_input.value(),
            "price": self.price_input.value(),
            "warranty": self.warranty_input.value()
        }
