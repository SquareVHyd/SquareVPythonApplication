from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLineEdit, QLabel, QAbstractItemView, QMessageBox, QComboBox, QHeaderView, QInputDialog, QStatusBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QShortcut, QKeySequence
from app.services.module_service import ModuleService
from app.services.module_type_service import ModuleTypeService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.ui.modules.price_list_lookup_dialog import PriceListLookupDialog
from app.utils.worker_thread import Worker

class ModuleItemsDialog(QDialog):
    def __init__(self, module_type_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Module Item Manager"); self.resize(900, 600)
        self.module_service = ModuleService(); self.type_service = ModuleTypeService(); self.current_type_id = module_type_id
        self._cache = []; self._search_timer = QTimer(); self._search_timer.setSingleShot(True); self._search_timer.timeout.connect(self._perform_search); self._worker = None
        self.setup_ui(); self._load_types_and_initial_items()

    def setup_ui(self):
        layout = QVBoxLayout(self); top = QHBoxLayout()
        top.addWidget(QLabel("Module Type:")); self.type_combo = QComboBox(); self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        top.addWidget(self.type_combo, 1); self.search_box = QLineEdit(); self.search_box.setPlaceholderText("Search items..."); self.search_box.textChanged.connect(self._debounce_search)
        top.addWidget(self.search_box, 1); self.add_btn = QPushButton("➕ Add New Item"); self.add_btn.clicked.connect(self._add_items); top.addWidget(self.add_btn); layout.addLayout(top)
        self.table = SearchableTable(); self.table.setColumnCount(5); self.table.setHorizontalHeaderLabels(["SEQNo", "Item ID", "Description", "Qty", "ModuleItemID"])
        self.table.hideColumn(0); self.table.hideColumn(4); self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setSortingEnabled(True); self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.verticalHeader().setSectionsMovable(True); self.table.verticalHeader().sectionMoved.connect(lambda: self._update_visual_indices())
        self.table.horizontalHeader().sortIndicatorChanged.connect(lambda: self._update_visual_indices()); layout.addWidget(self.table)
        self.status_bar = QStatusBar(); layout.addWidget(self.status_bar)
        btns = QHBoxLayout(); self.edit_btn = QPushButton("✏️ Edit Qty/SEQ"); self.edit_btn.clicked.connect(self._edit_item); self.remove_btn = QPushButton("🗑️ Remove Selected"); self.remove_btn.clicked.connect(self._remove_items)
        btns.addWidget(self.edit_btn); btns.addWidget(self.remove_btn); btns.addStretch(); layout.addLayout(btns)
        self.table.itemSelectionChanged.connect(self._update_status_bar_stats)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self._add_items); QShortcut(QKeySequence("Ctrl+E"), self, activated=self._edit_item)
        QShortcut(QKeySequence("Delete"), self, activated=self._remove_items); QShortcut(QKeySequence("Ctrl+F"), self, activated=lambda: self.search_box.setFocus())

    def _load_types_and_initial_items(self):
        types = self.type_service.get_all_module_types(); self.type_combo.blockSignals(True)
        init_idx = -1
        for t in types:
            self.type_combo.addItem(f"{t[1]} ({t[2]})", t[0])
            if t[0] == self.current_type_id: init_idx = self.type_combo.count() - 1
        if init_idx != -1: self.type_combo.setCurrentIndex(init_idx)
        self.type_combo.blockSignals(False); self._load_items_async()

    def _on_type_changed(self): self.current_type_id = self.type_combo.currentData(); self._load_items_async()

    def _load_items_async(self):
        if self._worker: return
        self._worker = Worker(self.module_service.get_items_by_module_type, self.current_type_id)
        self._worker.result.connect(self._items_loaded); self._worker.error.connect(self._on_load_error); self._worker.start()

    def _items_loaded(self, rows): self._cache = list(rows); self._render(self._cache); self._worker = None

    def _render(self, rows):
        self.table.setSortingEnabled(False); self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row): self.table.setItem(r, c, NumericTableWidgetItem(str(val if val is not None else "")))
        self.table.setSortingEnabled(True); self._update_visual_indices()

    def _update_status_bar_stats(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel: self.status_bar.clearMessage(); return
        self.status_bar.showMessage(f"Count: {len(sel)}")

    def _update_visual_indices(self):
        self.table.blockSignals(True)
        try:
            cnt, lbls = self.table.rowCount(), [""] * self.table.rowCount()
            for v in range(cnt):
                l = self.table.verticalHeader().logicalIndex(v); num = str(v + 1); lbls[l] = num
                it = self.table.item(l, 0); 
                if it: it.setText(num)
            self.table.setVerticalHeaderLabels(lbls)
        finally: self.table.blockSignals(False)

    def closeEvent(self, event):
        self.table.blockSignals(True)
        try:
            cnt, items = self.table.rowCount(), []
            for v in range(cnt):
                l = self.table.verticalHeader().logicalIndex(v)
                items.append({"mid": int(self.table.item(l, 4).text()), "iid": int(self.table.item(l, 1).text()), "q": float(self.table.item(l, 3).text()), "s": v + 1})
            off = cnt + 1000
            for i in items: self.module_service.update_module(i["mid"], self.current_type_id, i["iid"], i["q"], i["s"] + off)
            for i in items: self.module_service.update_module(i["mid"], self.current_type_id, i["iid"], i["q"], i["s"])
        except Exception as e: print(f"Error saving: {e}")
        finally: self.table.blockSignals(False); super().closeEvent(event)

    def _on_load_error(self, err): QMessageBox.critical(self, "Error", str(err)); self._worker = None
    def _debounce_search(self): self._search_timer.start(300)
    def _perform_search(self):
        kw = self.search_box.text().lower()
        if not kw: self._render(self._cache); return
        self._render([r for r in self._cache if any(kw in str(c).lower() for c in [r[0], r[1], r[2], r[4]])])

    def _add_items(self):
        dialog = PriceListLookupDialog(self)
        if dialog.exec():
            sel, mx = dialog.selected_price_items, self.table.rowCount()
            for item in sel: mx += 1; self.module_service.create_module(self.current_type_id, item[0], 1, mx)
            self._load_items_async()

    def _edit_item(self):
        sel = self.table.selectedItems()
        if not sel: return
        row = sel[0].row()
        qty, ok = QInputDialog.getDouble(self, "Edit Quantity", "Enter Quantity:", float(self.table.item(row, 3).text()), 0, 1000000, 2)
        if ok: self.table.item(row, 3).setText(str(qty))

    def _remove_items(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel: return
        if QMessageBox.question(self, "Remove", f"Remove {len(sel)} items?") == QMessageBox.Yes:
            for i in sorted(sel, key=lambda x: x.row(), reverse=True): self.module_service.delete_module(int(self.table.item(i.row(), 4).text()))
            self._load_items_async()