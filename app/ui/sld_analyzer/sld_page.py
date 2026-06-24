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
        self.current_quote_id = None
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header Area
        header_layout = QHBoxLayout()
        title = QLabel("📏 SLD Analyzer (GA Diagrams)")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0f172a;")
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setFixedWidth(100)
        self.refresh_btn.clicked.connect(self.refresh_diagrams)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)
        main_layout.addLayout(header_layout)

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
        
    def refresh_diagrams(self):
        if self.current_quote_id:
            self.load_quotation(self.current_quote_id)

    def load_quotation(self, quote_id):
        self.current_quote_id = quote_id
        # Clear existing panels
        while self.panels_layout.count():
            item = self.panels_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
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
            # panel = ("ID", "PanelName", "PanelQty", "LengthXmm", "HeightYmm", "DepthZmm", "StandRequired")
            panel_id = panel[0]
            modules = self.service.get_panel_modules(panel_id)
            card = PanelCardWidget(panel, modules)
            self.panels_layout.addWidget(card)
