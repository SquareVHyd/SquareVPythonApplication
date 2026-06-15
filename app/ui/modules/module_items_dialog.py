from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QAbstractItemView, QMessageBox, QComboBox, QHeaderView, QInputDialog, QStatusBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QShortcut, QKeySequence
from app.services.module_service import ModuleService
from app.services.price_list_service import PriceListService
from app.services.module_type_service import ModuleTypeService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.ui.modules.price_list_lookup_dialog import PriceListLookupDialog
from app.utils.worker_thread import Worker


class ModuleItemsDialog(QDialog):
    # Assuming tbl_ModuleItems schema: ID (ModuleTypeID), DriveDescription (PK), BOM, LP, %Discount, Selection
    def __init__(self, module_type_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Module Item Manager")
        self.resize(900, 600)
        from app.ui.modules.module_item_form import ModuleItemForm # Import here to avoid circular dependency
        
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
        self.table = SearchableTable() # Assuming tbl_ModuleItems schema: ID (ModuleTypeID), DriveDescription (PK), BOM, LP, %Discount, Selection
        self.table.setStyleSheet("QTableView { selection-background-color: #93c5fd; selection-color: #000000; } QHeaderView::section { background-color: #fce4ec; border: 1px solid #e2e8f0; }")
        self.table.setColumnCount(7) # SEQNo, ModuleItemID, Drive Description, BOM, LP, % Discount, Selection
        self.table.setHorizontalHeaderLabels([
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
        # rows are expected to be: (module_item_id, drive_description, bom, lp, discount, selection, sequence_number)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            # Column mapping for the new table headers:
            # "SEQNo" (0), "ModuleItemID" (1), "Drive Description" (2), "BOM" (3), "LP" (4), "% Discount" (5), "Selection" (6)
            self.table.setItem(r, 0, NumericTableWidgetItem(str(row[6] if row[6] is not None else ""))) # Sequence Number
            self.table.setItem(r, 1, NumericTableWidgetItem(str(row[0] if row[0] is not None else ""))) # ModuleItemID
            self.table.setItem(r, 2, NumericTableWidgetItem(str(row[1] if row[1] is not None else ""))) # Drive Description
            self.table.setItem(r, 3, NumericTableWidgetItem(str(row[2] if row[2] is not None else ""))) # BOM
            self.table.setItem(r, 4, NumericTableWidgetItem(str(row[3] if row[3] is not None else ""))) # LP
            self.table.setItem(r, 5, NumericTableWidgetItem(f"{float(row[4])*100:.2f}" if row[4] is not None else "")) # % Discount (display as percentage)
            self.table.setItem(r, 6, NumericTableWidgetItem(str(row[5] if row[5] is not None else ""))) # Selection
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
                item = self.table.item(l_row, 0) # SEQNo column
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
            # (module_item_id, drive_description, bom, lp, discount, selection, sequence_number)
            for v_row in range(row_count):
                l_row = self.table.verticalHeader().logicalIndex(v_row)
                items_to_update.append({
                    "module_item_id": int(self.table.item(l_row, 1).text()), # ModuleItemID
                    "drive_description": self.table.item(l_row, 2).text(),
                    "bom": float(self.table.item(l_row, 3).text()),
                    "lp": float(self.table.item(l_row, 4).text()),
                    "discount": float(self.table.item(l_row, 5).text()) / 100.0, # Convert back to fraction
                    "selection": self.table.item(l_row, 6).text(),
                    "new_seq": v_row + 1
                })

            # Update sequence numbers directly. Assuming the DB handles sequence updates.
            for item in items_to_update:
                self.module_service.update_module_item(
                    item["module_item_id"], self.current_type_id, item["drive_description"],
                    item["bom"], item["lp"], item["discount"], item["selection"], item["new_seq"]
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
            or keyword in str(row[1]).lower()   # ModuleItemID
            or keyword in str(row[2]).lower()   # Drive Description
            or keyword in str(row[3]).lower()   # BOM
            or keyword in str(row[4]).lower()   # LP
            or keyword in str(row[5]).lower()   # % Discount
            or keyword in str(row[6]).lower()   # Selection
        ]
        self._render(filtered)

    def _add_items(self):
        from app.ui.modules.module_item_form import ModuleItemForm
        dialog = ModuleItemForm(self.current_type_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                try:
                    # Get max sequence for new item
                    max_seq = 0
                    if self.table.rowCount() > 0:
                        for r in range(self.table.rowCount()):
                            seq_item = self.table.item(r, 0) # SEQNo column
                            if seq_item:
                                max_seq = max(max_seq, int(seq_item.text()))
                    data["sequence_number"] = max_seq + 1

                    self.module_service.create_module_item(**data)
                    QMessageBox.information(self, "Success", "Module item added successfully.")
                    self._load_items_async()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to add module item: {e}")

    def _edit_item(self):
        selected = self.table.selectedItems()
        if not selected: return
        row = selected[0].row()
        
        module_item_id = int(self.table.item(row, 1).text()) # ModuleItemID
        current_data = {
            "module_item_id": module_item_id,
            "drive_description": self.table.item(row, 2).text(),
            "bom": float(self.table.item(row, 3).text()),
            "lp": float(self.table.item(row, 4).text()),
            "discount": float(self.table.item(row, 5).text()) / 100.0, # Convert back to fraction
            "selection": self.table.item(row, 6).text(),
            "sequence_number": int(self.table.item(row, 0).text()) # SEQNo
        }
        
        from app.ui.modules.module_item_form import ModuleItemForm
        dialog = ModuleItemForm(self.current_type_id, module_item_data=current_data, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                try:
                    self.module_service.update_module_item(module_item_id, **data)
                    QMessageBox.information(self, "Success", "Module item updated successfully.")
                    self._load_items_async()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to update module item: {e}")

    def _remove_items(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected: return
        if QMessageBox.question(self, "Remove", f"Remove {len(selected)} items?") == QMessageBox.Yes:
            for index in sorted(selected, key=lambda x: x.row(), reverse=True):
                module_item_id = int(self.table.item(index.row(), 1).text()) # ModuleItemID is at column 1
                self.module_service.delete_module_item(module_item_id) 
            self._load_items_async()