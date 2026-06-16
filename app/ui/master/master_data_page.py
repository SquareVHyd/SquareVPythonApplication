from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
    QLabel, QPushButton, QHeaderView, QMessageBox, QLineEdit, QDialog, QFormLayout, QStatusBar, QApplication
)
from PySide6.QtCore import Qt, QTimer
from sqlalchemy import text
from app.config.database import get_session

from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.ui.master.generic_crud_dialog import GenericCrudDialog # Import the new dialog

class MasterDataPage(QWidget):
    def __init__(self):
        super().__init__()
        self.current_table_name = None
        self.current_table_columns = [] # Stores (column_name, type_oid, display_type)
        self.primary_key_column = None
        self.filter_line_edits = {} # Stores QLineEdit for column filters
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self.setup_ui()
        self.refresh_table_list()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header controls
        top_header = QHBoxLayout()
        top_header.addWidget(QLabel("Select Table:"))
        
        self.table_selector = QComboBox()
        self.table_selector.setMinimumWidth(300)
        self.table_selector.currentIndexChanged.connect(self.load_table_data)
        top_header.addWidget(self.table_selector)

        self.refresh_schema_btn = QPushButton("🔄 Refresh Schema")
        self.refresh_schema_btn.clicked.connect(self.refresh_table_list)
        top_header.addWidget(self.refresh_schema_btn)
        
        top_header.addStretch()
        layout.addLayout(top_header)

        # CRUD and General Search
        crud_search_row = QHBoxLayout()
        self.add_btn = QPushButton("➕ Add New")
        self.add_btn.setToolTip("(Ctrl+N)")
        self.add_btn.clicked.connect(self._add_row)
        self.edit_btn = QPushButton("✏️ Edit Selected")
        self.edit_btn.setToolTip("(Ctrl+E)")
        self.edit_btn.clicked.connect(self._edit_row)
        self.delete_btn = QPushButton("🗑️ Delete Selected")
        self.delete_btn.setToolTip("(Delete)")
        self.delete_btn.clicked.connect(self._delete_row)

        self.general_search_box = QLineEdit()
        self.general_search_box.setPlaceholderText("General Search (all columns)...")
        self.general_search_box.textChanged.connect(self._debounce_search)

        crud_search_row.addWidget(self.add_btn)
        crud_search_row.addWidget(self.edit_btn)
        crud_search_row.addWidget(self.delete_btn)
        crud_search_row.addStretch()
        crud_search_row.addWidget(QLabel("Search All Columns:"))
        crud_search_row.addWidget(self.general_search_box)
        layout.addLayout(crud_search_row)

        # Dynamic Column Filters
        self.filter_widgets_container = QWidget()
        self.filter_widgets_layout = QHBoxLayout(self.filter_widgets_container)
        self.filter_widgets_layout.setContentsMargins(0, 0, 0, 0)
        self.filter_widgets_layout.setSpacing(5)
        layout.addWidget(self.filter_widgets_container)

        # Data Table
        self.table = SearchableTable()
        self.table.setStyleSheet("QTableView { selection-background-color: #93c5fd; selection-color: #000000; } QHeaderView::section { background-color: #fce4ec; border: 1px solid #e2e8f0; }")
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Status bar for selection stats
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("QStatusBar { background-color: #f8fafc; color: #475569; border-top: 1px solid #e2e8f0; font-size: 11px; }")
        layout.addWidget(self.status_bar)

        self.table.itemSelectionChanged.connect(self._update_status_bar_stats)

    def _update_status_bar_stats(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.status_bar.clearMessage()
            return

        count = len(selected_rows)
        msg = f"Count: {count}"
        self.status_bar.showMessage(msg)

    def refresh_table_list(self):
        """Fetch all table names from the public schema."""
        query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('categories', 'metrics', 'sub_targets', 'tblCategory', 'tblMake', 'tblModSwg')
            ORDER BY table_name
        """)
        with get_session() as session:
            try:
                result = session.execute(query)
                tables = [row[0] for row in result.fetchall()]
                
                self.table_selector.blockSignals(True)
                self.table_selector.clear()
                self.table_selector.addItem("-- Select a Table --")
                self.table_selector.addItems(tables)
                self.table_selector.blockSignals(False)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not fetch table names: {e}")

    def _get_table_primary_key(self, table_name):
        """Helper to find the primary key column of a table in PostgreSQL."""
        query = text(f"""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = '"{table_name}"'::regclass AND i.indisprimary;
        """)
        with get_session() as session:
            try:
                result = session.execute(query)
                row = result.fetchone()
                return row[0] if row else None
            except Exception as e:
                print(f"Error fetching PK for {table_name}: {e}")
                return None

    def load_table_data(self):
        table_name = self.table_selector.currentText()
        if not table_name or table_name.startswith("--"):
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self.current_table_name = None
            self.current_table_columns = []
            self.primary_key_column = None
            self._clear_column_filters()
            return

        self.current_table_name = table_name
        self.primary_key_column = self._get_table_primary_key(table_name)

        with get_session() as session:
            try:
                # Fetch all rows from the selected table
                result = session.execute(text(f'SELECT * FROM "{table_name}"'))
                
                # Store column names (mocking the structure for compatibility with display logic)
                columns = list(result.keys())
                self.current_table_columns = [[col] for col in columns]
                rows = result.fetchall()

                # Configure table structure
                self.table.setColumnCount(len(columns))
                self.table.setHorizontalHeaderLabels(columns)
                self.table.setRowCount(len(rows))

                # Populate data grid
                for r_idx, row in enumerate(rows):
                    for c_idx, value in enumerate(row):
                        text_val = str(value) if value is not None else ""
                        item = NumericTableWidgetItem(text_val)
                        # Set read-only flags for the master data viewer
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                        self.table.setItem(r_idx, c_idx, item)

                self.table.resizeColumnsToContents()
                if self.table.columnCount() > 0:
                    self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
                
                self._create_column_filters(columns)
            except Exception as e:
                QMessageBox.critical(self, "Query Error", f"Failed to load data from {table_name}:\n{e}")

    def _clear_column_filters(self):
        while self.filter_widgets_layout.count():
            item = self.filter_widgets_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.filter_line_edits.clear()

    def _create_column_filters(self, column_names):
        self._clear_column_filters()
        for col_name in column_names:
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(f"Filter {col_name}...")
            line_edit.textChanged.connect(self._debounce_search)
            self.filter_widgets_layout.addWidget(line_edit)
            self.filter_line_edits[col_name] = line_edit
        self.filter_widgets_layout.addStretch() # Push filters to the left

    def _debounce_search(self):
        self._search_timer.start(300)

    def _perform_search(self):
        if not self.current_table_name:
            return

        general_keyword = self.general_search_box.text().lower().strip()
        column_filters = {col: le.text().lower().strip() for col, le in self.filter_line_edits.items() if le.text().strip()}

        with get_session() as session:
            try:
                query_str = f'SELECT * FROM "{self.current_table_name}"'
                where_clauses = []
                params = {}

                # Add individual column filters using named parameters
                for i, (col_name, filter_text) in enumerate(column_filters.items()):
                    p_name = f"col_{i}"
                    where_clauses.append(f'CAST("{col_name}" AS TEXT) ILIKE :{p_name}')
                    params[p_name] = f'%{filter_text}%'
                
                # Add general search filter (applies to all visible columns)
                if general_keyword:
                    clauses = []
                    for i, col_info in enumerate(self.current_table_columns):
                        col_name = col_info[0]
                        p_name = f"gen_{i}"
                        clauses.append(f'CAST("{col_name}" AS TEXT) ILIKE :{p_name}')
                        params[p_name] = f'%{general_keyword}%'
                    where_clauses.append(f"({' OR '.join(clauses)})")

                if where_clauses:
                    query_str += " WHERE " + " AND ".join(where_clauses)
                
                result = session.execute(text(query_str), params)
                rows = result.fetchall()

                # Re-render table with filtered data
                self.table.setSortingEnabled(False)
                self.table.setRowCount(len(rows))
                for r_idx, row in enumerate(rows):
                    for c_idx, value in enumerate(row):
                        text_val = str(value) if value is not None else ""
                        item = NumericTableWidgetItem(text_val)
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                        self.table.setItem(r_idx, c_idx, item)
                self.table.setSortingEnabled(True)
                self.table.resizeColumnsToContents()
            except Exception as e:
                QMessageBox.critical(self, "Filter Error", f"Failed to apply filters: {e}")

    def _add_row(self):
        if not self.current_table_name:
            QMessageBox.warning(self, "No Table Selected", "Please select a table first.")
            return
        
        # Show all columns including primary key for input in the same widget
        cols_for_input = [col[0] for col in self.current_table_columns]
        
        dialog = GenericCrudDialog(cols_for_input, parent=self)
        if dialog.exec() == QDialog.Accepted:
            raw_data = dialog.get_data()
            # Skip empty values to allow database defaults (e.g. for auto-increment IDs)
            data = {k: v for k, v in raw_data.items() if v.strip() != ""}
            
            if not data:
                return

            with get_session() as session:
                try:
                    columns = ", ".join([f'"{c}"' for c in data.keys()])
                    placeholders = ", ".join([f":{c}" for c in data.keys()])
                    query = text(f'INSERT INTO "{self.current_table_name}" ({columns}) VALUES ({placeholders})')
                    
                    session.execute(query, data)
                    session.commit()
                    QMessageBox.information(self, "Success", "Record added successfully.")
                    self.load_table_data() # Refresh table
                except Exception as e:
                    QMessageBox.critical(self, "Database Error", f"Failed to add record: {e}")

    def _edit_row(self):
        if not self.current_table_name:
            QMessageBox.warning(self, "No Table Selected", "Please select a table first.")
            return
        if not self.primary_key_column:
            QMessageBox.warning(self, "No Primary Key", "Cannot edit: Primary key not identified for this table.")
            return

        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select a row to edit.")
            return
        if len(selected_rows) > 1:
            QMessageBox.warning(self, "Multiple Selection", "Please select only one row to edit.")
            return

        row_index = selected_rows[0].row()
        current_data = {}
        for c_idx, col_info in enumerate(self.current_table_columns):
            col_name = col_info[0]
            item = self.table.item(row_index, c_idx)
            current_data[col_name] = item.text() if item else ""
        
        dialog = GenericCrudDialog([col[0] for col in self.current_table_columns], initial_data=current_data, parent=self)
        if dialog.exec() == QDialog.Accepted:
            updated_data = dialog.get_data()
            
            pk_value = updated_data.pop(self.primary_key_column) # Get PK value and remove from data to update
            
            with get_session() as session:
                try:
                    set_clauses = [f'"{c}" = :{c}' for c in updated_data.keys()]
                    query = text(f'UPDATE "{self.current_table_name}" SET {", ".join(set_clauses)} WHERE "{self.primary_key_column}" = :pk_val')
                    
                    params = updated_data.copy()
                    params["pk_val"] = pk_value
                    
                    session.execute(query, params)
                    session.commit()
                    QMessageBox.information(self, "Success", "Record updated successfully.")
                    self.load_table_data() # Refresh table
                except Exception as e:
                    QMessageBox.critical(self, "Database Error", f"Failed to update record: {e}")

    def _delete_row(self):
        if not self.current_table_name:
            QMessageBox.warning(self, "No Table Selected", "Please select a table first.")
            return
        if not self.primary_key_column:
            QMessageBox.warning(self, "No Primary Key", "Cannot delete: Primary key not identified for this table.")
            return

        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select row(s) to delete.")
            return

        pk_values_to_delete = []
        for index in selected_rows:
            # Find the index of the primary key column
            pk_col_idx = -1
            for i, col_info in enumerate(self.current_table_columns):
                if col_info[0] == self.primary_key_column:
                    pk_col_idx = i
                    break
            
            if pk_col_idx == -1: 
                QMessageBox.critical(self, "Error", f"Primary key column '{self.primary_key_column}' not found in table display. Cannot delete.")
                return

            item = self.table.item(index.row(), pk_col_idx)
            if item:
                pk_values_to_delete.append(item.text())
        
        if not pk_values_to_delete:
            QMessageBox.warning(self, "No IDs Found", "Could not retrieve IDs for selected rows.")
            return

        confirm_msg = f"Are you sure you want to delete {len(pk_values_to_delete)} record(s) from '{self.current_table_name}'?"
        if QMessageBox.question(self, "Confirm Delete", confirm_msg, QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            with get_session() as session:
                try:
                    # PostgreSQL ANY operator is used to match against the array of primary keys
                    query = text(f'DELETE FROM "{self.current_table_name}" WHERE "{self.primary_key_column}" = ANY(:ids)')
                    
                    session.execute(query, {"ids": pk_values_to_delete})
                    session.commit()
                    QMessageBox.information(self, "Success", f"{len(pk_values_to_delete)} record(s) deleted successfully.")
                    self.load_table_data() # Refresh table
                except Exception as e:
                    QMessageBox.critical(self, "Database Error", f"Failed to delete record(s): {e}")

    def load_table_and_filter(self, table_name: str, column_name: str, filter_value: str):
        """
        Loads a specific table and applies a filter to a given column.
        This method is intended to be called externally, e.g., from MainWindow.
        """
        # 1. Select the table in the QComboBox
        index = self.table_selector.findText(table_name)
        if index != -1:
            self.table_selector.setCurrentIndex(index)
            # Calling setCurrentIndex will trigger load_table_data, which also creates filters.
            # We need to ensure filters are ready before setting text.
            QApplication.processEvents() # Process events to ensure UI updates

            # 2. Apply the filter to the specific column's QLineEdit
            if column_name in self.filter_line_edits:
                # Clear all other filters first to ensure only the desired filter is active
                for le in self.filter_line_edits.values():
                    le.clear()
                self.general_search_box.clear()

                self.filter_line_edits[column_name].setText(filter_value)
            else:
                QMessageBox.warning(self, "Filter Error", f"Column '{column_name}' not found for filtering in table '{table_name}'.")
        else:
            QMessageBox.warning(self, "Table Not Found", f"Table '{table_name}' not found in master data.")