from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QWidget, QLineEdit, QScrollArea, QMessageBox, QGridLayout, QFrame,
    QFileDialog, QInputDialog
)
from PySide6.QtCore import Qt, QMarginsF, QPoint
from PySide6.QtGui import QFont, QPainter, QPageSize, QPageLayout, QPdfWriter, QPixmap
from datetime import datetime
import os

from app.services.test_report_service import TestReportService
from app.services.quotation_service import QuotationService


class TestReportsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.quote_id = None
        self.project_name = None
        self.service = TestReportService()
        self.quote_service = QuotationService()
        self.panels = []
        
        # Data dictionaries for input fields
        self.general_inputs = {}
        self.ir1_inputs = {}
        self.ir2_inputs = {}
        self.ir3_inputs = {}
        self.footer_inputs = {}
        self.header_details = {}

        self.setup_ui()

    def load_quotation(self, quote_id, project_name):
        self.quote_id = quote_id
        self.project_name = project_name
        self.header_details = self.service.get_header_details(self.quote_id)
        self.load_panels()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- Top Bar for Panel Selection ---
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Select Panel:"))
        self.panel_combo = QComboBox()
        self.panel_combo.currentIndexChanged.connect(self.on_panel_selected)
        top_bar.addWidget(self.panel_combo)
        
        self.save_btn = QPushButton("💾 Save Data")
        self.save_btn.clicked.connect(self.save_report)
        top_bar.addWidget(self.save_btn)
        
        self.pdf_btn = QPushButton("📄 Save as PDF")
        self.pdf_btn.clicked.connect(self.save_as_pdf)
        top_bar.addWidget(self.pdf_btn)
        
        top_bar.addStretch()
        main_layout.addLayout(top_bar)
        
        # --- Scrollable Document Area ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignCenter)
        scroll_area.setStyleSheet("QScrollArea { background-color: #e2e8f0; border: none; }")
        
        self.doc_widget = QWidget()
        # Style to look like an A4 document page
        self.doc_widget.setStyleSheet("""
            QWidget { 
                background-color: white; 
                color: black; 
                font-family: Arial;
                font-size: 12px;
            }
            QLabel { padding: 2px; }
        """)
        self.doc_widget.setFixedWidth(850) # Standard A4 rough width ratio
        
        self.doc_layout = QVBoxLayout(self.doc_widget)
        self.doc_layout.setContentsMargins(40, 40, 40, 40)
        self.doc_layout.setSpacing(10)
        
        # Company Header Layout
        company_header_layout = QHBoxLayout()
        company_header_layout.addStretch()
        
        logo_lbl = QLabel()
        logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Images", "SQV_Header.png"))
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaledToHeight(40, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pixmap)
            company_header_layout.addWidget(logo_lbl)
            
        company_lbl = QLabel(" SQUARE V ENGINEERING ENTERPRISES")
        company_font = QFont("Arial", 25, QFont.Bold)
        company_lbl.setFont(company_font)
        company_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        company_header_layout.addWidget(company_lbl)
        
        company_header_layout.addStretch()
        self.doc_layout.addLayout(company_header_layout)
        
        # Title
        title_lbl = QLabel("Test Certificate")
        title_font = QFont("Arial", 28, QFont.Bold)
        title_font.setUnderline(True)
        title_lbl.setFont(title_font)
        title_lbl.setAlignment(Qt.AlignCenter)
        self.doc_layout.addWidget(title_lbl)
        
        # --- Header Grid ---
        header_frame = QFrame()
        header_frame.setFrameShape(QFrame.Box)
        header_grid = QGridLayout(header_frame)
        
        # Date
        today = datetime.now().strftime("%d-%b-%y")
        
        # Row 0
        header_grid.addWidget(QLabel("Slno:"), 0, 0)
        self.lbl_slno = QLabel("-")
        header_grid.addWidget(self.lbl_slno, 0, 1)
        
        header_grid.addWidget(QLabel("TcNo:"), 0, 2)
        self.lbl_tcno = QLabel(f"SVEE_{today.split('-')[2]}_00X")
        header_grid.addWidget(self.lbl_tcno, 0, 3)
        
        header_grid.addWidget(QLabel("Date:"), 0, 4)
        header_grid.addWidget(QLabel(today), 0, 5)
        
        # Row 1
        header_grid.addWidget(QLabel("Panel Serial No:"), 1, 0)
        self.lbl_panel_serial = QLabel("")
        header_grid.addWidget(self.lbl_panel_serial, 1, 1)
        
        header_grid.addWidget(QLabel("Panel Name:"), 1, 2)
        self.lbl_panel_name = QLabel("")
        header_grid.addWidget(self.lbl_panel_name, 1, 3, 1, 3)
        
        # Row 2
        header_grid.addWidget(QLabel("Customer:"), 2, 0)
        self.lbl_customer_name = QLabel("")
        header_grid.addWidget(self.lbl_customer_name, 2, 1, 1, 5)
        
        # Row 3
        header_grid.addWidget(QLabel("Location / Site:"), 3, 0)
        self.lbl_address = QLabel("")
        self.lbl_address.setWordWrap(True)
        header_grid.addWidget(self.lbl_address, 3, 1, 1, 5)
        
        # Row 4
        header_grid.addWidget(QLabel("Order Reference:"), 4, 0)
        self.lbl_customer_po = QLabel("")
        header_grid.addWidget(self.lbl_customer_po, 4, 1, 1, 5)
        
        # Row 5
        header_grid.addWidget(QLabel("Test Date:"), 5, 0)
        self.lbl_test_date = QLabel("")
        header_grid.addWidget(self.lbl_test_date, 5, 1, 1, 5)
        
        # Row 6
        header_grid.addWidget(QLabel("Project:"), 6, 0)
        self.lbl_project = QLabel("")
        header_grid.addWidget(self.lbl_project, 6, 1, 1, 5)
        
        # Row 5
        header_grid.addWidget(QLabel("Instruments:"), 5, 0)
        header_grid.addWidget(QLabel("Insulation Resistance With 5000V Megger, 200 Gega Ohms, MAKE: HoldPeak"), 5, 1, 1, 5)
        
        self.doc_layout.addWidget(header_frame)
        
        # --- Helper for creating sections ---
        def create_section(title, columns, rows, input_dict):
            frame = QFrame()
            frame.setStyleSheet("QFrame { border: 1px solid black; } QLabel { border: none; } QLineEdit { border: 1px solid #ccc; }")
            layout = QGridLayout(frame)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(5)
            
            # Title Row
            t_lbl = QLabel(title)
            font = t_lbl.font()
            font.setUnderline(True)
            font.setBold(True)
            t_lbl.setFont(font)
            layout.addWidget(t_lbl, 0, 0, 1, 4)
            
            sno_lbl = QLabel("S.No.")
            font = sno_lbl.font()
            font.setBold(True)
            font.setUnderline(True)
            sno_lbl.setFont(font)
            layout.addWidget(sno_lbl, 1, 0)
            
            desc_lbl = QLabel("Description")
            font = desc_lbl.font()
            font.setBold(True)
            font.setUnderline(True)
            desc_lbl.setFont(font)
            layout.addWidget(desc_lbl, 1, 1)
            
            for col_idx, col_name in enumerate(columns):
                c_lbl = QLabel(col_name)
                font = c_lbl.font()
                font.setBold(True)
                font.setUnderline(True)
                c_lbl.setFont(font)
                layout.addWidget(c_lbl, 1, col_idx + 2)
                
            for row_idx, row_item in enumerate(rows):
                sno_val = QLabel(str(row_idx + 1))
                layout.addWidget(sno_val, row_idx + 2, 0)
                
                r_lbl = QLabel(row_item[0])
                layout.addWidget(r_lbl, row_idx + 2, 1)
                
                # Result input
                res_in = QLineEdit()
                res_in.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ccc; padding: 2px;")
                layout.addWidget(res_in, row_idx + 2, 2)
                
                # Remark input
                rem_in = QLineEdit()
                rem_in.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ccc; padding: 2px;")
                layout.addWidget(rem_in, row_idx + 2, 3)
                
                input_dict[row_item[1]] = {"result": res_in, "remark": rem_in}
                
            self.doc_layout.addWidget(frame)
            return frame
            
        # General Inspection
        gen_rows = [
            ("Physical Inspection", "PhysicalInspection"),
            ("Paint Thickness", "PaintThickness"),
            ("Paint Shade", "PaintShade"),
            ("Make of Equipment and Elecrical operation", "MakeOfEquipmentAndElectricalOperation"),
            ("Bill of Material", "BillOfMaterial"),
            ("Aluminum BB Torque", "AluminumBBTorque")
        ]
        self.general_frame = create_section("General Inspection", ["Result", "Remarks"], gen_rows, self.general_inputs)
        
        # IR Helper
        ir_rows = [
            ("Between Phases R-B", "PhaseRB"),
            ("Between Phases Y-B", "PhaseYB"),
            ("Between Phases B-R", "PhaseBR"),
            ("Phase to Neutral", "PhaseToNeutral"),
            ("Phase to Earth", "PhaseToEarth"),
            ("Body to Neutral", "BodyToNeutral")
        ]
        
        self.ir1_frame = create_section("IR-1 | LV Test Before HV Test(500Vac):", ["Result", "Remark"], ir_rows, self.ir1_inputs)
        self.ir2_frame = create_section("IR-2 | High Voltage test at 2.5 Kv for period of ONE minute", ["Result", "Remark"], ir_rows, self.ir2_inputs)
        self.ir3_frame = create_section("IR-3 | LV Test After HV Test (500V)", ["Result", "Remark"], ir_rows, self.ir3_inputs)
        
        # --- Footer ---
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(QLabel("Witnessed By:"))
        self.footer_inputs["WitnessedBy"] = QLineEdit()
        footer_layout.addWidget(self.footer_inputs["WitnessedBy"])
        
        footer_layout.addStretch()
        
        stamp_lbl = QLabel("Signature & Stamp")
        stamp_lbl.setAlignment(Qt.AlignCenter)
        stamp_lbl.setStyleSheet("border: 1px dashed #cbd5e1; color: #94a3b8;")
        stamp_lbl.setFixedSize(150, 100)
        footer_layout.addWidget(stamp_lbl)
        
        footer_layout.addStretch()
        
        footer_layout.addWidget(QLabel("Tested By:"))
        self.footer_inputs["TestedBy"] = QLineEdit()
        footer_layout.addWidget(self.footer_inputs["TestedBy"])
        
        self.doc_layout.addLayout(footer_layout)
        
        notes_lbl = QLabel("Notes: Test Conducted at Ambient temperature of 29 Degree centigrade.")
        self.doc_layout.addWidget(notes_lbl)

        self.doc_layout.addStretch()
        scroll_area.setWidget(self.doc_widget)
        main_layout.addWidget(scroll_area)

    def load_panels(self):
        self.panels = self.quote_service.get_panels_by_quote(self.quote_id)
        
        self.lbl_customer_name.setText(self.header_details.get("CustomerName", ""))
        self.lbl_address.setText(self.header_details.get("FullAddress", ""))
        self.lbl_customer_po.setText(self.header_details.get("CustomerPONo", ""))
        
        date_quote = self.header_details.get("Date_Quote", "")
        if hasattr(date_quote, "strftime"):
            date_quote = date_quote.strftime("%d-%b-%Y")
        self.lbl_test_date.setText(str(date_quote))
        
        self.lbl_project.setText(self.header_details.get("QuoteProjectName", ""))

        self.panel_combo.blockSignals(True)
        self.panel_combo.clear()
        
        for idx, p in enumerate(self.panels):
            p_id = p[0]
            p_serial = p[3]
            p_name = p[4]
            self.panel_combo.addItem(f"{p_serial} - {p_name}", userData=p_id)
            
        self.panel_combo.blockSignals(False)
        
        if self.panel_combo.count() > 0:
            self.panel_combo.setCurrentIndex(0)
            self.on_panel_selected(0)

    def on_panel_selected(self, index):
        if index < 0:
            return
            
        panel_id = self.panel_combo.currentData()
        panel_text = self.panel_combo.currentText()
        parts = panel_text.split(" - ", 1)
        
        self.lbl_slno.setText(str(index + 1))
        self.lbl_panel_serial.setText(parts[0] if len(parts) > 0 else "")
        self.lbl_panel_name.setText(parts[1] if len(parts) > 1 else "")

        # Fetch data
        report_data = self.service.get_or_create_report(panel_id)
        self.populate_data(report_data)

    def populate_data(self, data):
        insp = data.get("inspection", {})
        gen = data.get("general", {})
        ir = data.get("ir", {})

        # Clear first
        for k, v in self.general_inputs.items():
            v["result"].setText("")
            v["remark"].setText("")
        for k, v in self.ir1_inputs.items():
            v["result"].setText("")
            v["remark"].setText("")
        for k, v in self.ir2_inputs.items():
            v["result"].setText("")
            v["remark"].setText("")
        for k, v in self.ir3_inputs.items():
            v["result"].setText("")
            v["remark"].setText("")

        self.footer_inputs["WitnessedBy"].setText(insp.get("WitnessedBy") or "")
        self.footer_inputs["TestedBy"].setText(insp.get("TestedBy") or "")

        # General
        for k, v in self.general_inputs.items():
            v["result"].setText(gen.get(k) or "")
            v["remark"].setText("") # We have single Remarks field in DB for general, let's map it or ignore

        # IR1
        for k, v in self.ir1_inputs.items():
            v["result"].setText(ir.get(f"IR1_{k}") or "")
            
        # IR2
        for k, v in self.ir2_inputs.items():
            v["result"].setText(ir.get(f"IR2_{k}") or "")
            
        # IR3
        for k, v in self.ir3_inputs.items():
            v["result"].setText(ir.get(f"IR3_{k}") or "")


    def save_report(self):
        panel_id = self.panel_combo.currentData()
        if not panel_id:
            return

        inspection_data = {
            "InspectorName": "",
            "Remarks": "",
            "WitnessedBy": self.footer_inputs["WitnessedBy"].text(),
            "TestedBy": self.footer_inputs["TestedBy"].text()
        }

        general_data = {
            "PhysicalInspection": self.general_inputs["PhysicalInspection"]["result"].text(),
            "PaintThickness": self.general_inputs["PaintThickness"]["result"].text(),
            "PaintShade": self.general_inputs["PaintShade"]["result"].text(),
            "MakeOfEquipmentAndElectricalOperation": self.general_inputs["MakeOfEquipmentAndElectricalOperation"]["result"].text(),
            "BillOfMaterial": self.general_inputs["BillOfMaterial"]["result"].text(),
            "AluminumBBTorque": self.general_inputs["AluminumBBTorque"]["result"].text(),
            "Remarks": ""
        }

        ir_data = {}
        for k, v in self.ir1_inputs.items():
            ir_data[f"IR1_{k}"] = v["result"].text()
        for k, v in self.ir2_inputs.items():
            ir_data[f"IR2_{k}"] = v["result"].text()
        for k, v in self.ir3_inputs.items():
            ir_data[f"IR3_{k}"] = v["result"].text()

        try:
            self.service.save_report(panel_id, inspection_data, general_data, ir_data)
            QMessageBox.information(self, "Success", "Test report saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save test report: {e}")

    def save_as_pdf(self):
        panel_name = self.lbl_panel_name.text().replace(" ", "_")
        if not panel_name:
            QMessageBox.warning(self, "Warning", "Please select a panel first.")
            return

        test_type, ok = QInputDialog.getItem(self, "Select Test Type", "Select Test Type for PDF:", ["Hv-Test", "Lv-Test"], 0, False)
        if not ok:
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save as PDF", f"{panel_name}_{test_type}_TestCertificate.pdf", "PDF Files (*.pdf)")
        if not file_path:
            return

        is_lv = (test_type == "Lv-Test")
        if is_lv:
            self.ir2_frame.hide()
            self.ir3_frame.hide()

        try:
            pdf_writer = QPdfWriter(file_path)
            pdf_writer.setPageSize(QPageSize.A4)
            pdf_writer.setPageMargins(QMarginsF(10, 10, 10, 10), QPageLayout.Millimeter)
            
            painter = QPainter()
            painter.begin(pdf_writer)
            try:
                # Scale the widget to fit the A4 page width
                rect = painter.viewport()
                size = self.doc_widget.size()
                
                scale = rect.width() / size.width()
                painter.scale(scale, scale)
                
                self.doc_widget.render(painter, QPoint(0, 0))
            finally:
                painter.end()
                del painter
            
            QMessageBox.information(self, "Success", f"PDF saved successfully to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate PDF:\n{e}")
        finally:
            if is_lv:
                self.ir2_frame.show()
                self.ir3_frame.show()
