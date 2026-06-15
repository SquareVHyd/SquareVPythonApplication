from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QComboBox, QAbstractItemView, QMessageBox, QStatusBar, QHeaderView
)
from PySide6.QtCore import Qt, QTimer
from app.services.quotation_service import QuotationService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.utils.worker_thread import Worker

class ModuleItemsViewerDialog(QWidget):
    def __init__(self, parent_window=None):
        super().__init__(parent_window)
        self.main_window = parent_window # Store reference to the main window (QuotationDetailsPage/Window)
        self.quote_id = None
        self.initial_panel_id = None
        self.service = QuotationService()
        self.initial_pm_id = None

        self._panels_lookup = [] # (ID, QuoteID, PanelCategory, PanelSerial, PanelName, ...)
        self._panel_modules_lookup = [] # (ID, PanelID, PanelName, IngOg, PanelModQty, ModuleTypeID, Pnl_Module_Type, ...)
        self._module_items_cache = [] # Cache for the currently displayed module items

        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._worker = None

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        self.back_btn = QPushButton("⬅️ Back to Quotations")
        self.back_btn.clicked.connect(lambda: self.main_window.show_quotations())
        self.title_label = QLabel("Module Items Viewer")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(self.back_btn)
        header_layout.addWidget(self.title_label)

        # Top controls: Panel and Module selection
        top_controls_layout = QHBoxLayout()
        top_controls_layout.addWidget(QLabel("Select Panel:"))
        self.panel_combo = QComboBox()
        self.panel_combo.setMinimumWidth(200)
        self.panel_combo.currentIndexChanged.connect(self._on_panel_selected)
        top_controls_layout.addWidget(self.panel_combo)

        top_controls_layout.addWidget(QLabel("Select Module:"))
        self.module_combo = QComboBox()
        self.module_combo.setMinimumWidth(250)
        self.module_combo.setEnabled(False) # Disabled until a panel is selected
        self.module_combo.currentIndexChanged.connect(self._on_module_selected)
        top_controls_layout.addWidget(self.module_combo)

        top_controls_layout.addStretch()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search module items...")
        self.search_box.textChanged.connect(self._debounce_search)
        top_controls_layout.addWidget(self.search_box)

        layout.addLayout(header_layout) # Add the new header layout
        layout.addLayout(top_controls_layout) # Then the existing top controls

        # Table for Module Items
        self.table = SearchableTable()
        self.table.setColumnCount(14) # Based on tbl_ModuleItems schema
        self.table.setHorizontalHeaderLabels([
            "ID", "Drive Description", "BOM", "Unit Panel", "Make", "Model",
            "LP", "% Discount", "After Discount Price", "Total Price",
            "Total BOM Qty", "Selection", "PNL Name", "PNL Qty"
        ])

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)

    def load_viewer(self, quote_id, initial_panel_id=None, initial_pm_id=None):
        self.quote_id = quote_id
        self.initial_panel_id = initial_panel_id
        self.initial_pm_id = initial_pm_id
        self.title_label.setText(f"Module Items: Quote ID {quote_id}")
        self._load_panels()
        # Clear search box and table when loading new quote
        self.search_box.clear()

    def _load_panels(self):
        self.panel_combo.blockSignals(True)
        self.panel_combo.clear()
        self.panel_combo.addItem("--- Select a Panel ---", None)
        try:
            self._panels_lookup = self.service.get_panels_by_quote(self.quote_id)
            for panel in self._panels_lookup:
                self.panel_combo.addItem(f"{panel[4]} (ID: {panel[0]})", panel[0]) # PanelName (ID: PanelID)
            
            if self.initial_panel_id is not None:
                idx = self.panel_combo.findData(self.initial_panel_id)
                if idx >= 0: self.panel_combo.setCurrentIndex(idx)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load panels: {e}")
        finally:
            self.panel_combo.blockSignals(False)

    def _on_panel_selected(self):
        panel_id = self.panel_combo.currentData()
        self.module_combo.blockSignals(True)
        self.module_combo.clear()
        self.module_combo.addItem("--- Select a Module ---", None)
        self.module_combo.setEnabled(False)
        self._module_items_cache = []
        self._render_module_items([]) # Clear table

        if panel_id is not None:
            try:
                self._panel_modules_lookup = self.service.get_panel_modules_by_panel_id(panel_id)
                for pm in self._panel_modules_lookup:
                    # Display: IngOg - Pnl_Module_Type (PanelModQty) [ModuleID: pm.ID]
                    display_text = f"{pm[3]} - {pm[6]} ({pm[4]}) [ModuleID: {pm[0]}]"
                    self.module_combo.addItem(display_text, pm[0]) # Store PanelModule.ID as data
                self.module_combo.setEnabled(True)
                
                if self.initial_pm_id is not None:
                    idx = self.module_combo.findData(self.initial_pm_id)
                    if idx >= 0: self.module_combo.setCurrentIndex(idx)
                    self.initial_pm_id = None # Only auto-select once
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load modules for panel: {e}")
        self.module_combo.blockSignals(False)

    def _on_module_selected(self):
        panel_module_id = self.module_combo.currentData()
        self._module_items_cache = []
        self._render_module_items([]) # Clear table

        if panel_module_id is not None:
            # Find the selected panel module to get its ModuleTypeID
            selected_pm = next((pm for pm in self._panel_modules_lookup if pm[0] == panel_module_id), None)
            if selected_pm and len(selected_pm) > 5: # Ensure ModuleTypeID exists
                module_type_id = selected_pm[5] # ModuleTypeID is at index 5
                self._load_module_items_async(module_type_id)
            else:
                QMessageBox.warning(self, "Error", "Selected module details not found.")

    def _load_module_items_async(self, module_type_id):
        if self._worker: return
        self.status_bar.showMessage("Loading module items...")
        self._worker = Worker(self.service.get_module_items_by_module_type_id, module_type_id)
        self._worker.result.connect(self._on_module_items_loaded)
        self._worker.error.connect(self._on_load_error)
        self._worker.start()

    def _on_module_items_loaded(self, rows):
        self._module_items_cache = list(rows)
        self._render_module_items(self._module_items_cache)
        self.status_bar.showMessage(f"Found {len(rows)} module items", 5000)
        self._worker = None

    def _render_module_items(self, rows):
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = NumericTableWidgetItem(str(val) if val is not None else "")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable) # All items read-only
                self.table.setItem(r, c, item)
        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()
        self.table.blockSignals(False)

    def _on_load_error(self, err):
        QMessageBox.critical(self, "Database Error", f"Could not load module items: {err}")
        self._worker = None

    def _debounce_search(self):
        self._search_timer.stop() # Reset timer if text changes rapidly
        self._search_timer.start(300)

    def _perform_search(self):
        keyword = self.search_box.text().lower().strip()
        if not keyword:
            self._render_module_items(self._module_items_cache)
            return
        
        filtered = [
            row for row in self._module_items_cache 
            if any(keyword in str(c).lower() for c in row)
        ]
        self._render_module_items(filtered)