from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QAbstractItemView, QMessageBox, QStatusBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QShortcut, QKeySequence

from app.services.quotation_service import QuotationService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.utils.worker_thread import Worker
from app.ui.quotations.panel_form import PanelForm

class PanelManagerDialog(QDialog):
    """Dialog to manage panels for a specific quotation."""
    
    def __init__(self, quote_id, project_name, parent=None):
        super().__init__(parent)
        self.quote_id = quote_id
        self.service = QuotationService()
        self.setWindowTitle(f"Project Panels: {project_name}")
        self.resize(1100, 650)
        
        self._cache = []
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._worker = None
        
        self.setup_ui()
        self.refresh_table()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        title = QLabel(f"Quotation ID: {self.quote_id}")
        title.setStyleSheet("font-size: 14px; color: #64748b;")

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search panels by name, serial or category...")
        self.search_box.textChanged.connect(self._debounce_search)

        self.add_btn = QPushButton("➕ Add Panel")
        self.add_btn.clicked.connect(self.add_panel)
        
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.clicked.connect(self.edit_panel)
        
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self.delete_panel)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.search_box)
        header.addWidget(self.add_btn)
        header.addWidget(self.edit_btn)
        header.addWidget(self.delete_btn)
        layout.addLayout(header)

        # Table setup matching existing UI
        self.table = SearchableTable()
        self.table.setStyleSheet("QTableView { selection-background-color: #93c5fd; selection-color: #000000; }")
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels([
            "ID", "QuoteID", "Category", "Serial", "Panel Name", "Qty", 
            "L (mm)", "H (mm)", "D (mm)", "Waste", "KA Rating", 
            "Earth Runs", "Stand", "Busbar Material"
        ])
        self.table.hideColumn(0) # Hide ID
        self.table.hideColumn(1) # Hide QuoteID
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.itemDoubleClicked.connect(self.edit_panel)
        layout.addWidget(self.table)
        
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)

    def refresh_table(self):
        if self._worker: return
        self.status_bar.showMessage("Loading panels...")
        self._worker = Worker(self.service.get_panels_by_quote, self.quote_id)
        self._worker.result.connect(self._on_data_loaded)
        self._worker.start()

    def _on_data_loaded(self, rows):
        self._cache = list(rows)
        self._render(self._cache)
        self.status_bar.showMessage(f"Found {len(rows)} panels", 5000)
        self._worker = None

    def _render(self, rows):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c in range(len(row)):
                val = str(row[c]) if row[c] is not None else ""
                item = NumericTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, item)
        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()

    def _debounce_search(self):
        self._search_timer.start(300)

    def _perform_search(self):
        keyword = self.search_box.text().lower().strip()
        if not keyword:
            self._render(self._cache)
            return
        filtered = [row for row in self._cache if any(keyword in str(cell).lower() for cell in row)]
        self._render(filtered)

    def add_panel(self):
        dialog = PanelForm(self.quote_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            try:
                self.service.create_panel(**dialog.get_data())
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add panel: {e}")

    def edit_panel(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected: return
        row = selected[0].row()
        
        panel_id = int(self.table.item(row, 0).text())
        # Map table columns back to a dict for the form
        cols = ["id", "quote_id", "category", "serial", "name", "qty", "length", "height", "depth", "waste", "ka_rating", "earth_runs", "stand", "busbar"]
        current_data = {cols[i]: self.table.item(row, i).text() for i in range(len(cols))}
        
        dialog = PanelForm(self.quote_id, panel_data=current_data, parent=self)
        if dialog.exec() == QDialog.Accepted:
            try:
                self.service.update_panel(panel_id, **dialog.get_data())
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update panel: {e}")

    def delete_panel(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected: return
        if QMessageBox.question(self, "Confirm", f"Delete {len(selected)} panel(s)?") == QMessageBox.Yes:
            try:
                for idx in selected:
                    self.service.delete_panel(int(self.table.item(idx.row(), 0).text()))
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {e}")