from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView, QCheckBox
)
from PySide6.QtCore import Qt
from app.services.po_customer_service import POCustomerService

class SelectQuoteItemsDialog(QDialog):
    def __init__(self, quote_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Items from Quote Used Quantity")
        self.resize(900, 500)
        self.quote_id = quote_id
        self.service = POCustomerService()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Select", "Description", "Used Qty", "Unit Price", "Order Qty", "Warranty"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Selected")
        self.add_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)

    def load_data(self):
        items = self.service.get_quote_used_items(self.quote_id)
        self.table.setRowCount(len(items))
        
        for r, item in enumerate(items):
            # Checkbox
            chk = QCheckBox()
            chk.setStyleSheet("margin-left: 10px;")
            self.table.setCellWidget(r, 0, chk)
            
            # Read-only data
            desc_item = QTableWidgetItem(item["Description"])
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 1, desc_item)
            
            qty_item = QTableWidgetItem(str(item["TotalQty"]))
            qty_item.setFlags(qty_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 2, qty_item)
            
            # Editable inputs for Order
            price_val = item["UnitPrice"] if item["UnitPrice"] is not None else 0.0
            price_input = QTableWidgetItem(str(price_val))
            self.table.setItem(r, 3, price_input)
            
            order_qty_input = QTableWidgetItem(str(item["TotalQty"]))
            self.table.setItem(r, 4, order_qty_input)
            
            warranty_input = QTableWidgetItem("1.0") # Default 1 year
            self.table.setItem(r, 5, warranty_input)

    def get_selected_items(self):
        selected = []
        for r in range(self.table.rowCount()):
            chk = self.table.cellWidget(r, 0)
            if chk.isChecked():
                desc = self.table.item(r, 1).text()
                price = float(self.table.item(r, 3).text() or 0)
                qty = float(self.table.item(r, 4).text() or 0)
                warranty = float(self.table.item(r, 5).text() or 0)
                selected.append({
                    "Description": desc,
                    "Price": price,
                    "Qty": qty,
                    "Warranty": warranty
                })
        return selected
