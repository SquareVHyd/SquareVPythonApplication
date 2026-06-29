from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QComboBox, QAbstractItemView, QMessageBox, QStatusBar, QHeaderView, QDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QShortcut, QKeySequence
from sqlalchemy import text
from app.config.database import get_session
from app.services.quotation_service import QuotationService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.ui.quotations.panels.panel_delegates import ComboBoxDelegate, SpinBoxDelegate, DoubleSpinBoxDelegate
from app.ui.quotations.module_items.module_item_form import ModuleItemForm
from app.ui.quotations.module_items.select_module_items_dialog import SelectModuleItemsDialog
from app.utils.worker_thread import Worker

class ModuleItemsViewerDialog(QWidget):
    def __init__(self, parent_window=None):
        super().__init__()
        self.main_window = parent_window
        self.quote_id = None
        self.initial_panel_id = None
        self.initial_pm_id = None
        self.service = QuotationService()
        self._panels_lookup = []
        self._panel_modules_lookup = []
        self._cache = []
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._worker = None
        self.setup_ui()
        self.table.itemChanged.connect(self._handle_item_changed)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        btn_style = """
            QPushButton {
                background-color: #e0f2fe;
                color: #0c4a6e;
                border: 1px solid #bae6fd;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #bae6fd; }
            QPushButton:pressed { background-color: #7dd3fc; }
            QPushButton:disabled { background-color: transparent; color: #94a3b8; border: none; }
            QComboBox {
                background-color: white;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 5px 12px;
                font-size: 13px;
                color: #0f172a;
            }
            QComboBox::drop-down {
                border-left: 1px solid #cbd5e1;
                width: 24px;
            }
        """
        self.setStyleSheet(self.styleSheet() + btn_style)

        
        header = QHBoxLayout()
        self.back_btn = QPushButton("⬅️ Back")
        self.back_btn.clicked.connect(lambda: self.main_window.show_quotations())
        self.title_label = QLabel("Module Items Viewer")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.panel_combo = QComboBox(); self.panel_combo.setPlaceholderText("Select Panel..."); self.panel_combo.setMinimumWidth(180)
        self.panel_combo.currentIndexChanged.connect(self._on_panel_changed)
        self.module_combo = QComboBox(); self.module_combo.setPlaceholderText("Select Module..."); self.module_combo.setMinimumWidth(220)
        self.module_combo.currentIndexChanged.connect(self._on_module_changed)
        self.search_box = QLineEdit(); self.search_box.setPlaceholderText("Search items...")
        self.search_box.textChanged.connect(self._debounce_search)
        header.addWidget(self.back_btn); header.addWidget(self.title_label); header.addWidget(QLabel("Panel:"))
        header.addWidget(self.panel_combo); header.addWidget(QLabel("Module:")); header.addWidget(self.module_combo)
        header.addStretch(); header.addWidget(self.search_box); layout.addLayout(header)
        actions = QHBoxLayout()
        self.add_btn = QPushButton("➕ Add Item"); self.add_btn.clicked.connect(self._add_item)
        self.add_from_mod_btn = QPushButton("📂 Add From Module")
        self.add_from_mod_btn.clicked.connect(self._add_from_module)
        
        self.edit_btn = QPushButton("✏️ Edit Item"); self.edit_btn.clicked.connect(self._edit_item)
        self.delete_btn = QPushButton("🗑️ Delete Item")
        self.delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #fee2e2;
                        color: #991b1b;
                        border: 1px solid #fecaca;
                        padding: 6px 12px;
                        border-radius: 4px;
                        font-weight: bold;
                        font-size: 13px;
                    }
                    QPushButton:hover { background-color: #fecaca; }
                    QPushButton:pressed { background-color: #fca5a5; }
                    QPushButton:disabled { background-color: transparent; color: #94a3b8; border: none; }
                """); self.delete_btn.clicked.connect(self._delete_item)
        
        actions.addWidget(self.add_btn); actions.addWidget(self.add_from_mod_btn); actions.addWidget(self.edit_btn); actions.addWidget(self.delete_btn)
        actions.addStretch(); layout.addLayout(actions)
        self.table = SearchableTable(); self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "DriveDescription", "Make", "BOM", "LP", "%Discount", "Total Amount"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive); self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setItemDelegateForColumn(3, DoubleSpinBoxDelegate(self, min_val=0.0))
        self.table.setItemDelegateForColumn(4, DoubleSpinBoxDelegate(self, min_val=0.0))
        self.table.setItemDelegateForColumn(5, DoubleSpinBoxDelegate(self, min_val=0.0, max_val=100.0))
        
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self.table)
        
        # Summary footer
        self.summary_frame = QWidget()
        self.summary_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 4px;")
        summary_layout = QHBoxLayout(self.summary_frame)
        summary_layout.setContentsMargins(10, 10, 10, 10)
        self.summary_lbl = QLabel("Overall Discount: 0.00% | Total List Price: ₹0.00 | Total Price: ₹0.00")
        self.summary_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1e293b;")
        summary_layout.addStretch()
        summary_layout.addWidget(self.summary_lbl)
        layout.addWidget(self.summary_frame)
        
        self.status_bar = QStatusBar(); layout.addWidget(self.status_bar)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self._add_item)
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self._edit_item)
        QShortcut(QKeySequence("Delete"), self, activated=self._delete_item)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=lambda: self.search_box.setFocus())

    def load_viewer(self, quote_id, initial_panel_id=None, initial_pm_id=None):
        self.quote_id, self.initial_panel_id, self.initial_pm_id = quote_id, initial_panel_id, initial_pm_id
        self.title_label.setText(f"Module Items: Quote ID {quote_id}"); self._load_panels()

    def _load_panels(self):
        self.panel_combo.blockSignals(True); self.panel_combo.clear()
        self.panel_combo.addItem("--- All Panels (Summary) ---", None)
        self._panels_lookup = self.service.get_panels_by_quote(self.quote_id)
        for p in self._panels_lookup: self.panel_combo.addItem(f"{p[4]} (Qty: {p[5]})", p[0])
        if self.initial_panel_id:
            idx = self.panel_combo.findData(self.initial_panel_id)
            if idx >= 0: self.panel_combo.setCurrentIndex(idx)
            self.initial_panel_id = None
        self.panel_combo.blockSignals(False); self._on_panel_changed()

    def _on_panel_changed(self):
        panel_id = self.panel_combo.currentData()
        self.module_combo.blockSignals(True); self.module_combo.clear()
        self._panel_modules_lookup = []
        if panel_id is not None:
            self.module_combo.addItem("--- All Modules (Summary) ---", None)
            self._panel_modules_lookup = self.service.get_panel_modules_by_panel_id(panel_id)
            for pm in self._panel_modules_lookup: self.module_combo.addItem(f"{pm[7]} - {pm[4]}", pm[0])
            if self.initial_pm_id:
                idx = self.module_combo.findData(self.initial_pm_id)
                if idx >= 0: self.module_combo.setCurrentIndex(idx)
                self.initial_pm_id = None
        self.module_combo.blockSignals(False); self._on_module_changed()

    def _on_module_changed(self):
        self._load_items_async()

    def _load_items_async(self):
        if self._worker: return
        panel_id = self.panel_combo.currentData()
        pm_id = self.module_combo.currentData()

        # Update button states: disable CRUD for summary view
        is_summary = (pm_id is None)
        self.add_btn.setEnabled(not is_summary)
        self.add_from_mod_btn.setEnabled(not is_summary)
        self.edit_btn.setEnabled(not is_summary)
        self.delete_btn.setEnabled(not is_summary)

        def fetch_data():
            with get_session() as session:
                if pm_id is not None:
                    # Single Module Logic
                    selected_pm = next((pm for pm in self._panel_modules_lookup if pm[0] == pm_id), None)
                    if not selected_pm: return [], 1, 1, "", 0
                    pnl_qty, mod_qty = int(selected_pm[3] or 1), int(selected_pm[5] or 1)
                    pnl_name = self.panel_combo.currentText().split(" (Qty:")[0]
                    sql = text("""SELECT mi."ID", mi."DriveDescription", mi."BOM", mi."LP", mi."%Discount", pl."Make", pl."Model" FROM public."tbl_ModuleItems" mi LEFT JOIN public."vwPriceList" pl ON mi."DriveDescription" = pl."ItemDescription" WHERE mi."ID" = :pm_id""")
                    rows = session.execute(sql, {"pm_id": pm_id}).fetchall()
                    return rows, pnl_qty, mod_qty, pnl_name, pm_id
                else:
                    # Aggregated Summary Logic (Combine items across all modules in quote or panel)
                    where_clause = 'p."QuoteID" = :tid' if panel_id is None else 'p."ID" = :tid'
                    sql = text(f"""
                        SELECT 
                            0 as "ID",
                            mi."DriveDescription",
                            SUM(
                                COALESCE(p."PanelQty", 1) * 
                                COALESCE(pm."PanelModQty", 1) *
                                CASE 
                                    WHEN mi."BOM" IS NOT NULL AND mi."BOM" <> 0 THEN mi."BOM" 
                                    ELSE 1
                                END
                            ) as "TotalBOM",
                            MAX(mi."LP") as "LP",
                            MAX(mi."%Discount") as "Discount",
                            MAX(pl."Make") as "Make",
                            MAX(pl."Model") as "Model"
                        FROM public."tbl_Panels" p
                        JOIN public."tbl_PanelModules" pm ON p."ID" = pm."PanelID"
                        JOIN public."tbl_ModuleItems" mi ON pm."ID" = mi."ID"
                        LEFT JOIN public."vwPriceList" pl ON mi."DriveDescription" = pl."ItemDescription"
                        WHERE {where_clause}
                        GROUP BY mi."DriveDescription"
                        ORDER BY mi."DriveDescription"
                    """)
                    rows = session.execute(sql, {"tid": self.quote_id if panel_id is None else panel_id}).fetchall()
                    return rows, 1, 1, "Combined Summary", 0

        self._worker = Worker(fetch_data)
        self._worker.result.connect(self._items_loaded); self._worker.error.connect(self._on_load_error); self._worker.start()

    def _items_loaded(self, result):
        rows, pnl_qty, mod_qty, pnl_name, pm_id_for_status = result
        is_summary = (pm_id_for_status == 0)
        self.table.blockSignals(True); self._cache = []; self.table.setSortingEnabled(False)
        self.table.clearContents(); self.table.setRowCount(0); self.table.setRowCount(len(rows))
        self.table.setColumnHidden(0, is_summary)
        for r, row in enumerate(rows):
            pm_id_row, desc, bom, lp, disc, make, model = row
            bom_val = float(bom) if (bom is not None and float(bom) != 0) else float(mod_qty)
            if not is_summary:
                # If not summary, the query gives us item BOM but we need to account for mod_qty if it's default 0/null
                bom_val = float(bom) if (bom is not None and float(bom) != 0) else float(mod_qty)
            else:
                # If summary, the query ALREADY calculated TotalBOM
                bom_val = float(bom) if bom is not None else 0.0

            lp_val, disc_val = float(lp or 0), float(disc or 0)
            total_amount = bom_val * lp_val * (1 - disc_val)
            
            data = [pm_id_row, desc, str(make or ""), bom_val, lp_val, f"{disc_val*100:.2f}%", f"₹{total_amount:,.2f}"]
            self._cache.append(row)
            for c, val in enumerate(data):
                item = NumericTableWidgetItem(str(val))
                if (not is_summary and c in {3, 4, 5}) or (is_summary and c in {4, 5}): 
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                else: item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if c == 0: item.setData(Qt.UserRole, (pm_id_row, desc))
                self.table.setItem(r, c, item)
        self._update_summary_labels()
        self.table.setSortingEnabled(True); self.table.resizeColumnsToContents(); self.table.blockSignals(False)
        msg = f"Loaded {len(rows)} unique items (Summary view)" if is_summary else f"Loaded {len(rows)} items for panel module ID: {pm_id_for_status}"
        self.status_bar.showMessage(msg)
        self._worker = None

    def _update_summary_labels(self):
        sum_lp = 0.0
        sum_total = 0.0
        
        self.table.blockSignals(True)
        was_sorting = self.table.isSortingEnabled()
        if was_sorting:
            self.table.setSortingEnabled(False)
            
        def safe_num(text, default=0.0):
            try: return float(text.replace('₹', '').replace(',', '').replace('%', '').strip() or default)
            except: return default

        for r in range(self.table.rowCount()):
            bom = safe_num(self.table.item(r, 3).text(), 0.0)
            lp = safe_num(self.table.item(r, 4).text(), 0.0)
            disc = safe_num(self.table.item(r, 5).text(), 0.0) / 100.0
            
            row_lp = bom * lp
            row_total = row_lp * (1 - disc)
            
            sum_lp += row_lp
            sum_total += row_total
            
            self.table.item(r, 6).setText(f"₹{row_total:,.2f}")

        if was_sorting:
            self.table.setSortingEnabled(True)

        overall_disc = ((sum_lp - sum_total) / sum_lp * 100) if sum_lp > 0 else 0.0
        self.summary_lbl.setText(
            f"Overall Discount: {overall_disc:.2f}%  |  "
            f"Total List Price: ₹{sum_lp:,.2f}  |  "
            f"Total Price: ₹{sum_total:,.2f}"
        )
        self.table.blockSignals(False)

    def _handle_item_changed(self, item):
        col = item.column()
        if col not in {3, 4, 5}: return
        self.table.blockSignals(True)
        try:
            row = item.row()
            pk_data = self.table.item(row, 0).data(Qt.UserRole)
            if not pk_data: return
            is_summary = (pk_data[0] == 0)
            def safe_num(text, default=1.0):
                try: return float(text.replace('₹', '').replace(',', '').replace('%', '').strip() or default)
                except: return default
            
            bom = safe_num(self.table.item(row, 3).text(), 1.0)
            lp = safe_num(self.table.item(row, 4).text(), 0.0)
            disc = safe_num(self.table.item(row, 5).text(), 0.0) / 100.0
            
            if is_summary:
                # Bulk Update across the current scope (Quote or Panel)
                panel_id = self.panel_combo.currentData()
                where_clause = 'p."QuoteID" = :tid' if panel_id is None else 'p."ID" = :tid'
                sql = text(f"""
                    UPDATE public."tbl_ModuleItems"
                    SET "LP" = :lp, "%Discount" = :disc
                    WHERE "DriveDescription" = :desc
                    AND "ID" IN (
                        SELECT pm."ID"
                        FROM public."tbl_PanelModules" pm
                        JOIN public."tbl_Panels" p ON pm."PanelID" = p."ID"
                        WHERE {where_clause}
                    )
                """)
                with get_session() as session:
                    session.execute(sql, {
                        "lp": lp,
                        "disc": disc,
                        "desc": pk_data[1], # DriveDescription
                        "tid": self.quote_id if panel_id is None else panel_id
                    })
                    session.commit()
            else:
                self.service.update_module_item(pm_id, desc, bom, lp, disc)
                
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, self._update_summary_labels)
        except Exception as e: print(f"Error during inline update: {e}")
        finally: self.table.blockSignals(False)

    def _add_from_module(self):
        pm_id = self.module_combo.currentData()
        selected_pm = next((pm for pm in self._panel_modules_lookup if pm[0] == pm_id), None)
        if not selected_pm: return
        dialog = SelectModuleItemsDialog(target_pm_id=pm_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self._load_items_async()

    def _add_item(self):
        pm_id = self.module_combo.currentData()
        selected_pm = next((pm for pm in self._panel_modules_lookup if pm[0] == pm_id), None)
        if not selected_pm: return
        # Extract PanelModQty from index 5 of the selected panel module lookup data
        mod_qty = float(selected_pm[5] or 1.0)
        dialog = ModuleItemForm(pm_id, module_item_data={"bom": mod_qty}, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                try: self.service.create_module_item(**data); self._load_items_async()
                except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def _edit_item(self):
        selected = self.table.selectedItems()
        if not selected: return
        row = selected[0].row(); pk_data = self.table.item(row, 0).data(Qt.UserRole)
        # Indices match setup_ui: 0:ID, 1:Desc, 2:Make, 3:BOM, 4:LP, 5:Disc
        current_data = {
            "module_type_id": pk_data[0], 
            "drive_description": pk_data[1], 
            "bom": float(self.table.item(row, 3).text() or 1.0), 
            "lp": float(self.table.item(row, 4).text() or 0.0), 
            "discount": float(self.table.item(row, 5).text().replace('%', '') or 0.0) / 100.0, 
            "sequence_number": row + 1
        }
        dialog = ModuleItemForm(pk_data[0], module_item_data=current_data, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                try: self.service.update_module_item(pk_data[0], pk_data[1], **data); self._load_items_async()
                except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def _delete_item(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected: return
        if QMessageBox.question(self, "Remove", "Remove selected item(s)?") == QMessageBox.Yes:
            try:
                for idx in sorted(selected, key=lambda x: x.row(), reverse=True):
                    pk = self.table.item(idx.row(), 0).data(Qt.UserRole); self.service.delete_module_item(pk[0], pk[1])
                self._load_items_async()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def _show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item: return
        
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        replace_action = menu.addAction("🔄 Replace Item (Across Quote)")
        
        action = menu.exec(self.table.mapToGlobal(pos))
        if action == replace_action:
            self._replace_item_across_quote(item.row())

    def _replace_item_across_quote(self, row):
        pk_data = self.table.item(row, 0).data(Qt.UserRole)
        if not pk_data: return
        
        pm_id, old_desc = pk_data
        
        # Prepare data for ModuleItemForm
        def safe_num(text, default=1.0):
            try: return float(text.replace('₹', '').replace(',', '').replace('%', '').strip() or default)
            except: return default

        current_data = {
            "module_type_id": pm_id,
            "drive_description": old_desc,
            "bom": safe_num(self.table.item(row, 3).text(), 1.0),
            "lp": safe_num(self.table.item(row, 4).text(), 0.0),
            "discount": safe_num(self.table.item(row, 5).text(), 0.0) / 100.0,
            "sequence_number": row + 1
        }
        
        dialog = ModuleItemForm(pm_id, module_item_data=current_data, parent=self)
        dialog.setWindowTitle("Replace Item Across Quotation")
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                try:
                    self.service.replace_module_item_across_panels(
                        self.quote_id, 
                        old_desc, 
                        data["drive_description"], 
                        data["bom"], 
                        data["lp"], 
                        data["discount"]
                    )
                    self._load_items_async()
                    QMessageBox.information(self, "Success", f"Replaced '{old_desc}' with '{data['drive_description']}' across the quotation.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))

    def _debounce_search(self): self._search_timer.start(300)
    
    def _perform_search(self):
        kw = self.search_box.text().lower().strip()
        if not kw: self._on_module_changed(); return
        for r in range(self.table.rowCount()):
            match = any(kw in self.table.item(r, c).text().lower() for c in range(self.table.columnCount()))
            self.table.setRowHidden(r, not match)
    def _on_load_error(self, err): QMessageBox.critical(self, "Database Error", f"Failed to load items: {err}"); self._worker = None