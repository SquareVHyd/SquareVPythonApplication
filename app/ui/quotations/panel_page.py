from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QAbstractItemView, QMessageBox, QStatusBar, QDialog,
    QTextEdit, QComboBox, QMenu
)
from PySide6.QtCore import Qt, QTimer, QEvent, QPoint
from PySide6.QtGui import QShortcut, QKeySequence, QAction
import operator # For evaluating expressions


from app.services.quotation_service import QuotationService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.utils.worker_thread import Worker
from app.ui.quotations.panel_form import PanelForm
from app.ui.quotations.panel_delegates import ComboBoxDelegate

class SumCalculatorDialog(QDialog):
    """Dialog to sum multiple values and return the total for dimension columns."""
    def __init__(self, title, current_value, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(350, 250)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Enter values or simple expressions (e.g., '10+5', '2*3', '10\\n5\\n2'):"))
        self.text_edit = QTextEdit()
        if current_value and current_value != "0":
            self.text_edit.setText(current_value)
        layout.addWidget(self.text_edit)
        
        self.result_label = QLabel("Total Sum: 0")
        self.result_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2563eb;")
        layout.addWidget(self.result_label)

        # Monitor text for '+' symbol to trigger partial calculation
        self.text_edit.textChanged.connect(self._on_text_changed)
        # Install event filter to capture Enter key
        self.text_edit.installEventFilter(self)
        
        buttons = QHBoxLayout()
        btn_ok = QPushButton("Apply Total")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_ok)
        buttons.addWidget(btn_cancel)
        layout.addLayout(buttons)
        
        self.total = 0
        self._calculate()

    def eventFilter(self, obj, event):
        """Capture Enter/Return keys to finalize calculation and accept dialog."""
        if obj is self.text_edit and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self.accept()
                return True
        return super().eventFilter(obj, event)

    def _on_text_changed(self):
        """Calculates the sum when '+' or newline is entered, preventing 'in-between' updates."""
        text = self.text_edit.toPlainText()
        if text and (text[-1] == '+' or text[-1] == '\n'):
            self._calculate()

    def accept(self):
        """Finalizes the sum before closing the dialog."""
        self._calculate()
        super().accept()

    def _calculate(self):
        text = self.text_edit.toPlainText().strip()
        self.total = 0
        
        if not text:
            self.result_label.setText("Total Sum: 0")
            return

        # Replace '+' with newline to treat them as delimiters for terms to be summed.
        # This allows expressions like "2*4+2" to be split into "2*4" and "2" and then summed.
        processed_text = text.replace('+', '\n')
        
        # Split by newlines to get individual terms/expressions
        terms = [term.strip() for term in processed_text.split('\n') if term.strip()]

        current_total = 0.0
        for term in terms:
            try:
                # Evaluate each term as a separate expression
                current_total += eval(term, {"__builtins__": None}, {})
            except (SyntaxError, NameError, TypeError, ZeroDivisionError):
                # If a term is invalid (e.g., "2*4+"), ignore it or handle as 0
                continue

        self.total = int(round(current_total))
        self.result_label.setText(f"Total Sum: {self.total}")

