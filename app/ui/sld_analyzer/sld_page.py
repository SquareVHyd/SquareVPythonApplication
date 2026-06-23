from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QScrollArea, QFrame, QPushButton
)
from PySide6.QtCore import Qt
from app.services.sld_service import SldAnalyzerService
from app.ui.sld_analyzer.panel_view_widget import PanelCardWidget

class SldPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = SldAnalyzerService()
        self.setup_ui()
        self.load_quotations()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header Area
        header_layout = QHBoxLayout()
        title = QLabel("📏 SLD Analyzer")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0f172a;")
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setFixedWidth(100)
        self.refresh_btn.clicked.connect(self.load_quotations)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)
        main_layout.addLayout(header_layout)

        # Controls Area
        controls_frame = QFrame()
        controls_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #cbd5e1; border-radius: 8px; }")
        controls_layout = QHBoxLayout(controls_frame)
        
        controls_layout.addWidget(QLabel("<b>Select Quotation:</b>"))
        
        self.quote_combo = QComboBox()
        self.quote_combo.setMinimumWidth(400)
        self.quote_combo.currentIndexChanged.connect(self.on_quotation_selected)
        controls_layout.addWidget(self.quote_combo)
        controls_layout.addStretch()
        
        main_layout.addWidget(controls_frame)

        # Scroll Area for Panels
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #f8fafc; }")
        
        self.panels_container = QWidget()
        self.panels_container.setStyleSheet("background-color: #f8fafc;")
        self.panels_layout = QVBoxLayout(self.panels_container)
        self.panels_layout.setAlignment(Qt.AlignTop)
        
        self.scroll_area.setWidget(self.panels_container)
        main_layout.addWidget(self.scroll_area)

    def load_quotations(self):
        self.quote_combo.blockSignals(True)
        self.quote_combo.clear()
        
        quotations = self.service.get_all_quotations()
        
        self.quote_combo.addItem("-- Select a Quotation --", None)
        for q in quotations:
            # q = ("ID", "QuoteRereceNo", "QuoteProjectName", "CustomerName")
            q_id, ref, proj, cust = q[0], q[1], q[2], q[3]
            display_text = f"{ref} - {proj} ({cust})"
            self.quote_combo.addItem(display_text, q_id)
            
        self.quote_combo.blockSignals(False)

    def on_quotation_selected(self):
        # Clear existing panels
        while self.panels_layout.count():
            item = self.panels_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        quote_id = self.quote_combo.currentData()
        if not quote_id:
            lbl = QLabel("Please select a quotation to view its SLD panels.")
            lbl.setStyleSheet("color: #64748b; font-size: 16px; margin: 20px;")
            self.panels_layout.addWidget(lbl)
            return
            
        panels = self.service.get_panels_for_quotation(quote_id)
        if not panels:
            lbl = QLabel("No panels found for this quotation.")
            lbl.setStyleSheet("color: #64748b; font-size: 16px; margin: 20px;")
            self.panels_layout.addWidget(lbl)
            return
            
        for panel in panels:
            # panel = ("ID", "PanelName", "PanelQty", "LengthXmm", "HeightYmm", "DepthZmm")
            card = PanelCardWidget(panel)
            self.panels_layout.addWidget(card)
