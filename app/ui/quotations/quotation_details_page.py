from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QFrame, QSplitter, QMessageBox
)
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import Qt
from app.ui.quotations.quotation_page import QuotationPage
from app.ui.quotations.panel_page import PanelPage
from app.ui.quotations.modules.panel_module_page import PanelModulePage
from app.ui.quotations.quotation_common_specs_page import QuotationCommonSpecsPage
from app.ui.quotations.module_items.module_items_viewer_dialog import ModuleItemsViewerDialog
from app.ui.quotations.quotation_preview import QuotationPreviewPage
from app.ui.quotations.quotation_revision_page import QuotationRevisionPage

class QuotationDetailsPage(QWidget): # Changed from QMainWindow to QWidget
    """A dedicated page for Quotation management with a sidebar layout."""

    def __init__(self, parent_main_window=None): # Added parent_main_window to allow switching back
        super().__init__(parent_main_window)
        self.parent_main_window = parent_main_window # Store reference to MainWindow

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #e2e8f0; }")

        # Sidebar setup matching MainWindow UI
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("sidebar")
        sidebar_frame.setMinimumWidth(200)
        sidebar_frame.setMaximumWidth(400)
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(12)

        title = QLabel("Quotation")
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

        self.quotations_btn = QPushButton("📄 Quotations List")
        self.quotations_btn.clicked.connect(self.show_quotations)
        self.quotations_btn.setToolTip(self.shortcuts_tip)

        self.preview_btn = QPushButton("📑 Quotation Process")
        self.preview_btn.clicked.connect(self.show_preview)
        self.preview_btn.setToolTip("View and Manage the entire quotation hierarchy")

        self.revision_btn = QPushButton("🔄 Revisions")
        self.revision_btn.clicked.connect(self.show_revision)
        self.revision_btn.setToolTip("Manage quotation revisions")
        self.revision_btn.setEnabled(False)

        self.panels_btn = QPushButton("🔌 Panels")
        self.panels_btn.clicked.connect(self.show_panels)
        self.panels_btn.setToolTip("Manage panels for the selected quotation")
        self.panels_btn.setEnabled(False)

        self.panel_modules_btn = QPushButton("📦 Panel Modules")
        self.panel_modules_btn.clicked.connect(self.show_panel_modules)
        self.panel_modules_btn.setToolTip("Manage modules for all panels in this quotation")
        self.panel_modules_btn.setEnabled(False)

        self.items_btn = QPushButton("📦 Used Quantity")
        self.items_btn.clicked.connect(self.show_items)
        self.items_btn.setToolTip("View all module items for the selected quotation")
        self.items_btn.setEnabled(False)

        sidebar_layout.addWidget(title)
        sidebar_layout.addWidget(self.quotations_btn)
        sidebar_layout.addWidget(self.preview_btn)
        sidebar_layout.addWidget(self.revision_btn)
        sidebar_layout.addWidget(self.panels_btn)
        sidebar_layout.addWidget(self.panel_modules_btn)
        sidebar_layout.addWidget(self.items_btn)
        sidebar_layout.addStretch()

        # Close button to return to main ERP (now switches back to dashboard)
        self.close_btn = QPushButton("↩️ Back to ERP")
        self.close_btn.clicked.connect(self._back_to_erp)
        sidebar_layout.addWidget(self.close_btn)

        # Content pages
        self.pages = QStackedWidget()

        # Welcome Page
        self.welcome_page = QLabel(
            "Welcome to Quotation Management\n\nSelect a module from the sidebar to begin."
        )
        self.welcome_page.setAlignment(Qt.AlignCenter)
        self.welcome_page.setWordWrap(True)
        self.welcome_page.setStyleSheet("font-size: 16px; color: #64748b;")

        # Quotation Pages
        self.quotation_page = QuotationPage(self) # Pass self (QuotationDetailsPage) as parent
        self.panel_page = PanelPage(self) # Pass self (QuotationDetailsPage) as parent
        self.panel_module_page = PanelModulePage(self) # Pass self (QuotationDetailsPage) as parent
        self.common_specs_page = QuotationCommonSpecsPage(self)
        self.module_items_viewer_page = ModuleItemsViewerDialog(self) # Instantiate as a page
        self.preview_page = QuotationPreviewPage(self)
        self.revision_page = QuotationRevisionPage(self)

        self.pages.addWidget(self.welcome_page)
        self.pages.addWidget(self.quotation_page)
        self.pages.addWidget(self.panel_page)
        self.pages.addWidget(self.panel_module_page)
        self.pages.addWidget(self.common_specs_page)
        self.pages.addWidget(self.module_items_viewer_page) # Add to stacked widget
        self.pages.addWidget(self.preview_page)
        self.pages.addWidget(self.revision_page)

        self.splitter.addWidget(sidebar_frame)
        self.splitter.addWidget(self.pages)
        self.splitter.setStretchFactor(1, 1)

        self.layout.addWidget(self.splitter)

        # Apply consistent styling matching MainWindow
        self.setStyleSheet(
            "#sidebar { background-color: #f0f2f5; } "
            "#appTitle { font-size: 20px; font-weight: bold; margin-bottom: 16px; }"
            "QHeaderView::section { background-color: #fce4ec; border: 1px solid #e2e8f0; padding: 4px; font-weight: bold; }"
        )

        # Esc shortcut to go back to ERP (dashboard)
        self.esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.esc_shortcut.activated.connect(self._back_to_erp)

    def _back_to_erp(self):
        if self.parent_main_window:
            self.parent_main_window.show_dashboard() # Go back to dashboard

    def show_quotations(self):
        self.pages.setCurrentIndex(1)

    def show_panels(self):
        selected = self.quotation_page.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            quote_id = int(self.quotation_page.table.item(row, 0).text())
            project_name = self.quotation_page.table.item(row, 7).text()
            self.open_panel_view(quote_id, project_name)
        else:
            self.show_quotations()

    def open_panel_view(self, quote_id, project_name):
        self.panel_page.load_quotation(quote_id, project_name)
        self.pages.setCurrentWidget(self.panel_page)

    def show_panel_modules(self):
        selected = self.quotation_page.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            quote_id = int(self.quotation_page.table.item(row, 0).text())
            project_name = self.quotation_page.table.item(row, 7).text()
            self.panel_module_page.load_quotation(quote_id, project_name)
            self.pages.setCurrentWidget(self.panel_module_page)
        else:
            self.panel_module_page.clear_page()
            self.show_quotations()

    def update_panels_button_state(self, enabled):
        self.panels_btn.setEnabled(enabled)
        self.panel_modules_btn.setEnabled(enabled)
        self.revision_btn.setEnabled(enabled)
        self.items_btn.setEnabled(enabled)

    def show_common_specs(self):
        selected = self.quotation_page.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            quote_id = int(self.quotation_page.table.item(row, 0).text())
            project_name = self.quotation_page.table.item(row, 7).text()
            self.common_specs_page.load_quotation(quote_id, project_name)
            self.pages.setCurrentWidget(self.common_specs_page)

    def show_revision(self):
        selected = self.quotation_page.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            quote_id = int(self.quotation_page.table.item(row, 0).text())
            project_name = self.quotation_page.table.item(row, 7).text()
            self.revision_page.load_quotation(quote_id, project_name)
            self.pages.setCurrentWidget(self.revision_page)
        else:
            self.show_quotations()

    def show_items(self, initial_panel_id=None, initial_pm_id=None):
        selected = self.quotation_page.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            quote_id = int(self.quotation_page.table.item(row, 0).text())
            self.module_items_viewer_page.load_viewer(quote_id, initial_panel_id, initial_pm_id)
            self.pages.setCurrentWidget(self.module_items_viewer_page)
        else:
            self.show_quotations()

    def show_preview(self):
        """Switches to the hierarchical Quotation Preview page."""
        selected = self.quotation_page.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            quote_id = int(self.quotation_page.table.item(row, 0).text())
            project_name = self.quotation_page.table.item(row, 7).text()
            self.preview_page.load_quotation(quote_id, project_name)
            self.pages.setCurrentWidget(self.preview_page)
        else:
            QMessageBox.warning(self, "Selection Required", "Please select a quotation to preview.")