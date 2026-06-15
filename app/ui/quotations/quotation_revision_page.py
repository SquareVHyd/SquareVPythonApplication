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
        self.table.setHorizontalHeaderLabels(["ID", "QuoteID", "Rev No", "Date", "Description"])
        self.table.hideColumn(0)
        self.table.hideColumn(1)
        self.table.itemChanged.connect(self._handle_item_changed)
        layout.addWidget(self.table)
        
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)

    def load_quotation(self, quote_id, project_name):
        self.quote_id = quote_id
        self.title_label.setText(f"Revisions: {project_name}")
        self.refresh_table()

    def refresh_table(self):
        if self._worker or self.quote_id is None: return
        self._worker = Worker(self.service.get_revisions_list, self.quote_id)
        self._worker.result.connect(self._on_data_loaded)
        self._worker.start()

    def _on_data_loaded(self, rows):
        self.table.blockSignals(True)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = NumericTableWidgetItem(str(val) if val is not None else "")
                # According to schema: 2=RevisionNo, 3=QuoteRevisionDate, 4=QuoteRevisionDescription
                item.setFlags(item.flags() | Qt.ItemIsEditable if c == 4 else item.flags() & ~Qt.ItemIsEditable)
                if c == 3 and isinstance(val, datetime):
                    item.setText(val.strftime("%d-%b-%Y %H:%M"))
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()
        self.table.blockSignals(False)
        self._worker = None

    def _add_revision(self):
        try:
            self.service.create_revision(self.quote_id)
            self.refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _handle_item_changed(self, item):
        if item.column() != 4: return
        self.table.blockSignals(True)
        try:
            rev_id = int(self.table.item(item.row(), 0).text())
            self.service.update_revision_field(rev_id, "QuoteRevisionDescription", item.text())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Update failed: {e}")
            self.refresh_table()
        finally:
            self.table.blockSignals(False)