from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QComboBox, QDateEdit, QFrame,
    QAbstractItemView
)
from PySide6.QtCore import Qt, QDate
from app.services.po_process_service import POProcessService

class MinutesOfMeetingPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = POProcessService()
        self.current_mom_id = None
        self.current_quote_id = None
        self.po_data = [] # Stores PO list for dropdown logic
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Title
        title = QLabel("Minutes of Meeting (MOM)")
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
            QLineEdit, QComboBox, QDateEdit {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                selection-background-color: #93c5fd;
            }
        """)
        form_layout = QGridLayout(form_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)

        # PO Selection
        form_layout.addWidget(QLabel("Select PO:"), 0, 0)
        self.po_combo = QComboBox()
        self.po_combo.currentIndexChanged.connect(self.on_po_changed)
        form_layout.addWidget(self.po_combo, 0, 1)

        # PO Date Info
        form_layout.addWidget(QLabel("PO Date:"), 0, 2)
        self.po_date_info = QLineEdit()
        self.po_date_info.setReadOnly(True)
        self.po_date_info.setStyleSheet("background-color: #e2e8f0; color: #1e293b; font-weight: bold;")
        form_layout.addWidget(self.po_date_info, 0, 3)

        # Read-only Customer Info
        form_layout.addWidget(QLabel("Customer Name:"), 1, 0)
        self.customer_info = QLineEdit()
        self.customer_info.setReadOnly(True)
        self.customer_info.setStyleSheet("background-color: #e2e8f0; color: #1e293b; font-weight: bold;")
        form_layout.addWidget(self.customer_info, 1, 1)

        # Date Dispatch
        form_layout.addWidget(QLabel("Date Dispatch:"), 1, 2)
        self.date_dispatch = QDateEdit(QDate.currentDate())
        self.date_dispatch.setCalendarPopup(True)
        self.date_dispatch.setDisplayFormat("yyyy-MM-dd")
        form_layout.addWidget(self.date_dispatch, 1, 3)

        # Panel Name Dropdown
        form_layout.addWidget(QLabel("Panel Name:"), 2, 0)
        self.panel_combo = QComboBox()
        self.panel_combo.setEditable(True) # Allow custom typing if needed, but defaults to fetched lists
        form_layout.addWidget(self.panel_combo, 2, 1)

        # Customer Representative
        form_layout.addWidget(QLabel("Customer Rep:"), 2, 2)
        self.cust_rep_entry = QLineEdit()
        form_layout.addWidget(self.cust_rep_entry, 2, 3)

        # SQV Representative
        form_layout.addWidget(QLabel("SQV Rep:"), 3, 0)
        self.sqv_rep_entry = QLineEdit()
        form_layout.addWidget(self.sqv_rep_entry, 3, 1)

        # Remarks
        form_layout.addWidget(QLabel("Remarks:"), 3, 2)
        self.remarks_entry = QLineEdit()
        form_layout.addWidget(self.remarks_entry, 3, 3)

        # General Remark
        form_layout.addWidget(QLabel("General Remark:"), 4, 0)
        self.general_remark_entry = QLineEdit()
        form_layout.addWidget(self.general_remark_entry, 4, 1, 1, 3)

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

        self.add_btn = QPushButton("➕ Add MOM")
        self.add_btn.setStyleSheet(btn_style)
        self.add_btn.clicked.connect(self.add_mom)

        self.update_btn = QPushButton("✏️ Update MOM")
        self.update_btn.setStyleSheet(btn_style)
        self.update_btn.clicked.connect(self.update_mom)
        self.update_btn.setEnabled(False)

        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setStyleSheet(delete_btn_style)
        self.delete_btn.clicked.connect(self.delete_mom)
        self.delete_btn.setEnabled(False)

        self.clear_btn = QPushButton("🧹 Clear Form")
        self.clear_btn.setStyleSheet(clear_btn_style)
        self.clear_btn.clicked.connect(self.clear_form)

        btn_layout.addStretch()
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.update_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.clear_btn)
        
        form_layout.addLayout(btn_layout, 5, 0, 1, 4)
        
        layout.addWidget(form_frame)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "ID", "PO No", "PO Date", "Customer", 
            "Customer Rep", "SQV Rep", "Panel Name", 
            "Remarks", "General Remark", "Date Dispatch", "PO_ID"
        ])
        
        # Interactive Headers
        for i in range(11):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionsMovable(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Force form usage
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

        layout.addWidget(self.table)

    def load_quotation(self, quote_id):
        """Loads POs into dropdown and fetches all MOM records for the given quote."""
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
        """When PO changes, auto-fill Customer Info and fetch Panel Names."""
        idx = self.po_combo.currentIndex()
        if idx <= 0:
            self.customer_info.clear()
            self.po_date_info.clear()
            self.panel_combo.clear()
            return
            
        po_id = self.po_combo.currentData()
        # Find customer name and po date
        for po in self.po_data:
            if po['ID'] == po_id:
                self.customer_info.setText(po['CustomerName'])
                self.po_date_info.setText(str(po['PO_Date']))
                break
                
        # Fetch panels
        panels = self.service.get_panels_for_po(po_id)
        self.panel_combo.clear()
        if panels:
            self.panel_combo.addItems(panels)

    def load_table_data(self):
        """Loads MOM data into the table."""
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        
        if not self.current_quote_id:
            self.table.blockSignals(False)
            return
            
        moms = self.service.get_all_moms(self.current_quote_id)
        self.table.setRowCount(len(moms))
        
        for row, mom in enumerate(moms):
            cols = [
                str(mom.get("ID", "")),
                str(mom.get("PO_No", "")),
                str(mom.get("PO_Date", "")),
                str(mom.get("Customer_Name", "")),
                str(mom.get("Customer_Representative", "")),
                str(mom.get("SQV_Representatives", "")),
                str(mom.get("Panel_Name", "")),
                str(mom.get("Remarks", "")),
                str(mom.get("General_Remark", "")),
                str(mom.get("Date_Dispatch", "")),
                str(mom.get("PO_ID", ""))
            ]
            for col, text in enumerate(cols):
                item = QTableWidgetItem(text)
                if col == 0:
                    item.setData(Qt.UserRole, mom.get("ID"))
                self.table.setItem(row, col, item)
                
        self.table.hideColumn(10) # Hide PO_ID, only needed for reference
        self.table.blockSignals(False)

    def on_table_selection(self):
        """Populates form when a table row is selected."""
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            self.clear_form(clear_table_selection=False)
            return
            
        row = selected[0].row()
        
        # Get data
        self.current_mom_id = self.table.item(row, 0).data(Qt.UserRole)
        po_id = int(self.table.item(row, 10).text()) if self.table.item(row, 10).text() else None
        
        # Find index of PO in combo
        po_idx = 0
        for i in range(self.po_combo.count()):
            if self.po_combo.itemData(i) == po_id:
                po_idx = i
                break
        self.po_combo.setCurrentIndex(po_idx)
        
        # We need to manually set panel name in combo since it might not be in the list 
        # or the combo just refreshed from PO change.
        panel_name = self.table.item(row, 6).text()
        if self.panel_combo.findText(panel_name) == -1:
            self.panel_combo.addItem(panel_name)
        self.panel_combo.setCurrentText(panel_name)
        
        self.cust_rep_entry.setText(self.table.item(row, 4).text())
        self.sqv_rep_entry.setText(self.table.item(row, 5).text())
        self.remarks_entry.setText(self.table.item(row, 7).text())
        self.general_remark_entry.setText(self.table.item(row, 8).text())
        
        date_str = self.table.item(row, 9).text()
        if date_str and date_str != "None":
            self.date_dispatch.setDate(QDate.fromString(date_str, "yyyy-MM-dd"))
            
        self.add_btn.setEnabled(False)
        self.update_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

    def get_form_data(self):
        po_id = self.po_combo.currentData()
        if not po_id:
            QMessageBox.warning(self, "Validation Error", "Please select a PO.")
            return None
            
        cust_rep = self.cust_rep_entry.text().strip()
        sqv_rep = self.sqv_rep_entry.text().strip()
        
        if not cust_rep:
            QMessageBox.warning(self, "Validation Error", "Customer Representative is mandatory.")
            return None
            
        if not sqv_rep:
            QMessageBox.warning(self, "Validation Error", "SQV Representative is mandatory.")
            return None
            
        return {
            "po_id": po_id,
            "date_dispatch": self.date_dispatch.date().toString("yyyy-MM-dd"),
            "cust_rep": self.cust_rep_entry.text().strip(),
            "sqv_rep": self.sqv_rep_entry.text().strip(),
            "panel_name": self.panel_combo.currentText().strip(),
            "remarks": self.remarks_entry.text().strip(),
            "gen_remark": self.general_remark_entry.text().strip()
        }

    def add_mom(self):
        data = self.get_form_data()
        if not data: return
        
        if self.service.create_mom(data):
            QMessageBox.information(self, "Success", "Minutes of Meeting added successfully.")
            self.load_table_data()
            self.clear_form()
        else:
            QMessageBox.critical(self, "Error", "Failed to add Minutes of Meeting.")

    def update_mom(self):
        if not self.current_mom_id: return
        data = self.get_form_data()
        if not data: return
        
        if self.service.update_mom(self.current_mom_id, data):
            QMessageBox.information(self, "Success", "Minutes of Meeting updated successfully.")
            self.load_table_data()
            self.clear_form()
        else:
            QMessageBox.critical(self, "Error", "Failed to update Minutes of Meeting.")

    def delete_mom(self):
        if not self.current_mom_id: return
        
        reply = QMessageBox.question(self, 'Confirm Delete', 
                                     'Are you sure you want to delete this Minutes of Meeting record?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.service.delete_mom(self.current_mom_id):
                QMessageBox.information(self, "Success", "Record deleted successfully.")
                self.load_table_data()
                self.clear_form()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete record.")

    def clear_form(self, clear_table_selection=True):
        self.current_mom_id = None
        self.po_combo.setCurrentIndex(0)
        self.customer_info.clear()
        self.po_date_info.clear()
        self.panel_combo.clear()
        self.cust_rep_entry.clear()
        self.sqv_rep_entry.clear()
        self.remarks_entry.clear()
        self.general_remark_entry.clear()
        self.date_dispatch.setDate(QDate.currentDate())
        
        self.add_btn.setEnabled(True)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        
        if clear_table_selection:
            self.table.clearSelection()
