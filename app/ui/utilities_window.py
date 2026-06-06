from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, 
    QStackedWidget, QFrame
)
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import Qt
from app.ui.electricity_bill_page import ElectricityBillPage
from app.ui.zed_scorecard_page import ZEDScoreCardPage
from app.ui.timely_delivery_page import TimelyDeliveryPage

class UtilitiesWindow(QMainWindow):
    """A dedicated window for utility management tools with a sidebar layout similar to MainWindow."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Utilities")
        self.resize(1200, 800)  # Set a default size for the normal window mode
        
        main_container = QWidget()
        main_layout = QHBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar setup matching MainWindow UI
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("sidebar")
        sidebar_frame.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(12)

        title = QLabel("Utilities")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignCenter)

        self.shortcuts_tip = (
            "<b>Keyboard Shortcuts:</b><br>"
            "F1 / Ctrl+H - Help<br>"
            "Ctrl+F - Focus Search<br>"
            "Ctrl+R - Refresh Table<br>"
            "Ctrl+N - Add New<br>"
            "Ctrl+E - Edit Selected<br>"
            "Delete - Delete Selected<br>"
            "Ctrl+S - Save Excel<br>"
            "Ctrl+P - Export PDF"
        )

        self.eb_bill_btn = QPushButton("⚡ Electricity Bills")
        self.eb_bill_btn.clicked.connect(self.show_eb_bill)
        self.eb_bill_btn.setToolTip(self.shortcuts_tip)

        self.zed_scorecard_btn = QPushButton("🏅 ZEDScoreCard")
        self.zed_scorecard_btn.clicked.connect(self.show_zed_scorecard)
        self.zed_scorecard_btn.setToolTip(self.shortcuts_tip)

        self.delivery_btn = QPushButton("🚚 Timely Delivery")
        self.delivery_btn.clicked.connect(self.show_timely_delivery)
        self.delivery_btn.setToolTip(self.shortcuts_tip)

        sidebar_layout.addWidget(title)
        sidebar_layout.addWidget(self.eb_bill_btn)
        sidebar_layout.addWidget(self.zed_scorecard_btn)
        sidebar_layout.addWidget(self.delivery_btn)
        sidebar_layout.addStretch()
        
        # Close button to return to main ERP
        self.close_btn = QPushButton("↩️ Back to ERP")
        self.close_btn.clicked.connect(self.close)
        sidebar_layout.addWidget(self.close_btn)

        # Content pages
        self.pages = QStackedWidget()
        
        # Welcome Dashboard for Utilities
        self.welcome_page = QLabel(
            "Welcome to Utilities\n\nSelect a utility from the sidebar to begin."
        )
        self.welcome_page.setAlignment(Qt.AlignCenter)
        self.welcome_page.setWordWrap(True)
        
        # Utility Pages
        self.eb_page = ElectricityBillPage()
        self.zed_page = ZEDScoreCardPage()
        self.delivery_page = TimelyDeliveryPage()

        self.pages.addWidget(self.welcome_page)
        self.pages.addWidget(self.eb_page)
        self.pages.addWidget(self.zed_page)
        self.pages.addWidget(self.delivery_page)

        main_layout.addWidget(sidebar_frame)
        main_layout.addWidget(self.pages, 1)

        self.setCentralWidget(main_container)
        
        # Apply consistent styling
        self.setStyleSheet(
            "#sidebar { background-color: #f0f2f5; } "
            "#appTitle { font-size: 20px; font-weight: bold; margin-bottom: 16px; }"
        )
        
        # Allow closing the fullscreen window with Escape key for better UX
        self.esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.esc_shortcut.activated.connect(self.close)

    def show_eb_bill(self):
        """Navigates to the Electricity Bill management page."""
        self.pages.setCurrentIndex(1)

    def show_zed_scorecard(self):
        """Navigates to the ZED ScoreCard management page."""
        self.pages.setCurrentIndex(2)

    def show_timely_delivery(self):
        """Navigates to the Timely Delivery management page."""
        self.pages.setCurrentIndex(3)