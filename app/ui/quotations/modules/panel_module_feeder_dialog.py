from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QHeaderView, QDialogButtonBox, QMessageBox
)
from app.services.quotation_service import QuotationService

class PanelModuleFeederDialog(QDialog):
    def __init__(self, pm_id, qty=1, parent=None):
        super().__init__(parent)
        self.pm_id = pm_id
        self.qty = qty
        self.service = QuotationService()
        
        self.setWindowTitle(f"Feeder Details (Module ID: {pm_id}, Qty: {qty})")
        self.resize(500, 300)
        
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Feeder ID", "Description"])
        
        # Adjust column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 150)
        
        self.table.setRowCount(self.qty)
        
        layout.addWidget(self.table)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.save_data)
        self.buttons.rejected.connect(self.reject)
        
        layout.addWidget(self.buttons)
        
        self.load_data()
        
    def load_data(self):
        feeder, desc = self.service.get_feeder_details(self.pm_id)
        
        feeders = [f.strip() for f in feeder.split(",")] if feeder else []
        descs = [d.strip() for d in desc.split(",")] if desc else []
        
        for i in range(self.qty):
            f_val = feeders[i] if i < len(feeders) else ""
            d_val = descs[i] if i < len(descs) else ""
            
            f_item = QTableWidgetItem(f_val)
            d_item = QTableWidgetItem(d_val)
            
            self.table.setItem(i, 0, f_item)
            self.table.setItem(i, 1, d_item)
            
    def save_data(self):
        feeders = []
        descs = []
        
        for i in range(self.qty):
            f_item = self.table.item(i, 0)
            d_item = self.table.item(i, 1)
            
            f_val = f_item.text().strip() if f_item else ""
            d_val = d_item.text().strip() if d_item else ""
            
            # Avoid comma issues if possible, but keep simple as requested
            feeders.append(f_val)
            descs.append(d_val)
            
        # Join with comma
        feeder_str = ",".join(feeders)
        desc_str = ",".join(descs)
        
        try:
            self.service.update_feeder_details(self.pm_id, feeder_str, desc_str)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save feeder details:\n{e}")
