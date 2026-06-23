from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QAbstractItemView, QMessageBox, QStatusBar, QDialog,
    QTextEdit, QComboBox, QMenu, QSplitter, QTabWidget, QGroupBox, QFrame,
    QStyledItemDelegate
)
from PySide6.QtCore import Qt, QTimer, QEvent, QPoint
from PySide6.QtGui import QShortcut, QKeySequence, QAction, QColor
import operator # For evaluating expressions


from app.services.quotation_service import QuotationService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.utils.worker_thread import Worker
from app.ui.quotations.panels.panel_form import PanelForm
from app.ui.quotations.panels.panel_delegates import ComboBoxDelegate

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
        self.quote_id = None
        self.service = QuotationService()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Calculation Block (Moved to Top) ---
        calc_frame = QFrame()
        calc_frame.setStyleSheet("QFrame { background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; }")
        calc_layout = QHBoxLayout(calc_frame)
        calc_layout.setContentsMargins(15, 10, 15, 10)
        
        self.lbl_panel_wt = QLabel("Panel Weight: 0.00 kg")
        self.lbl_panel_wt.setStyleSheet("border: none; background: transparent; color: #334155;")
        
        self.lbl_wastage_wt = QLabel("Wastage Weight: 0.00 kg")
        self.lbl_wastage_wt.setStyleSheet("border: none; background: transparent; color: #334155;")
        
        self.lbl_total_wt = QLabel("Total Weight: 0.00 kg")
        self.lbl_total_wt.setStyleSheet("border: none; background: transparent; color: #334155;")
        
        self.lbl_unit_cost = QLabel("Metal Unit Cost: ₹0.00")
        self.lbl_unit_cost.setStyleSheet("border: none; background: transparent; color: #334155;")
        
        self.lbl_unit_panel_cost = QLabel("Unit Panel Cost: ₹0.00")
        self.lbl_unit_panel_cost.setStyleSheet("border: none; background: transparent; font-weight: bold; color: #0f172a;")
        
        self.lbl_total_cost = QLabel("Total Cost: ₹0.00")
        self.lbl_total_cost.setStyleSheet("border: none; background: transparent; font-weight: bold; color: #dc2626; font-size: 14px;")
        
        calc_layout.addWidget(QLabel("<b>Steel Cost Summary:</b>"))
        calc_layout.addStretch()
        
        def sep():
            lbl = QLabel(" | ")
            lbl.setStyleSheet("border: none; background: transparent; color: #94a3b8;")
            return lbl
        
        calc_layout.addWidget(self.lbl_panel_wt)
        calc_layout.addWidget(sep())
        calc_layout.addWidget(self.lbl_wastage_wt)
        calc_layout.addWidget(sep())
        calc_layout.addWidget(self.lbl_total_wt)
        calc_layout.addWidget(sep())
        calc_layout.addWidget(self.lbl_unit_cost)
        calc_layout.addWidget(sep())
        calc_layout.addWidget(self.lbl_unit_panel_cost)
        calc_layout.addWidget(sep())
        calc_layout.addWidget(self.lbl_total_cost)
        
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
        # Ensure all columns visible with horizontal scrollbar; no internal vertical scroll
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
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
        
        default_steel_cost = self.service.get_metal_cost_from_quote(self.quote_id, "steel") if self.quote_id else 0.0
        # No input field to set text anymore, it auto-calculates in calculate_steel_cost
            
        if not panel_id:
            self.table.setRowCount(0)
            self._fit_table_height()
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
        self._fit_table_height()
        self.calculate_weights()

    def _fit_table_height(self):
        """Resize the table widget to show ALL rows with no internal vertical scrollbar."""
        header_h = self.table.horizontalHeader().height()
        row_count = self.table.rowCount()
        if row_count > 0:
            # Use actual row height; fall back to 30px if not yet laid out
            single_h = self.table.rowHeight(0)
            if single_h <= 0:
                single_h = 30
            rows_h = single_h * row_count
        else:
            rows_h = 0
        # Extra space: horizontal scrollbar (~22px) + borders (4px) + margins (8px) + 1 spare row (30px)
        extra = 22 + 4 + 8 + 30
        self.table.setFixedHeight(header_h + rows_h + extra)

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
            self.lbl_panel_wt.setText("Panel Weight: 0.00 kg")
            self.lbl_wastage_wt.setText("Wastage Weight: 0.00 kg")
            self.lbl_total_wt.setText("Total Weight: 0.00 kg")
            self.calculate_steel_cost()
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
                
            self.lbl_panel_wt.setText(f"Panel Weight: {panel_wt:.2f} kg")
            self.lbl_wastage_wt.setText(f"Wastage Weight: {wastage_wt:.2f} kg")
            self.lbl_total_wt.setText(f"Total Weight: {total_wt:.2f} kg")
            self.current_total_wt = total_wt
            self.calculate_steel_cost()
            
        except Exception as e:
            print(f"Weight calculation error: {e}")

    def calculate_steel_cost(self):
        if not hasattr(self, 'current_total_wt'):
            self.calculate_weights()
            
        try:
            unit_cost = self.service.get_metal_cost_from_quote(self.quote_id, "steel") if self.quote_id else 0.0
            total_weight = getattr(self, 'current_total_wt', 0.0)
            
            panel_qty = 1
            if self.panel_id:
                panel = self.service.get_panel_by_id(self.panel_id)
                if panel:
                    try:
                        panel_qty = int(panel.get("PanelQty", 1))
                    except ValueError:
                        pass
            
            unit_panel_cost = total_weight * unit_cost
            total_cost = unit_panel_cost * panel_qty
            
            self.lbl_unit_cost.setText(f"Metal Unit Cost: ₹{unit_cost:.2f}")
            self.lbl_unit_panel_cost.setText(f"Unit Panel Cost: ₹{unit_panel_cost:.2f}")
            self.lbl_total_cost.setText(f"Total Cost: ₹{total_cost:,.2f}")
            
        except Exception as e:
            QMessageBox.critical(self, "Calculation Error", f"Failed to calculate cost: {e}")

    def _setup_delegates(self):
        from app.ui.quotations.panels.panel_delegates import ComboBoxDelegate
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

class KeyValueComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, items=None):
        super().__init__(parent)
        self._items = items if items is not None else []

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        for k, v in self._items:
            editor.addItem(v, k)
        QTimer.singleShot(0, editor.showPopup)
        editor.installEventFilter(self)
        return editor

    def setEditorData(self, editor, index):
        current_id = index.model().data(index, Qt.UserRole)
        if current_id is not None:
            idx = editor.findData(current_id)
            if idx >= 0:
                editor.setCurrentIndex(idx)
                return
        text = index.model().data(index, Qt.EditRole)
        idx = editor.findText(str(text))
        if idx >= 0:
            editor.setCurrentIndex(idx)

    def setModelData(self, editor, model, index):
        idx = editor.currentIndex()
        if idx >= 0:
            text = editor.itemText(idx)
            user_data = editor.itemData(idx)
            model.setData(index, text, Qt.EditRole)
            model.setData(index, user_data, Qt.UserRole)

    def eventFilter(self, editor, event):
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.commitData.emit(editor)
            self.closeEditor.emit(editor, QStyledItemDelegate.NoHint)
            return True
        return super().eventFilter(editor, event)

class PanelBBSelectorWidget(QWidget):
    """Widget to manage busbar specifications for a specific panel."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.panel_id = None
        self.quote_id = None
        self.panel_length = 0.0  # default for ReqLength on new rows
        self.service = QuotationService()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table = SearchableTable()
        self.table.setColumnCount(21)
        self.table.setHorizontalHeaderLabels([
            "ID", "PanelID", "Req Length", "Neutral Rating", "Bus Section", "Section Qty", "Amps Req",
            "Amps Sel", "Clearence", "Qty PH", "Qty Nu", "Qty Earth",
            "BB Phase", "BB Neutral", "BB Earth",
            "Unit PH Kg", "Unit N Kg", "Unit Earth Kg",
            "Unit PH Length", "Unit N Length", "Unit Earth Length"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.itemChanged.connect(self._handle_bb_item_changed)
        # Ensure all columns visible with horizontal scrollbar; no internal vertical scroll
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        toolbar = QHBoxLayout()
        self.btn_add = QPushButton("➕ Add Row")
        self.btn_edit = QPushButton("✏️ Edit Row")
        self.btn_delete = QPushButton("🗑️ Delete Row")
        
        self.btn_add.clicked.connect(self.add_row)
        self.btn_edit.clicked.connect(self.edit_row)
        self.btn_delete.clicked.connect(self.delete_row)
        
        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_delete)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # --- Calculation Block (Moved to Top) ---
        calc_frame = QFrame()
        calc_frame.setStyleSheet("QFrame { background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; }")
        calc_layout = QHBoxLayout(calc_frame)
        calc_layout.setContentsMargins(15, 10, 15, 10)
        
        self.lbl_total_weight = QLabel("Total Weight: 0.00 kg")
        self.lbl_total_weight.setStyleSheet("border: none; background: transparent; color: #334155;")
        
        self.lbl_unit_cost = QLabel("Metal Unit Cost: ₹0.00")
        self.lbl_unit_cost.setStyleSheet("border: none; background: transparent; color: #334155;")
        
        self.lbl_unit_panel_cost = QLabel("Unit Panel Cost: ₹0.00")
        self.lbl_unit_panel_cost.setStyleSheet("border: none; background: transparent; font-weight: bold; color: #0f172a;")
        
        self.lbl_total_cost = QLabel("Total Cost: ₹0.00")
        self.lbl_total_cost.setStyleSheet("border: none; background: transparent; font-weight: bold; color: #dc2626; font-size: 14px;")
        
        calc_layout.addWidget(QLabel("<b>Busbar Cost Summary:</b>"))
        calc_layout.addStretch()
        
        sep1 = QLabel(" | ")
        sep1.setStyleSheet("border: none; background: transparent; color: #94a3b8;")
        sep2 = QLabel(" | ")
        sep2.setStyleSheet("border: none; background: transparent; color: #94a3b8;")
        sep3 = QLabel(" | ")
        sep3.setStyleSheet("border: none; background: transparent; color: #94a3b8;")
        
        calc_layout.addWidget(self.lbl_total_weight)
        calc_layout.addWidget(sep1)
        calc_layout.addWidget(self.lbl_unit_cost)
        calc_layout.addWidget(sep2)
        calc_layout.addWidget(self.lbl_unit_panel_cost)
        calc_layout.addWidget(sep3)
        calc_layout.addWidget(self.lbl_total_cost)
        
        layout.addWidget(calc_frame)
        
        layout.addWidget(self.table)
        
        # --- Save Button ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_save = QPushButton("💾 Save Busbar Specification")
        self.btn_save.setFixedWidth(250)
        self.btn_save.setStyleSheet("background-color: #10b981; color: white; font-weight: bold; padding: 10px; border-radius: 6px; border: none;")
        self.btn_save.clicked.connect(self.save_data)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def _fit_table_height(self):
        """Resize the table widget to show ALL rows with no internal vertical scrollbar."""
        header_h = self.table.horizontalHeader().height()
        row_count = self.table.rowCount()
        if row_count > 0:
            # Use actual row height; fall back to 30px if not yet laid out
            single_h = self.table.rowHeight(0)
            if single_h <= 0:
                single_h = 30
            rows_h = single_h * row_count
        else:
            rows_h = 0
        # Extra space: horizontal scrollbar (~22px) + borders (4px) + margins (8px) + 1 spare row (30px)
        extra = 22 + 4 + 8 + 30
        self.table.setFixedHeight(header_h + rows_h + extra)

    def load_data(self, panel_id, panel_length=0.0):
        self.panel_id = panel_id
        self.panel_length = panel_length
        if not panel_id:
            self.table.setRowCount(0)
            self._fit_table_height()
            return

        self.table.blockSignals(True)
        rows = self.service.get_panel_bb_configs_by_panel(self.panel_id)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            # DB columns: 0=ID,1=PanelID,2=NeutralRating,...,13=Select_BB_Earth,14=ReqLength
            # Table columns: 0=ID,1=PanelID,2=ReqLength,3=NeutralRating,...,14=BB_Earth,15-20=calculated
            for c, val in enumerate(row):
                if c == 14:
                    table_col = 2   # ReqLength beside PanelID
                elif c <= 1:
                    table_col = c   # ID, PanelID unchanged
                else:
                    table_col = c + 1  # shift all other DB cols by +1

                text = str(val) if val is not None else ""
                item = NumericTableWidgetItem(text)

                if c in [11, 12, 13] and val:  # BB Phase/Neutral/Earth IDs
                    try:
                        bb_id = int(val)
                        bb_size = self.service.get_bb_size_by_id(bb_id)
                        item.setText(bb_size)
                        item.setData(Qt.UserRole, bb_id)
                    except ValueError:
                        pass

                # Editable: ReqLength (table_col=2) and data cols 3-14; read-only: 0,1
                if table_col >= 2:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, table_col, item)

            # Calculated columns 15-20 (read-only)
            for tc in [15, 16, 17, 18, 19, 20]:
                item = NumericTableWidgetItem("0.00")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, tc, item)

            # qty_col, bb_col, kg_col, len_col  (all shifted +1 from DB col)
            self._recalc_unit_kg_and_length(r, 9, 12, 15, 18)   # PH
            self._recalc_unit_kg_and_length(r, 10, 13, 16, 19)  # Nu
            self._recalc_unit_kg_and_length(r, 11, 14, 17, 20)  # Earth

            # Initialize dropdowns if Amps Req is present (table col 6)
            amps_item = self.table.item(r, 6)
            if amps_item:
                self._update_bb_dropdowns(amps_item.text())

        self.table.fix_column_widths()
        self.table.blockSignals(False)
        self._fit_table_height()
        self._update_cost_summary()

    def _recalc_unit_kg_and_length(self, row, qty_col, bb_col, kg_target_col, len_target_col):
        qty_item = self.table.item(row, qty_col)
        bb_item = self.table.item(row, bb_col)
        kg_target_item = self.table.item(row, kg_target_col)
        len_target_item = self.table.item(row, len_target_col)
        
        if not kg_target_item:
            kg_target_item = NumericTableWidgetItem("0.00")
            kg_target_item.setFlags(kg_target_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, kg_target_col, kg_target_item)
            
        if not len_target_item:
            len_target_item = NumericTableWidgetItem("0.00")
            len_target_item.setFlags(len_target_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, len_target_col, len_target_item)
            
        qty = 0
        if qty_item and qty_item.text().strip():
            try:
                qty = int(qty_item.text().strip())
            except ValueError:
                pass
                
        kg_per_meter = 0.0
        run_length = 0.0
        if bb_item:
            bb_id = bb_item.data(Qt.UserRole)
            if bb_id is not None:
                try:
                    bb_id_int = int(bb_id)
                    kg_per_meter = self.service.get_bb_metal_kg_per_meter(bb_id_int)
                    run_length = self.service.get_bb_run_length(bb_id_int)
                except ValueError:
                    pass
                    
        total_kg = qty * kg_per_meter
        total_len = qty * run_length
        kg_target_item.setText(f"{total_kg:.2f}" if total_kg > 0 else "0.00")
        len_target_item.setText(f"{total_len:.2f}" if total_len > 0 else "0.00")

    def _handle_bb_item_changed(self, item):
        if not item:
            return
        row, col = item.row(), item.column()
        if col == 6:  # Amps Req is now table col 6 (DB col 5, shifted +1)
            self.table.blockSignals(True)
            self._update_bb_dropdowns(item.text())
            self.table.blockSignals(False)

        if col in [9, 12]:    # Qty PH (9) or BB Phase (12)
            self._recalc_unit_kg_and_length(row, 9, 12, 15, 18)
            self._update_cost_summary()
        elif col in [10, 13]: # Qty Nu (10) or BB Neutral (13)
            self._recalc_unit_kg_and_length(row, 10, 13, 16, 19)
            self._update_cost_summary()
        elif col in [11, 14]: # Qty Earth (11) or BB Earth (14)
            self._recalc_unit_kg_and_length(row, 11, 14, 17, 20)
            self._update_cost_summary()

    def _update_cost_summary(self):
        total_weight = 0.0
        for r in range(self.table.rowCount()):
            for c in [15, 16, 17]:  # Unit PH Kg, Unit N Kg, Unit Earth Kg
                item = self.table.item(r, c)
                if item and item.text().strip():
                    try:
                        total_weight += float(item.text().strip())
                    except ValueError:
                        pass
        
        metal_unit_cost = 0.0
        panel_qty = 1
        if self.panel_id:
            panel = self.service.get_panel_by_id(self.panel_id)
            if panel:
                metal = panel.get("BusbarMaterial", "Aluminium")
                if not metal:
                    metal = "Aluminium"
                metal_unit_cost = self.service.get_metal_cost_from_quote(self.quote_id, metal) if self.quote_id else 0.0
                try:
                    panel_qty = int(panel.get("PanelQty", 1))
                except ValueError:
                    panel_qty = 1
                
        unit_panel_cost = total_weight * metal_unit_cost
        total_cost = unit_panel_cost * panel_qty
        
        self.lbl_total_weight.setText(f"Total Weight: {total_weight:.2f} kg")
        self.lbl_unit_cost.setText(f"Metal Unit Cost: ₹{metal_unit_cost:.2f}")
        self.lbl_unit_panel_cost.setText(f"Unit Panel Cost: ₹{unit_panel_cost:.2f}")
        self.lbl_total_cost.setText(f"Total Cost: ₹{total_cost:.2f}")

    def _update_bb_dropdowns(self, amps_text):
        if not self.panel_id:
            return
        try:
            amps_req = float(amps_text.strip()) if amps_text.strip() else 0.0
            if amps_req > 0:
                panel = self.service.get_panel_by_id(self.panel_id)
                metal = panel.get("BusbarMaterial", "Aluminium") if panel else "Aluminium"
                sizes = self.service.get_bb_sizes_by_amps_and_metal(amps_req, metal)
                delegate_sizes = [("", "")] + [(bb_id, bb_size) for bb_id, bb_size in sizes]
                for c in [12, 13, 14]:  # BB Phase/Neutral/Earth now at cols 12,13,14
                    delegate = KeyValueComboBoxDelegate(self, items=delegate_sizes)
                    self.table.setItemDelegateForColumn(c, delegate)
        except ValueError:
            pass

    def add_row(self):
        if not self.panel_id:
            QMessageBox.warning(self, "Warning", "No panel selected.")
            return
        try:
            self.service.add_panel_bb_config(self.panel_id, req_length=self.panel_length)
            self.load_data(self.panel_id, self.panel_length)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add row: {e}")

    def edit_row(self):
        if not self.table.selectionModel().hasSelection():
            QMessageBox.warning(self, "Warning", "Please select a row to edit.")
            return
        row = self.table.currentRow()
        item = self.table.item(row, 2)
        if item:
            self.table.setCurrentItem(item)
            self.table.editItem(item)

    def delete_row(self):
        if not self.table.selectionModel().hasSelection():
            QMessageBox.warning(self, "Warning", "Please select a row to delete.")
            return
        row = self.table.currentRow()
        bb_id_item = self.table.item(row, 0)
        if not bb_id_item:
            return
        try:
            bb_id = int(bb_id_item.text())
            reply = QMessageBox.question(self, 'Confirm Delete', 'Are you sure you want to delete this specification?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.service.delete_panel_bb_config(bb_id)
                self.load_data(self.panel_id, self.panel_length)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete row: {e}")

    def save_data(self):
        if not self.panel_id or self.table.rowCount() == 0:
            return

        try:
            for row in range(self.table.rowCount()):
                bb_id_item = self.table.item(row, 0)
                if not bb_id_item:
                    continue
                bb_id = int(bb_id_item.text())
                
                def get_text(c, default):
                    item = self.table.item(row, c)
                    if not item: return default
                    if c in [12, 13, 14]:  # BB Phase/Neutral/Earth cols (shifted)
                        user_data = item.data(Qt.UserRole)
                        if user_data is not None:
                            return str(user_data)
                    val = item.text().strip()
                    return val if val else default

                def get_int(c, default):
                    item = self.table.item(row, c)
                    val = item.text().strip() if item else ""
                    try: return int(val) if val else default
                    except: return default

                def get_float(c, default):
                    item = self.table.item(row, c)
                    val = item.text().strip() if item else ""
                    try: return float(val) if val else default
                    except: return default

                data = {
                    "NeutralRating": get_int(3, 100),
                    "BusSection": get_text(4, "Main"),
                    "BusSectionQty": get_int(5, 1),
                    "AmpsRequested": get_int(6, 0),
                    "AmpsSelected": get_text(7, "0"),
                    "BusbarClearence": get_text(8, "Standard"),
                    "BB_QtyPH": get_int(9, 1),
                    "BB_QtyNu": get_int(10, 1),
                    "BB_QtyEarth": get_int(11, 1),
                    "Select_BB_Phase": get_text(12, ""),
                    "Select_BB_Neutral": get_text(13, ""),
                    "Select_BB_Earth": get_text(14, ""),
                    "ReqLength": get_float(2, self.panel_length)  # col 2 = Req Length
                }
                self.service.update_full_panel_bb_config(bb_id, data)

            QMessageBox.information(self, "Success", "Busbar specification saved successfully.")
            # Refresh the quotation-level busbar summary after saving
            p = self.parent()
            while p is not None:
                if isinstance(p, PanelPage):
                    p.bb_summary_widget.refresh()
                    break
                p = p.parent()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save record: {e}")

class BusbarSummaryWidget(QWidget):
    """Read-only summary table: unique busbar IDs + total quantities across all panels in the quotation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.quote_id = None
        self.service = QuotationService()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header row
        header = QHBoxLayout()
        title = QLabel("<b>Busbar Summary (All Panels in Quotation)</b>")
        title.setStyleSheet("font-size: 13px; color: #0f172a;")
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setFixedHeight(24)
        self.refresh_btn.clicked.connect(self.refresh)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        # Summary table
        self.table = SearchableTable()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["BB ID", "Busbar Size", "Total Qty"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        from PySide6.QtWidgets import QHeaderView
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

    def load(self, quote_id):
        self.quote_id = quote_id
        self.refresh()

    def refresh(self):
        if not self.quote_id:
            self.table.setRowCount(0)
            return
        try:
            rows = self.service.get_busbar_summary_by_quote(self.quote_id)
            self.table.blockSignals(True)
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                bb_id, bb_size, total_qty = row[0], row[1], row[2]
                id_item = NumericTableWidgetItem(str(bb_id) if bb_id is not None else "")
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
                size_item = NumericTableWidgetItem(str(bb_size) if bb_size is not None else "")
                size_item.setFlags(size_item.flags() & ~Qt.ItemIsEditable)
                qty_item = NumericTableWidgetItem(str(int(total_qty)) if total_qty is not None else "0")
                qty_item.setFlags(qty_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, 0, id_item)
                self.table.setItem(r, 1, size_item)
                self.table.setItem(r, 2, qty_item)
            self.table.resizeColumnsToContents()
            self.table.blockSignals(False)

            # Fit height to content (no internal scroll)
            row_count = max(len(rows), 1)
            hdr_h = self.table.horizontalHeader().height()
            row_h = self.table.rowHeight(0) if len(rows) > 0 else 26
            self.table.setFixedHeight(min(hdr_h + row_h * row_count + 10, 220))
        except Exception as e:
            print(f"BusbarSummaryWidget refresh error: {e}")
            self.table.setRowCount(0)


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
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # ── Header toolbar ────────────────────────────────────────────────────
        header = QHBoxLayout()
        self.back_btn = QPushButton("⬅️ Back to Quotations List")
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

        # ── Single scroll area containing ALL sections ─────────────────────
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        scroll_container = QWidget()
        scroll_layout = QVBoxLayout(scroll_container)
        scroll_layout.setContentsMargins(2, 2, 2, 2)
        scroll_layout.setSpacing(8)
        scroll.setWidget(scroll_container)
        layout.addWidget(scroll, 1)

        # ── Helper: build a non-collapsible section ───────────────────────────
        def make_section(title, content_widget, color="#0f172a", border="#e2e8f0"):
            frame = QFrame()
            frame.setFrameShape(QFrame.StyledPanel)
            frame.setStyleSheet(
                f"QFrame {{ border: 1px solid {border}; border-radius: 6px; "
                f"background-color: #ffffff; margin-bottom: 2px; }}"
            )
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(0, 0, 0, 0)
            frame_layout.setSpacing(0)

            # Section header bar (no collapse toggle)
            header_bar = QFrame()
            header_bar.setStyleSheet(
                f"QFrame {{ background-color: #f8fafc; border: none; "
                f"border-bottom: 1px solid {border}; border-radius: 0px; }}"
            )
            header_bar.setFixedHeight(36)
            hb_layout = QHBoxLayout(header_bar)
            hb_layout.setContentsMargins(10, 0, 10, 0)

            lbl = QLabel(f"<b>{title}</b>")
            lbl.setStyleSheet(
                f"border: none; background: transparent; color: {color}; font-size: 13px;"
            )

            hb_layout.addWidget(lbl)
            hb_layout.addStretch()
            frame_layout.addWidget(header_bar)

            # Content wrapper — always visible
            content_wrap = QWidget()
            cw_layout = QVBoxLayout(content_wrap)
            cw_layout.setContentsMargins(8, 8, 8, 8)
            cw_layout.setSpacing(0)
            cw_layout.addWidget(content_widget)
            frame_layout.addWidget(content_wrap)

            scroll_layout.addWidget(frame)
            return frame

        # ── Section 1: Panels List ────────────────────────────────────────────
        panels_container = QWidget()
        panels_layout = QVBoxLayout(panels_container)
        panels_layout.setContentsMargins(0, 0, 0, 0)
        panels_layout.setSpacing(4)

        self.table = SearchableTable()
        self.table.setStyleSheet("QTableView { selection-background-color: #fbcfe8; selection-color: black; }")
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels([
            "ID", "QuoteID", "Category", "Serial", "Panel Name", "Qty",
            "L (mm)", "H (mm)", "D (mm)", "Waste", "KA Rating",
            "Earth Runs", "Stand", "Busbar Material"
        ])
        self.table.hideColumn(0)
        self.table.hideColumn(1)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.table.itemChanged.connect(self._handle_item_changed)
        self.table.itemSelectionChanged.connect(self._on_panel_selection_changed)
        self.table.setMinimumHeight(180)
        # Ensure all columns visible with horizontal scrollbar
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        # Dropdown delegates
        self.table.setItemDelegateForColumn(12, ComboBoxDelegate(self, items=["Yes", "No"]))
        self.table.setItemDelegateForColumn(13, ComboBoxDelegate(self, items=["Aluminium", "Copper"]))
        self.table.setItemDelegateForColumn(10, ComboBoxDelegate(self, items=[
            "7kA", "10kA", "16kA", "25kA", "36kA", "40kA", "50kA", "65kA", "100kA", "150KA"
        ]))

        panels_layout.addWidget(self.table)
        make_section("📋 Panels List", panels_container, color="#0f172a", border="#cbd5e1")

        # ── Section 2: Steel Specification ───────────────────────────────────
        self.steel_widget = SteelSelectorWidget(self)
        make_section("🔩 Steel Specification", self.steel_widget, color="#166534", border="#bbf7d0")

        # ── Section 3: Busbar Specification ──────────────────────────────────
        self.bb_widget = PanelBBSelectorWidget(self)
        make_section("⚡ Busbar Specification", self.bb_widget, color="#1e40af", border="#bfdbfe")

        # ── Section 4: Busbar Summary (all panels in quotation) ───────────────
        self.bb_summary_widget = BusbarSummaryWidget(self)
        make_section("📊 Busbar Summary", self.bb_summary_widget, color="#0277bd", border="#90caf9")

        scroll_layout.addStretch()

        # ── Status bar ────────────────────────────────────────────────────────
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)

    def load_quotation(self, quote_id, project_name):
        """Update the page context and fetch data."""
        self.quote_id = quote_id
        self.steel_widget.quote_id = quote_id
        self.bb_widget.quote_id = quote_id
        self.title_label.setText(f"Panels: {project_name} (ID: {quote_id})")
        self.bb_summary_widget.load(quote_id)
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
        # Keep busbar summary in sync whenever panel data reloads
        self.bb_summary_widget.refresh()

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
            self.bb_widget.load_data(panel_id, p_len)

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