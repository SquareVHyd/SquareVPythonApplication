from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QAbstractItemView, QMessageBox, QComboBox, QHeaderView, QInputDialog, QStatusBar
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

        self.add_btn = QPushButton("➕ Add New Item")
        self.add_btn.setToolTip("Add New Item (Ctrl+N)")
        self.add_btn.clicked.connect(self._add_items)
        top_layout.addWidget(self.add_btn)
        
        layout.addLayout(top_layout)
        
        # Table
        self.table = SearchableTable()
        self.table.setStyleSheet("QTableView { selection-background-color: #93c5fd; selection-color: #000000; } QHeaderView::section { background-color: #fce4ec; border: 1px solid #e2e8f0; }")
        self.table.setColumnCount(5) # These labels should match the query in ModuleService.get_items_by_module_type
        self.table.setHorizontalHeaderLabels([ # These labels should match the query in ModuleService.get_items_by_module_type
            "SEQNo", "Item ID", "Description", "Qty", "ModuleItemID"
        ])
        self.table.hideColumn(0) # Hide SEQNo column as per request
        self.table.hideColumn(4)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionsMovable(True)

        # Enable adjustable rows via vertical header
        self.table.verticalHeader().setSectionsMovable(True)
        self.table.verticalHeader().sectionMoved.connect(self._on_row_moved)

        # Update sequence numbers when column order changes or table is sorted
        self.table.horizontalHeader().sectionMoved.connect(self._on_row_moved)
        self.table.horizontalHeader().sortIndicatorChanged.connect(lambda: self._update_visual_indices())

        layout.addWidget(self.table)
        
        # Footer Status Bar for selection statistics
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("QStatusBar { background-color: #f8fafc; color: #475569; border-top: 1px solid #e2e8f0; font-size: 11px; }")
        layout.addWidget(self.status_bar)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.edit_btn = QPushButton("✏️ Edit Qty/SEQ")
        self.edit_btn.setToolTip("Edit Quantity or Sequence (Ctrl+E)")
        self.edit_btn.clicked.connect(self._edit_item)
        
        self.remove_btn = QPushButton("🗑️ Remove Selected")
        self.remove_btn.setToolTip("Remove Selected Items (Delete)")
        self.remove_btn.clicked.connect(self._remove_items)
        
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        self.table.itemSelectionChanged.connect(self._update_status_bar_stats)
        
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
        self._update_visual_indices()

    def _update_status_bar_stats(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.status_bar.clearMessage()
            return

        count = len(selected_rows)
        msg = f"Count: {count}"
        self.status_bar.showMessage(msg)

    def _on_row_moved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        """Trigger visual index update after a row is moved."""
        self._update_visual_indices()

    def _update_visual_indices(self):
        """Update the vertical header labels and the hidden serial column to match the visual order."""
        self.table.blockSignals(True)
        try:
            count = self.table.rowCount()
            labels = [""] * count
            for v_row in range(count):
                l_row = self.table.verticalHeader().logicalIndex(v_row)
                display_num = str(v_row + 1)
                labels[l_row] = display_num
                
                # Update the hidden column 0 (SEQNo) so it reflects the current visual position
                item = self.table.item(l_row, 0)
                if item:
                    item.setText(display_num)
            
            self.table.setVerticalHeaderLabels(labels)
        finally:
            self.table.blockSignals(False)

    def closeEvent(self, event):
        """Save the current sequence and quantities to the database before closing."""
        self.table.blockSignals(True)
        try:
            row_count = self.table.rowCount()
            items_to_update = []

            # 1. Collect all visual items first to get a consistent snapshot
            for v_row in range(row_count):
                l_row = self.table.verticalHeader().logicalIndex(v_row)
                items_to_update.append({
                    "module_item_id": int(self.table.item(l_row, 4).text()),
                    "item_id": int(self.table.item(l_row, 1).text()),
                    "qty": float(self.table.item(l_row, 3).text()),
                    "new_seq": v_row + 1
                })

            # 2. Define a temporary offset greater than the largest possible sequence number
            # to avoid uq_module_seq constraint violations during the update process.
            temp_offset = row_count + 1000

            # 3. Pass 1: Move items to temporary high sequence numbers to "clear" the [1, N] range.
            for item in items_to_update:
                self.module_service.update_module(
                    item["module_item_id"], self.current_type_id, item["item_id"], item["qty"], item["new_seq"] + temp_offset
                )

            # 4. Pass 2: Apply the final intended sequence numbers.
            for item in items_to_update:
                self.module_service.update_module(
                    item["module_item_id"], self.current_type_id, item["item_id"], item["qty"], item["new_seq"]
                )
        except Exception as e:
            print(f"Error saving module item states: {e}")
        finally:
            self.table.blockSignals(False)
            super().closeEvent(event)

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
        filtered = [
            row for row in self._cache 
            if keyword in str(row[0]).lower()   # SEQNo
            or keyword in str(row[1]).lower()   # Item ID (now effectively the first searchable column)
            or keyword in str(row[2]).lower()   # Description
            or keyword in str(row[4]).lower()   # ModuleItemID
        ]
        self._render(filtered)

    def _add_items(self):
        dialog = PriceListLookupDialog(self)
        if dialog.exec():
            selected_items = dialog.selected_price_items
            if not selected_items: return
            
            max_seq = self.table.rowCount() # New items will be added at the end, so their sequence is current row count + 1

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
        
        # Get current values
        current_seq = int(self.table.item(row, 0).text()) # Get current SEQNo from hidden column
        item_id = int(self.table.item(row, 1).text())
        
        module_item_id = int(self.table.item(row, 4).text()) # ModuleItemID is at column 4
        qty, ok1 = QInputDialog.getDouble(self, "Edit Quantity", "Enter Quantity:", float(self.table.item(row, 3).text()), 0, 1000000, 2)
        if not ok1: return
        
        # Update UI directly; database update is removed to prevent SQL errors
        self.table.item(row, 3).setText(str(qty))

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