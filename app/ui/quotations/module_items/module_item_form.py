from PySide6.QtWidgets import (
 QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
 QSpinBox, QComboBox, QDialogButtonBox, QPushButton, QMessageBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt
from app.services.price_list_service import PriceListService
from app.services.module_service import ModuleService

class ModuleItemForm(QDialog):
    def __init__(self, module_type_id, module_item_data=None, parent=None):
        super().__init__(parent)
        self.module_type_id = module_type_id
        self.module_item_data = module_item_data
        self.pricelist_service = PriceListService()
        self.module_service = ModuleService()
        self._pricelist_data_map = {}
        self._unique_makes = []
        self.setWindowTitle("Edit Module Item" if module_item_data else "Add Module Item")
        self.setMinimumWidth(400)
        self.setup_ui()
        self.load_pricelist_items()
        if module_item_data:
            self.fill_data(module_item_data)

    def setup_ui(self):
        layout = QVBoxLayout(self); form = QFormLayout()
        self.drive_description_combo = QComboBox(); self.drive_description_combo.setEditable(True)
        self.drive_description_combo.setInsertPolicy(QComboBox.NoInsert)
        self.drive_description_combo.lineEdit().setPlaceholderText("Search Drive Description...")
        self.drive_description_combo.currentIndexChanged.connect(self._on_description_selected)
        self.bom_input = QDoubleSpinBox(); self.bom_input.setMinimum(1.0); self.bom_input.setMaximum(99999.0)
        self.make_input = QComboBox(); self.make_input.setEditable(True); self.make_input.setInsertPolicy(QComboBox.NoInsert)
        self.make_input.editTextChanged.connect(self._on_make_changed); self.make_input.lineEdit().setPlaceholderText("Search Make...")
        self.lp_input = QDoubleSpinBox(); self.lp_input.setMinimum(1.0); self.lp_input.setMaximum(9999999.0)
        self.discount_input = QDoubleSpinBox(); self.discount_input.setMinimum(0.0); self.discount_input.setMaximum(100.0)
        self.selection_input = QLineEdit(); self.sequence_input = QSpinBox(); self.sequence_input.setRange(1, 9999)
        form.addRow("Drive Description:", self.drive_description_combo); form.addRow("BOM (Used Qty):", self.bom_input); form.addRow("Make:", self.make_input)
        form.addRow("List Price (LP):", self.lp_input); form.addRow("Discount (%):", self.discount_input)
        form.addRow("Selection (Model):", self.selection_input); form.addRow("Sequence:", self.sequence_input)
        layout.addLayout(form); buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); layout.addWidget(buttons)

    def load_pricelist_items(self):
        self.drive_description_combo.blockSignals(True); self.make_input.blockSignals(True)
        self.drive_description_combo.clear(); self.drive_description_combo.addItem("", None)
        self.make_input.clear(); self.make_input.addItem("", None)
        try:
            items_data, _ = self.pricelist_service.get_all_price_items(); self._pricelist_data_map = {}
            unique_makes = set()
            for row in items_data:
                desc, make = row[1], row[4]
                self.drive_description_combo.addItem(desc, row[0])
                self._pricelist_data_map[desc] = {"item_id": row[0], "model": row[2], "make": row[4], "list_price": row[5], "discount_percent": row[6], "used_qty": row[8]}
                if make: unique_makes.add(make)
            self.make_input.addItems(sorted(list(unique_makes)))
            self._filter_drive_descriptions_by_make()
        except Exception as e: QMessageBox.critical(self, "Database Error", f"Error loading price list items: {e}")
        finally: self.drive_description_combo.blockSignals(False); self.make_input.blockSignals(False)

    def _on_make_changed(self, text): self._filter_drive_descriptions_by_make(text)

    def _filter_drive_descriptions_by_make(self, selected_make_text=""):
        self.drive_description_combo.blockSignals(True); self.drive_description_combo.clear(); self.drive_description_combo.addItem("", None)
        lower_make = selected_make_text.lower().strip()
        for desc, data in self._pricelist_data_map.items():
            if not lower_make or lower_make in str(data.get("make", "")).lower().strip():
                self.drive_description_combo.addItem(desc, data["item_id"])
        self.drive_description_combo.blockSignals(False)

    def _on_description_selected(self):
        selected_desc = self.drive_description_combo.currentText(); data = self._pricelist_data_map.get(selected_desc)
        self.make_input.blockSignals(True)
        if data:
            self.bom_input.setValue(float(data.get("used_qty") or 1.0))
            self.make_input.setCurrentText(str(data.get("make", "")))
            self.lp_input.setValue(float(data.get("list_price") or 1.0))
            self.discount_input.setValue(float(data.get("discount_percent") or 0) * 100.0)
            self.selection_input.setText(data.get("model", ""))
        else:
            self.bom_input.setValue(1.0); self.lp_input.setValue(1.0); self.discount_input.setValue(0.0); self.selection_input.clear()
        self.make_input.blockSignals(False)

    def fill_data(self, data):
        self.drive_description_combo.blockSignals(True); self.make_input.blockSignals(True)
        desc, make = data.get("drive_description", ""), data.get("make", "")
        self.make_input.setCurrentText(make); self._filter_drive_descriptions_by_make(make)
        idx = self.drive_description_combo.findText(desc)
        if idx >= 0: self.drive_description_combo.setCurrentIndex(idx)
        else: self.drive_description_combo.setEditText(desc)

        # Set values from database, which must override any defaults from the PriceList
        bom, lp = data.get("bom"), data.get("lp")
        self.bom_input.setValue(float(bom) if bom is not None else 1.0)
        self.lp_input.setValue(float(lp) if lp is not None else 1.0)
        self.discount_input.setValue(float(data.get("discount") or 0) * 100.0)
        self.selection_input.setText(str(data.get("selection", "")))
        
        self.sequence_input.setValue(int(data.get("sequence_number", 1)))
        self.drive_description_combo.blockSignals(False); self.make_input.blockSignals(False)

    def get_data(self):
        desc = self.drive_description_combo.currentText().strip()
        if not desc: QMessageBox.warning(self, "Validation", "Drive Description is required."); return None
        try: return {"module_type_id": self.module_type_id, "drive_description": desc, "bom": self.bom_input.value(), "lp": self.lp_input.value(), "discount": self.discount_input.value() / 100.0, "selection": self.selection_input.text().strip(), "sequence_number": self.sequence_input.value()}
        except: QMessageBox.warning(self, "Invalid Input", "BOM, List Price, and Discount must be numeric."); return None