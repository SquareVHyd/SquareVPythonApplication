from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QSpinBox, QComboBox, QDialogButtonBox
)

class PanelForm(QDialog):
    """Form for adding or editing a panel associated with a quotation."""
    
    def __init__(self, quote_id, panel_data=None, parent=None):
        super().__init__(parent)
        self.quote_id = quote_id
        self.setWindowTitle("Edit Panel" if panel_data else "Add New Panel")
        self.setMinimumWidth(400)
        self.setup_ui()
        if panel_data:
            self.fill_data(panel_data)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.category_input = QLineEdit()
        self.serial_input = QLineEdit()
        self.name_input = QLineEdit()
        
        self.qty_input = QSpinBox()
        self.qty_input.setRange(1, 1000)
        
        self.l_input = QSpinBox(); self.l_input.setRange(0, 10000)
        self.h_input = QSpinBox(); self.h_input.setRange(0, 10000)
        self.d_input = QSpinBox(); self.d_input.setRange(0, 10000)
        self.waste_input = QSpinBox(); self.waste_input.setRange(0, 100)
        
        self.ka_input = QLineEdit()
        self.earth_input = QLineEdit()
        self.stand_input = QComboBox()
        self.stand_input.addItems(["No", "Yes"])
        self.busbar_input = QLineEdit()
        
        form.addRow("Category:", self.category_input)
        form.addRow("Serial:", self.serial_input)
        form.addRow("Panel Name:", self.name_input)
        form.addRow("Quantity:", self.qty_input)
        form.addRow("Length (mm):", self.l_input)
        form.addRow("Height (mm):", self.h_input)
        form.addRow("Depth (mm):", self.d_input)
        form.addRow("Add Waste (%):", self.waste_input)
        form.addRow("KA Rating:", self.ka_input)
        form.addRow("Earth Runs:", self.earth_input)
        form.addRow("Stand Required:", self.stand_input)
        form.addRow("Busbar Material:", self.busbar_input)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def fill_data(self, data):
        self.category_input.setText(data.get("category", ""))
        self.serial_input.setText(data.get("serial", ""))
        self.name_input.setText(data.get("name", ""))
        self.qty_input.setValue(int(data.get("qty") or 1))
        self.l_input.setValue(int(data.get("length") or 0))
        self.h_input.setValue(int(data.get("height") or 0))
        self.d_input.setValue(int(data.get("depth") or 0))
        self.waste_input.setValue(int(data.get("waste") or 0))
        self.ka_input.setText(data.get("ka_rating", ""))
        self.earth_input.setText(data.get("earth_runs", ""))
        self.stand_input.setCurrentText(data.get("stand", "No"))
        self.busbar_input.setText(data.get("busbar", ""))

    def get_data(self):
        return {
            "quote_id": self.quote_id, "category": self.category_input.text(), "serial": self.serial_input.text(),
            "name": self.name_input.text(), "qty": self.qty_input.value(), "length": self.l_input.value(),
            "height": self.h_input.value(), "depth": self.d_input.value(), "waste": self.waste_input.value(),
            "ka_rating": self.ka_input.text(), "earth_runs": self.earth_input.text(), "stand": self.stand_input.currentText(),
            "busbar": self.busbar_input.text()
        }