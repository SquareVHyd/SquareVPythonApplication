from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QAbstractItemView,
    QFileDialog,
    QTextEdit,
    QMenu,
)

from PySide6.QtWidgets import QApplication  
from PySide6.QtGui import QShortcut, QKeySequence, QTextDocument, QPageSize
from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog

from PySide6.QtCore import Qt

from app.services.excel_service import ExcelService
from app.services.state_service import StateService
from app.ui.states.state_form import StateForm
from app.ui.searchable_table import NumericTableWidgetItem, SearchableTable


class StatePage(QWidget):
    def __init__(self):
        super().__init__()

        self.service = StateService()
        self._state_cache = []

        self.setup_ui()
        self.refresh_table()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        title = QLabel("States")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search states...")
        self.search_box.returnPressed.connect(self.search_states)
        self.search_box.textChanged.connect(self.search_states)

        self.search_shortcut = QShortcut(QKeySequence.Find, self)
        self.search_shortcut.activated.connect(self.focus_search)

        self.refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        self.refresh_shortcut.activated.connect(self.refresh_table)
        self.add_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        self.add_shortcut.activated.connect(self.add_state)
        self.edit_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        self.edit_shortcut.activated.connect(self.edit_state)
        self.delete_shortcut = QShortcut(QKeySequence.Delete, self)
        self.delete_shortcut.activated.connect(self.delete_state)
        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self.save_table_as_excel)
        self.print_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        self.print_shortcut.activated.connect(self.save_table_as_pdf)
        self.select_row_shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
        self.select_row_shortcut.activated.connect(self.select_current_row)
        self.select_col_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        self.select_col_shortcut.activated.connect(self.select_current_column)
        self.move_row_down_shortcut = QShortcut(QKeySequence("Ctrl+Down"), self)
        self.move_row_down_shortcut.activated.connect(lambda: self.move_selection(1, 0))
        self.move_row_up_shortcut = QShortcut(QKeySequence("Ctrl+Up"), self)
        self.move_row_up_shortcut.activated.connect(lambda: self.move_selection(-1, 0))
        self.move_col_right_shortcut = QShortcut(QKeySequence("Ctrl+Right"), self)
        self.move_col_right_shortcut.activated.connect(lambda: self.move_selection(0, 1))
        self.move_col_left_shortcut = QShortcut(QKeySequence("Ctrl+Left"), self)
        self.move_col_left_shortcut.activated.connect(lambda: self.move_selection(0, -1))
        self.help_shortcut = QShortcut(QKeySequence("F1"), self)
        self.help_shortcut.activated.connect(self.show_shortcuts)
        self.help_shortcut2 = QShortcut(QKeySequence("Ctrl+H"), self)
        self.help_shortcut2.activated.connect(self.show_shortcuts)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_table)

        
        self.add_btn = QPushButton("➕ Add")
        self.add_btn.clicked.connect(self.add_state)

        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.clicked.connect(self.edit_state)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self.delete_state)

        self.save_as_btn = QPushButton("Save As")
        self.save_as_btn = QPushButton("💾 Save As")
        save_menu = QMenu(self.save_as_btn)
        save_menu.addAction("Excel", self.save_table_as_excel)
        save_menu.addAction("PDF", self.save_table_as_pdf)
        self.save_as_btn.setMenu(save_menu)

        # Quotations button removed

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.search_box)
        header_layout.addWidget(self.refresh_btn)
        header_layout.addWidget(self.add_btn)
        header_layout.addWidget(self.edit_btn)
        header_layout.addWidget(self.delete_btn)
        header_layout.addWidget(self.save_as_btn)

        self.layout.addLayout(header_layout)

        self.table = SearchableTable()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "State Code", "State Name"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)

        self.layout.addWidget(self.table)

    def load_states(self):
        if not self._state_cache:
            self._reload_states()
            return
        self._render_states(self._state_cache)

    def _reload_states(self):
        self.table.setUpdatesEnabled(False)

        states, _ = self.service.get_all_states()
        self._state_cache = list(states)

        self._render_states(self._state_cache)

        self.table.setUpdatesEnabled(True)

    def _render_states(self, rows):
        self.table.setSortingEnabled(False)  # Prevent sorting during insert
        self.table.setUpdatesEnabled(False)  # Prevent repainting during insert

        self.table.clearSelection()
        self.table.setRowCount(len(rows))

        for index, row in enumerate(rows):
            self.table.setItem(index, 0, NumericTableWidgetItem(str(row[0] or "")))
            self.table.setItem(index, 1, NumericTableWidgetItem(str(row[1] or "")))
            self.table.setItem(index, 2, NumericTableWidgetItem(str(row[2] or "")))

        self.table.setUpdatesEnabled(True)
        self.table.setSortingEnabled(True)

        self.table.fix_column_widths()

    def search_states(self):
        keyword = self.search_box.text().strip().lower()
        if not keyword:
            self._render_states(self._state_cache)
            return

        rows = []
        for row in self._state_cache:
            search_text = " ".join([
                str(row[0] or ""),
                str(row[1] or ""),
                str(row[2] or ""),
            ]).lower()
            if keyword in search_text:
                rows.append(row)

        self._render_states(rows)

    def get_selected_state(self):
        selected = self.table.selectedItems()
        if not selected:
            return None

        row = selected[0].row()
        state_id = int(self.table.item(row, 0).text())
        return self.service.get_state(state_id)

    def focus_search(self):
        self.search_box.setFocus()

    def refresh_table(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)

        try:
            self.search_box.blockSignals(True)
            self.search_box.clear()
            self.search_box.blockSignals(False)

            states, _ = self.service.get_all_states()

            self._state_cache = list(states)

            self._render_states(self._state_cache)

            self.table.clearSelection()
            self.table.sortItems(0, Qt.AscendingOrder)
            self.table.scrollToTop()

        finally:
            QApplication.restoreOverrideCursor()

    def move_selection(self, row_delta=0, col_delta=0):
        if self.table.rowCount() == 0 or self.table.columnCount() == 0:
            return

        current = self.table.currentItem()
        row = current.row() if current else 0
        col = current.column() if current else 0

        row = max(0, min(self.table.rowCount() - 1, row + row_delta))
        col = max(0, min(self.table.columnCount() - 1, col + col_delta))

        self.table.setCurrentCell(row, col)
        self.table.scrollToItem(self.table.currentItem())

    def select_current_row(self):
        if self.table.rowCount() == 0:
            return

        current = self.table.currentItem() or self.table.item(0, 0)
        if current:
            self.table.selectRow(current.row())
            self.table.setCurrentCell(current.row(), current.column())

    def select_current_column(self):
        if self.table.columnCount() == 0:
            return

        current = self.table.currentItem() or self.table.item(0, 0)
        if current:
            self.table.selectColumn(current.column())
            self.table.setCurrentCell(current.row(), current.column())

    def show_shortcuts(self):
        shortcuts = (
            "Keyboard Shortcuts:\n"
            "F1 / Ctrl+H - Open shortcuts help\n"
            "Ctrl+F - Focus search box\n"
            "Ctrl+R - Refresh state list\n"
            "Ctrl+N - Add state\n"
            "Ctrl+E - Edit selected state\n"
            "Delete - Delete selected state\n"
            "Ctrl+S - Export states to Excel\n"
            "Ctrl+P - Export states to PDF\n"
            "Ctrl+Down / Ctrl+Up - Move row selection\n"
            "Ctrl+Right / Ctrl+Left - Move column selection\n"
            "Ctrl+Space - Select current row\n"
            "Ctrl+L - Select current column\n"
        )
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts)

    def reset_search(self):
        self.refresh_table()

    # Quotations/print functionality removed; PDF export remains via Save As -> PDF

    def build_state_request_letter(self, values):
        from datetime import datetime
        today = datetime.now().strftime("%d %B %Y")
        return (
            f"State ID: {values['ID']}\n"
            f"State Code: {values['State Code']}\n"
            f"State Name: {values['State Name']}\n\n"
            "Dear Supply Chain & Logistics,\n\n"
            "We are writing to request the processing and distribution of materials for the above-mentioned state region.\n\n"
            "MATERIALS TO BE DISTRIBUTED:\n"
            "1. \n"
            "2. \n"
            "3. \n\n"
            "DISTRIBUTION TERMS:\n"
            "• Please confirm receipt of this request within 24 hours\n"
            "• Estimated delivery date: [To be specified]\n"
            "• Distribution centers: [Centers to be specified]\n"
            "• Priority: High - State-wide initiative\n\n"
            "This is part of our state-wide operational initiative and requires immediate processing. Please coordinate with regional distribution centers for optimal delivery.\n\n"
            "Should you require any additional information or clarifications, please contact the Regional Management team.\n\n"
            "Thank you for your prompt attention to this matter.\n\n"
            "Yours sincerely,\n\n"
            "Regional Operations Department\n"
            "Enterprise ERP System"
        )

    def edit_request_letter(self, letter_text):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Request Letter")
        dialog.setMinimumSize(700, 520)

        layout = QVBoxLayout(dialog)
        editor = QTextEdit(dialog)
        editor.setPlainText(letter_text)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        layout.addWidget(editor)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            return editor.toPlainText()
        return None

    def build_print_html(self, title, body, values):
        from datetime import datetime
        today = datetime.now().strftime("%d %B %Y")
        
        rows = "".join(
            f"<tr><td class='label'>{key}</td><td class='value'>{value}</td></tr>"
            for key, value in values.items()
        )
        formatted_body = body.replace("\n", "<br>")
        
        return (
            "<html><head><meta charset='UTF-8'><style>"
            "* { margin: 0; padding: 0; }"
            "body { "
            "  font-family: 'Segoe UI', Arial, sans-serif; "
            "  line-height: 1.7; "
            "  color: #333; "
            "  background-color: #fff; "
            "  padding: 40px; "
            "}"
            ".header { "
            "  background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%); "
            "  color: white; "
            "  padding: 30px 40px; "
            "  margin: -40px -40px 0 -40px; "
            "  text-align: center; "
            "  border-bottom: 4px solid #1e40af; "
            "}"
            ".header h1 { font-size: 32px; font-weight: 600; letter-spacing: 1px; }"
            ".company-name { font-size: 14px; opacity: 0.9; margin-top: 8px; }"
            ".date-section { "
            "  text-align: right; "
            "  font-size: 13px; "
            "  color: #666; "
            "  margin: 20px 0 30px 0; "
            "}"
            ".content { margin: 30px 0; }"
            ".content p { margin-bottom: 15px; text-align: justify; }"
            ".content-header { "
            "  font-size: 14px; "
            "  font-weight: 600; "
            "  color: #1e3a8a; "
            "  margin-top: 25px; "
            "  margin-bottom: 10px; "
            "  border-bottom: 2px solid #ddd; "
            "  padding-bottom: 8px; "
            "}"
            ".state-info-table { "
            "  width: 100%; "
            "  border-collapse: collapse; "
            "  margin: 30px 0; "
            "  background-color: #f8f9fa; "
            "  border: 1px solid #dee2e6; "
            "}"
            ".state-info-table td { "
            "  padding: 12px 15px; "
            "  border: 1px solid #dee2e6; "
            "}"
            ".state-info-table .label { "
            "  font-weight: 600; "
            "  color: #1e3a8a; "
            "  width: 25%; "
            "  background-color: #eff6ff; "
            "}"
            ".state-info-table .value { color: #333; }"
            ".signature-section { "
            "  margin-top: 50px; "
            "  padding-top: 30px; "
            "  border-top: 2px solid #ddd; "
            "}"
            ".signature-block { "
            "  margin-top: 20px; "
            "  display: flex; "
            "  justify-content: space-between; "
            "}"
            ".signature { width: 45%; }"
            ".signature-line { "
            "  border-top: 1px solid #333; "
            "  margin-top: 40px; "
            "  padding-top: 5px; "
            "  font-size: 12px; "
            "}"
            ".footer { "
            "  text-align: center; "
            "  margin-top: 40px; "
            "  padding-top: 20px; "
            "  border-top: 1px solid #e9ecef; "
            "  font-size: 11px; "
            "  color: #6c757d; "
            "}"
            ".footer p { margin-bottom: 5px; }"
            "</style></head>"
            f"<body>"
            f"<div class='header'>"
            f"  <h1>MATERIALS REQUEST LETTER</h1>"
            f"  <div class='company-name'>Enterprise ERP System</div>"
            f"</div>"
            f"<div class='date-section'>Date: {today}</div>"
            f"<div class='state-info-table'>"
            f"  <tr>"
            f"    <td class='label'>State ID</td>"
            f"    <td class='value'>{values.get('ID', '')}</td>"
            f"  </tr>"
            f"  <tr>"
            f"    <td class='label'>State Code</td>"
            f"    <td class='value'>{values.get('State Code', '')}</td>"
            f"  </tr>"
            f"  <tr>"
            f"    <td class='label'>State Name</td>"
            f"    <td class='value'>{values.get('State Name', '')}</td>"
            f"  </tr>"
            f"</div>"
            f"<div class='content'>"
            f"  <div style='white-space: pre-wrap;'>{formatted_body}</div>"
            f"</div>"
            f"<div class='signature-section'>"
            f"  <div class='signature-block'>"
            f"    <div class='signature'>"
            f"      <div class='signature-line'>Prepared By<br/>Regional Operations Department</div>"
            f"    </div>"
            f"    <div class='signature'>"
            f"      <div class='signature-line'>Approved By<br/>Management</div>"
            f"    </div>"
            f"  </div>"
            f"</div>"
            f"<div class='footer'>"
            f"  <p>This document is generated by the Enterprise ERP System</p>"
            f"  <p>Confidential - For Internal Use Only</p>"
            f"  <p>&copy; 2026 Enterprise ERP System. All rights reserved.</p>"
            f"</div>"
            f"</body></html>"
        )

    def preview_and_save_pdf(self, html, save_title):
        try:
            document = QTextDocument()
            document.setHtml(html)

            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSize(QPageSize(QPageSize.A4))
            printer.setOrientation(QPrinter.Landscape)
            printer.setPageMargins(12, 12, 12, 12, QPrinter.Millimeter)

            preview = QPrintPreviewDialog(printer, self)
            preview.setWindowTitle("PDF Preview - State Request")
            preview.paintRequested.connect(lambda p: document.print_(p))
            result = preview.exec()
            
            if result != QDialog.Accepted:
                return

            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                save_title, 
                "", 
                "PDF Files (*.pdf)"
            )
            if not file_path:
                QMessageBox.information(self, "Save Cancelled", "PDF save was cancelled.")
                return
                
            if not file_path.lower().endswith(".pdf"):
                file_path += ".pdf"

            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)
            document.print_(printer)
            
            QMessageBox.information(
                self, 
                "PDF Exported Successfully", 
                f"PDF has been saved to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while generating PDF:\n{str(e)}")

    def save_table_as_excel(self):
        headers, rows = self.table.get_table_data()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save States Table as Excel",
            "",
            "Excel Files (*.xlsx)",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".xlsx"):
            file_path += ".xlsx"

        try:
            ExcelService().export(headers, rows, file_path)
            QMessageBox.information(self, "Saved", f"States table saved to:\n{file_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", f"Unable to save Excel file: {exc}")

    def save_table_as_pdf(self):
        html = self.table.to_html("States Table")
        self.preview_and_save_pdf(html, "Save States Table as PDF")

    def add_state(self):
        dialog = StateForm(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                self.service.create(data["state_code"], data["state_name"])
                self.refresh_table()

    def edit_state(self):
        state = self.get_selected_state()
        if not state:
            QMessageBox.warning(self, "Select state", "Please select a state to edit")
            return

        dialog = StateForm(self, state=state)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                self.service.update(state[0], data["state_code"], data["state_name"])
                self.refresh_table()

    def delete_state(self):
        state = self.get_selected_state()
        if not state:
            QMessageBox.warning(self, "Select state", "Please select a state to delete")
            return

        confirm = QMessageBox.question(
            self,
            "Delete state",
            "Are you sure you want to delete this state?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if confirm == QMessageBox.Yes:
            self.service.delete(state[0])
            self.refresh_table()
