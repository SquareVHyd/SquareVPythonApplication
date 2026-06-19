from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QAbstractItemView, QMessageBox, QStatusBar, QDialog, QComboBox, QMenu
)
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QAction
from app.services.quotation_service import QuotationService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.utils.worker_thread import Worker
from app.ui.quotations.modules.panel_module_form import PanelModuleForm
from app.ui.quotations.modules.panel_module_preview_dialog import PanelModulePreviewDialog
from app.ui.quotations.module_items.module_items_viewer_dialog import ModuleItemsViewerDialog
from app.ui.quotations.panel_delegates import ComboBoxDelegate

# Shared dropdown lists for Panel Modules
INGOG_LIST = ["Incomer", "Outgoing", "R_Outgoing", "L_Outgoing", "Buscoupler", "Change Over", "Add-ON", "Sub-Incomer", "Sub-Outgoing", "Sub-Incomer-2", "Sub-Outgoing-2", "Busduct"]
POLE_LIST = ["4P", "3P", "2P", "1P", "4P B-Curve", "4P C-Curve", "4P D-Curve", "3P B-Curve", "3P C-Curve", "3P D-Curve", "2P B-Curve", "2P C-Curve", "2P D-Curve", "1P B-Curve", "1P C-Curve", "1P D-Curve", "A1", "A2", "R1", "A7", "2P/30 mA", "4P/30mA", "2P/100 mA", "4P/100mA", "2P/300 mA", "4P/300mA"]
KA_LIST = ["7kA", "10kA", "16kA", "25kA", "36kA", "40kA", "50kA", "65kA", "100kA"]
RELEASE_LIST = ["FTFM", "ATFM", "ATAM", "MP", "Motorised", "EDO", "MDO"]
PROTECTION_LIST = ["L", "LS", "LSI", "LSIG"]

