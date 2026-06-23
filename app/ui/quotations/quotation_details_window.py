from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, 
    QStackedWidget, QFrame, QComboBox, QMessageBox
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

class QuotationDetailsWindow(QMainWindow):
    """A dedicated window for Quotation management with a sidebar layout similar to MainWindow."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quotation Details")
        self.resize(1200, 800)
        
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

        # Revision Dropdown
        self.revision_combo_label = QLabel("Active Revision:")
        self.revision_combo_label.hide()
        self.revision_combo = QComboBox()
        self.revision_combo.hide()
        self.revision_combo.currentIndexChanged.connect(self._on_revision_selected)

        sidebar_layout.addWidget(title)
        sidebar_layout.addWidget(self.quotations_btn)
        sidebar_layout.addWidget(self.preview_btn)
        sidebar_layout.addWidget(self.revision_btn)
        sidebar_layout.addWidget(self.panels_btn)
        sidebar_layout.addWidget(self.panel_modules_btn)
        sidebar_layout.addWidget(self.items_btn)
        sidebar_layout.addSpacing(20)
        sidebar_layout.addWidget(self.revision_combo_label)
        sidebar_layout.addWidget(self.revision_combo)
        sidebar_layout.addStretch()
        
        # Close button to return to main ERP
        self.close_btn = QPushButton("↩️ Back to ERP")
        self.close_btn.clicked.connect(self.close)
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
        self.quotation_page = QuotationPage(self)
        self.panel_page = PanelPage(self)
        self.panel_module_page = PanelModulePage(self)
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

        main_layout.addWidget(sidebar_frame)
        main_layout.addWidget(self.pages, 1)

        self.setCentralWidget(main_container)
        
        # Apply consistent styling matching MainWindow
        self.setStyleSheet(
            "#sidebar { background-color: #f0f2f5; } "
            "#appTitle { font-size: 20px; font-weight: bold; margin-bottom: 16px; }"
            "QHeaderView::section { background-color: #fce4ec; border: 1px solid #e2e8f0; padding: 4px; font-weight: bold; }"
        )
        
        self.esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.esc_shortcut.activated.connect(self.close)

    def show_quotations(self):
        self.revision_combo_label.hide()
        self.revision_combo.hide()
        self.pages.setCurrentIndex(1)

    def populate_revisions(self, base_quote_id, current_quote_id):
        """Populates the revisions dropdown for the selected quotation family."""
        self.revision_combo.blockSignals(True)
        self.revision_combo.clear()
        
        revisions = self.quotation_page.service.get_revisions_for_quote(base_quote_id)
        current_index = 0
        
        for i, rev in enumerate(revisions):
            rev_no = rev.get("RevisionNo", 0)
            ref_no = rev.get("QuoteRereceNo", f"Rev {rev_no}")
            display_text = f"Rev {rev_no} - {ref_no}"
            if rev_no == 0:
                display_text = f"Original - {ref_no}"
                
            self.revision_combo.addItem(display_text, rev["ID"])
            if rev["ID"] == current_quote_id:
                current_index = i
                
        if self.revision_combo.count() > 0:
            self.revision_combo.setCurrentIndex(current_index)
            self.revision_combo_label.show()
            self.revision_combo.show()
        else:
            self.revision_combo_label.hide()
            self.revision_combo.hide()
            
        self.revision_combo.blockSignals(False)

    def _on_revision_selected(self, index):
        """Triggered when the user selects a different revision from the dropdown."""
        if index < 0: return
        new_quote_id = self.revision_combo.itemData(index)
        combo_text = self.revision_combo.currentText()
        
        # Do not force selection in table since old revisions might not be in the max-revision table.
        # Just fetch the correct project name from the database.
        quote_data = self.quotation_page.service.get_quotation_by_id(new_quote_id)
        if quote_data:
            base_project_name = quote_data.get("QuoteProjectName", "Project")
        else:
            base_project_name = "Project"
            
        # Let QuotationPage update the row in-place if needed
        if hasattr(self.quotation_page, 'update_selected_row_with_quote'):
            self.quotation_page.update_selected_row_with_quote(new_quote_id)
            
        display_title = f"{base_project_name} ({combo_text})"
        
        # Now reload the currently visible page
        current_widget = self.pages.currentWidget()
        if hasattr(current_widget, 'load_quotation'):
            current_widget.load_quotation(new_quote_id, display_title)
        elif current_widget == self.module_items_viewer_page:
            self.module_items_viewer_page.load_viewer(new_quote_id)

    def _get_active_quote_id(self, default_id):
        if self.revision_combo_label.isVisible() and self.revision_combo.count() > 0:
            return self.revision_combo.currentData()
        return default_id

    def _get_display_project_name(self, base_project_name):
        if self.revision_combo_label.isVisible() and self.revision_combo.count() > 0:
            combo_text = self.revision_combo.currentText()
            return f"{base_project_name} ({combo_text})"
        return base_project_name

    def show_panels(self):
        """Switches to the Panel view for the selected quotation."""
        selected = self.quotation_page.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            table_quote_id = int(self.quotation_page.table.item(row, 0).text())
            project_name = self.quotation_page.table.item(row, 7).text()
            
            active_quote_id = self._get_active_quote_id(table_quote_id)
            display_name = self._get_display_project_name(project_name)
            
            self.open_panel_view(active_quote_id, display_name)
        else:
            # If no selection, just show the quotations list
            self.show_quotations()

    def open_panel_view(self, quote_id, project_name):
        """Configures the panel page and displays it in the main stack."""
        self.panel_page.load_quotation(quote_id, project_name)
        self.pages.setCurrentWidget(self.panel_page)

    def show_panel_modules(self):
        """Switches to the Panel Modules view for the selected quotation."""
        selected = self.quotation_page.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            table_quote_id = int(self.quotation_page.table.item(row, 0).text())
            project_name = self.quotation_page.table.item(row, 7).text()
            
            active_quote_id = self._get_active_quote_id(table_quote_id)
            display_name = self._get_display_project_name(project_name)
            
            self.panel_module_page.load_quotation(active_quote_id, display_name)
            self.pages.setCurrentWidget(self.panel_module_page)
        else:
            # If no quotation is selected, ensure the panel modules page is cleared
            # and navigate back to the quotations list.
            self.panel_module_page.clear_page()
            self.show_quotations()

    def update_panels_button_state(self, enabled):
        self.panels_btn.setEnabled(enabled)
        self.panel_modules_btn.setEnabled(enabled)
        self.revision_btn.setEnabled(enabled)
        self.items_btn.setEnabled(enabled)

    def show_revision(self):
        selected = self.quotation_page.table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            table_quote_id = int(self.quotation_page.table.item(row, 0).text())
            project_name = self.quotation_page.table.item(row, 7).text()
            
            active_quote_id = self._get_active_quote_id(table_quote_id)
            display_name = self._get_display_project_name(project_name)
            
            self.revision_page.load_quotation(active_quote_id, display_name)
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
            table_quote_id = int(self.quotation_page.table.item(row, 0).text())
            project_name = self.quotation_page.table.item(row, 7).text()
            
            active_quote_id = self._get_active_quote_id(table_quote_id)
            display_name = self._get_display_project_name(project_name)
            
            self.preview_page.load_quotation(active_quote_id, display_name)
            self.pages.setCurrentWidget(self.preview_page)
        else:
            QMessageBox.warning(self, "Selection Required", "Please select a quotation to preview.")