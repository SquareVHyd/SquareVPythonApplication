from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QMessageBox)
from PySide6.QtGui import QDoubleValidator
from app.services.busbar_service import BusbarService

class BusbarForm(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.service = BusbarService()
        self.setWindowTitle("Busbar Details")
        self.setMinimumWidth(400)
        
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
        self.setStyleSheet(btn_style)
        
        layout = QVBoxLayout(self)
        
        self.run_input = QLineEdit()
        self.run_input.setValidator(QDoubleValidator(0, 100000, 2))
        self.width_input = QLineEdit()
        self.thick_input = QLineEdit()
        
        self.metal_combo = QComboBox()
        self.sleeve_combo = QComboBox()
        
        layout.addWidget(QLabel("Run Length:"))
        layout.addWidget(self.run_input)
        layout.addWidget(QLabel("Busbar Width:"))
        layout.addWidget(self.width_input)
        layout.addWidget(QLabel("Busbar Thickness:"))
        layout.addWidget(self.thick_input)
        layout.addWidget(QLabel("Metal Property:"))
        layout.addWidget(self.metal_combo)
        layout.addWidget(QLabel("Sleeve Size:"))
        layout.addWidget(self.sleeve_combo)
        
        self._populate_combos()

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        if data:
            self.run_input.setText(str(data[1]))
            self.width_input.setText(str(data[2]))
            self.thick_input.setText(str(data[3]))
            self._set_combo_id(self.metal_combo, data[4]) # MetalPropID
            self._set_combo_id(self.sleeve_combo, data[5]) # SlevID

    def _populate_combos(self):
        for m in self.service.get_metals():
            self.metal_combo.addItem(f"{m[1]} (Density: {m[2]})", m[0])
        for s in self.service.get_sleeves():
            self.sleeve_combo.addItem(f"{s[1]}x{s[2]} -> Sleeve: {s[3]}", s[0])

    def _set_combo_id(self, combo, id_val):
        idx = combo.findData(id_val)
        if idx >= 0: combo.setCurrentIndex(idx)

    def get_data(self):
        return {
            "run": float(self.run_input.text() or 0),
            "width": int(self.width_input.text() or 0),
            "thick": int(self.thick_input.text() or 0),
            "metal_id": self.metal_combo.currentData(),
            "sleeve_id": self.sleeve_combo.currentData()
        }