class SteelSelectorDialog(QDialog):
    """Dialog to manage steel specifications for a specific panel."""
    def __init__(self, panel_id, parent=None):
        super().__init__(parent)
        self.panel_id = panel_id
        self.setWindowTitle(f"Steel Specification for Panel ID: {panel_id}")
        self.resize(1200, 400)
        self.service = QuotationService()
        
        layout = QVBoxLayout(self)

        # No CRUD buttons for single-row management
        # The layout will contain only the table

        self.table = SearchableTable()
        self.table.setColumnCount(19)
        self.table.setHorizontalHeaderLabels([
            "ID", "PanelID", "F/B Qty", "F/B Size", "Sides Qty", "Sides Size",
            "B/T Qty", "B/TSize", "Seating", "Canopy", "In/Out",
            "PanelFace", "Dbl Door", "Drawout", "ProtectionClass", "CableEntry",
            "Mounting", "Seat/Stand", "Stand Size"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.itemChanged.connect(self._handle_item_changed)
        layout.addWidget(self.table)
        
        self._setup_delegates()
        self.load_data()

        # Footer for Save action
        self.btn_save = QPushButton("💾 Save Steel Specification & Close")
        self.btn_save.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 8px;")
        self.btn_save.clicked.connect(self.accept)
        layout.addWidget(self.btn_save)

    def accept(self):
        """Gather data, apply defaults for empties, and save before closing."""
        if self.table.rowCount() == 0:
            super().accept()
            return

        try:
            row = 0
            steel_id = int(self.table.item(row, 0).text())
            
            def get_text(c, default):
                item = self.table.item(row, c)
                val = item.text().strip() if item else ""
                return val if val else default

            def get_int(c, default):
                item = self.table.item(row, c)
                val = item.text().strip() if item else ""
                try: return int(val) if val else default
                except: return default

            data = {
                "FrontBackQty": get_int(2, 0),
                "FrontBackSteelSize": get_text(3, "CRCA 1.2 mm"),
                "SidesQty": get_int(4, 0),
                "SidesSteelSize": get_text(5, "CRCA 1.2 mm"),
                "BottomTopQty": get_int(6, 0),
                "BottomSteelSize": get_text(7, "CRCA 1.2 mm"),
                "TypeOfSeating": get_text(8, "ISMC"),
                "Canopy": get_text(9, "No"),
                "IndoorOutdoor": get_text(10, "Indoor"),
                "PanelFace": get_text(11, "single"), # Corrected default case
                "DoubleDoor": get_text(12, "No"),
                "DrawoutFixed": get_text(13, "No"),
                "ProtectionClass": get_text(14, "IP 44"),
                "CableEntry": get_text(15, "Top"),
                "Mounting": get_text(16, "free stand"), # Corrected default case
                "SeatStand": get_text(17, "No"),
                "StandMetalSize": get_text(18, "0") # Corrected to get_text as per schema
            }

            self.service.update_full_steel_config(steel_id, data)
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save record: {e}")

    def _setup_delegates(self):
        from app.ui.quotations.panel_delegates import ComboBoxDelegate
        sizes = ["CRCA 1.2 mm", "CRCA 1.6 mm", "CRCA 2 mm", "CRCA 3 mm"]
        yn = ["No", "Yes"]
        seating = ["ISMC", "3 mm sheet", "Single value"]
        cable = ["Top", "Bottom", "Side", "Top&bottom"]
        mounting = ["Free Stand", "Wall"]
        in_out = ["Indoor", "Outdoor"] # Default is 'Indoor'
        face = ["single", "double"] # Default is 'single'
        p_class = ["IP 44", "IP 45", "IP 55", "IP 65"]

        # Assign delegates to specific columns based on requirements
        self.table.setItemDelegateForColumn(3, ComboBoxDelegate(self, items=sizes))
        self.table.setItemDelegateForColumn(5, ComboBoxDelegate(self, items=sizes))
        self.table.setItemDelegateForColumn(7, ComboBoxDelegate(self, items=sizes))
        self.table.setItemDelegateForColumn(8, ComboBoxDelegate(self, items=seating))
        self.table.setItemDelegateForColumn(9, ComboBoxDelegate(self, items=yn))
        self.table.setItemDelegateForColumn(10, ComboBoxDelegate(self, items=in_out)) # IndoorOutdoor
        self.table.setItemDelegateForColumn(11, ComboBoxDelegate(self, items=face)) # PanelFace
        self.table.setItemDelegateForColumn(12, ComboBoxDelegate(self, items=yn))
        self.table.setItemDelegateForColumn(13, ComboBoxDelegate(self, items=yn))
        self.table.setItemDelegateForColumn(14, ComboBoxDelegate(self, items=p_class))
        self.table.setItemDelegateForColumn(15, ComboBoxDelegate(self, items=cable))
        self.table.setItemDelegateForColumn(16, ComboBoxDelegate(self, items=mounting)) # Mounting
        self.table.setItemDelegateForColumn(17, ComboBoxDelegate(self, items=yn)) # Seat/Stand

    def load_data(self):
        self.table.blockSignals(True)
        rows = self.service.get_steel_configs_by_panel(self.panel_id)
        if not rows: # If no steel config exists, create one with defaults
            self.service.create_steel_config(self.panel_id)
            rows = self.service.get_steel_configs_by_panel(self.panel_id) # Re-fetch

        self.table.setRowCount(len(rows))
        editable_cols = set(range(2, 19))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                text = str(val) if val is not None else ""
                item = NumericTableWidgetItem(text)
                # All columns from 2 to 18 are editable
                item.setFlags(item.flags() | Qt.ItemIsEditable if c >= 2 else item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()
        self.table.blockSignals(False)

    def _handle_item_changed(self, item):
        self.table.blockSignals(True)
        row, col = item.row(), item.column()
        if not (2 <= col <= 18):
            self.table.blockSignals(False)
            return

        try:
            # Only perform UI formatting validation here; DB saving is now handled in accept()
            val = item.text().strip()
            if col in [2, 4, 6]: # Force integer for quantities
                try:
                    val = int(val or 0)
                except ValueError: # Catch specific error for int conversion
                    val = "0"
                item.setText(val)
        finally:
            self.table.blockSignals(False)
        
    def get_result(self):
        return str(self.total)

class PanelBBSelectorDialog(QDialog):
    """Dialog to manage busbar specifications for a specific panel."""
    def __init__(self, panel_id, parent=None):
        super().__init__(parent)
        self.panel_id = panel_id
        self.setWindowTitle(f"Busbar Specification for Panel ID: {panel_id}")
        self.resize(1100, 400)
        self.service = QuotationService()
        
        layout = QVBoxLayout(self)

        self.table = SearchableTable()
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels([
            "ID", "PanelID", "Neutral Rating", "Bus Section", "Section Qty", "Amps Req",
            "Amps Sel", "Clearence", "Qty PH", "Qty Nu", "Qty Earth",
            "BB Phase", "BB Neutral", "BB Earth"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table)
        
        self.load_data()

        self.btn_save = QPushButton("💾 Save Busbar Specification & Close")
        self.btn_save.setStyleSheet("background-color: #0277bd; color: white; font-weight: bold; padding: 8px;")
        self.btn_save.clicked.connect(self.accept)
        layout.addWidget(self.btn_save)

    def load_data(self):
        self.table.blockSignals(True)
        rows = self.service.get_panel_bb_configs_by_panel(self.panel_id)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                text = str(val) if val is not None else ""
                item = NumericTableWidgetItem(text)
                item.setFlags(item.flags() | Qt.ItemIsEditable if c >= 2 else item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()
        self.table.blockSignals(False)

    def accept(self):
        if self.table.rowCount() == 0:
            super().accept()
            return

        try:
            row = 0
            bb_id = int(self.table.item(row, 0).text())
            
            def get_text(c, default):
                item = self.table.item(row, c)
                val = item.text().strip() if item else ""
                return val if val else default

            def get_int(c, default):
                item = self.table.item(row, c)
                val = item.text().strip() if item else ""
                try: return int(val) if val else default
                except: return default

            data = {
                "NeutralRating": get_int(2, 100),
                "BusSection": get_text(3, "Main"),
                "BusSectionQty": get_int(4, 1),
                "AmpsRequested": get_int(5, 0),
                "AmpsSelected": get_text(6, "0"),
                "BusbarClearence": get_text(7, "Standard"),
                "BB_QtyPH": get_int(8, 1),
                "BB_QtyNu": get_int(9, 1),
                "BB_QtyEarth": get_int(10, 1),
                "Select_BB_Phase": get_text(11, ""),
                "Select_BB_Neutral": get_text(12, ""),
                "Select_BB_Earth": get_text(13, "")
            }
            self.service.update_full_panel_bb_config(bb_id, data)
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save record: {e}")

class PanelPage(QWidget):
    """Page to manage panels for a specific quotation, displayed in-place."""
    
    def __init__(self, parent_window=None):
        super().__init__()
        self.main_window = parent_window
        self.quote_id = None
        self.service = QuotationService()
        
        self._cache = []
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._worker = None
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        self.back_btn = QPushButton("⬅️ Back to Quotations List") # Parent is QuotationDetailsPage
        self.back_btn.clicked.connect(lambda: self.main_window.show_quotations())
        
        self.title_label = QLabel("Project Panels")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search panels...")
        self.search_box.textChanged.connect(self._debounce_search)

        self.add_btn = QPushButton("➕ Add Panel")
        self.add_btn.clicked.connect(self.add_panel)
        
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.clicked.connect(self.edit_panel)
        
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self.delete_panel)

        header.addWidget(self.back_btn)
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.search_box)
        header.addWidget(self.add_btn)
        header.addWidget(self.edit_btn)
        header.addWidget(self.delete_btn)
        layout.addLayout(header)

        self.table = SearchableTable()
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels([
            "ID", "QuoteID", "Category", "Serial", "Panel Name", "Qty", 
            "L (mm)", "H (mm)", "D (mm)", "Waste", "KA Rating", 
            "Earth Runs", "Stand", "Busbar Material"
        ])
        self.table.hideColumn(0)
        self.table.hideColumn(1)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        # Connect the signal for inline editing
        self.table.itemChanged.connect(self._handle_item_changed)
        layout.addWidget(self.table)

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Apply dropdown delegates for specific columns to allow inline selection
        self.table.setItemDelegateForColumn(12, ComboBoxDelegate(self, items=["Yes", "No"]))
        self.table.setItemDelegateForColumn(13, ComboBoxDelegate(self, items=["Aluminium", "Copper"]))
        self.table.setItemDelegateForColumn(10, ComboBoxDelegate(self, items=["7kA", "10kA", "16kA", "25kA", "36kA", "40kA", "50kA", "65kA", "100kA", "150KA"]))
        
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)

    def load_quotation(self, quote_id, project_name):
        """Update the page context and fetch data."""
        self.quote_id = quote_id
        self.title_label.setText(f"Panels: {project_name} (ID: {quote_id})")
        self.refresh_table()

    def refresh_table(self):
        if self._worker or self.quote_id is None: return
        self.status_bar.showMessage("Loading panels...")
        self._worker = Worker(self.service.get_panels_by_quote, self.quote_id)
        self._worker.result.connect(self._on_data_loaded)
        self._worker.start()

    def _on_data_loaded(self, rows):
        self._cache = list(rows)
        # Auto-generate steel rows for panels if missing
        pids = [r[0] for r in rows]
        if pids:
            self.service.ensure_steel_configs_for_panels(pids)
            self.service.ensure_panel_bb_configs_for_panels(pids)
        self._render(self._cache)
        self.status_bar.showMessage(f"Found {len(rows)} panels", 5000)
        self._worker = None

    def _render(self, rows):
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        # Columns 2 through 13 correspond to the editable data fields in tbl_Panels
        editable_cols = set(range(2, 14))

        for r, row in enumerate(rows):
            for c in range(len(row)):
                val = str(row[c]) if row[c] is not None else ""
                item = NumericTableWidgetItem(val)
                if c in editable_cols:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, item)
        self.table.setSortingEnabled(True)
        self.table.blockSignals(False)
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

    def _on_item_double_clicked(self, item):
        """Handles double-click to open calculator for specific dimensions."""
        if item.column() in [6, 7, 8]:  # L (mm), H (mm), D (mm)
            self._open_calculator(item)

    def _open_calculator(self, item):
        col_name = self.table.horizontalHeaderItem(item.column()).text()
        dialog = SumCalculatorDialog(f"Add Values - {col_name}", item.text(), self)
        if dialog.exec() == QDialog.Accepted:
            item.setText(dialog.get_result())

    def _show_context_menu(self, pos: QPoint):
        item = self.table.itemAt(pos)
        if not item: return
        
        row = item.row()
        panel_id = int(self.table.item(row, 0).text())
        panel_name = self.table.item(row, 4).text()
        
        menu = QMenu(self)
        select_steel_action = QAction(f"Select Steel Panel for: {panel_name}", self)
        select_steel_action.triggered.connect(lambda: self._open_steel_selector(panel_id))
        menu.addAction(select_steel_action)

        select_bb_action = QAction(f"Busbar Details for: {panel_name}", self)
        select_bb_action.triggered.connect(lambda: self._open_bb_selector(panel_id))
        menu.addAction(select_bb_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _open_steel_selector(self, panel_id):
        dialog = SteelSelectorDialog(panel_id, self)
        dialog.exec()

    def _open_bb_selector(self, panel_id):
        dialog = PanelBBSelectorDialog(panel_id, self)
        dialog.exec()

    def add_panel(self):
        dialog = PanelForm(self.quote_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.service.create_panel(**dialog.get_data())
            self.refresh_table()

    def edit_panel(self):
        row = self.table.currentIndex().row()
        if row < 0: return
        panel_id = int(self.table.item(row, 0).text())
        cols = ["id", "quote_id", "category", "serial", "name", "qty", "length", "height", "depth", "waste", "ka_rating", "earth_runs", "stand", "busbar"]
        current_data = {cols[i]: self.table.item(row, i).text() for i in range(len(cols))}
        dialog = PanelForm(self.quote_id, panel_data=current_data, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.service.update_panel(panel_id, **dialog.get_data())
            self.refresh_table()

    def delete_panel(self):
        indexes = self.table.selectionModel().selectedIndexes()
        if not indexes: return
        
        # Get unique rows from selected cells
        rows_to_delete = sorted(list(set(idx.row() for idx in indexes)), reverse=True)
        
        if QMessageBox.question(self, "Confirm", f"Delete {len(rows_to_delete)} selected panel(s)?") == QMessageBox.Yes:
            for row in rows_to_delete:
                panel_id = int(self.table.item(row, 0).text())
                self.service.delete_panel(panel_id)
            self.refresh_table()

    def _handle_item_changed(self, item):
        """Handles inline updates when a table cell is edited."""
        self.table.blockSignals(True)
        row = item.row()
        col = item.column()
        
        # Indices 2-13: Category, Serial, Name, Qty, L, H, D, Waste, KA, Earth, Stand, Busbar
        if not (2 <= col <= 13):
            self.table.blockSignals(False)
            return

        try:
            panel_id_item = self.table.item(row, 0)
            if not panel_id_item:
                self.table.blockSignals(False)
                return
                
            panel_id = int(panel_id_item.text())

            # Map column index to database column name
            column_map = {
                2: "PanelCategory",
                3: "PanelSerial",
                4: "PanelName",
                5: "PanelQty",
                6: "LengthXmm",
                7: "HeightYmm",
                8: "DepthZmm",
                9: "AddWaste",
                10: "PanelKARating",
                11: "EarthRuns",
                12: "StandRequired",
                13: "BusbarMaterial"
            }
            db_column_name = column_map.get(col)
            if not db_column_name:
                self.table.blockSignals(False)
                return

            new_value_str = item.text().strip()
            new_value = new_value_str

            # Validate numeric inputs for Qty, L, H, D, and Waste
            if col in [5, 6, 7, 8, 9]: # Qty, L, H, D, Waste
                try:
                    new_value = int(new_value_str or 0)
                except ValueError:
                    QMessageBox.warning(self, "Invalid Input", f"Please enter a valid number for {self.table.horizontalHeaderItem(col).text()}.")
                    self.refresh_table()
                    self.table.blockSignals(False)
                    return

            self.service.update_panel_field(panel_id, db_column_name, new_value)
            
            # Update local cache to keep it in sync with the UI
            for i, cached_row in enumerate(self._cache):
                if cached_row[0] == panel_id:
                    updated_list = list(cached_row)
                    updated_list[col] = new_value
                    self._cache[i] = tuple(updated_list)
                    break

        except Exception as e:
            QMessageBox.critical(self, "Update Error", f"Failed to update record: {e}")
            self.refresh_table()
        finally:
            self.table.blockSignals(False)