from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLineEdit, QLabel, QMessageBox, QMenu, QAbstractItemView, QApplication, QStatusBar)
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence, QDoubleValidator, QAction
from app.services.busbar_service import BusbarService
from app.ui.searchable_table import NumericTableWidgetItem, SearchableTable

class SleeveForm(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Sleeve Size")
        layout = QVBoxLayout(self)
        
        self.width_input = QLineEdit()
        self.width_input.setValidator(QDoubleValidator(0, 1000, 2))
        self.thick_input = QLineEdit()
        self.thick_input.setValidator(QDoubleValidator(0, 1000, 2))
        self.sw_input = QLineEdit()
        self.sw_input.setValidator(QDoubleValidator(0, 1000, 2))
        self.special_input = QLineEdit()
        self.special_input.setValidator(QDoubleValidator(0, 10000, 2))
        self.normal_input = QLineEdit()
        self.normal_input.setValidator(QDoubleValidator(0, 10000, 2))
        
        layout.addWidget(QLabel("BB Width:"))
        layout.addWidget(self.width_input)
        layout.addWidget(QLabel("BB Thick:"))
        layout.addWidget(self.thick_input)
        layout.addWidget(QLabel("Sleeve Width:"))
        layout.addWidget(self.sw_input)
        layout.addWidget(QLabel("Special Rate:"))
        layout.addWidget(self.special_input)
        layout.addWidget(QLabel("Normal Rate:"))
        layout.addWidget(self.normal_input)
        
        btns = QHBoxLayout()
        save = QPushButton("💾 Save")
        save.clicked.connect(self.accept)
        btns.addWidget(save)
        layout.addLayout(btns)
        
        if data:
            self.width_input.setText(str(data[1]))
            self.thick_input.setText(str(data[2]))
            self.sw_input.setText(str(data[3]))
            self.special_input.setText(str(data[4]))
            self.normal_input.setText(str(data[5]))

    def get_data(self):
        return {
            "b_width": float(self.width_input.text() or 0),
            "b_thick": float(self.thick_input.text() or 0),
            "s_width": float(self.sw_input.text() or 0),
            "s_rate": float(self.special_input.text() or 0),
            "n_rate": float(self.normal_input.text() or 0)
        }

class SleeveManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sleeve Sizes Manager")
        self.setMinimumWidth(700)
        self.service = BusbarService()
        
        self._cache = []
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        header = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search sleeves...")
        self.search_box.textChanged.connect(self.search)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        add_btn = QPushButton("➕ Add")
        self.edit_btn = QPushButton("✏️ Edit")
        self.delete_btn = QPushButton("🗑️ Delete")
        
        self.refresh_btn.clicked.connect(self.load_data)
        add_btn.clicked.connect(self.add_item)
        self.edit_btn.clicked.connect(self.edit_item)
        self.delete_btn.clicked.connect(self.delete_item)

        header.addWidget(self.search_box)
        header.addWidget(self.refresh_btn)
        header.addWidget(add_btn)
        header.addWidget(self.edit_btn)
        header.addWidget(self.delete_btn)
        self.layout.addLayout(header)

        self.table = SearchableTable()
        self.table.setStyleSheet("QTableView { selection-background-color: #93c5fd; selection-color: #000000; } QHeaderView::section { background-color: #fce4ec; border: 1px solid #e2e8f0; }")
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "BB Width", "BB Thick", "Sleeve Width", "Special Rate", "Normal Rate"])
        self.table.hideColumn(0)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        self.layout.addWidget(self.table)

        # Footer Status Bar for selection statistics
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("QStatusBar { background-color: #f8fafc; color: #475569; border-top: 1px solid #e2e8f0; font-size: 11px; }")
        self.layout.addWidget(self.status_bar)

        self.table.itemSelectionChanged.connect(self._update_status_bar_stats)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.add_item)
        QShortcut(QKeySequence("Ctrl+E"), self).activated.connect(self.edit_item)
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.load_data)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self.search_box.setFocus)
        QShortcut(QKeySequence(Qt.Key_Delete), self).activated.connect(self.delete_item)

    def _update_status_bar_stats(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.status_bar.clearMessage()
            return

        count = len(selected_rows)
        msg = f"Count: {count}"
        self.status_bar.showMessage(msg)

    def load_data(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self._cache = self.service.get_sleeves()
            self._render(self._cache)
        finally:
            QApplication.restoreOverrideCursor()

    def _render(self, rows):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table.setItem(i, j, NumericTableWidgetItem(str(val or "")))
        self.table.setSortingEnabled(True)
        self.table.fix_column_widths()

    def search(self):
        kw = self.search_box.text().lower()
        filtered = [r for r in self._cache if kw in " ".join(map(str, r)).lower()]
        self._render(filtered)

    def add_item(self):
        dialog = SleeveForm(self)
        if dialog.exec() == QDialog.Accepted:
            d = dialog.get_data()
            self.service.create_sleeve(d['b_width'], d['b_thick'], d['s_width'], d['s_rate'], d['n_rate'])
            self.load_data()

    def edit_item(self):
        sel = self.table.selectedItems()
        if not sel: return
        row_idx = sel[0].row()
        sleeve_id = int(self.table.item(row_idx, 0).text())
        
        # Find original row in cache
        orig_row = next(r for r in self._cache if r[0] == sleeve_id)
        dialog = SleeveForm(self, orig_row)
        if dialog.exec() == QDialog.Accepted:
            d = dialog.get_data()
            self.service.update_sleeve(sleeve_id, d['b_width'], d['b_thick'], d['s_width'], d['s_rate'], d['n_rate'])
            self.load_data()

    def delete_item(self):
        sel = self.table.selectedItems()
        if not sel: return
        sleeve_id = int(self.table.item(sel[0].row(), 0).text())
        if QMessageBox.question(self, "Delete", "Delete this sleeve size?") == QMessageBox.Yes:
            self.service.delete_sleeve(sleeve_id)
            self.load_data()

    def mouseDoubleClickEvent(self, event):
        self.edit_item()