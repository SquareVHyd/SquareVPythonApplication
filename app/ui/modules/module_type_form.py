from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QComboBox, QDialogButtonBox, QMessageBox
)

class ModuleTypeForm(QDialog):
    def __init__(self, parent=None, makes=None, swgs=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Module Type Editor")
        self.setMinimumWidth(400)
        
        self.makes = makes or []
        self.swgs = swgs or []
        self.initial_data = initial_data
        
        self.setup_ui()
        
        if initial_data:
            self.name_input.setText(initial_data.get("ModuleType", ""))
            self._select_combo_data(self.make_combo, initial_data.get("ModuleMakeID"))
            self._select_combo_data(self.swg_combo, initial_data.get("ModSwgID"))

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Module Type Name:"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)
        
        layout.addWidget(QLabel("Module Make:"))
        self.make_combo = QComboBox()
        for mid, mname in self.makes:
            self.make_combo.addItem(mname, mid)
        layout.addWidget(self.make_combo)
        
        layout.addWidget(QLabel("SWG:"))
        self.swg_combo = QComboBox()
        for sid, sname in self.swgs:
            self.swg_combo.addItem(sname, sid)
        layout.addWidget(self.swg_combo)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def _select_combo_data(self, combo, data):
        index = combo.findData(data)
        if index >= 0:
            combo.setCurrentIndex(index)

    def get_data(self):
        return {
            "ModuleType": self.name_input.text().strip(),
            "ModuleMakeID": self.make_combo.currentData(),
            "ModSwgID": self.swg_combo.currentData()
        }

    def validate(self):
        data = self.get_data()
        if not data["ModuleType"]:
            QMessageBox.warning(self, "Validation", "Module Type Name is required.")
            return False
        if data["ModuleMakeID"] is None or data["ModSwgID"] is None:
            QMessageBox.warning(self, "Validation", "Please select Make and SWG.")
            return False
        return True

    def accept(self):
        if self.validate():
            super().accept()