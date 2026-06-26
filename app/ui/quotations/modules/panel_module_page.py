from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QAbstractItemView, QMessageBox, QStatusBar, QDialog, QComboBox, QMenu, QSplitter
)
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QAction
from app.services.quotation_service import QuotationService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.utils.worker_thread import Worker
from app.ui.quotations.modules.panel_module_form import PanelModuleForm
from app.ui.quotations.modules.panel_module_preview_dialog import PanelModulePreviewDialog
from app.ui.quotations.module_items.module_items_viewer_dialog import ModuleItemsViewerDialog
from app.ui.quotations.panels.panel_delegates import ComboBoxDelegate, DoubleSpinBoxDelegate
from app.ui.quotations.module_items.module_item_form import ModuleItemForm
from app.ui.quotations.module_items.select_module_items_dialog import SelectModuleItemsDialog

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
        
        self.table.itemSelectionChanged.connect(self._on_module_selection_changed)

        # Add a splitter to contain both tables vertically
        self.splitter = QSplitter(Qt.Vertical)
        
        # Modules table wrapper
        self.modules_wrapper = QWidget()
        modules_layout = QVBoxLayout(self.modules_wrapper)
        modules_layout.setContentsMargins(0, 0, 0, 0)
        modules_layout.addWidget(self.table)
        
        # Items table wrapper
        self.items_wrapper = QWidget()
        items_layout = QVBoxLayout(self.items_wrapper)
        items_layout.setContentsMargins(0, 0, 0, 0)
        
        items_header = QHBoxLayout()
        self.items_label = QLabel("Module Items")
        self.items_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        items_header.addWidget(self.items_label)
        
        items_header.addStretch()
        self.item_add_btn = QPushButton("➕ Add Item")
        self.item_add_btn.clicked.connect(self._add_item)
        self.item_add_from_mod_btn = QPushButton("📂 Add From Module")
        self.item_add_from_mod_btn.clicked.connect(self._add_from_module)
        self.item_edit_btn = QPushButton("✏️ Edit Item")
        self.item_edit_btn.clicked.connect(self._edit_item)
        self.item_del_btn = QPushButton("🗑️ Delete Item")
        self.item_del_btn.clicked.connect(self._delete_item)
        
        items_header.addWidget(self.item_add_btn)
        items_header.addWidget(self.item_add_from_mod_btn)
        items_header.addWidget(self.item_edit_btn)
        items_header.addWidget(self.item_del_btn)
        
        items_layout.addLayout(items_header)
        
        self.items_table = SearchableTable()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels(["ID", "Description", "Make", "BOM", "LP", "Disc", "Amount"])
        self.items_table.hideColumn(0)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # Apply delegates for inline editing
        self.items_table.setItemDelegateForColumn(3, DoubleSpinBoxDelegate(self, min_val=0.0))
        self.items_table.setItemDelegateForColumn(4, DoubleSpinBoxDelegate(self, min_val=0.0))
        self.items_table.setItemDelegateForColumn(5, DoubleSpinBoxDelegate(self, min_val=0.0, max_val=100.0))
        self.items_table.itemChanged.connect(self._handle_module_item_changed)
        items_layout.addWidget(self.items_table)
        
        self.splitter.addWidget(self.modules_wrapper)
        self.splitter.addWidget(self.items_wrapper)
        
        # Replace the direct widget addition with splitter
        layout.addWidget(self.splitter)
        
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
        self.items_table.setRowCount(0)
        self.items_label.setText("Module Items")
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

    def _on_module_selection_changed(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            self.items_table.setRowCount(0)
            self.items_label.setText("Module Items")
            return
            
        row = selected[0].row()
        pm_id_str = self.table.item(row, 0).text()
        if not pm_id_str:
            return
        pm_id = int(pm_id_str)
        mt_name = self.table.item(row, 6).text()
        m_qty_str = self.table.item(row, 4).text()
        m_qty = float(m_qty_str) if m_qty_str else 1.0
        
        self.items_label.setText(f"Module Items: {mt_name}")
        
        self._items_worker = Worker(self.service.get_module_items_by_panel_module_id, pm_id)
        self._items_worker.result.connect(lambda items: self._render_items(items, m_qty))
        self._items_worker.start()

    def _render_items(self, items, m_qty):
        self.items_table.blockSignals(True)
        self.items_table.setSortingEnabled(False)
        self.items_table.clearContents()
        self.items_table.setRowCount(0)
        self.items_table.setRowCount(len(items))
        for r, item in enumerate(items):
            # item is tuple: (ID, Desc, BOM, LP, Disc, Make, Amount)
            self.items_table.setItem(r, 0, NumericTableWidgetItem(str(item[0])))
            self.items_table.setItem(r, 1, NumericTableWidgetItem(str(item[1])))
            self.items_table.setItem(r, 2, NumericTableWidgetItem(str(item[5] or "")))
            
            bom = float(item[2]) if item[2] else 0.0
            bom_val = bom if bom != 0.0 else m_qty
            
            self.items_table.setItem(r, 3, NumericTableWidgetItem(str(bom_val)))
            self.items_table.setItem(r, 4, NumericTableWidgetItem(f"{item[3]:,.2f}" if item[3] else "0.00"))
            self.items_table.setItem(r, 5, NumericTableWidgetItem(f"{item[4]*100:.1f}%" if item[4] else "0.0%"))
            self.items_table.setItem(r, 6, NumericTableWidgetItem(f"{item[6]:,.2f}" if item[6] else "0.00"))
            
            for c in range(7):
                it = self.items_table.item(r, c)
                if it:
                    if c in {3, 4, 5}:
                        it.setFlags(it.flags() | Qt.ItemIsEditable)
                    else:
                        it.setFlags(it.flags() & ~Qt.ItemIsEditable)
        
        self.items_table.setSortingEnabled(True)
        self.items_table.resizeColumnsToContents()
        self.items_table.blockSignals(False)
        self._items_worker = None

    def _get_selected_module_info(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected: return None
        row = selected[0].row()
        pm_id_str = self.table.item(row, 0).text()
        if not pm_id_str: return None
        pm_id = int(pm_id_str)
        m_qty_str = self.table.item(row, 4).text()
        m_qty = float(m_qty_str) if m_qty_str else 1.0
        return pm_id, m_qty

    def _add_item(self):
        info = self._get_selected_module_info()
        if not info: return
        pm_id, m_qty = info
        
        dialog = ModuleItemForm(pm_id, module_item_data={"bom": m_qty}, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                try: 
                    self.service.create_module_item(
                        data["module_type_id"],
                        data["drive_description"],
                        data["bom"],
                        data["lp"],
                        data["discount"]
                    )
                    self._on_module_selection_changed()
                except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def _add_from_module(self):
        info = self._get_selected_module_info()
        if not info: return
        pm_id, _ = info
        
        dialog = SelectModuleItemsDialog(target_pm_id=pm_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self._on_module_selection_changed()

    def _edit_item(self):
        info = self._get_selected_module_info()
        if not info: return
        pm_id, _ = info
        
        selected = self.items_table.selectionModel().selectedRows()
        if not selected: return
        row = selected[0].row()
        
        desc = self.items_table.item(row, 1).text()
        bom = float(self.items_table.item(row, 3).text() or 1.0)
        lp = float(self.items_table.item(row, 4).text().replace(',', '') or 0.0)
        disc = float(self.items_table.item(row, 5).text().replace('%', '') or 0.0) / 100.0

        current_data = {
            "module_type_id": pm_id, 
            "drive_description": desc, 
            "bom": bom, 
            "lp": lp, 
            "discount": disc
        }
        
        dialog = ModuleItemForm(pm_id, module_item_data=current_data, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                try: 
                    self.service.update_module_item(
                        pm_id, desc,
                        data["module_type_id"],
                        data["drive_description"],
                        data["bom"],
                        data["lp"],
                        data["discount"]
                    )
                    self._on_module_selection_changed()
                except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def _delete_item(self):
        info = self._get_selected_module_info()
        if not info: return
        pm_id, _ = info
        
        selected = self.items_table.selectionModel().selectedRows()
        if not selected: return
        
        if QMessageBox.question(self, "Remove", "Remove selected item(s)?") == QMessageBox.Yes:
            try:
                for idx in sorted(selected, key=lambda x: x.row(), reverse=True):
                    desc = self.items_table.item(idx.row(), 1).text()
                    self.service.delete_module_item(pm_id, desc)
                self._on_module_selection_changed()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def _handle_module_item_changed(self, item):
        col = item.column()
        if col not in {3, 4, 5}: return
        
        info = self._get_selected_module_info()
        if not info: return
        pm_id, _ = info

        self.items_table.blockSignals(True)
        try:
            row = item.row()
            desc = self.items_table.item(row, 1).text()
            
            def safe_num(text, default=1.0):
                try: return float(text.replace('₹', '').replace(',', '').replace('%', '').strip() or default)
                except: return default
            
            bom = safe_num(self.items_table.item(row, 3).text(), 1.0)
            lp = safe_num(self.items_table.item(row, 4).text(), 0.0)
            disc = safe_num(self.items_table.item(row, 5).text(), 0.0) / 100.0
            
            self.service.update_module_item(pm_id, desc, pm_id, desc, bom, lp, disc)
            amt = bom * lp * (1 - disc)
            it_amt = self.items_table.item(row, 6)
            
            def deferred_ui_update():
                if it_amt: it_amt.setText(f"{amt:g}")
                self._update_cost_summary()

            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, deferred_ui_update)
            
        except Exception as e:
            print(f"Error handling module item edit: {e}")
        finally:
            self.items_table.blockSignals(False)

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