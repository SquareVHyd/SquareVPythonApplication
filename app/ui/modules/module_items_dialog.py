from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QAbstractItemView, QMessageBox, QComboBox, QHeaderView, QInputDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QShortcut, QKeySequence

from app.services.module_service import ModuleService
from app.services.module_type_service import ModuleTypeService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.ui.modules.price_list_lookup_dialog import PriceListLookupDialog
from app.utils.worker_thread import Worker


class ModuleItemsDialog(QDialog):
    def __init__(self, module_type_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Module Item Manager")
        self.resize(900, 600)
        
        self.module_service = ModuleService()
        self.type_service = ModuleTypeService()
        self.current_type_id = module_type_id
        
        self._cache = []
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._worker = None

        self.setup_ui()
        self._load_types_and_initial_items() # This method will now also trigger initial item loading

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Top selection and search
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Module Type:"))
        self.type_combo = QComboBox()
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        top_layout.addWidget(self.type_combo, 1)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search items by description or ID...")
        self.search_box.textChanged.connect(self._debounce_search)
        top_layout.addWidget(self.search_box, 1)

        self.add_btn = QPushButton("Add New Item")
        self.add_btn.clicked.connect(self._add_items)
        top_layout.addWidget(self.add_btn)
        
        layout.addLayout(top_layout)
        
        # Table
        self.table = SearchableTable()
        self.table.setColumnCount(5) # These labels should match the query in ModuleService.get_items_by_module_type
        self.table.setHorizontalHeaderLabels([ # These labels should match the query in ModuleService.get_items_by_module_type
            "SEQNo", "Item ID", "Description", "Qty", "ModuleItemID"
        ])
        self.table.hideColumn(4)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.edit_btn = QPushButton("Edit Qty/SEQ")
        self.edit_btn.clicked.connect(self._edit_item)
        btn_layout.addWidget(self.edit_btn) # Add edit button to layout
        
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self._remove_items)
        
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # Shortcuts
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self._add_items)
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self._edit_item)
        QShortcut(QKeySequence("Delete"), self, activated=self._remove_items)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=lambda: self.search_box.setFocus())

    def _load_types_and_initial_items(self):
        types = self.type_service.get_all_module_types()
        self.type_combo.blockSignals(True)
        initial_index = -1
        for t in types:
            self.type_combo.addItem(f"{t[1]} ({t[2]})", t[0])
            if t[0] == self.current_type_id:
                initial_index = self.type_combo.count() - 1
        if initial_index != -1:
            self.type_combo.setCurrentIndex(initial_index)
        self.type_combo.blockSignals(False)
        self._load_items_async() # Load items for the initially selected type

    def _on_type_changed(self):
        self.current_type_id = self.type_combo.currentData()
        self._load_items_async()

    def _load_items_async(self):
        if self._worker: return
        self._worker = Worker(self.module_service.get_items_by_module_type, self.current_type_id)
        self._worker.result.connect(self._items_loaded)
        self._worker.error.connect(self._on_load_error)
        self._worker.start()

    def _items_loaded(self, rows):
        self._cache = list(rows)
        self._render(self._cache)
        self._worker = None

    def _render(self, rows):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c in range(len(row)):
                self.table.setItem(r, c, NumericTableWidgetItem(str(row[c] if row[c] is not None else "")))
        self.table.setSortingEnabled(True)

    def _on_load_error(self, err):
        QMessageBox.critical(self, "Database Error", f"Could not load module items: {err}")
        self._worker = None

    def _debounce_search(self):
        self._search_timer.start(300)

    def _perform_search(self):
        keyword = self.search_box.text().lower()
        if not keyword:
            self._render(self._cache)
            return
        filtered = [row for row in self._cache if keyword in str(row[2]).lower() or keyword in str(row[1]).lower()]
        self._render(filtered)

    def _add_items(self):
        dialog = PriceListLookupDialog(self)
        if dialog.exec():
            selected_items = dialog.selected_price_items
            if not selected_items: return
            
            max_seq = 0
            if self._cache:
                # Assuming _cache stores (SEQNo, Item ID, Description, Qty, ModuleItemID) as per table headers
                max_seq = max((int(row[0] or 0) for row in self._cache), default=0)

            for item in selected_items:
                price_list_id = item[0] # item is (ID, ItemDescription)
                max_seq += 1
                # create_module(module_type_id, price_list_item_id, quantity, sequence_number)
                # The create_module call will now correctly save to the database due to the commit in the repository.
                # The _load_items_async() call after the loop will refresh the UI.
                self.module_service.create_module(self.current_type_id, price_list_id, 1, max_seq)
            self._load_items_async()

    def _edit_item(self):
        selected = self.table.selectedItems()
        if not selected: return
        row = selected[0].row()
        
        # Ensure a valid row is selected
        if row < 0 or row >= self.table.rowCount():
            return

        module_item_id = int(self.table.item(row, 4).text()) # ModuleItemID is at column 4
        qty, ok1 = QInputDialog.getDouble(self, "Edit Quantity", "Enter Quantity:", float(self.table.item(row, 3).text()), 0, 1000000, 2)
        if not ok1: return
        seq, ok2 = QInputDialog.getInt(self, "Edit SEQNo", "Enter SEQNo:", int(self.table.item(row, 0).text()), 1, 32767)
        if not ok2: return
        # update_module(module_item_id, module_type_id, price_list_item_id, quantity, sequence_number)
        # price_list_item_id is at column 1
        self.module_service.update_module(module_item_id, self.current_type_id, int(self.table.item(row, 1).text()), qty, seq) # This will also commit changes
        self._load_items_async()

    def _remove_items(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected: return
        if QMessageBox.question(self, "Remove", f"Remove {len(selected)} items?") == QMessageBox.Yes:
            # Iterate through selected rows and delete each module item
            # It's safer to iterate in reverse if deleting from the underlying data structure
            # but here we are just calling a service method and then reloading all data.
            # The ModuleItemID is at column 4
            for index in sorted(selected, key=lambda x: x.row(), reverse=True):
                module_item_id = int(self.table.item(index.row(), 4).text()) # This will also commit changes
                self.module_service.delete_module(module_item_id) 
            self._load_items_async()