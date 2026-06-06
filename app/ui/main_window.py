from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QFrame,
    QMessageBox,
)
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import Qt

from app.ui.pricelist.pricelist_page import PriceListPage
from app.ui.customers.customer_page import CustomerPage
from app.ui.modules.module_view_page import ModuleViewPage
from app.ui.busbar.busbar_page import BusbarPage
from app.config.ui_state import UIStateManager
from app.ui.dashboard.dashboard_page import DashboardPage


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("SQV Engineering")
        # Track the utilities window instance to prevent garbage collection
        self.utilities_window = None
        self.tools_window = None
        
        # Restore window geometry from last session
        geom = UIStateManager.get_window_geometry()
        self.setGeometry(geom["x"], geom["y"], geom["width"], geom["height"])

        main_container = QWidget()
        main_layout = QHBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)

        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("sidebar")
        sidebar_frame.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(12)

        title = QLabel("Menu")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignCenter)

        self.shortcuts_tip = (
            "<b>Keyboard Shortcuts:</b><br>"
            "F1 / Ctrl+H - Show help<br>"
            "Ctrl+F - Focus search box<br>"
            "Ctrl+R - Refresh current table<br>"
            "Ctrl+N - Add new record<br>"
            "Ctrl+E - Edit selected record<br>"
            "Delete - Delete selected record<br>"
            "Ctrl+S - Save current table as Excel<br>"
            "Ctrl+P - Export current table to PDF"
        )

        self.dashboard_btn = QPushButton("📊 Dashboard")
        self.customers_btn = QPushButton("👥 Customers")
        self.pricelist_btn = QPushButton("🧾 Price List")
        self.modules_btn = QPushButton("📚 Modules")
        self.busbar_btn = QPushButton("⚡ Busbar Materials")
        self.utilities_btn = QPushButton("🔧 Utilities")
        self.tools_btn = QPushButton("🛠️ Tools")

        self.dashboard_btn.setToolTip(self.shortcuts_tip)
        self.customers_btn.setToolTip(self.shortcuts_tip)
        self.pricelist_btn.setToolTip(self.shortcuts_tip)
        self.modules_btn.setToolTip(self.shortcuts_tip)
        self.busbar_btn.setToolTip(self.shortcuts_tip)
        self.utilities_btn.setToolTip(self.shortcuts_tip)
        self.tools_btn.setToolTip(self.shortcuts_tip)

        self.dashboard_btn.clicked.connect(self.show_dashboard)
        self.customers_btn.clicked.connect(self.show_customers)
        self.pricelist_btn.clicked.connect(self.show_pricelist)
        self.modules_btn.clicked.connect(self.show_modules)
        self.busbar_btn.clicked.connect(self.show_busbar)
        self.utilities_btn.clicked.connect(self.show_utilities)
        self.tools_btn.clicked.connect(self.show_tools)

        self.help_btn = QPushButton("❓ Help")
        self.help_btn.setToolTip(self.shortcuts_tip)
        self.help_btn.clicked.connect(self.show_shortcuts)

        sidebar_layout.addWidget(title)
        sidebar_layout.addWidget(self.dashboard_btn)
        sidebar_layout.addWidget(self.customers_btn)
        sidebar_layout.addWidget(self.pricelist_btn)
        sidebar_layout.addWidget(self.modules_btn)
        sidebar_layout.addWidget(self.busbar_btn)
        sidebar_layout.addWidget(self.utilities_btn)
        sidebar_layout.addWidget(self.tools_btn)
        sidebar_layout.addWidget(self.help_btn)
        sidebar_layout.addStretch()

        from app.ui.dashboard.dashboard_page import DashboardPage
        self.pages = QStackedWidget()
        self.pages.addWidget(DashboardPage())
       

        self.pages.addWidget(CustomerPage())
        self.pages.addWidget(PriceListPage())
        self.pages.addWidget(ModuleViewPage())
        self.pages.addWidget(BusbarPage())

        self.shortcut_help = QShortcut(QKeySequence("F1"), self)
        self.shortcut_help.activated.connect(self.show_shortcuts)
        self.shortcut_help2 = QShortcut(QKeySequence("Ctrl+H"), self)
        self.shortcut_help2.activated.connect(self.show_shortcuts)

        main_layout.addWidget(sidebar_frame)
        main_layout.addWidget(self.pages, 1)

        self.setCentralWidget(main_container)
        self.setStyleSheet(
            "#sidebar { background-color: #f0f2f5; } "
            "#appTitle { font-size: 20px; font-weight: bold; margin-bottom: 16px; }"
        )
        
        # Always open the dashboard page on login/startup
        self.pages.setCurrentIndex(0)


    def closeEvent(self, event):
        """Save UI state before closing."""
        # Save window geometry
        geom = self.geometry()
        UIStateManager.save_window_geometry(geom.x(), geom.y(), geom.width(), geom.height())
        
        # Save current page
        UIStateManager.save_current_page(self.pages.currentIndex())
        
        # Save state for all individual pages (e.g., column widths and positions)
        for i in range(self.pages.count()):
            page = self.pages.widget(i)
            if hasattr(page, "_save_state"):
                page._save_state()

        event.accept()

    def show_shortcuts(self):
        current = self.pages.currentWidget()
        if hasattr(current, "show_shortcuts"):
            current.show_shortcuts()
            return

        shortcuts = (
            "Keyboard Shortcuts:\n"
            "F1 / Ctrl+H - Show keyboard shortcuts\n"
            "Ctrl+F - Focus search box\n"
            "Ctrl+R - Refresh current table\n"
            "Ctrl+N - Add new record\n"
            "Ctrl+E - Edit selected record\n"
            "Delete - Delete selected record\n"
            "Ctrl+S - Save current table as Excel\n"
            "Ctrl+P - Export current table to PDF\n"
            "Ctrl+Arrow Keys - Move between rows and columns\n"
            "Ctrl+Space - Select current row\n"
            "Ctrl+L - Select current column\n"
        )
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts)

    def show_dashboard(self):
        self.pages.setCurrentIndex(0)
        UIStateManager.save_current_page(0)

    def show_customers(self):
        self.pages.setCurrentIndex(1)
        UIStateManager.save_current_page(1)

    def show_pricelist(self):
        self.pages.setCurrentIndex(2)
        UIStateManager.save_current_page(2)

    def show_modules(self):
        self.pages.setCurrentIndex(3)
        UIStateManager.save_current_page(3)

    def show_busbar(self):
        self.pages.setCurrentIndex(4)
        UIStateManager.save_current_page(4)

    def show_utilities(self):
        """Opens the Utilities window and ensures it comes to the front."""
        from app.ui.utilities_window import UtilitiesWindow
        
        # Robust check to see if the window was previously closed/destroyed
        if self.utilities_window is not None:
            try:
                # Accessing windowTitle() will trigger a RuntimeError if the C++ object is deleted
                _ = self.utilities_window.windowTitle()
            except RuntimeError:
                self.utilities_window = None

        if self.utilities_window is None:
            self.utilities_window = UtilitiesWindow(self)
            
        self.utilities_window.show()
        # Bring to front and give focus if already open
        self.utilities_window.raise_()
        self.utilities_window.activateWindow()

    def show_tools(self):
        """Opens the Tools window and ensures it comes to the front."""
        from app.ui.tools_window import ToolsWindow

        if self.tools_window is not None:
            try:
                _ = self.tools_window.windowTitle()
            except RuntimeError:
                self.tools_window = None

        if self.tools_window is None:
            self.tools_window = ToolsWindow(self)
            
        self.tools_window.show()
        self.tools_window.raise_()
        self.tools_window.activateWindow()
