from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QAbstractItemView, QMessageBox, QStatusBar
)
from PySide6.QtCore import Qt, QTimer
from app.services.quotation_service import QuotationService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.utils.worker_thread import Worker
from app.ui.quotations.panel_delegates import ComboBoxDelegate
from app.ui.quotations.ctc_constants import (
    GST_OPTIONS, FREIGHT_OPTIONS, PAYMENT_OPTIONS, WARRANTY_OPTIONS,
    VALIDITY_OPTIONS, PACKING_OPTIONS, INSPECTION_OPTIONS, DELIVERY_OPTIONS
)

class QuotationCTCDialog(QDialog):
    """Dialog to manage Commercial Terms & Conditions (CTC) for a specific quotation in table format."""
    
    def __init__(self, quote_id, project_name, parent=None):
        super().__init__(parent)
        self.service = QuotationService()
        self.quote_id = quote_id
        self.setWindowTitle(f"Quotation CTC Table: {project_name} (ID: {quote_id})")
        self.resize(1100, 450)
        
        self._cache = []
        self._worker = None
        
        self.setup_ui()
        self.refresh_table()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        self.title_label = QLabel(f"CTC Records for Quote ID: {self.quote_id}")
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_table)

        self.add_btn = QPushButton("➕ Add CTC Entry")
        self.add_btn.setToolTip("Creates an entry for this quotation if missing")
        self.add_btn.clicked.connect(self._add_default_ctc)

        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.refresh_btn)
        header.addWidget(self.add_btn)
        layout.addLayout(header)

        self.table = SearchableTable()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "ID", "QuoteID", "GST / Taxes", "Freight & Insurance", "Payment", 
            "Warranty", "Validity", "Packing", "Inspection", "Delivery", 
            "Bank Details", "Notes"
        ])
        self.table.hideColumn(0)
        self.table.hideColumn(1)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.itemChanged.connect(self._handle_item_changed)
        
        self.table.setItemDelegateForColumn(2, ComboBoxDelegate(self, items=GST_OPTIONS, editable=True))
        self.table.setItemDelegateForColumn(3, ComboBoxDelegate(self, items=FREIGHT_OPTIONS, editable=True))
        self.table.setItemDelegateForColumn(4, ComboBoxDelegate(self, items=PAYMENT_OPTIONS, editable=True))
        self.table.setItemDelegateForColumn(5, ComboBoxDelegate(self, items=WARRANTY_OPTIONS, editable=True))
        self.table.setItemDelegateForColumn(6, ComboBoxDelegate(self, items=VALIDITY_OPTIONS, editable=True))
        self.table.setItemDelegateForColumn(7, ComboBoxDelegate(self, items=PACKING_OPTIONS, editable=True))
        self.table.setItemDelegateForColumn(8, ComboBoxDelegate(self, items=INSPECTION_OPTIONS, editable=True))
        self.table.setItemDelegateForColumn(9, ComboBoxDelegate(self, items=DELIVERY_OPTIONS, editable=True))
        
        layout.addWidget(self.table)
        
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)

    def refresh_table(self):
        if self._worker: return
        self.status_bar.showMessage("Loading CTC data...")
        self._worker = Worker(self.service.get_quote_ctc_list, self.quote_id)
        self._worker.result.connect(self._on_data_loaded)
        self._worker.start()

    def _on_data_loaded(self, rows):
        self._cache = list(rows)
        self._render(self._cache)
        self.status_bar.showMessage(f"Found {len(rows)} record(s)", 5000)
        self._worker = None

    def _render(self, rows):
        self.table.blockSignals(True)
        self.table.setRowCount(len(rows))
        
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                text = str(val) if val is not None else ""
                item = NumericTableWidgetItem(text)
                # Allow editing for columns GSTTax and onwards
                if c >= 2:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, item)
        
        self.table.resizeColumnsToContents()
        self.table.blockSignals(False)

    def _add_default_ctc(self):
        """Ensures at least one CTC row exists for this quotation."""
        try:
            self.service.save_quote_ctc(QuoteID=self.quote_id)
            self.refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add CTC: {e}")

    def _handle_item_changed(self, item):
        """Handles inline cell updates for CTC fields."""
        self.table.blockSignals(True)
        row, col = item.row(), item.column()
        if col < 2: 
            self.table.blockSignals(False)
            return

        try:
            ctc_id = int(self.table.item(row, 0).text())
            column_map = {
                2: "GSTTax", 3: "FreightAndInsurance", 4: "Payment", 
                5: "Warranty", 6: "Validity", 7: "Packing", 
                8: "Inspection", 9: "Delivery", 10: "BankDetails", 11: "Notes"
            }
            db_col = column_map.get(col)
            if db_col:
                new_val = item.text().strip()
                self.service.update_quote_ctc_field(ctc_id, db_col, new_val)
        except Exception as e:
            QMessageBox.critical(self, "Update Error", f"Failed to update CTC: {e}")
            self.refresh_table()
        finally:
            self.table.blockSignals(False)