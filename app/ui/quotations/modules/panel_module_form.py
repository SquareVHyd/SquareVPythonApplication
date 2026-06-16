from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, 
    QSpinBox, QComboBox, QDialogButtonBox, QPushButton, QMessageBox
)
from app.services.quotation_service import QuotationService

class QuickModuleTypeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Module Type")
        layout = QFormLayout(self)
        self.type_input = QLineEdit()
        layout.addRow("Type Name:", self.type_input)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    def get_name(self): return self.type_input.text().strip()

class PanelModuleForm(QDialog):
    def __init__(self, quote_id, panel_id=None, pm_data=None, parent=None, dropdown_lists=None):
        super().__init__(parent)
        self.quote_id = quote_id
        self.initial_panel_id = panel_id
        self.service = QuotationService()
        self.dropdown_lists = dropdown_lists or {}
        self.setWindowTitle("Edit Panel Module" if pm_data else "Add Panel Module")
        self.setMinimumWidth(400)
        self.setup_ui()
        self.load_lookups()
        if pm_data: self.fill_data(pm_data)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.panel_combo = QComboBox()
        self.ing_og_combo = QComboBox()
        self.ing_og_combo.setEditable(True)
        self.qty_input = QSpinBox()
        self.qty_input.setRange(1, 1000)
        type_layout = QHBoxLayout()
        self.type_combo = QComboBox()
        self.add_type_btn = QPushButton("+")
        self.add_type_btn.setFixedWidth(30)
        self.add_type_btn.clicked.connect(self._quick_add_type)
        type_layout.addWidget(self.type_combo, 1)
        type_layout.addWidget(self.add_type_btn)
        self.pole_combo = QComboBox(); self.pole_combo.setEditable(True)
        self.ka_combo = QComboBox(); self.ka_combo.setEditable(True)
        self.release_combo = QComboBox(); self.release_combo.setEditable(True)
        self.protection_combo = QComboBox(); self.protection_combo.setEditable(True)
        self.remark_input = QLineEdit()
        form.addRow("Target Panel:", self.panel_combo)
        form.addRow("Incomer/Outgoing:", self.ing_og_combo)
        form.addRow("Quantity:", self.qty_input)
        form.addRow("Module Type:", type_layout)
        form.addRow("Poles:", self.pole_combo)
        form.addRow("KA Rating:", self.ka_combo)
        form.addRow("Release:", self.release_combo)
        form.addRow("Protection:", self.protection_combo)
        form.addRow("Remark:", self.remark_input)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_lookups(self):
        panels = self.service.get_panels_by_quote(self.quote_id)
        for p in panels: self.panel_combo.addItem(p[4], p[0])
        if self.initial_panel_id is not None:
            idx = self.panel_combo.findData(self.initial_panel_id)
            if idx >= 0: self.panel_combo.setCurrentIndex(idx)
        types = self.service.get_module_costs_lookup()
        for t in types: self.type_combo.addItem(t[1], t[0])
        self.ing_og_combo.addItems(self.dropdown_lists.get("ingog", []))
        self.pole_combo.addItems(self.dropdown_lists.get("pole", []))
        self.ka_combo.addItems(self.dropdown_lists.get("ka", []))
        self.release_combo.addItems(self.dropdown_lists.get("release", []))
        self.protection_combo.addItems(self.dropdown_lists.get("protection", []))

    def _quick_add_type(self):
        dialog = QuickModuleTypeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            name = dialog.get_name()
            if name:
                try:
                    new_id = self.service.create_module_type_quick(name)
                    self.load_lookups()
                    index = self.type_combo.findData(new_id)
                    if index >= 0: self.type_combo.setCurrentIndex(index)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to add module type: {e}")

    def fill_data(self, data):
        idx = self.panel_combo.findData(int(data.get("panel_id") or 0))
        if idx >= 0: self.panel_combo.setCurrentIndex(idx)
        self.ing_og_combo.setCurrentText(data.get("ing_og", ""))
        self.qty_input.setValue(int(data.get("qty") or 1))
        t_idx = self.type_combo.findData(int(data.get("type_id") or 0))
        if t_idx >= 0: self.type_combo.setCurrentIndex(t_idx)
        self.pole_combo.setCurrentText(data.get("pole", ""))
        self.ka_combo.setCurrentText(data.get("ka", ""))
        self.release_combo.setCurrentText(data.get("release", ""))
        self.protection_combo.setCurrentText(data.get("protection", ""))
        self.remark_input.setText(data.get("remark", ""))

    def get_data(self):
        def update_and_get(combo, list_key):
            val = combo.currentText().strip()
            shared_list = self.dropdown_lists.get(list_key, [])
            if val and val not in shared_list: shared_list.append(val)
            return val
        return {
            "panel_id": self.panel_combo.currentData(),
            "ing_og": update_and_get(self.ing_og_combo, "ingog"),
            "qty": self.qty_input.value(),
            "type_id": self.type_combo.currentData(),
            "pole": update_and_get(self.pole_combo, "pole"),
            "ka": update_and_get(self.ka_combo, "ka"),
            "release": update_and_get(self.release_combo, "release"),
            "protection": update_and_get(self.protection_combo, "protection"),
            "remark": self.remark_input.text()
        }