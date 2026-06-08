import math
import re
import os
import pandas as pd
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QMessageBox,
    QDialog,
    QAbstractItemView,
    QComboBox,
    QStatusBar
)

from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import Qt, QTimer

from app.services.price_list_service import PriceListService
from app.ui.pricelist.pricelist_form import PriceListForm
from app.ui.searchable_table import (
    SearchableTable,
    NumericTableWidgetItem
)
from app.utils.worker_thread import Worker
from app.config.ui_state import UIStateManager


class PriceListPage(QWidget):

    def __init__(self):

        super().__init__()

        self.service = PriceListService()

        self._cache = []
        self._search_timer = QTimer()

        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(
            self._perform_search
        )

        self._worker = None

        self.setup_ui()
        self._populate_filter_lookups()

        self._load_async()
        self._restore_state()

    def setup_ui(self):

        layout = QVBoxLayout(self)

        header = QHBoxLayout()

        title = QLabel("Price List")

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(
            "General Search (Description, Model, Category, Make)..."
        )

        self.search_box.textChanged.connect(
            self._debounce_search
        )

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setToolTip("(Ctrl+R)")
        self.add_btn = QPushButton("➕ Add")
        self.add_btn.setToolTip("(Ctrl+N)")
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setToolTip("(Ctrl+E)")
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setToolTip("(Delete)")
        self.export_excel_btn = QPushButton("📊 Export Excel")
        self.export_excel_btn.setToolTip("(Ctrl+Shift+E)")

        self.refresh_btn.clicked.connect(
            self.refresh_table
        )

        self.add_btn.clicked.connect(
            self.add_item
        )

        self.edit_btn.clicked.connect(
            self.edit_item
        )

        self.delete_btn.clicked.connect(
            self.delete_item
        )

        self.export_excel_btn.clicked.connect(
            self.export_to_excel
        )

        # Row for individual filters and Clear All button
        filter_row = QHBoxLayout()
        self.model_filter = QLineEdit()
        self.model_filter.setPlaceholderText("Filter Model...")
        self.model_filter.textChanged.connect(self._debounce_search)

        self.category_filter = QComboBox()
        self.category_filter.setEditable(True)
        self.category_filter.setInsertPolicy(QComboBox.NoInsert)
        self.category_filter.lineEdit().setPlaceholderText("Filter Category...")
        self.category_filter.editTextChanged.connect(self._debounce_search)

        self.make_filter = QComboBox()
        self.make_filter.setEditable(True)
        self.make_filter.setInsertPolicy(QComboBox.NoInsert)
        self.make_filter.lineEdit().setPlaceholderText("Filter Make...")
        self.make_filter.editTextChanged.connect(self._debounce_search)

        self.clear_filters_btn = QPushButton("🧹 Clear")
        self.clear_filters_btn.setFixedWidth(80)
        self.clear_filters_btn.clicked.connect(self.clear_all_filters)

        # Align filters with columns: ID(0), Desc(1), Model(2), Category(3), Make(4)
        filter_row.addWidget(QLabel("Filters:"), 1)     # Aligned with ID/Description
        filter_row.addWidget(self.model_filter, 2)      # Respected Column: Model
        filter_row.addWidget(self.category_filter, 2)   # Respected Column: Category
        filter_row.addWidget(self.make_filter, 2)       # Respected Column: Make
        filter_row.addWidget(self.clear_filters_btn)
        filter_row.addStretch(1)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.search_box)
        header.addWidget(self.refresh_btn)
        header.addWidget(self.add_btn)
        header.addWidget(self.edit_btn)
        header.addWidget(self.delete_btn)
        header.addWidget(self.export_excel_btn)

        layout.addLayout(header)
        layout.addLayout(filter_row)

        self.table = SearchableTable()

        self.table.setColumnCount(12)

        self.table.setHorizontalHeaderLabels([
            "ID",
            "Description",
            "Model",
            "Category",
            "Make",
            "List Price",
            "Discount %",
            "Net Price",
            "Used Qty",
            "Total Amount",
            "CategoryID",
            "MakeID"
        ])
        # self.table.hideColumn(0) # ID column is now visible
        self.table.hideColumn(10)
        self.table.hideColumn(11)

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        
        # Connect itemChanged signal for in-place editing of price columns
        self.table.itemChanged.connect(self._handle_item_changed)
        
        
        # Enable movable columns and rows
        self.table.horizontalHeader().setSectionsMovable(True)
        self.table.verticalHeader().setSectionsMovable(True)
        
        # Store column adjustments (width and order) as they happen
        self.table.horizontalHeader().sectionResized.connect(self._save_state)
        self.table.horizontalHeader().sectionMoved.connect(self._save_state)

        self.table.setSortingEnabled(True)

        layout.addWidget(self.table)

        # Footer Status Bar for selection statistics
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("QStatusBar { background-color: #f8fafc; color: #475569; border-top: 1px solid #e2e8f0; font-size: 11px; }")
        layout.addWidget(self.status_bar)

        self.table.itemSelectionChanged.connect(self._update_status_bar_stats)

    def _update_status_bar_stats(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.status_bar.clearMessage()
            return

        count = len(selected_items)
        total_sum = 0.0
        numeric_found = False

        for item in selected_items:
            try:
                # Clean string for float conversion
                val = float(item.text().replace('₹', '').replace(',', '').strip())
                total_sum += val
                numeric_found = True
            except (ValueError, TypeError):
                continue

        msg = f"Count: {count}"
        if numeric_found:
            msg += f"  |  Sum: {total_sum:,.2f}"
        
        self.status_bar.showMessage(msg)

        QShortcut(
            QKeySequence("Ctrl+N"),
            self,
            activated=self.add_item
        )

        QShortcut(
            QKeySequence("Ctrl+E"),
            self,
            activated=self.edit_item
        )

        QShortcut(
            QKeySequence("Delete"),
            self,
            activated=self.delete_item
        )

        QShortcut(
            QKeySequence("Ctrl+R"),
            self,
            activated=self.refresh_table
        )

        QShortcut(
            QKeySequence.Find,
            self,
            activated=self.focus_search
        )

    def focus_search(self):
        self.search_box.setFocus()

    def _populate_filter_lookups(self):
        """Populate the filter dropdowns with unique categories and makes."""
        self.category_filter.blockSignals(True)
        self.make_filter.blockSignals(True)
        
        self.category_filter.clear()
        self.category_filter.addItem("") # Empty first item
        for row in self.service.get_all_categories():
            self.category_filter.addItem(str(row[1] or ""))
            
        self.make_filter.clear()
        self.make_filter.addItem("") # Empty first item
        for row in self.service.get_all_makes():
            self.make_filter.addItem(str(row[1] or ""))
            
        self.category_filter.blockSignals(False)
        self.make_filter.blockSignals(False)

    def _load_async(self):

        # Fix: Prevent 'QThread: Destroyed while thread is still running'
        if self._worker and self._worker.isRunning():
            return

        self._worker = Worker(
            self.service.get_all_price_items
        )
        self._worker.result.connect(self._loaded)
        self._worker.error.connect(self._on_load_error)
        self._worker.start()

    def _loaded(self, result):

        rows, _ = result

        self._cache = list(rows)
        self._render(self._cache)
        self._worker = None

    def _on_load_error(self, err):
        QMessageBox.critical(self, "Database Error", f"Could not load price list: {err}")
        self._worker = None

    def _render(self, rows):
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)

        self.table.setRowCount(len(rows))

        # Define which columns are editable for in-place editing
        editable_cols = {5, 6} # List Price, Discount %

        for r, row in enumerate(rows):
            for c in range(len(row)):
                val = row[c]
                if c == 6 and val is not None:
                    # Display fractional discount as percentage (e.g., 0.1 -> 10.0)
                    text = f"{(float(val) * 100):.2f}"
                else:
                    # Ensure 0 values are rendered correctly and not treated as empty strings
                    text = str(val) if val is not None else ""
                
                table_item = NumericTableWidgetItem(text)
                table_item.setFlags(table_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, table_item)
                
                # Set editable flags for specific columns
                if c in editable_cols:
                    table_item.setFlags(table_item.flags() | Qt.ItemIsEditable)
                else:
                    table_item.setFlags(table_item.flags() & ~Qt.ItemIsEditable)

        self.table.blockSignals(False)
        self.table.setSortingEnabled(True)
        
        # Restore manual widths if they exist; otherwise, auto-fit to contents
        if not self._restore_state():
            self.table.resizeColumnsToContents()

    def _save_state(self):
        """Save header state to UIStateManager."""
        header_state = self.table.horizontalHeader().saveState()
        v_header_state = self.table.verticalHeader().saveState()
        if hasattr(UIStateManager, 'save_pricelist_page_state'):
            UIStateManager.save_pricelist_page_state({
                "header_state": header_state,
                "v_header_state": v_header_state
            })

    def _restore_state(self):
        """Restore header state from UIStateManager."""
        if hasattr(UIStateManager, 'get_pricelist_page_state'):
            state = UIStateManager.get_pricelist_page_state()
            if state:
                h_restored = False
                if state.get("header_state"):
                    h_restored = self.table.horizontalHeader().restoreState(state["header_state"])
                if state.get("v_header_state"):
                    self.table.verticalHeader().restoreState(state["v_header_state"])
                return h_restored
        return False

    def _debounce_search(self):

        self._search_timer.start(300)

    def _perform_search(self):

        keyword = self.search_box.text().lower()
        model_key = self.model_filter.text().lower()
        category_key = self.category_filter.currentText().lower()
        make_key = self.make_filter.currentText().lower()

        if not any([keyword, model_key, category_key, make_key]):
            self._render(self._cache)
            return

        filtered = []
        for row in self._cache:
            # Check general keyword
            match_general = True
            if keyword:
                search_content = " ".join([
                    str(row[0] or ""),
                    str(row[1] or ""),
                    str(row[2] or ""),
                    str(row[3] or ""),
                    str(row[4] or "")
                ]).lower()
                match_general = keyword in search_content

            # Check individual filters (AND logic)
            match_model = not model_key or model_key in str(row[2] or "").lower()
            match_category = not category_key or category_key in str(row[3] or "").lower()
            match_make = not make_key or make_key in str(row[4] or "").lower()

            if match_general and match_model and match_category and match_make:
                filtered.append(row)

        self._render(filtered)

    def clear_all_filters(self):
        """Resets all search fields which triggers re-render via textChanged signals."""
        self.search_box.clear()
        self.model_filter.clear()
        self.category_filter.setCurrentIndex(0)
        self.make_filter.setCurrentIndex(0)

    def get_selected_item(self):

        selected = self.table.selectedItems()
        if not selected:
            return None

        try:
            row = selected[0].row()
            item_id = int(
                self.table.item(row, 0).text()
            )
            # Fetch latest data from service for the form
            return self.service.get_price_item(item_id)
        except (ValueError, AttributeError, Exception):
            return None

    def add_item(self):

        dialog = PriceListForm(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                try:
                    self.service.create_price_item(**data)
                    QMessageBox.information(self, "Success", "Price list item added successfully.")
                    self.refresh_table()
                except Exception as e:
                    QMessageBox.critical(self, "Database Error", f"Could not create item: {e}")

    def edit_item(self):

        item = self.get_selected_item()
        if not item:
            QMessageBox.warning(self, "Selection Required", "Please select an item to edit.")
            return

        dialog = PriceListForm(
            self,
            price_item=item  # Ensures compatibility with PriceListForm.__init__
        )

        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                try:
                    # item[0] is the ID
                    self.service.update_price_item(
                        item[0],
                        **data
                    )
                    QMessageBox.information(self, "Success", "Price list item updated successfully.")
                    self.refresh_table()
                except Exception as e:
                    QMessageBox.critical(self, "Database Error", f"Could not update item: {e}")

    def delete_item(self):

        item = self.get_selected_item()
        if not item:
            QMessageBox.warning(self, "Selection Required", "Please select an item to delete.")
            return

        if QMessageBox.question(
            self,
            "Delete",
            f"Are you sure you want to delete the selected item?\n\nDescription: {item[1]}"
        ) == QMessageBox.Yes:
            try:
                self.service.delete_price_item(item[0])
                QMessageBox.information(self, "Deleted", "Item removed from price list.")
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Could not delete item: {e}")

    def refresh_table(self):

        self.clear_all_filters()

        self._load_async()

    def export_to_excel(self):
        """Exports data from vwPriceList to the specified Excel path."""
        export_path = r"G:\My Drive\PRINT\Reports_Import\Export_PriceListSql.xlsx"
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            
            # Fetch data from the view via the service
            data, keys = self.service.get_pricelist_view_data()
            
            # Convert to DataFrame
            df = pd.DataFrame([list(row) for row in data], columns=keys)
            
            # Clean illegal control characters that break Excel/XML exports
            # This removes characters in the ranges [#x0-#x8], [#xB-#xC], [#xE-#x1F]
            illegal_char_re = re.compile(r"[\000-\010]|[\013-\014]|[\016-\037]")
            df = df.map(lambda x: illegal_char_re.sub("", x) if isinstance(x, str) else x)
            
            df.to_excel(export_path, index=False)
            
            QMessageBox.information(self, "Success", f"Data exported successfully to:\n{export_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export to Excel: {e}")

    def _handle_item_changed(self, item):
        # Block signals to prevent re-triggering this slot when we update other cells programmatically
        self.table.blockSignals(True)

        row = item.row()
        col = item.column()
        
        editable_cols_map = {
            5: "list_price",       # "List Price"
            6: "discount_percent"  # "Discount %"
        }

        if col not in editable_cols_map:
            self.table.blockSignals(False)
            return

        item_id = int(self.table.item(row, 0).text())
        new_value_str = item.text()
        field_name = editable_cols_map[col]
        
        original_value_in_cache = None
        for i, cached_row in enumerate(self._cache):
            if cached_row[0] == item_id:
                original_value_in_cache = cached_row[col]
                break

        try:
            # Fetch the current row data from cache to reconstruct the full payload for the service
            current_row = None
            for cached in self._cache:
                if cached[0] == item_id:
                    current_row = list(cached)
                    break
            
            if not current_row:
                raise ValueError("Item record not found in local cache.")

            # 1. Update the specific field being edited and validate
            # Numeric fields (List Price, Discount %)
            try:
                new_val = float(new_value_str or 0)
                if col == 6:
                    # Convert percentage input to fraction (e.g., 10 -> 0.1)
                    new_val = round(new_val, 2) / 100.0
            except ValueError:
                raise ValueError(f"Invalid numeric input for {field_name.replace('_', ' ')}")
            
            if new_val < 0: raise ValueError("Values cannot be negative.")
            
            current_row[col] = new_val
            
            # 2. Re-calculate derived values to keep database consistent, with robust conversion
            try:
                lp = float(current_row[5] or 0)
                dp = float(current_row[6] or 0)
                qty = float(current_row[8] or 0)
            except ValueError:
                raise ValueError("List Price, Discount, or Quantity in cache is not a valid number.")
            
            # Update Net Price (rounded to 4 decimals) and Total Amount using the formula: lp * (1 - discount / 100)
            # We multiply dp (fraction) by 100 to get the percentage for the formula
            discount_val = dp * 100
            current_row[7] = math.ceil(lp * (1 - discount_val / 100) * 10000) / 10000
            current_row[9] = float(current_row[7] or 0) * qty

            # 3. Build the full payload. The service requires all fields for the UPDATE query.
            payload = {
                "item_description": current_row[1],
                "model": current_row[2],
                "list_price": float(current_row[5] or 0),
                "discount_percent": float(current_row[6] or 0),
                "net_price": float(current_row[7] or 0),
                "used_qty": float(current_row[8] or 0),
                "total_amount": float(current_row[9] or 0),
                "category_id": current_row[10],
                "make_id": current_row[11]
            }

            # Update the database using the item_id and the full record details
            self.service.update_price_item(item_id=item_id, **payload)
            
            # Fetch the entire updated item from the database to get all recalculated values
            updated_item_data = self.service.get_price_item(item_id)
            if updated_item_data:
                # Update the cache with the fully updated row
                for i, cached_row in enumerate(self._cache):
                    if cached_row[0] == item_id:
                        self._cache[i] = updated_item_data
                        break
                # Re-render the specific row in the table
                self._update_table_row(row, updated_item_data)
            else:
                QMessageBox.warning(self, "Update Failed", f"Could not retrieve updated data for item {item_id}.")
                self.refresh_table() # Fallback to full refresh if updated data can't be fetched

        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", f"Please enter a valid number for {self.table.horizontalHeaderItem(col).text()}: {e}")
            # Revert the cell in the UI to its original value from cache
            if original_value_in_cache is not None:
                # If it's the discount column, convert back to percentage for display
                if col == 6:
                    item.setText(f"{(float(original_value_in_cache) * 100):.2f}")
                else:
                    item.setText(str(original_value_in_cache))
            else:
                self.refresh_table() # If original not found, refresh the whole table
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Could not update item: {e}")
            self.refresh_table() # Refresh on DB error too
        finally:
            self.table.blockSignals(False)

    def _update_table_row(self, row_index, row_data):
        # This method updates a single row in the table with new data
        # It assumes row_data is a tuple/list matching the table's column structure
        editable_cols = {5, 6} # List Price, Discount %

        for c in range(len(row_data)):
            val = row_data[c]
            if c == 6 and val is not None:
                text = f"{(float(val) * 100):.2f}"
            else:
                text = str(val) if val is not None else ""
            
            table_item = self.table.item(row_index, c)
            if not table_item:
                table_item = NumericTableWidgetItem()
                self.table.setItem(row_index, c, table_item)
            
            table_item.setText(text)
            # Re-apply editable flags, as setting text might reset some properties
            if c in editable_cols:
                table_item.setFlags(table_item.flags() | Qt.ItemIsEditable)
            else:
                table_item.setFlags(table_item.flags() & ~Qt.ItemIsEditable)