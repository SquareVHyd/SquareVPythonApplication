from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QComboBox, QDateEdit, QFrame,
    QAbstractItemView, QCheckBox, QDoubleSpinBox
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QDate
from app.services.po_process_service import POProcessService

class ComplaintsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = POProcessService()
        self.current_complaint_id = None
        self.current_quote_id = None
        self.po_data = [] # Stores PO list for dropdown logic
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Title
        title = QLabel("Complaints Management")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f172a;")
        layout.addWidget(title)

        # Form Frame
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            QLabel { border: none; font-weight: bold; color: #475569; }
            QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                selection-background-color: #93c5fd;
            }
            QCheckBox { border: none; font-weight: bold; color: #475569; }
        """)
        form_layout = QGridLayout(form_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)

        # Row 0
        form_layout.addWidget(QLabel("Select PO:"), 0, 0)
        self.po_combo = QComboBox()
        self.po_combo.currentIndexChanged.connect(self.on_po_changed)
        form_layout.addWidget(self.po_combo, 0, 1)

        form_layout.addWidget(QLabel("Complaint Date:"), 0, 2)
        self.complaint_date = QDateEdit(QDate.currentDate())
        self.complaint_date.setCalendarPopup(True)
        self.complaint_date.setDisplayFormat("yyyy-MM-dd")
        form_layout.addWidget(self.complaint_date, 0, 3)

        # Row 1
        form_layout.addWidget(QLabel("Customer Name:"), 1, 0)
        self.customer_info = QLineEdit()
        self.customer_info.setReadOnly(True)
        self.customer_info.setStyleSheet("background-color: #e2e8f0; color: #1e293b; font-weight: bold;")
        form_layout.addWidget(self.customer_info, 1, 1)

        form_layout.addWidget(QLabel("Panel Name:"), 1, 2)
        self.panel_combo = QComboBox()
        self.panel_combo.setEditable(True)
        form_layout.addWidget(self.panel_combo, 1, 3)

        # Row 2
        form_layout.addWidget(QLabel("Site:"), 2, 0)
        self.site_entry = QLineEdit()
        form_layout.addWidget(self.site_entry, 2, 1)

        form_layout.addWidget(QLabel("Complaint Type:"), 2, 2)
        self.complaint_type_entry = QLineEdit()
        form_layout.addWidget(self.complaint_type_entry, 2, 3)

        # Row 3
        form_layout.addWidget(QLabel("Description:"), 3, 0)
        self.description_entry = QLineEdit()
        form_layout.addWidget(self.description_entry, 3, 1, 1, 3)

        # Row 4
        form_layout.addWidget(QLabel("Attended By:"), 4, 0)
        self.attended_by_entry = QLineEdit()
        form_layout.addWidget(self.attended_by_entry, 4, 1)

        form_layout.addWidget(QLabel("Feedback:"), 4, 2)
        self.feedback_entry = QLineEdit()
        form_layout.addWidget(self.feedback_entry, 4, 3)

        # Row 5
        form_layout.addWidget(QLabel("Warranty:"), 5, 0)
        self.warranty_entry = QLineEdit()
        form_layout.addWidget(self.warranty_entry, 5, 1)

        form_layout.addWidget(QLabel("Charged Amount:"), 5, 2)
        self.charged_amount_entry = QLineEdit()
        form_layout.addWidget(self.charged_amount_entry, 5, 3)
        
        form_layout.addWidget(QLabel("Status:"), 5, 4)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["pending", "task completed"])
        self.status_combo.setItemData(0, QColor("#ffffcc"), Qt.BackgroundRole)
        self.status_combo.setItemData(1, QColor("#ccffcc"), Qt.BackgroundRole)
        self.status_combo.currentIndexChanged.connect(self.update_status_color)
        form_layout.addWidget(self.status_combo, 5, 5)

        # Buttons Layout
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 10, 0, 0)
        
        btn_style = """
            QPushButton {
                background-color: #0d6efd;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover { background-color: #0b5ed7; }
        """
        delete_btn_style = btn_style.replace("#0d6efd", "#ef4444").replace("#0b5ed7", "#dc2626")
        clear_btn_style = btn_style.replace("#0d6efd", "#64748b").replace("#0b5ed7", "#475569")

        self.add_btn = QPushButton("➕ Add Complaint")
        self.add_btn.setStyleSheet(btn_style)
        self.add_btn.clicked.connect(self.add_complaint)

        self.update_btn = QPushButton("✏️ Update")
        self.update_btn.setStyleSheet(btn_style)
        self.update_btn.clicked.connect(self.update_complaint)
        self.update_btn.setEnabled(False)

        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setStyleSheet(delete_btn_style)
        self.delete_btn.clicked.connect(self.delete_complaint)
        self.delete_btn.setEnabled(False)

        self.clear_btn = QPushButton("🧹 Clear Form")
        self.clear_btn.setStyleSheet(clear_btn_style)
        self.clear_btn.clicked.connect(self.clear_form)

        btn_layout.addStretch()
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.update_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.clear_btn)
        
        form_layout.addLayout(btn_layout, 6, 0, 1, 6)
        
        layout.addWidget(form_frame)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            "ID", "PO No", "Complaint Date", "Customer", 
            "Panel Name", "Site", "Type", "Description", 
            "Warranty", "Attended By", "Feedback", "Charged", "Status"
        ])
        
        # Interactive Headers
        for i in range(13):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionsMovable(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(True)
        
        self.table.itemSelectionChanged.connect(self.on_table_selection)
        
        self.table.setStyleSheet("""
            QTableView { 
                selection-background-color: #93c5fd; 
                selection-color: #000000; 
                background-color: white;
                border: 1px solid #e2e8f0;
            } 
            QHeaderView::section { 
                background-color: #fce4ec; 
                border: 1px solid #e2e8f0; 
                font-weight: bold; 
                padding: 4px;
            }
        """)

        self.update_status_color()
        layout.addWidget(self.table)

    def update_status_color(self):
        text = self.status_combo.currentText().lower()
        if text == "pending":
            self.status_combo.setStyleSheet("QComboBox { background-color: #ffffcc; border: 1px solid #cbd5e1; border-radius: 4px; padding: 6px; selection-background-color: #93c5fd; }")
        elif text == "task completed":
            self.status_combo.setStyleSheet("QComboBox { background-color: #ccffcc; border: 1px solid #cbd5e1; border-radius: 4px; padding: 6px; selection-background-color: #93c5fd; }")
        else:
            self.status_combo.setStyleSheet("QComboBox { background-color: white; border: 1px solid #cbd5e1; border-radius: 4px; padding: 6px; selection-background-color: #93c5fd; }")

    def load_quotation(self, quote_id):
        self.current_quote_id = quote_id
        
        # Load POs related to this quote
        self.po_combo.blockSignals(True)
        self.po_combo.clear()
        self.po_data = self.service.get_pos_for_quotation(quote_id)
        
        self.po_combo.addItem("-- Select PO --", None)
        for po in self.po_data:
            display_text = f"PO: {po['PO_No']} | {po['PO_Date']} | {po['CustomerName']}"
            self.po_combo.addItem(display_text, po['ID'])
            
        self.po_combo.blockSignals(False)
        self.load_table_data()

    def on_po_changed(self):
        idx = self.po_combo.currentIndex()
        if idx <= 0:
            self.customer_info.clear()
            self.panel_combo.clear()
            return
            
        po_id = self.po_combo.currentData()
        for po in self.po_data:
            if po['ID'] == po_id:
                self.customer_info.setText(po['CustomerName'])
                break
                
        panels = self.service.get_panels_for_po(po_id)
        self.panel_combo.clear()
        if panels:
            self.panel_combo.addItems(panels)

    def load_table_data(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        
        if not self.current_quote_id:
            self.table.blockSignals(False)
            return
            
        complaints = self.service.get_all_complaints(self.current_quote_id)
        self.table.setRowCount(len(complaints))
        
        for row, comp in enumerate(complaints):
            cols = [
                str(comp.get("ID", "")),
                str(comp.get("PO_No", "")),
                str(comp.get("Complaint_Date", "")),
                str(comp.get("Customer_Name", "")),
                str(comp.get("Panel_Name", "")),
                str(comp.get("Site", "")),
                str(comp.get("Complaint_Type", "")),
                str(comp.get("Complaint_Description", "")),
                str(comp.get("Warranty", "")),
                str(comp.get("Attended_By", "")),
                str(comp.get("Feedback", "")),
                str(comp.get("Charged_Amount", "0.00")),
                str(comp.get("status", "pending")),
                str(comp.get("PO_ID", ""))
            ]
            
            # The column count is 13, but we pass 14 elements including hidden PO_ID
            for col in range(13):
                item = QTableWidgetItem(cols[col])
                if col == 0:
                    item.setData(Qt.UserRole, comp.get("ID"))
                    item.setData(Qt.UserRole + 1, comp.get("PO_ID"))
                
                # Apply colors for Status column (index 12)
                if col == 12:
                    status_val = cols[col].lower()
                    if status_val == "pending":
                        item.setBackground(QColor("#ffffcc")) # Light Yellow
                    elif status_val == "task completed":
                        item.setBackground(QColor("#ccffcc")) # Light Green

                self.table.setItem(row, col, item)
                
        self.table.blockSignals(False)

    def on_table_selection(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            self.clear_form(clear_table_selection=False)
            return
            
        row = selected[0].row()
        
        self.current_complaint_id = self.table.item(row, 0).data(Qt.UserRole)
        po_id = self.table.item(row, 0).data(Qt.UserRole + 1)
        
        po_idx = 0
        for i in range(self.po_combo.count()):
            if self.po_combo.itemData(i) == po_id:
                po_idx = i
                break
        self.po_combo.setCurrentIndex(po_idx)
        
        date_str = self.table.item(row, 2).text()
        if date_str and date_str != "None":
            self.complaint_date.setDate(QDate.fromString(date_str, "yyyy-MM-dd"))
            
        self.customer_info.setText(self.table.item(row, 3).text())
        
        panel_name = self.table.item(row, 4).text()
        if self.panel_combo.findText(panel_name) == -1:
            self.panel_combo.addItem(panel_name)
        self.panel_combo.setCurrentText(panel_name)
        
        self.site_entry.setText(self.table.item(row, 5).text())
        self.complaint_type_entry.setText(self.table.item(row, 6).text())
        self.description_entry.setText(self.table.item(row, 7).text())
        self.warranty_entry.setText(self.table.item(row, 8).text())
        self.attended_by_entry.setText(self.table.item(row, 9).text())
        self.feedback_entry.setText(self.table.item(row, 10).text())
        
        charged_amount = self.table.item(row, 11).text()
        if charged_amount and charged_amount != "None":
            self.charged_amount_entry.setText(charged_amount)
        else:
            self.charged_amount_entry.clear()
            
        status = self.table.item(row, 12).text()
        idx = self.status_combo.findText(status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
        
        self.add_btn.setEnabled(False)
        self.update_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

    def get_form_data(self):
        po_id = self.po_combo.currentData()
        if not po_id:
            QMessageBox.warning(self, "Validation Error", "Please select a PO.")
            return None
            
        charged_str = self.charged_amount_entry.text().strip()
        try:
            charged_amount = float(charged_str) if charged_str else 0.0
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Charged amount must be a valid number.")
            return None

        return {
            "po_id": po_id,
            "comp_date": self.complaint_date.date().toString("yyyy-MM-dd"),
            "panel_name": self.panel_combo.currentText().strip(),
            "site": self.site_entry.text().strip(),
            "cust_name": self.customer_info.text().strip(),
            "comp_type": self.complaint_type_entry.text().strip(),
            "comp_desc": self.description_entry.text().strip(),
            "warranty": self.warranty_entry.text().strip(),
            "attended_by": self.attended_by_entry.text().strip(),
            "feedback": self.feedback_entry.text().strip(),
            "charged_amount": charged_amount,
            "status": self.status_combo.currentText()
        }

    def add_complaint(self):
        data = self.get_form_data()
        if not data: return
        
        if self.service.create_complaint(data):
            QMessageBox.information(self, "Success", "Complaint added successfully.")
            self.load_table_data()
            self.clear_form()
        else:
            QMessageBox.critical(self, "Error", "Failed to add Complaint.")

    def update_complaint(self):
        if not self.current_complaint_id: return
        data = self.get_form_data()
        if not data: return
        
        if self.service.update_complaint(self.current_complaint_id, data):
            QMessageBox.information(self, "Success", "Complaint updated successfully.")
            self.load_table_data()
            self.clear_form()
        else:
            QMessageBox.critical(self, "Error", "Failed to update Complaint.")

    def delete_complaint(self):
        if not self.current_complaint_id: return
        
        reply = QMessageBox.question(self, 'Confirm Delete', 
                                     'Are you sure you want to delete this Complaint record?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.service.delete_complaint(self.current_complaint_id):
                QMessageBox.information(self, "Success", "Record deleted successfully.")
                self.load_table_data()
                self.clear_form()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete record.")

    def clear_form(self, clear_table_selection=True):
        self.current_complaint_id = None
        self.po_combo.setCurrentIndex(0)
        self.customer_info.clear()
        self.panel_combo.clear()
        self.complaint_date.setDate(QDate.currentDate())
        self.site_entry.clear()
        self.complaint_type_entry.clear()
        self.description_entry.clear()
        self.warranty_entry.clear()
        self.attended_by_entry.clear()
        self.feedback_entry.clear()
        self.charged_amount_entry.clear()
        self.status_combo.setCurrentIndex(0)
        
        self.add_btn.setEnabled(True)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        
        if clear_table_selection:
            self.table.clearSelection()
