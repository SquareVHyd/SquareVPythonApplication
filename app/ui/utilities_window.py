from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, 
    QStackedWidget, QFrame, QButtonGroup
)
from app.ui.components.menu_button import MenuButton
import os
import sys
import subprocess
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import Qt
from app.ui.Utilities.electricity_bill_page import ElectricityBillPage
from app.ui.Utilities.zed_scorecard_page import ZEDScoreCardPage
from app.ui.Utilities.timely_delivery_page import TimelyDeliveryPage

from app.ui.Utilities.util_appstoor.app_suite.gst_calculator_qt import GstCalculatorWidget
from app.ui.Utilities.util_appstoor.app_suite.busbar_calculator_qt import BusbarCalculatorWidget
from app.ui.Utilities.util_appstoor.app_suite.business_calculator_qt import BusinessCalculatorWidget

class AppSuitePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        # Header layout
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_layout.setSpacing(10)
        
        self.btn_business = QPushButton("💼 Business Tools")
        self.btn_busbar = QPushButton("⚡ Busbar Calculator")
        self.btn_gst = QPushButton("📄 GST Calculator")
        
        nav_btn_style = """
            QPushButton {
                background-color: #f1f5f9;
                color: #000000;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
                outline: none;
            }
            QPushButton:hover {
                background-color: #e0f2fe;
                color: #000000;
            }
            QPushButton:checked {
                background-color: #e2e8f0;
                color: #000000;
                border: 1px solid #cbd5e1;
                border-bottom: 4px solid #3b82f6;
            }
        """
        
        for btn in (self.btn_business, self.btn_busbar, self.btn_gst):
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setStyleSheet(nav_btn_style)
            btn.setCursor(Qt.PointingHandCursor)
            header_layout.addWidget(btn)
            
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Stacked Widget for the apps
        self.apps_stack = QStackedWidget()
        
        # Load the PySide6 versions of the apps
        self.business_widget = BusinessCalculatorWidget()
        self.busbar_widget = BusbarCalculatorWidget()
        self.gst_widget = GstCalculatorWidget()
        
        self.apps_stack.addWidget(self.business_widget) # Index 0
        self.apps_stack.addWidget(self.busbar_widget) # Index 1
        self.apps_stack.addWidget(self.gst_widget) # Index 2
        
        layout.addWidget(self.apps_stack, 1)
        
        # Set default tab
        self.btn_business.setChecked(True)
        
        # Connect Header Buttons
        self.btn_business.clicked.connect(lambda: self.apps_stack.setCurrentIndex(0))
        self.btn_busbar.clicked.connect(lambda: self.apps_stack.setCurrentIndex(1))
        self.btn_gst.clicked.connect(lambda: self.apps_stack.setCurrentIndex(2))
        
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

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.eb_bill_btn = MenuButton("⚡ Electricity Bills")
        self.eb_bill_btn.clicked.connect(self.show_eb_bill)
        self.eb_bill_btn.setToolTip(self.shortcuts_tip)

        self.zed_scorecard_btn = MenuButton("🏅 ZEDScoreCard")
        self.zed_scorecard_btn.clicked.connect(self.show_zed_scorecard)
        self.zed_scorecard_btn.setToolTip(self.shortcuts_tip)

        self.delivery_btn = MenuButton("🚚 Timely Delivery")
        self.delivery_btn.clicked.connect(self.show_timely_delivery)
        self.delivery_btn.setToolTip(self.shortcuts_tip)

        self.tally_reports_btn = MenuButton("📊 Tally Reports")
        self.tally_reports_btn.setCheckable(False)
        self.tally_reports_btn.clicked.connect(self.show_tally_reports)
        self.tally_reports_btn.setToolTip("Launch Tally Analyzer Web App")

        self.app_suite_btn = MenuButton("🛠️ App Suite")
        self.app_suite_btn.clicked.connect(self.show_app_suite)
        self.app_suite_btn.setToolTip("Launch utility applications suite")

        self.ar_dashboard_btn = MenuButton("📈 AR Dashboard")
        self.ar_dashboard_btn.setCheckable(False)
        self.ar_dashboard_btn.clicked.connect(self.show_ar_dashboard)
        self.ar_dashboard_btn.setToolTip("Generate AR Dashboard")
        
        self.btn_group.addButton(self.eb_bill_btn)
        self.btn_group.addButton(self.zed_scorecard_btn)
        self.btn_group.addButton(self.delivery_btn)
        self.btn_group.addButton(self.app_suite_btn)

        sidebar_layout.addWidget(title)
        sidebar_layout.addWidget(self.eb_bill_btn)
        sidebar_layout.addWidget(self.zed_scorecard_btn)
        sidebar_layout.addWidget(self.delivery_btn)
        sidebar_layout.addWidget(self.tally_reports_btn)
        sidebar_layout.addWidget(self.app_suite_btn)
        sidebar_layout.addWidget(self.ar_dashboard_btn)
        sidebar_layout.addStretch()
        
        # Close button to return to main ERP
        self.close_btn = MenuButton("↩️ Back to ERP")
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
        
        # App Suite Page
        self.app_suite_page = AppSuitePage()

        self.pages.addWidget(self.welcome_page)
        self.pages.addWidget(self.eb_page)
        self.pages.addWidget(self.zed_page)
        self.pages.addWidget(self.delivery_page)
        self.pages.addWidget(self.app_suite_page)

        main_layout.addWidget(sidebar_frame)
        main_layout.addWidget(self.pages, 1)

        self.setCentralWidget(main_container)
        
        # Apply consistent styling
        self.setStyleSheet(
            "#sidebar { background-color: #f8fafc; } "
            "#appTitle { font-size: 20px; font-weight: bold; margin-bottom: 16px; padding-left: 10px; }"
        )
        
        # Allow closing the fullscreen window with Escape key for better UX
        self.esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.esc_shortcut.activated.connect(self.close)

    def show_eb_bill(self):
        """Navigates to the Electricity Bill management page."""
        self.pages.setCurrentIndex(1)
        self.eb_bill_btn.setChecked(True)

    def show_zed_scorecard(self):
        """Navigates to the ZED ScoreCard management page."""
        self.pages.setCurrentIndex(2)
        self.zed_scorecard_btn.setChecked(True)

    def show_timely_delivery(self):
        """Navigates to the Timely Delivery management page."""
        self.pages.setCurrentIndex(3)
        self.delivery_btn.setChecked(True)

    def show_tally_reports(self):
        """Launches the Tally Analyzer app in the background directly."""
        script_path = os.path.join(
            os.path.dirname(__file__), 
            "Utilities", "util_appstoor", "tally_analyzer", "app.py"
        )
        try:
            # We use Popen without waiting, so it runs in background and opens browser
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            print(f"Error launching Tally Analyzer: {e}")
            
    def show_ar_dashboard(self):
        """Launches the AR Dashboard generator in the background directly."""
        script_path = os.path.join(
            os.path.dirname(__file__), 
            "Utilities", "util_appstoor", "ARFollowup", "generate_dashboard.py"
        )
        try:
            # We use Popen without waiting, so it runs in background
            subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            print(f"Error launching AR Dashboard: {e}")
        
    def show_app_suite(self):
        """Navigates to the App Suite page."""
        self.pages.setCurrentIndex(4)
        self.app_suite_btn.setChecked(True)