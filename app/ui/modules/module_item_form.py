from PySide6.QtWidgets import (
 QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
 QSpinBox, QComboBox, QDialogButtonBox, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from app.services.price_list_service import PriceListService # Assuming this exists
from app.services.module_service import ModuleService # Assuming this exists

class ModuleItemForm(QDialog):
 def __init__(self, module_type_id, module_item_data=None, parent=None):
 super().__init__(parent)
 self.module_type_id = module_type_id
 self.module_item_data = module_item_data
 self.pricelist_service = PriceListService()
 self.module_service = ModuleService() # For potential lookups if needed
 self.setWindowTitle("Edit Module Item" if module_item_data else "Add Module Item")
 self.setMinimumWidth(400)
 self.setup_ui()
 self.load_pricelist_items()
 if module_item_data:
 self.fill_data(module_item_data)

 def setup_ui(self):
 layout = QVBoxLayout(self)
 form = QFormLayout()

 self.drive_description_combo = QComboBox()
 self.drive_description_combo.setEditable(True)
 self.drive_description_combo.currentIndexChanged.connect(self._on_description_selected)

 self.bom_input = QLineEdit()
 self.lp_input = QLineEdit()
 self.discount_input = QLineEdit()
 self.selection_input = QLineEdit()
 self.sequence_input = QSpinBox()
 self.sequence_input.setRange(1, 9999)

 form.addRow("Drive Description:", self.drive_description_combo)
 form.addRow("BOM (Used Qty):", self.bom_input)
 form.addRow("List Price (LP):", self.lp_input)
 form.addRow("Discount (%):", self.discount_input)
 form.addRow("Selection (Model):", self.selection_input)
 form.addRow("Sequence:", self.sequence_input)

 layout.addLayout(form)
 buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
 buttons.accepted.connect(self.accept)
 buttons.rejected.connect(self.reject)
 layout.addWidget(buttons)

 def load_pricelist_items(self):
 self.drive_description_combo.clear()
 self.drive_description_combo.addItem("", None) # Add an empty item
 try:
 # "ID", "Description", "Model", "Category", "Make", "List Price", "Discount %", "Net Price", "Used Qty", "Total Amount", "CategoryID", "MakeID"
 items = self.pricelist_service.get_all_price_items() # Using existing method, assuming it returns all columns
 self._pricelist_data_map = {} # Map description to full data
 for item_id, desc, model, category, make, lp, discount_pct, net_price, used_qty, total_amount, cat_id, make_id in items:
 self.drive_description_combo.addItem(desc, item_id)
 self._pricelist_data_map[desc] = {
 "item_id": item_id,
 "model": model,
 "list_price": lp,
 "discount_percent": discount_pct,
 "used_qty": used_qty,
 "net_price": net_price,
 "total_amount": total_amount
 }
 except Exception as e:
 QMessageBox.critical(self, "Database Error", f"Error loading price list items: {e}")

 def _on_description_selected(self):
 selected_desc = self.drive_description_combo.currentText()
 data = self._pricelist_data_map.get(selected_desc)
 if data:
 self.bom_input.setText(str(data.get("used_qty", "")))
 self.lp_input.setText(str(data.get("list_price", "")))
 # Convert discount from fraction to percentage for display
 discount_pct_val = data.get("discount_percent", 0)
 self.discount_input.setText(f"{discount_pct_val * 100:.2f}")
 self.selection_input.setText(data.get("model", ""))
 else:
 # Clear fields if no matching item or empty selection
 self.bom_input.clear()
 self.lp_input.clear()
 self.discount_input.clear()
 self.selection_input.clear()

 def fill_data(self, data):
 # For editing, data comes from tbl_ModuleItems
 # data will be (module_item_id, drive_description, bom, lp, discount, selection, sequence_number)
 desc = data.get("drive_description", "")
 idx = self.drive_description_combo.findText(desc)
 if idx >= 0:
 self.drive_description_combo.setCurrentIndex(idx)
 else:
 # If description not in dropdown, add it (editable combo box)
 self.drive_description_combo.setEditText(desc)
 self._on_description_selected() # Try to populate if it matches an existing item

 self.bom_input.setText(str(data.get("bom", "")))
 self.lp_input.setText(str(data.get("lp", "")))
 # Discount from DB is likely a fraction, convert to percentage for display
 db_discount = data.get("discount", 0)
 self.discount_input.setText(f"{float(db_discount) * 100:.2f}")
 self.selection_input.setText(str(data.get("selection", "")))
 self.sequence_input.setValue(int(data.get("sequence_number", 1)))

 def get_data(self):
 # Convert discount percentage back to fraction for saving
 try:
 discount_pct_str = self.discount_input.text().strip()
 discount_val = float(discount_pct_str) / 100.0 if discount_pct_str else 0.0
 except ValueError:
 QMessageBox.warning(self, "Invalid Input", "Discount must be a valid number.")
 return None

 return {
 "module_type_id": self.module_type_id,
 "drive_description": self.drive_description_combo.currentText().strip(),
 "bom": float(self.bom_input.text()) if self.bom_input.text().strip() else None,
 "lp": float(self.lp_input.text()) if self.lp_input.text().strip() else None,
 "discount": discount_val,
 "selection": self.selection_input.text().strip(),
 "sequence_number": self.sequence_input.value()
 }