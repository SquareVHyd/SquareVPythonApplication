from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox, QComboBox, QDialogButtonBox
from app.services.quotation_service import QuotationService

class PanelModuleForm(QDialog):
    def __init__(self, quote_id, panel_id=None, pm_data=None, parent=None):
        super().__init__(parent)
        self.quote_id = quote_id
        self.initial_panel_id = panel_id # Store the panel_id passed for new modules
        self.service = QuotationService()
        self.setWindowTitle("Edit Panel Module" if pm_data else "Add Panel Module")
        self.setMinimumWidth(400)
        self.setup_ui()
        self.load_lookups()
        if pm_data: self.fill_data(pm_data)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.panel_combo = QComboBox()
        self.ing_og_input = QLineEdit()
        self.qty_input = QSpinBox()
        self.qty_input.setRange(1, 1000)
        self.type_combo = QComboBox()
        self.pole_input = QLineEdit()
        self.ka_input = QLineEdit()
        self.release_input = QLineEdit()
        self.protection_input = QLineEdit()
        self.remark_input = QLineEdit()

        form.addRow("Target Panel:", self.panel_combo)
        form.addRow("Incomer/Outgoing:", self.ing_og_input)
        form.addRow("Quantity:", self.qty_input)
        form.addRow("Module Type:", self.type_combo)
        form.addRow("Poles:", self.pole_input)
        form.addRow("KA Rating:", self.ka_input)
        form.addRow("Release:", self.release_input)
        form.addRow("Protection:", self.protection_input)
        form.addRow("Remark:", self.remark_input)
        
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_lookups(self):
        panels = self.service.get_panels_by_quote(self.quote_id)
        for p in panels: self.panel_combo.addItem(p[4], p[0]) # ID, Name
        
        # Set initial selection if panel_id was provided (for new modules)
        if self.initial_panel_id is not None:
            idx = self.panel_combo.findData(self.initial_panel_id)
            if idx >= 0: self.panel_combo.setCurrentIndex(idx)
        types = self.service.get_module_costs_lookup()
        for t in types: self.type_combo.addItem(t[1], t[0]) # ID, Type

    def fill_data(self, data):
        idx = self.panel_combo.findData(int(data.get("panel_id") or 0))
        if idx >= 0: self.panel_combo.setCurrentIndex(idx)
        
        self.ing_og_input.setText(data.get("ing_og", ""))
        self.qty_input.setValue(int(data.get("qty") or 1))
        
        t_idx = self.type_combo.findData(int(data.get("type_id") or 0))
        if t_idx >= 0: self.type_combo.setCurrentIndex(t_idx)
        
        self.pole_input.setText(data.get("pole", ""))
        self.ka_input.setText(data.get("ka", ""))
        self.release_input.setText(data.get("release", ""))
        self.protection_input.setText(data.get("protection", ""))
        self.remark_input.setText(data.get("remark", ""))

    def get_data(self):
        return {
            "panel_id": self.panel_combo.currentData(),
            "ing_og": self.ing_og_input.text(),
            "qty": self.qty_input.value(),
            "type_id": self.type_combo.currentData(),
            "pole": self.pole_input.text(),
            "ka": self.ka_input.text(),
            "release": self.release_input.text(),
            "protection": self.protection_input.text(),
            "remark": self.remark_input.text()
        }