from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QAbstractItemView, QMessageBox, QDialogButtonBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QShortcut, QKeySequence

from app.services.price_list_service import PriceListService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.utils.worker_thread import Worker

class PriceListLookupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Price List Items")
        self.resize(800, 600)

        self.service = PriceListService()
        self._cache = []
        self.selected_price_items = [] # To store selected items

        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._worker = None

        self.setup_ui()
        self._load_data_async()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Search and Refresh
        search_layout = QVBoxLayout()

        row1 = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("General Search (Description, Model, Category, Make)...")
        self.search_box.textChanged.connect(self._debounce_search)
        row1.addWidget(self.search_box)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_table)
        row1.addWidget(self.refresh_btn)
        search_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.model_filter = QLineEdit()
        self.model_filter.setPlaceholderText("Filter Model...")
        self.model_filter.textChanged.connect(self._debounce_search)

        self.category_filter = QLineEdit()
        self.category_filter.setPlaceholderText("Filter Category...")
        self.category_filter.textChanged.connect(self._debounce_search)

        self.make_filter = QLineEdit()
        self.make_filter.setPlaceholderText("Filter Make...")
        self.make_filter.textChanged.connect(self._debounce_search)
        
        self.clear_filters_btn = QPushButton("Clear All Filters")
        self.clear_filters_btn.clicked.connect(self.clear_all_filters)

        row2.addWidget(QLabel("Narrow by:"))
        row2.addWidget(self.model_filter)
        row2.addWidget(self.category_filter)
        row2.addWidget(self.make_filter)
        row2.addWidget(self.clear_filters_btn)
        search_layout.addLayout(row2)

        layout.addLayout(search_layout)

        # Table
        self.table = SearchableTable()
        self.table.setColumnCount(12) # Based on PriceListRepository.get_all_price_items query
        self.table.setHorizontalHeaderLabels([
            "ID", "Item Description", "Model", "Category", "Make",
            "List Price", "Discount %", "Net Price", "Used Qty", "Total Amount",
            "CategoryID", "MakeID"
        ])
        self.table.hideColumn(0) # Hide ID visually, but still retrieve it
        self.table.hideColumn(10) # Hide CategoryID
        self.table.hideColumn(11) # Hide MakeID
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection) # Enable multi-selection
        layout.addWidget(self.table)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Add to Module")
        button_box.accepted.connect(self._add_selected_to_module)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Shortcuts
        QShortcut(QKeySequence.Find, self, activated=lambda: self.search_box.setFocus())
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.refresh_table)

    def _load_data_async(self):
        if self._worker: return
        self._worker = Worker(self.service.get_all_price_items)
        self._worker.result.connect(self._loaded)
        self._worker.error.connect(self._on_load_error)
        self._worker.start()

    def _loaded(self, result):
        rows, _ = result # PriceListService.get_all_price_items returns (rows, keys)
        self._cache = list(rows)
        self._render(self._cache)
        self._worker = None

    def _on_load_error(self, err):
        QMessageBox.critical(self, "Database Error", f"Could not load price list items: {err}")
        self._worker = None

    def _render(self, rows):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                self.table.setItem(r, c, NumericTableWidgetItem(str(value if value is not None else "")))
        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()

    def _debounce_search(self):
        self._search_timer.start(300)

    def _perform_search(self):
        keyword = self.search_box.text().lower()
        model_key = self.model_filter.text().lower()
        category_key = self.category_filter.text().lower()
        make_key = self.make_filter.text().lower()

        if not any([keyword, model_key, category_key, make_key]):
            self._render(self._cache)
            return

        filtered = []
        for row in self._cache:
            # Check general keyword
            match_general = True
            if keyword:
                search_content = " ".join([
                    str(row[1] or ""),
                    str(row[2] or ""),
                    str(row[3] or ""),
                    str(row[4] or "")
                ]).lower()
                match_general = keyword in search_content

            # Check individual filters (AND logic)
            match_model = not model_key or model_key in str(row[2]).lower()
            match_category = not category_key or category_key in str(row[3]).lower()
            match_make = not make_key or make_key in str(row[4]).lower()

            if match_general and match_model and match_category and match_make:
                filtered.append(row)
        self._render(filtered)

    def clear_all_filters(self):
        """Resets all search fields."""
        self.search_box.clear()
        self.model_filter.clear()
        self.category_filter.clear()
        self.make_filter.clear()

    def refresh_table(self):
        self.clear_all_filters()
        self._load_data_async()

    def _add_selected_to_module(self):
        selected_rows = self.table.selectionModel().selectedRows()
        self.selected_price_items = []
        for index in selected_rows:
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(index.row(), col)
                row_data.append(item.text() if item else None)
            # We need the ID (column 0) for create_module and ItemDescription (column 1) for context
            self.selected_price_items.append((int(row_data[0]), row_data[1]))
        self.accept()