class PanelModulePage(QWidget):
    def __init__(self, parent_window=None):
        super().__init__()
        self.main_window = parent_window
        self.quote_id = None
        self.service = QuotationService()
        self._cache = []
        self._panels_lookup = [] # To store (panel_id, panel_name) for dropdown
        self._module_types_map = {} # To store name -> ID mapping for inline editing
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._worker = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        
        self.back_btn = QPushButton("⬅️ Back to Quotations List") # Parent is QuotationDetailsPage
        self.back_btn.clicked.connect(lambda: self.main_window.show_quotations())
        
        self.title_label = QLabel("Quotation Panel Modules")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        # Panel selection for adding new modules
        self.panel_selection_combo = QComboBox()
        self.panel_selection_combo.setPlaceholderText("Select Panel for New Module")
        self.panel_selection_combo.setMinimumWidth(200)
        self.panel_selection_combo.currentIndexChanged.connect(self.refresh_table)

        self.preview_btn = QPushButton("👁️ Preview All Panels")
        self.preview_btn.clicked.connect(self._show_all_panels_preview)

        self.items_btn = QPushButton("📦 Items")
        self.items_btn.clicked.connect(self._show_module_items_viewer)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search modules...")
        self.search_box.textChanged.connect(self._debounce_search)

        self.add_btn = QPushButton("➕ Add Module")
        self.add_btn.clicked.connect(self.add_module)
        
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.clicked.connect(self.edit_module)
        
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self.delete_module)

        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.clicked.connect(self.copy_module)
        
        self.paste_btn = QPushButton("📋 Paste")
        self.paste_btn.clicked.connect(self.paste_module)

        header.addWidget(self.back_btn)
        header.addWidget(self.title_label)
        header.addWidget(self.panel_selection_combo)
        header.addWidget(self.preview_btn)
        header.addWidget(self.items_btn)
        header.addStretch()
        header.addWidget(self.search_box)
        header.addWidget(self.add_btn)
        header.addWidget(self.edit_btn)
        header.addWidget(self.delete_btn)
        header.addWidget(self.copy_btn)
        header.addWidget(self.paste_btn)
        layout.addLayout(header)

        self.table = SearchableTable()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "ID", "PanelID", "Panel Name", "In/Out", "Qty", 
            "TypeID", "Module Type", "Pole", "KA", "Release", "Protection", "Remark"
        ])
        self.table.hideColumn(0)
        self.table.hideColumn(1)
        self.table.hideColumn(5)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.itemDoubleClicked.connect(self.edit_module)
        self.table.itemChanged.connect(self._handle_item_changed)

        # Right-click context menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Apply dropdown delegates for specific columns
        self.table.setItemDelegateForColumn(3, ComboBoxDelegate(self, items=INGOG_LIST, editable=True))
        self.table.setItemDelegateForColumn(7, ComboBoxDelegate(self, items=POLE_LIST, editable=True))
        self.table.setItemDelegateForColumn(8, ComboBoxDelegate(self, items=KA_LIST, editable=True))
        self.table.setItemDelegateForColumn(9, ComboBoxDelegate(self, items=RELEASE_LIST, editable=True))
        self.table.setItemDelegateForColumn(10, ComboBoxDelegate(self, items=PROTECTION_LIST, editable=True))

        layout.addWidget(self.table)
        
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)

    def load_quotation(self, quote_id, project_name):
        self.quote_id = quote_id
        self.project_name = project_name
        self.title_label.setText(f"Modules: {project_name} (ID: {quote_id})")
        self._load_panels_for_dropdown()
        self._load_module_types()
        self.refresh_table()

    def clear_page(self):
        self.quote_id = None
        self.project_name = ""
        self.title_label.setText("Quotation Panel Modules")
        self.panel_selection_combo.clear()
        self.table.setRowCount(0)
        self._cache = []
        self.status_bar.clearMessage()

    def _load_panels_for_dropdown(self):
        self._panels_lookup = self.service.get_panels_by_quote(self.quote_id)
        self.panel_selection_combo.blockSignals(True)
        self.panel_selection_combo.clear()
        self.panel_selection_combo.addItem("Select Panel...", None)
        for panel in self._panels_lookup:
            self.panel_selection_combo.addItem(f"{panel[4]} (ID: {panel[0]})", panel[0])
        self.panel_selection_combo.blockSignals(False)

    def _load_module_types(self):
        try:
            types = self.service.get_module_costs_lookup()
            self._module_types_map = {t[1]: t[0] for t in types}
            module_types_list = [t[1] for t in types]
            self.table.setItemDelegateForColumn(6, ComboBoxDelegate(self, items=module_types_list, editable=False))
        except Exception as e:
            print(f"Error loading module types for delegate: {e}")

    def refresh_table(self):
        if self._worker or self.quote_id is None: return
        panel_id = self.panel_selection_combo.currentData()
        if panel_id is not None:
            self.status_bar.showMessage(f"Loading modules for panel ID: {panel_id}...")
            self._worker = Worker(self.service.get_panel_modules_by_panel_id, panel_id)
        else:
            self.status_bar.showMessage("Loading all panel modules...")
            self._worker = Worker(self.service.get_all_modules_by_quote, self.quote_id)
        self._worker.result.connect(self._on_data_loaded)
        self._worker.start()

    def _on_data_loaded(self, rows):
        self._cache = list(rows)
        self._render(self._cache)
        self.status_bar.showMessage(f"Found {len(rows)} modules", 5000)
        self._worker = None

    def _render(self, rows):
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        display_to_sql_map = {
            0: 0, 1: 1, 2: 2, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 10, 10: 11, 11: 12
        }
        editable_display_cols = {3, 4, 6, 7, 8, 9, 10, 11}
        for r, row in enumerate(rows):
            for display_col_idx in range(self.table.columnCount()):
                sql_col_idx = display_to_sql_map.get(display_col_idx)
                val = row[sql_col_idx] if sql_col_idx is not None and sql_col_idx < len(row) else ""
                item = NumericTableWidgetItem(str(val) if val is not None else "")
                if display_col_idx in editable_display_cols:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, display_col_idx, item)
        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()
        self.table.blockSignals(False)

    def _debounce_search(self): self._search_timer.start(300)
    def _perform_search(self):
        kw = self.search_box.text().lower().strip()
        self._render([r for r in self._cache if any(kw in str(c).lower() for c in r)] if kw else self._cache)

    def _get_dropdown_data(self):
        return {"ingog": INGOG_LIST, "pole": POLE_LIST, "ka": KA_LIST, "release": RELEASE_LIST, "protection": PROTECTION_LIST}

    def add_module(self):
        selected_panel_id = self.panel_selection_combo.currentData()
        if selected_panel_id is None:
            QMessageBox.warning(self, "Selection Required", "Please select a target panel from the dropdown to add a module.")
            return
        dialog = PanelModuleForm(self.quote_id, panel_id=selected_panel_id, parent=self, dropdown_lists=self._get_dropdown_data())
        if dialog.exec() == QDialog.Accepted:
            try:
                self.service.create_panel_module(**dialog.get_data())
                self._load_module_types()
                QMessageBox.information(self, "Success", "Panel module added successfully.")
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add panel module: {e}")

    def edit_module(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected: return
        row = selected[0].row()
        pm_id = int(self.table.item(row, 0).text())
        keys = ["id", "panel_id", "panel_name", "ing_og", "qty", "type_id", "type_name", "pole", "ka", "release", "protection", "remark"]
        data = {keys[i]: self.table.item(row, i).text() for i in range(len(keys))}
        dialog = PanelModuleForm(self.quote_id, pm_data=data, panel_id=int(data["panel_id"]), parent=self, dropdown_lists=self._get_dropdown_data())
        if dialog.exec() == QDialog.Accepted:
            try:
                self.service.update_panel_module(pm_id, **dialog.get_data())
                self._load_module_types()
                QMessageBox.information(self, "Success", "Panel module updated successfully.")
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update panel module: {e}")

    def delete_module(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected: return
        if QMessageBox.question(self, "Confirm", "Delete selected module(s)?") == QMessageBox.Yes:
            for idx in selected: self.service.delete_panel_module(int(self.table.item(idx.row(), 0).text()))
            self.refresh_table()

    def copy_module(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Selection Required", "Please select a module to copy.")
            return
        row = selected[0].row()
        module_id = int(self.table.item(row, 0).text())
        module_name = self.table.item(row, 6).text()
        
        self.service.clipboard["type"] = "module"
        self.service.clipboard["id"] = module_id
        self.service.clipboard["name"] = module_name
        QMessageBox.information(self, "Copied", f"Module '{module_name}' copied to clipboard.")

    def paste_module(self):
        target_panel_id = self.panel_selection_combo.currentData()
        if target_panel_id is None:
            QMessageBox.warning(self, "Error", "Please select a target panel from the dropdown to paste into.")
            return
            
        if self.service.clipboard.get("type") != "module" or not self.service.clipboard.get("id"):
            QMessageBox.warning(self, "Clipboard Empty", "No module in clipboard to paste.")
            return
            
        try:
            self.service.copy_panel_module(self.service.clipboard["id"], target_panel_id)
            QMessageBox.information(self, "Pasted", "Module pasted successfully.")
            self.refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to paste module: {e}")

    def _handle_item_changed(self, item):
        if not item or item.row() < 0: return
        self.table.blockSignals(True)
        row, col = item.row(), item.column()
        if col not in [3, 4, 6, 7, 8, 9, 10, 11]:
            self.table.blockSignals(False)
            return
        try:
            pm_id = int(self.table.item(row, 0).text())
            val = item.text().strip()
            if col == 6:
                type_id = self._module_types_map.get(val)
                if type_id is not None:
                    id_item = self.table.item(row, 5)
                    if id_item: id_item.setText(str(type_id))
                    self.service.update_panel_module_field(pm_id, "ModuleTypeID", type_id)
                self.table.blockSignals(False)
                return
            col_map = {3: "IngOg", 4: "PanelModQty", 7: "ModPole", 8: "ModKa", 9: "Release", 10: "Protection", 11: "Remark"}
            db_field = col_map.get(col)
            if col == 4:
                try: val = int(val or 1)
                except: val = 1; item.setText("1")
            self.service.update_panel_module_field(pm_id, db_field, val)
        except Exception as e:
            print(f"Inline update failed: {e}")
        finally: self.table.blockSignals(False)

    def _show_all_panels_preview(self):
        if self.quote_id is None:
            QMessageBox.warning(self, "No Quotation Selected", "Please select a quotation first.")
            return
        PanelModulePreviewDialog(self.quote_id, self.project_name, self).exec()

    def _show_context_menu(self, pos: QPoint):
        item = self.table.itemAt(pos)
        if not item: return
        row = item.row()
        pm_id = int(self.table.item(row, 0).text())
        panel_id = int(self.table.item(row, 1).text())
        module_type_name = self.table.item(row, 6).text()
        menu = QMenu(self)
        items_action = QAction(f"📦 View Items: {module_type_name}", self)
        items_action.triggered.connect(lambda: self._show_module_items_viewer(panel_id, pm_id))
        menu.addAction(items_action)
        menu.addSeparator()
        edit_action = QAction("✏️ Edit Module", self)
        edit_action.triggered.connect(self.edit_module)
        menu.addAction(edit_action)
        delete_action = QAction("🗑️ Delete Module", self)
        delete_action.triggered.connect(self.delete_module)
        menu.addAction(delete_action)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _show_module_items_viewer(self, panel_id=None, pm_id=None):
        if self.quote_id is None:
            QMessageBox.warning(self, "No Quotation Selected", "Please select a quotation first.")
            return
        self.main_window.show_items(initial_panel_id=panel_id, initial_pm_id=pm_id)