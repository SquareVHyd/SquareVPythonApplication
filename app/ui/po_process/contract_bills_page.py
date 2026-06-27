from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QComboBox, QDateEdit, QFrame,
    QAbstractItemView
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QDoubleValidator
from app.services.po_process_service import POProcessService

class ContractBillsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = POProcessService()
        self.current_bill_no = None
        self.current_quote_id = None
        self.po_data = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        title = QLabel("Contract Bills")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f172a;")
        layout.addWidget(title)

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

        # Row 0
        form_layout.addWidget(QLabel("Project Name:"), 0, 0)
        self.project_name_combo = QComboBox()
        self.project_name_combo.setEditable(True)
        form_layout.addWidget(self.project_name_combo, 0, 1)

        form_layout.addWidget(QLabel("Bill Date:"), 0, 2)
        self.bill_date_edit = QDateEdit(QDate.currentDate())
        self.bill_date_edit.setCalendarPopup(True)
        self.bill_date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addWidget(self.bill_date_edit, 0, 3)

        # Row 1
        form_layout.addWidget(QLabel("Contractor Name:"), 1, 0)
        self.contractor_name_entry = QLineEdit()
        form_layout.addWidget(self.contractor_name_entry, 1, 1)

        form_layout.addWidget(QLabel("Type Of Job:"), 1, 2)
        self.job_type_entry = QLineEdit()
        form_layout.addWidget(self.job_type_entry, 1, 3)

        # Row 2
        form_layout.addWidget(QLabel("Amount:"), 2, 0)
        self.amount_entry = QLineEdit()
        validator = QDoubleValidator()
        validator.setBottom(0.0)
        validator.setDecimals(2)
        self.amount_entry.setValidator(validator)
        form_layout.addWidget(self.amount_entry, 2, 1)

        # Row 3
        form_layout.addWidget(QLabel("PO No:"), 3, 0)
        self.po_no_combo = QComboBox()
        form_layout.addWidget(self.po_no_combo, 3, 1)

        # Buttons
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

        self.add_btn = QPushButton("➕ Add Bill")
        self.add_btn.setStyleSheet(btn_style)
        self.add_btn.clicked.connect(self.add_bill)

        self.update_btn = QPushButton("✏️ Update Bill")
        self.update_btn.setStyleSheet(btn_style)
        self.update_btn.clicked.connect(self.update_bill)
        self.update_btn.setEnabled(False)

        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setStyleSheet(delete_btn_style)
        self.delete_btn.clicked.connect(self.delete_bill)
        self.delete_btn.setEnabled(False)

        self.clear_btn = QPushButton("🧹 Clear Form")
        self.clear_btn.setStyleSheet(clear_btn_style)
        self.clear_btn.clicked.connect(self.clear_form)

        btn_layout.addStretch()
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.update_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.clear_btn)
        
        form_layout.addLayout(btn_layout, 4, 0, 1, 4)
        layout.addWidget(form_frame)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Bill No", "Bill Date", "Contractor", "Type of Job", "Amount", "Project Name", "PO No"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget { background-color: white; border: 1px solid #e2e8f0; border-radius: 4px; }
            QHeaderView::section { background-color: #fce4ec; border: 1px solid #e2e8f0; padding: 4px; font-weight: bold; }
        """)
        self.table.itemSelectionChanged.connect(self.on_table_selection)
        layout.addWidget(self.table)

    def load_quotation(self, quote_id, quote_project_name=None):
        self.current_quote_id = quote_id
        
        self.po_no_combo.blockSignals(True)
        self.po_no_combo.clear()
        self.po_data = self.service.get_pos_for_quotation(quote_id)
        
        self.po_no_combo.addItem("-- Select PO --", None)
        for po in self.po_data:
            self.po_no_combo.addItem(f"PO: {po['PO_No']}", po['ID'])
            
        self.po_no_combo.blockSignals(False)
        
        if quote_project_name:
            if self.project_name_combo.findText(quote_project_name) == -1:
                self.project_name_combo.addItem(quote_project_name)
            self.project_name_combo.setCurrentText(quote_project_name)
            
        self.load_data()

    def load_data(self):
        self.table.setRowCount(0)
        bills = self.service.get_all_contract_bills()
        
        valid_po_ids = {po['ID'] for po in self.po_data}
        filtered_bills = [b for b in bills if b.get("PO_ID") in valid_po_ids]
        
        for i, bill in enumerate(filtered_bills):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(str(bill.get("Bill_No", ""))))
            self.table.setItem(i, 1, QTableWidgetItem(str(bill.get("Bill_Date", ""))))
            self.table.setItem(i, 2, QTableWidgetItem(bill.get("Contractor_Name", "")))
            self.table.setItem(i, 3, QTableWidgetItem(bill.get("Type_Of_Job", "")))
            self.table.setItem(i, 4, QTableWidgetItem(str(bill.get("Amount", ""))))
            self.table.setItem(i, 5, QTableWidgetItem(bill.get("Project_Name", "")))
            
            po_no_item = QTableWidgetItem(str(bill.get("PO_No", "")) if bill.get("PO_No") is not None else "")
            po_no_item.setData(Qt.UserRole, bill.get("PO_ID"))
            self.table.setItem(i, 6, po_no_item)

    def clear_form(self):
        self.current_bill_no = None
        self.bill_date_edit.setDate(QDate.currentDate())
        self.contractor_name_entry.clear()
        self.job_type_entry.clear()
        self.amount_entry.clear()
        self.po_no_combo.setCurrentIndex(0)
        
        self.add_btn.setEnabled(True)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.table.clearSelection()

    def on_table_selection(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return
            
        row = selected[0].row()
        self.current_bill_no = int(self.table.item(row, 0).text())
        
        date_str = self.table.item(row, 1).text()
        self.bill_date_edit.setDate(QDate.fromString(date_str, "yyyy-MM-dd") if date_str else QDate.currentDate())
        
        self.contractor_name_entry.setText(self.table.item(row, 2).text())
        self.job_type_entry.setText(self.table.item(row, 3).text())
        self.amount_entry.setText(self.table.item(row, 4).text())
        
        project_name = self.table.item(row, 5).text()
        if self.project_name_combo.findText(project_name) == -1:
            self.project_name_combo.addItem(project_name)
        self.project_name_combo.setCurrentText(project_name)
        
        po_id = self.table.item(row, 6).data(Qt.UserRole)
        idx = 0
        for i in range(self.po_no_combo.count()):
            if self.po_no_combo.itemData(i) == po_id:
                idx = i
                break
        self.po_no_combo.setCurrentIndex(idx)
        
        self.add_btn.setEnabled(False)
        self.update_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

    def get_form_data(self):
        project_name = self.project_name_combo.currentText().strip()
        contractor = self.contractor_name_entry.text().strip()
        job_type = self.job_type_entry.text().strip()
        amount_text = self.amount_entry.text().strip()
        
        po_id = self.po_no_combo.currentData()
        if not po_id:
            QMessageBox.warning(self, "Validation Error", "Please select a PO.")
            return None
            
        po_no_text = self.po_no_combo.currentText().replace("PO: ", "").strip()
        po_no = None
        if po_no_text and po_no_text != "-- Select PO --":
            try:
                po_no = int(po_no_text)
            except ValueError:
                pass
        
        if not all([project_name, contractor, job_type, amount_text]):
            QMessageBox.warning(self, "Validation Error", "All fields are required.")
            return None
            
        try:
            amount = float(amount_text)
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Amount must be a valid number.")
            return None
            
        return {
            "bill_date": self.bill_date_edit.date().toPython(),
            "contractor": contractor,
            "job_type": job_type,
            "amount": amount,
            "project_name": project_name,
            "po_id": po_id,
            "po_no": po_no
        }

    def add_bill(self):
        data = self.get_form_data()
        if not data:
            return
            
        bill_no = self.service.add_contract_bill(data)
        if bill_no:
            QMessageBox.information(self, "Success", "Contract Bill added successfully.")
            self.load_data()
            self.clear_form()
            self.load_project_names()
        else:
            QMessageBox.critical(self, "Error", "Failed to add Contract Bill.")

    def update_bill(self):
        if not self.current_bill_no:
            return
            
        data = self.get_form_data()
        if not data:
            return
            
        if self.service.update_contract_bill(self.current_bill_no, data):
            QMessageBox.information(self, "Success", "Contract Bill updated successfully.")
            self.load_data()
            self.clear_form()
            self.load_project_names()
        else:
            QMessageBox.critical(self, "Error", "Failed to update Contract Bill.")

    def delete_bill(self):
        if not self.current_bill_no:
            return
            
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to delete this bill?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.service.delete_contract_bill(self.current_bill_no):
                QMessageBox.information(self, "Success", "Contract Bill deleted successfully.")
                self.load_data()
                self.clear_form()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete Contract Bill.")
