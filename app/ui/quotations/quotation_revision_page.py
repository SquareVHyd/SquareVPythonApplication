from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QAbstractItemView, QMessageBox, QStatusBar
)
from PySide6.QtCore import Qt
from datetime import datetime
from app.services.quotation_service import QuotationService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.utils.worker_thread import Worker

class QuotationRevisionPage(QWidget):
    def __init__(self, parent_window=None):
        super().__init__()
        self.main_window = parent_window
        self.quote_id = None
        self.base_quote_id = None
        self.service = QuotationService()
        self._worker = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        
        self.title_label = QLabel("Quotation Revisions")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.add_btn = QPushButton("➕ Add Revision")
        self.add_btn.clicked.connect(self._add_revision)

        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.add_btn)
        layout.addLayout(header)

        self.table = SearchableTable()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Revision No", "Date", "Ref No", "Project"])
        self.table.hideColumn(0)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.itemDoubleClicked.connect(self._switch_to_revision)
        layout.addWidget(self.table)
        
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Double-click a revision to open it.")
        layout.addWidget(self.status_bar)

    def load_quotation(self, quote_id, project_name):
        self.quote_id = quote_id
        quote_data = self.service.get_quotation_by_id(quote_id)
        if quote_data and quote_data.get("BaseQuoteID"):
            self.base_quote_id = quote_data.get("BaseQuoteID")
        else:
            self.base_quote_id = quote_id
            
        self.title_label.setText(f"Revisions: {project_name}")
        self.refresh_table()

    def refresh_table(self):
        if self._worker or self.base_quote_id is None: return
        self._worker = Worker(self.service.get_revisions_for_quote, self.base_quote_id)
        self._worker.result.connect(self._on_data_loaded)
        self._worker.start()

    def _on_data_loaded(self, rows):
        self.table.blockSignals(True)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            # ID, RevisionNo, Date_Quote, QuoteRereceNo, QuoteProjectName
            cols = [
                row.get("ID", ""),
                row.get("RevisionNo", 0),
                row.get("Date_Quote", ""),
                row.get("QuoteRereceNo", ""),
                row.get("QuoteProjectName", "")
            ]
            for c, val in enumerate(cols):
                item = NumericTableWidgetItem(str(val) if val is not None else "")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if c == 2 and isinstance(val, datetime):
                    item.setText(val.strftime("%d-%b-%Y"))
                self.table.setItem(r, c, item)
                
            # Highlight current loaded quote
            if row.get("ID") == self.quote_id:
                for c in range(5):
                    self.table.item(r, c).setBackground(Qt.yellow)
                    
        self.table.resizeColumnsToContents()
        self.table.blockSignals(False)
        self._worker = None

    def _add_revision(self):
        try:
            new_quote_id = self.service.create_revision(self.quote_id)
            QMessageBox.information(self, "Success", "Revision created successfully.")
            
            # Update main window combobox and switch context
            if hasattr(self.main_window, 'populate_revisions'):
                self.main_window.populate_revisions(self.base_quote_id, new_quote_id)
            
            # The dropdown switch should trigger reload of this page, but we'll refresh just in case
            self.quote_id = new_quote_id
            self.refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _switch_to_revision(self, item):
        rev_id = int(self.table.item(item.row(), 0).text())
        if hasattr(self.main_window, 'populate_revisions'):
            self.main_window.populate_revisions(self.base_quote_id, rev_id)