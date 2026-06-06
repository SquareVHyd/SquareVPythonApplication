from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLineEdit, QLabel, QMessageBox, QMenu, QAbstractItemView, QApplication)
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence, QDoubleValidator, QAction
from app.services.busbar_service import BusbarService
from app.ui.searchable_table import NumericTableWidgetItem, SearchableTable

class MetalForm(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Metal Property")
        layout = QVBoxLayout(self)
        
        self.metal_input = QLineEdit()
        self.density_input = QLineEdit()
        self.density_input.setValidator(QDoubleValidator(0, 100, 4))
        self.curr_density_input = QLineEdit()
        self.curr_density_input.setValidator(QDoubleValidator(0, 100, 4))
        self.cost_input = QLineEdit()
        self.cost_input.setValidator(QDoubleValidator(0, 10000, 2))
        
        layout.addWidget(QLabel("Metal Name:"))
        layout.addWidget(self.metal_input)
        layout.addWidget(QLabel("Density (mm3 to Kg factor):"))
        layout.addWidget(self.density_input)
        layout.addWidget(QLabel("Current Density:"))
        layout.addWidget(self.curr_density_input)
        layout.addWidget(QLabel("Unit Cost/Kg:"))
        layout.addWidget(self.cost_input)
        
        btns = QHBoxLayout()
        save = QPushButton("Save")
        save.clicked.connect(self.accept)
        btns.addWidget(save)
        layout.addLayout(btns)
        
        if data:
            self.metal_input.setText(str(data[1]))
            self.density_input.setText(str(data[2]))
            self.curr_density_input.setText(str(data[3]))
            self.cost_input.setText(str(data[4]))
            
            # Disable density fields during editing to prevent accidental calculation shifts
            self.density_input.setEnabled(False)
            self.curr_density_input.setEnabled(False)

    def get_data(self):
        return {
            "metal": self.metal_input.text().strip(),
            "density": float(self.density_input.text() or 0),
            "curr_density": float(self.curr_density_input.text() or 0),
            "cost": float(self.cost_input.text() or 0)
        }

class MetalManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Metal Properties Manager")
        self.setMinimumWidth(600)
        self.service = BusbarService()
        
        # Use a list to store data for filtering
        self._cache = []
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        header = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search metals...")
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
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Metal", "Density", "Curr Density", "Unit Cost"])
        self.table.hideColumn(0)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        self.layout.addWidget(self.table)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.add_item)
        QShortcut(QKeySequence("Ctrl+E"), self).activated.connect(self.edit_item)
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.load_data)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self.search_box.setFocus)
        QShortcut(QKeySequence(Qt.Key_Delete), self).activated.connect(self.delete_item)

    def load_data(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self._cache = self.service.get_metals()
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
        dialog = MetalForm(self)
        if dialog.exec() == QDialog.Accepted:
            d = dialog.get_data()
            self.service.create_metal(d['metal'], d['density'], d['curr_density'], d['cost'])
            self.load_data()

    def edit_item(self):
        sel = self.table.selectedItems()
        if not sel: return
        row_idx = sel[0].row()
        metal_id = int(self.table.item(row_idx, 0).text())
        
        # Find original row in cache
        orig_row = next(r for r in self._cache if r[0] == metal_id)
        dialog = MetalForm(self, orig_row)
        if dialog.exec() == QDialog.Accepted:
            d = dialog.get_data()
            self.service.update_metal(metal_id, d['metal'], d['density'], d['curr_density'], d['cost'])
            self.load_data()

    def delete_item(self):
        sel = self.table.selectedItems()
        if not sel: return
        metal_id = int(self.table.item(sel[0].row(), 0).text())
        if QMessageBox.question(self, "Delete", "Delete this metal property?") == QMessageBox.Yes:
            self.service.delete_metal(metal_id)
            self.load_data()

    def mouseDoubleClickEvent(self, event):
        self.edit_item()