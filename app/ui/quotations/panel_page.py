from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QAbstractItemView, QMessageBox, QStatusBar, QDialog,
    QTextEdit, QComboBox, QMenu, QSplitter, QTabWidget, QGroupBox, QFrame
)
from PySide6.QtCore import Qt, QTimer, QEvent, QPoint
from PySide6.QtGui import QShortcut, QKeySequence, QAction, QColor
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

    def get_result(self):
        return str(self.total)

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

class SteelSelectorWidget(QWidget):
    """Widget to manage steel specifications for a specific panel."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.panel_id = None
        self.service = QuotationService()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Calculation Block (Moved to Top) ---
        calc_frame = QFrame()
        calc_frame.setStyleSheet("QFrame { background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; }")
        calc_layout = QHBoxLayout(calc_frame)
        calc_layout.setContentsMargins(15, 10, 15, 10)
        
        self.unit_cost_input = QLineEdit()
        self.unit_cost_input.setPlaceholderText("Unit Cost (₹)")
        self.unit_cost_input.setFixedWidth(100)
        self.unit_cost_input.setStyleSheet("padding: 4px; border: 1px solid #94a3b8; border-radius: 4px; background-color: white;")
        
        default_steel_cost = self.service.get_steel_unit_cost()
        if default_steel_cost > 0:
            self.unit_cost_input.setText(str(default_steel_cost))
        
        calc_btn = QPushButton("⚡ Calculate Cost")
        calc_btn.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; padding: 5px 15px; border-radius: 4px; border: none;")
        calc_btn.clicked.connect(self.calculate_steel_cost)
        
        self.panel_wt_lbl = QLabel("Panel Weight: 0.00 kg")
        self.panel_wt_lbl.setStyleSheet("border: none; background: transparent; color: #334155;")
        
        self.wastage_wt_lbl = QLabel("Wastage Weight: 0.00 kg")
        self.wastage_wt_lbl.setStyleSheet("border: none; background: transparent; color: #334155;")
        
        self.total_wt_lbl = QLabel("Total Weight: 0.00 kg")
        self.total_wt_lbl.setStyleSheet("border: none; background: transparent; font-weight: bold; color: #0f172a;")
        
        self.cost_lbl = QLabel("Total Cost: ₹0.00")
        self.cost_lbl.setStyleSheet("border: none; background: transparent; font-weight: bold; color: #dc2626; font-size: 14px;")
        
        unit_lbl = QLabel("<b>Unit Cost/kg:</b>")
        unit_lbl.setStyleSheet("border: none; background: transparent; color: #334155;")
        
        calc_layout.addWidget(unit_lbl)
        calc_layout.addWidget(self.unit_cost_input)
        calc_layout.addWidget(calc_btn)
        calc_layout.addStretch()
        
        sep1 = QLabel(" | ")
        sep1.setStyleSheet("border: none; background: transparent; color: #94a3b8;")
        sep2 = QLabel(" | ")
        sep2.setStyleSheet("border: none; background: transparent; color: #94a3b8;")
        sep3 = QLabel(" | ")
        sep3.setStyleSheet("border: none; background: transparent; color: #94a3b8;")
        
        calc_layout.addWidget(self.panel_wt_lbl)
        calc_layout.addWidget(sep1)
        calc_layout.addWidget(self.wastage_wt_lbl)
        calc_layout.addWidget(sep2)
        calc_layout.addWidget(self.total_wt_lbl)
        calc_layout.addWidget(sep3)
        calc_layout.addWidget(self.cost_lbl)
        
        layout.addWidget(calc_frame)
        
        # --- Steel Table ---
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
        
        # --- Save Button ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_save = QPushButton("💾 Save Steel Specification")
        self.btn_save.setFixedWidth(250)
        self.btn_save.setStyleSheet("background-color: #10b981; color: white; font-weight: bold; padding: 10px; border-radius: 6px; border: none;")
        self.btn_save.clicked.connect(self.save_data)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def load_data(self, panel_id, p_len=0.0, p_hgt=0.0, p_dep=0.0, p_waste=0.0):
        self.panel_id = panel_id
        self.p_len = p_len
        self.p_hgt = p_hgt
        self.p_dep = p_dep
        self.p_waste = p_waste
        
        default_steel_cost = self.service.get_steel_unit_cost()
        if default_steel_cost > 0:
            self.unit_cost_input.setText(str(default_steel_cost))
            
        if not panel_id:
            self.table.setRowCount(0)
            self.calculate_weights()
            return

        self.table.blockSignals(True)
        rows = self.service.get_steel_configs_by_panel(self.panel_id)
        if not rows:
            self.service.create_steel_config(self.panel_id)
            rows = self.service.get_steel_configs_by_panel(self.panel_id)

        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                text = str(val) if val is not None else ""
                item = NumericTableWidgetItem(text)
                item.setFlags(item.flags() | Qt.ItemIsEditable if c >= 2 else item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()
        self.table.blockSignals(False)
        self.calculate_weights()

    def save_data(self):
        if not self.panel_id or self.table.rowCount() == 0:
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
                "PanelFace": get_text(11, "single"),
                "DoubleDoor": get_text(12, "No"),
                "DrawoutFixed": get_text(13, "No"),
                "ProtectionClass": get_text(14, "IP 44"),
                "CableEntry": get_text(15, "Top"),
                "Mounting": get_text(16, "free stand"),
                "SeatStand": get_text(17, "No"),
                "StandMetalSize": get_text(18, "0")
            }

            self.service.update_full_steel_config(steel_id, data)
            QMessageBox.information(self, "Success", "Steel specification saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save record: {e}")

    def calculate_weights(self):
        if self.table.rowCount() == 0:
            self.current_total_wt = 0.0
            self.panel_wt_lbl.setText("Panel Weight: 0.00 kg")
            self.wastage_wt_lbl.setText("Wastage Weight: 0.00 kg")
            self.total_wt_lbl.setText("Total Weight: 0.00 kg")
            return
        
        try:
            row = 0
            def get_val(c):
                item = self.table.item(row, c)
                return item.text().strip() if item else ""
            
            fb_qty = float(get_val(2) or 0)
            fb_size = get_val(3)
            sides_qty = float(get_val(4) or 0)
            sides_size = get_val(5)
            bt_qty = float(get_val(6) or 0)
            bt_size = get_val(7)
            
            import re
            def get_thick(s):
                m = re.search(r"(\d+(\.\d+)?)", s)
                return float(m.group(1)) if m else 0.0

            fb_t = get_thick(fb_size)
            sides_t = get_thick(sides_size)
            bt_t = get_thick(bt_size)
            
            density = 7850
            
            # Dimensions are in mm, volume in m^3 -> multiply by 1e-9
            # Multiplied by 2 because each category represents a pair of sheets (Front/Back, Bottom/Top, Left/Right Sides)
            fb_wt = fb_t * self.p_hgt * self.p_len * density * 1e-9 * fb_qty 
            bt_wt = bt_t * self.p_len * self.p_dep * density * 1e-9 * bt_qty 
            sides_wt = sides_t * self.p_dep * self.p_hgt * density * 1e-9 * sides_qty
            
            panel_wt = fb_wt + bt_wt + sides_wt
            
            if hasattr(self, 'p_waste') and self.p_waste > 0 and self.p_waste < 100:
                total_wt = panel_wt * 100.0 / (100.0 - self.p_waste)
                wastage_wt = total_wt - panel_wt
            else:
                total_wt = panel_wt
                wastage_wt = 0.0
                
            self.panel_wt_lbl.setText(f"Panel Weight: {panel_wt:.2f} kg")
            self.wastage_wt_lbl.setText(f"Wastage Weight: {wastage_wt:.2f} kg")
            self.total_wt_lbl.setText(f"Total Weight: {total_wt:.2f} kg")
            self.current_total_wt = total_wt
            
        except Exception as e:
            print(f"Weight calculation error: {e}")

    def calculate_steel_cost(self):
        if not hasattr(self, 'current_total_wt'):
            self.calculate_weights()
            
        try:
            unit_cost = float(self.unit_cost_input.text() or 0)
            total_cost = getattr(self, 'current_total_wt', 0.0) * unit_cost
            self.cost_lbl.setText(f"Total Cost: ₹{total_cost:,.2f}")
            
        except Exception as e:
            QMessageBox.critical(self, "Calculation Error", f"Failed to calculate cost: {e}")

    def _setup_delegates(self):
        from app.ui.quotations.panel_delegates import ComboBoxDelegate
        sizes = ["CRCA 1.2 mm", "CRCA 1.6 mm", "CRCA 2 mm", "CRCA 3 mm"]
        yn = ["No", "Yes"]
        seating = ["ISMC", "3 mm sheet", "Single value"]
        cable = ["Top", "Bottom", "Side", "Top&bottom"]
        mounting = ["Free Stand", "Wall"]
        in_out = ["Indoor", "Outdoor"]
        face = ["single", "double"]
        p_class = ["IP 44", "IP 45", "IP 55", "IP 65"]

        self.table.setItemDelegateForColumn(3, ComboBoxDelegate(self, items=sizes))
        self.table.setItemDelegateForColumn(5, ComboBoxDelegate(self, items=sizes))
        self.table.setItemDelegateForColumn(7, ComboBoxDelegate(self, items=sizes))
        self.table.setItemDelegateForColumn(8, ComboBoxDelegate(self, items=seating))
        self.table.setItemDelegateForColumn(9, ComboBoxDelegate(self, items=yn))
        self.table.setItemDelegateForColumn(10, ComboBoxDelegate(self, items=in_out))
        self.table.setItemDelegateForColumn(11, ComboBoxDelegate(self, items=face))
        self.table.setItemDelegateForColumn(12, ComboBoxDelegate(self, items=yn))
        self.table.setItemDelegateForColumn(13, ComboBoxDelegate(self, items=yn))
        self.table.setItemDelegateForColumn(14, ComboBoxDelegate(self, items=p_class))
        self.table.setItemDelegateForColumn(15, ComboBoxDelegate(self, items=cable))
        self.table.setItemDelegateForColumn(16, ComboBoxDelegate(self, items=mounting))
        self.table.setItemDelegateForColumn(17, ComboBoxDelegate(self, items=yn))

    def _handle_item_changed(self, item):
        self.table.blockSignals(True)
        row, col = item.row(), item.column()
        if not (2 <= col <= 18):
            self.table.blockSignals(False)
            return

        try:
            val = item.text().strip()
            if col in [2, 4, 6]:
                try:
                    val = int(val or 0)
                except ValueError:
                    val = "0"
                item.setText(str(val))
            item.setBackground(QColor(255, 255, 204)) # Light yellow
            self.calculate_weights()

        finally:
            self.table.blockSignals(False)

class PanelBBSelectorWidget(QWidget):
    """Widget to manage busbar specifications for a specific panel."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.panel_id = None
        self.service = QuotationService()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table = SearchableTable()
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels([
            "ID", "PanelID", "Neutral Rating", "Bus Section", "Section Qty", "Amps Req",
            "Amps Sel", "Clearence", "Qty PH", "Qty Nu", "Qty Earth",
            "BB Phase", "BB Neutral", "BB Earth"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table)

        self.btn_save = QPushButton("💾 Save Busbar Specification")
        self.btn_save.setStyleSheet("background-color: #0277bd; color: white; font-weight: bold; padding: 8px;")
        self.btn_save.clicked.connect(self.save_data)
        layout.addWidget(self.btn_save)

    def load_data(self, panel_id):
        self.panel_id = panel_id
        if not panel_id:
            self.table.setRowCount(0)
            return

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

    def save_data(self):
        if not self.panel_id or self.table.rowCount() == 0:
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
            QMessageBox.information(self, "Success", "Busbar specification saved successfully.")
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

        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.clicked.connect(self.copy_panel)
        
        self.paste_btn = QPushButton("📋 Paste")
        self.paste_btn.clicked.connect(self.paste_panel)

        header.addWidget(self.back_btn)
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.search_box)
        header.addWidget(self.add_btn)
        header.addWidget(self.edit_btn)
        header.addWidget(self.delete_btn)
        header.addWidget(self.copy_btn)
        header.addWidget(self.paste_btn)
        layout.addLayout(header)

        self.splitter = QSplitter(Qt.Vertical)
        
        # Top Panel for main table
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        self.table = SearchableTable()
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels([
            "ID", "QuoteID", "Category", "Serial", "Panel Name", "Qty", 
            "L (mm)", "H (mm)", "D (mm)", "Waste", "KA Rating", 
            "Earth Runs", "Stand", "Busbar Material"
        ])
        self.table.hideColumn(0)
        self.table.hideColumn(1)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows) # Select whole rows to trigger detail update
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.table.itemChanged.connect(self._handle_item_changed)
        
        # Connect selection change to load data into bottom tabs
        self.table.itemSelectionChanged.connect(self._on_panel_selection_changed)

        top_layout.addWidget(self.table)
        self.splitter.addWidget(top_widget)

        # Apply dropdown delegates for specific columns to allow inline selection
        self.table.setItemDelegateForColumn(12, ComboBoxDelegate(self, items=["Yes", "No"]))
        self.table.setItemDelegateForColumn(13, ComboBoxDelegate(self, items=["Aluminium", "Copper"]))
        self.table.setItemDelegateForColumn(10, ComboBoxDelegate(self, items=["7kA", "10kA", "16kA", "25kA", "36kA", "40kA", "50kA", "65kA", "100kA", "150KA"]))
        
        # Bottom Panels for Details (Stacked)
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        
        steel_group = QGroupBox("Steel Specification")
        steel_layout = QVBoxLayout(steel_group)
        self.steel_widget = SteelSelectorWidget(self)
        steel_layout.addWidget(self.steel_widget)
        
        bb_group = QGroupBox("Busbar Specification")
        bb_layout = QVBoxLayout(bb_group)
        self.bb_widget = PanelBBSelectorWidget(self)
        bb_layout.addWidget(self.bb_widget)
        
        details_layout.addWidget(steel_group)
        details_layout.addWidget(bb_group)
        
        self.splitter.addWidget(details_widget)
        self.splitter.setSizes([350, 350]) # Split roughly equal
        
        layout.addWidget(self.splitter)
        
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

    def _on_panel_selection_changed(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.steel_widget.load_data(None)
            self.bb_widget.load_data(None)
            return
            
        row = selected_items[0].row()
        panel_id_item = self.table.item(row, 0)
        if panel_id_item:
            panel_id = int(panel_id_item.text())
            
            def get_dim(col):
                try: return float(self.table.item(row, col).text())
                except: return 0.0
            
            p_len = get_dim(6)
            p_hgt = get_dim(7)
            p_dep = get_dim(8)
            p_waste = get_dim(9)

            self.steel_widget.load_data(panel_id, p_len, p_hgt, p_dep, p_waste)
            self.bb_widget.load_data(panel_id)

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
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Selection Required", "Please select panel(s) to delete.")
            return

        if QMessageBox.question(self, "Confirm Delete", 
                               f"Are you sure you want to delete {len(selected)} panel(s)?",
                               QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                for index in selected:
                    pid = int(self.table.item(index.row(), 0).text())
                    self.service.delete_panel(pid)
                QMessageBox.information(self, "Deleted", "Panel(s) removed successfully.")
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {e}")

    def copy_panel(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Selection Required", "Please select a panel to copy.")
            return
        row = selected[0].row()
        panel_id = int(self.table.item(row, 0).text())
        panel_name = self.table.item(row, 4).text()
        
        self.service.clipboard["type"] = "panel"
        self.service.clipboard["id"] = panel_id
        self.service.clipboard["name"] = panel_name
        QMessageBox.information(self, "Copied", f"Panel '{panel_name}' copied to clipboard.")

    def paste_panel(self):
        if not self.quote_id:
            QMessageBox.warning(self, "Error", "No quotation selected.")
            return
            
        if self.service.clipboard.get("type") != "panel" or not self.service.clipboard.get("id"):
            QMessageBox.warning(self, "Clipboard Empty", "No panel in clipboard to paste.")
            return
            
        try:
            self.service.copy_panel(self.service.clipboard["id"], self.quote_id)
            QMessageBox.information(self, "Pasted", "Panel pasted successfully.")
            self.refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to paste panel: {e}")

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
            
            item.setBackground(QColor(255, 255, 204)) # Light yellow
            
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