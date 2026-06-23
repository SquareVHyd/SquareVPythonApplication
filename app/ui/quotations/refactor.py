import re

with open(r'f:\python_project\sqv_180062026\SquareVPythonApplication\app\ui\quotations\panel_page.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update imports
content = content.replace(
    "QTextEdit, QComboBox, QMenu",
    "QTextEdit, QComboBox, QMenu, QSplitter, QTabWidget"
)

# 2. Add get_result to SumCalculatorDialog
content = content.replace(
    "    def accept(self):\n        \"\"\"Finalizes the sum before closing the dialog.\"\"\"\n        self._calculate()\n        super().accept()\n\n    def _calculate(self):",
    "    def accept(self):\n        \"\"\"Finalizes the sum before closing the dialog.\"\"\"\n        self._calculate()\n        super().accept()\n\n    def get_result(self):\n        return str(self.total)\n\n    def _calculate(self):"
)

# 3. Replace SteelSelectorDialog and PanelBBSelectorDialog with Widgets
new_widgets = """class SteelSelectorWidget(QWidget):
    \"\"\"Widget to manage steel specifications for a specific panel.\"\"\"
    def __init__(self, parent=None):
        super().__init__(parent)
        self.panel_id = None
        self.service = QuotationService()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

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

        self.btn_save = QPushButton("💾 Save Steel Specification")
        self.btn_save.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 8px;")
        self.btn_save.clicked.connect(self.save_data)
        layout.addWidget(self.btn_save)

    def load_data(self, panel_id):
        self.panel_id = panel_id
        if not panel_id:
            self.table.setRowCount(0)
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
        finally:
            self.table.blockSignals(False)

class PanelBBSelectorWidget(QWidget):
    \"\"\"Widget to manage busbar specifications for a specific panel.\"\"\"
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
"""

# Replace the block from SteelSelectorDialog up to PanelPage class
match = re.search(r"class SteelSelectorDialog.*?class PanelPage", content, flags=re.DOTALL)
if match:
    content = content[:match.start()] + new_widgets + "\nclass PanelPage" + content[match.end()-len("class PanelPage"):]

# 4. Modify PanelPage setup_ui to use QSplitter and QTabWidget
setup_ui_old = """        self.table = SearchableTable()
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
        layout.addWidget(self.status_bar)"""

setup_ui_new = """        self.splitter = QSplitter(Qt.Vertical)
        
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
        
        # Bottom Panel for Details (Tabs)
        self.tabs = QTabWidget()
        
        self.steel_widget = SteelSelectorWidget(self)
        self.tabs.addTab(self.steel_widget, "Steel Specification")
        
        self.bb_widget = PanelBBSelectorWidget(self)
        self.tabs.addTab(self.bb_widget, "Busbar Specification")
        
        self.splitter.addWidget(self.tabs)
        self.splitter.setSizes([400, 300]) # Example default sizes
        
        layout.addWidget(self.splitter)
        
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)"""

content = content.replace(setup_ui_old, setup_ui_new)

# 5. Remove context menu functions and add _on_panel_selection_changed
content = re.sub(
    r"    def _show_context_menu\(self, pos: QPoint\):.*?def add_panel\(self\):",
    """    def _on_panel_selection_changed(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.steel_widget.load_data(None)
            self.bb_widget.load_data(None)
            return
            
        row = selected_items[0].row()
        panel_id_item = self.table.item(row, 0)
        if panel_id_item:
            panel_id = int(panel_id_item.text())
            self.steel_widget.load_data(panel_id)
            self.bb_widget.load_data(panel_id)

    def add_panel(self):""",
    content,
    flags=re.DOTALL
)

with open(r'f:\python_project\sqv_180062026\SquareVPythonApplication\app\ui\quotations\panel_page.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Refactoring complete.")
