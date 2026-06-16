from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, 
    QLabel, QAbstractItemView, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt
from app.services.quotation_service import QuotationService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem

class SelectModuleItemsDialog(QDialog):
    def __init__(self, target_mt_id, parent=None):
        super().__init__(parent)
        self.service = QuotationService()
        self.setWindowTitle("Select Module Items")
        self.target_mt_id = target_mt_id
        self.resize(1000, 600)
        self.setup_ui()
        self._load_makes()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        filters = QHBoxLayout()
        self.make_combo = QComboBox(); self.make_combo.setPlaceholderText("Select Make...")
        self.make_combo.currentTextChanged.connect(self._on_make_changed)
        
        self.type_combo = QComboBox(); self.type_combo.setPlaceholderText("Select Module Type...")
        self.type_combo.currentTextChanged.connect(self._load_items)
        
        self.search_box = QLineEdit(); self.search_box.setPlaceholderText("Search Item or SEQ...")
        self.search_box.textChanged.connect(self._filter_table)

        filters.addWidget(QLabel("Make:")); filters.addWidget(self.make_combo)
        filters.addWidget(QLabel("Module Type:")); filters.addWidget(self.type_combo)
        filters.addStretch(); filters.addWidget(QLabel("Filter:")); filters.addWidget(self.search_box)
        layout.addLayout(filters)

        self.table = SearchableTable(); self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Select", "SEQNo", "ItemDescription", "Qty", "Make", "ModuleType", "ModuleMake", "CatModSwg"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        self.add_sel_btn = QPushButton("Add Selected"); self.add_sel_btn.clicked.connect(self._add_selected)
        self.add_all_btn = QPushButton("Add All"); self.add_all_btn.clicked.connect(self._add_all)
        self.close_btn = QPushButton("Close"); self.close_btn.clicked.connect(self.reject)
        btns.addStretch(); btns.addWidget(self.add_sel_btn); btns.addWidget(self.add_all_btn); btns.addWidget(self.close_btn)
        layout.addLayout(btns)

    def _load_makes(self):
        self.make_combo.blockSignals(True); self.make_combo.clear()
        self.make_combo.addItems(self.service.get_vw_modules_full_makes())
        self.make_combo.blockSignals(False)

    def _on_make_changed(self, make):
        self.type_combo.blockSignals(True); self.type_combo.clear()
        if make: self.type_combo.addItems(self.service.get_vw_modules_full_types(make))
        self.type_combo.blockSignals(False)

    def _load_items(self):
        make, mt = self.make_combo.currentText(), self.type_combo.currentText()
        if not make or not mt: return
        self._raw_data = self.service.get_vw_modules_full_items(make, mt)
        self._render_table(self._raw_data)

    def _render_table(self, rows):
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            chk = NumericTableWidgetItem(""); chk.setCheckState(Qt.Unchecked)
            self.table.setItem(r, 0, chk)
            cols = ["SEQNo", "ItemDescription", "Qty", "Make", "ModuleType", "ModuleMake", "CatModSwg"]
            for c, key in enumerate(cols, 1):
                item = NumericTableWidgetItem(str(row.get(key, "")))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()

    def _filter_table(self, text):
        kw = text.lower()
        for r in range(self.table.rowCount()):
            match = kw in self.table.item(r, 1).text().lower() or kw in self.table.item(r, 2).text().lower()
            self.table.setRowHidden(r, not match)

    def _add_selected(self):
        items_to_add = []
        for r in range(self.table.rowCount()):
            if not self.table.isRowHidden(r) and self.table.item(r, 0).checkState() == Qt.Checked:
                items_to_add.append(self._raw_data[r])
        self._process_bulk(items_to_add)

    def _add_all(self):
        items_to_add = [self._raw_data[r] for r in range(self.table.rowCount()) if not self.table.isRowHidden(r)]
        self._process_bulk(items_to_add)

    def _process_bulk(self, items):
        if not items: return
        added, skipped = self.service.bulk_add_module_items_from_vw(items, self.target_mt_id)
        QMessageBox.information(self, "Success", f"{added} items added successfully.\n{skipped} items skipped because they already exist.")
        self.accept()