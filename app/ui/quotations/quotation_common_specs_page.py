from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QMessageBox, QStatusBar, QFormLayout, QLineEdit, QScrollArea, QComboBox
)
from PySide6.QtCore import Qt
from app.services.quotation_service import QuotationService
from app.ui.searchable_table import SearchableTable, NumericTableWidgetItem
from app.utils.worker_thread import Worker

class QuotationCommonSpecsPage(QWidget):
    def __init__(self, parent_window=None):
        super().__init__()
        self.main_window = parent_window
        self.quote_id = None
        self.service = QuotationService()
        self.spec_id = None # To store the ID of the common specs record
        self._worker = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        
        self.back_btn = QPushButton("⬅️ Back")
        self.back_btn.clicked.connect(lambda: self.main_window.show_quotations())

        self.title_label = QLabel("Quotation Common Specifications")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self._save_common_specs)

        header.addWidget(self.back_btn)
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.save_btn)
        layout.addLayout(header)

        # Use a ScrollArea for the form since there are many fields
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        container = QWidget()
        self.form_layout = QFormLayout()
        
        # Define standard values for dropdowns
        steel_values = [
            "2.0 mm(+/- 10%) Thick CRCA Sheet steel",
            "1.6 mm(+/- 10%) Thick CRCA Sheet steel",
            "3.0 mm(+/- 10%) Thick CRCA Sheet steel"
        ]

        self.frames_input = QComboBox(); self.frames_input.setEditable(True); self.frames_input.addItems(steel_values)
        self.partitions_input = QComboBox(); self.partitions_input.setEditable(True); self.partitions_input.addItems(steel_values)
        self.doors_input = QComboBox(); self.doors_input.setEditable(True); self.doors_input.addItems(steel_values)
        self.gland_plates_input = QComboBox(); self.gland_plates_input.setEditable(True); self.gland_plates_input.addItems(steel_values)
        
        self.system_input = QLineEdit()
        
        self.control_supply_input = QComboBox(); self.control_supply_input.setEditable(True)
        self.control_supply_input.addItems(["230 Vac/50Hz Phase & Neutral", "110 Vac/50Hz Phase & Neutral"])
        
        self.busbar_sleeves_input = QLineEdit()
        self.busbar_supports_input = QLineEdit()
        
        self.busbar_metal_input = QComboBox(); self.busbar_metal_input.setEditable(True)
        self.busbar_metal_input.addItems(["Aluminium", "Copper"])

        self.cd_al_input = QLineEdit()
        self.cd_cu_input = QLineEdit()
        self.painting_color_input = QLineEdit()

        self.form_layout.addRow("Frames:", self.frames_input)
        self.form_layout.addRow("Partitions:", self.partitions_input)
        self.form_layout.addRow("Doors:", self.doors_input)
        self.form_layout.addRow("Gland Plates:", self.gland_plates_input)
        self.form_layout.addRow("System:", self.system_input)
        self.form_layout.addRow("Control Supply:", self.control_supply_input)
        self.form_layout.addRow("Busbar Sleeves:", self.busbar_sleeves_input)
        self.form_layout.addRow("Busbar Supports:", self.busbar_supports_input)
        self.form_layout.addRow("Busbar Metal:", self.busbar_metal_input)
        self.form_layout.addRow("Current Density (AL):", self.cd_al_input)
        self.form_layout.addRow("Current Density (CU):", self.cd_cu_input)
        self.form_layout.addRow("Painting Color:", self.painting_color_input)

        container.setLayout(self.form_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)

    def load_quotation(self, quote_id, project_name):
        self.quote_id = quote_id
        self.spec_id = None # Reset spec_id
        self.title_label.setText(f"Common Specs: {project_name}")
        self.service.save_common_specs(quote_id) # Ensure record exists
        self._load_form_data()

    def _load_form_data(self):
        if self._worker or self.quote_id is None: return
        self._worker = Worker(self.service.get_common_specs_list, self.quote_id)
        self._worker.result.connect(self._on_data_loaded)
        self._worker.start()

    def _on_data_loaded(self, rows):
        if rows:
            data = rows[0] # Assuming one common specs record per quote
            self.spec_id = data[0]
            self.frames_input.setCurrentText(str(data[2]) if data[2] is not None else "")
            self.partitions_input.setCurrentText(str(data[3]) if data[3] is not None else "")
            self.doors_input.setCurrentText(str(data[4]) if data[4] is not None else "")
            self.gland_plates_input.setCurrentText(str(data[5]) if data[5] is not None else "")
            self.system_input.setText(str(data[6]) if data[6] is not None else "")
            self.control_supply_input.setCurrentText(str(data[7]) if data[7] is not None else "")
            self.busbar_sleeves_input.setText(str(data[8]) if data[8] is not None else "")
            self.busbar_supports_input.setText(str(data[9]) if data[9] is not None else "")
            self.busbar_metal_input.setCurrentText(str(data[10]) if data[10] is not None else "")
            self.cd_al_input.setText(str(data[11]) if data[11] is not None else "")
            self.cd_cu_input.setText(str(data[12]) if data[12] is not None else "")
            self.painting_color_input.setText(str(data[13]) if data[13] is not None else "")
        else:
            self.spec_id = None
            self.frames_input.clear()
            self.partitions_input.clear()
            self.doors_input.clear()
            self.gland_plates_input.clear()
            self.system_input.clear()
            self.control_supply_input.clear()
            self.busbar_sleeves_input.clear()
            self.busbar_supports_input.clear()
            self.busbar_metal_input.clear()
            self.cd_al_input.clear()
            self.cd_cu_input.clear()
            self.painting_color_input.clear()
        self._worker = None

    def _save_common_specs(self):
        if self.spec_id is None:
            QMessageBox.warning(self, "Error", "No common specifications record found to save.")
            return
        try:
            mapping = {
                "Frames": self.frames_input.currentText(),
                "Partitions": self.partitions_input.currentText(),
                "Doors": self.doors_input.currentText(),
                "GlandPlates": self.gland_plates_input.currentText(),
                "System": self.system_input.text(),
                "ControlSupply": self.control_supply_input.currentText(),
                "BusbarSleeves": self.busbar_sleeves_input.text(),
                "BusbarSupports": self.busbar_supports_input.text(),
                "BusbarMetal": self.busbar_metal_input.currentText(),
                "CurrentDensity_AL": self.cd_al_input.text(),
                "CurrentDensity_CU": self.cd_cu_input.text(),
                "PaintingColor": self.painting_color_input.text()
            }
            for col_name, value in mapping.items():
                self.service.update_common_specs_field(self.spec_id, col_name, value)
            QMessageBox.information(self, "Success", "Common specifications saved successfully.")
            self._load_form_data() # Reload to ensure UI is in sync
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Update failed: {e}")