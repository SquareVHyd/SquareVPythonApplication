from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QAbstractItemView, QMessageBox, QMenu, QStatusBar, QApplication
)
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QShortcut, QKeySequence, QAction

from app.services.quotation_service import QuotationService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.utils.worker_thread import Worker


class QuotationPage(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.service = QuotationService()
        self._cache = []
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._worker = None
        self.main_window = main_window # Store reference to main window
        self.setup_ui()
        self.refresh_table()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Quotations Management")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by Customer, Project, or Ref No...")
        self.search_box.textChanged.connect(self._debounce_search)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_table)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.search_box)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        # Table
        self.table = SearchableTable()
        self.table.setStyleSheet("QTableView { selection-background-color: #93c5fd; selection-color: #000000; }") # Keep existing style
        self.table.setColumnCount(11) # Increased by 1 for CustomerId
        self.table.setHorizontalHeaderLabels([
            "ID", "Customer ID", "Customer", "Req. Date", "Quote Date", "Ref No", 
            "Subject", "Project", "Contact", "Prepared By", "Status"
        ])
        self.table.hideColumn(0) # Hide Quote ID
        self.table.hideColumn(1) # Hide Customer ID
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        
        # Right-click context menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self.table)

        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)

        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.refresh_table)

    def refresh_table(self):
        if self._worker: return
        self.status_bar.showMessage("Fetching quotations...")
        self._worker = Worker(self.service.get_all_quotations)
        self._worker.result.connect(self._on_data_loaded)
        self._worker.start()

    def _on_data_loaded(self, rows):
        self._cache = list(rows)
        self._render(self._cache)
        self.status_bar.showMessage(f"Loaded {len(rows)} quotations", 5000)
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

    def _show_context_menu(self, pos: QPoint):
        item = self.table.itemAt(pos)
        if not item: return
        
        row = item.row()
        customer_name = self.table.item(row, 1).text()
        
        menu = QMenu(self)
        view_cust = menu.addAction(f"View Customer: {customer_name}")
        menu.exec(self.table.viewport().mapToGlobal(pos))
