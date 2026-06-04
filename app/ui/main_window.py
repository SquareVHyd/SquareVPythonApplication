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


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Enterprise ERP")
        
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

        title = QLabel("Enterprise ERP")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignCenter)

        self.dashboard_btn = QPushButton("Dashboard")
        self.customers_btn = QPushButton("Customers")
        self.pricelist_btn = QPushButton("Price List")
        self.modules_btn = QPushButton("Modules")
        self.busbar_btn = QPushButton("Busbar Materials")

        self.dashboard_btn.clicked.connect(self.show_dashboard)
        self.customers_btn.clicked.connect(self.show_customers)
        self.pricelist_btn.clicked.connect(self.show_pricelist)
        self.modules_btn.clicked.connect(self.show_modules)
        self.busbar_btn.clicked.connect(self.show_busbar)

        self.help_btn = QPushButton("Help")
        self.help_btn.clicked.connect(self.show_shortcuts)

        sidebar_layout.addWidget(title)
        sidebar_layout.addWidget(self.dashboard_btn)
        sidebar_layout.addWidget(self.customers_btn)
        sidebar_layout.addWidget(self.pricelist_btn)
        sidebar_layout.addWidget(self.modules_btn)
        sidebar_layout.addWidget(self.busbar_btn)
        sidebar_layout.addWidget(self.help_btn)
        sidebar_layout.addStretch()

        self.pages = QStackedWidget()
        self.dashboard_page = QLabel(
            "Welcome to Enterprise ERP\n\nUse the sidebar to open Customers or States management."
        )
        self.dashboard_page.setAlignment(Qt.AlignCenter)
        self.dashboard_page.setWordWrap(True)

        self.pages.addWidget(self.dashboard_page)
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
        
        # Restore last viewed page
        last_page = UIStateManager.get_current_page()
        self.pages.setCurrentIndex(last_page)


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
