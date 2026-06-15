from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
    QLabel, QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QMessageBox, QComboBox, QFileDialog,
    QTextEdit, QSplitter
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from sqlalchemy import text
from app.config.database import get_session
from datetime import datetime
import csv
import os
import tempfile
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

# reportlab imports for PDF generation
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors as rl_colors

# Using the DSN provided in the request
DSN_NAME = "PostgreSQLLH"

# Path to the logo used inside the drawn header
LOGO_PATH = os.path.join(os.path.dirname(__file__), "Images", "SQV_Header.png")


# ── Reusable header function ──────────────────────────────────────────────────
def draw_sqv_header(c, page_w, page_h, doc_number="SVEE/DOC/ZED1/001",
                    page_no=1, total_pages=1):
    """
    Draws the Square V Engineering Enterprises header on a reportlab canvas.

    Layout (landscape A4):
    ┌──────────┬──────────────────────────────────────────┬──────────────┐
    │  LOGO    │  Square V Engineering Enterprises        │  Document    │
    │          │  address lines                           │──────────────│
    │          │  GSTN                                    │  doc_number  │
    └──────────┴──────────────────────────────────────────┴──────────────┘
    Date: DD-Mon-YYYY HH:MM                           Page N of M
    """
    # ── dimensions ──────────────────────────────────────────────────────────
    header_h    = 30 * mm
    header_top  = page_h - 5 * mm
    header_bot  = header_top - header_h
    left_x      = 8 * mm
    right_x     = page_w - 8 * mm
    box_w       = right_x - left_x

    col1_w = 28 * mm   # logo column
    col3_w = 40 * mm   # document ref column
    col2_w = box_w - col1_w - col3_w

    x0 = left_x
    x1 = x0 + col1_w   # start of address column
    x2 = x1 + col2_w   # start of doc-ref column
    x3 = x2 + col3_w   # right edge

    # ── outer border ────────────────────────────────────────────────────────
    c.setLineWidth(1.2)
    c.setStrokeColor(rl_colors.black)
    c.rect(x0, header_bot, box_w, header_h, fill=0, stroke=1)

    # ── vertical dividers ───────────────────────────────────────────────────
    c.setLineWidth(0.8)
    c.line(x1, header_bot, x1, header_top)
    c.line(x2, header_bot, x2, header_top)

    # ── horizontal divider inside doc-ref column ────────────────────────────
    mid_y = header_bot + header_h * 0.52
    c.line(x2, mid_y, x3, mid_y)

    # ── LOGO (left column) ──────────────────────────────────────────────────
    if os.path.isfile(LOGO_PATH):
        pad = 2 * mm
        c.drawImage(
            ImageReader(LOGO_PATH),
            x0 + pad, header_bot + pad,
            width=col1_w - 2 * pad,
            height=header_h - 2 * pad,
            preserveAspectRatio=True,
            mask='auto'
        )
    else:
        _draw_logo_fallback(c, x0, header_bot, col1_w, header_h)

    # ── CENTRE COLUMN: company name + address ───────────────────────────────
    cx = x1 + col2_w / 2

    c.setFillColor(rl_colors.black)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(cx, header_bot + header_h - 7 * mm,
                        "Square V Engineering Enterprises")

    addr_lines = [
        ("Helvetica",      "Survey No:298(P), Pipe Line Road, Road No:14,"),
        ("Helvetica",      "Phase-I, IDA, Jeedimetla, Hyderabad - 500055,"),
        ("Helvetica",      "Telangana,  Mail: info.squarev@gamil.com,"),
        ("Helvetica-Bold", "GSTN:36AFKFS1080B1Z7"),
    ]
    line_gap = 4.8 * mm
    y_addr = header_bot + header_h - 13 * mm
    for i, (font, text) in enumerate(addr_lines):
        c.setFont(font, 9)
        c.drawCentredString(cx, y_addr - i * line_gap, text)

    # ── RIGHT COLUMN: Document label + number ───────────────────────────────
    rx = x2 + col3_w / 2

    c.setFont("Helvetica", 9)
    c.setFillColor(rl_colors.black)
    c.drawCentredString(rx, mid_y + 4 * mm, "Document")

    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(rx, header_bot + header_h * 0.18, doc_number)

    # ── DATE (below header, left) ───────────────────────────────────────────
    now_str = datetime.now().strftime("%d-%b-%Y  %H:%M")
    c.setFont("Helvetica", 9)
    c.setFillColor(rl_colors.black)
    c.drawString(x0, header_bot - 5 * mm, f"Date: {now_str}")

    # ── PAGE NUMBER (below header, right) ───────────────────────────────────
    c.drawRightString(x3, header_bot - 5 * mm, f"Page {page_no} of {total_pages}")

    # return y where body content should start
    return header_bot - 12 * mm


def _draw_logo_fallback(c, x, y, w, h):
    """Coloured triangle logo fallback when PNG is missing."""
    cx, cy = x + w / 2, y + h / 2
    s = min(w, h) * 0.55

    c.setFillColor(rl_colors.HexColor("#F5C400"))
    p = c.beginPath()
    p.moveTo(cx - s*0.05, cy); p.lineTo(cx - s*0.55, cy + s*0.5); p.lineTo(cx + s*0.45, cy + s*0.5)
    p.close(); c.drawPath(p, fill=1, stroke=0)

    c.setFillColor(rl_colors.HexColor("#D0021B"))
    p = c.beginPath()
    p.moveTo(cx + s*0.05, cy); p.lineTo(cx + s*0.55, cy + s*0.5); p.lineTo(cx - s*0.45, cy + s*0.5)
    p.close(); c.drawPath(p, fill=1, stroke=0)

    c.setFillColor(rl_colors.HexColor("#003087"))
    p = c.beginPath()
    p.moveTo(cx - s*0.55, cy + s*0.1); p.lineTo(cx, cy - s*0.5); p.lineTo(cx + s*0.55, cy + s*0.1)
    p.lineTo(cx + s*0.35, cy + s*0.1); p.lineTo(cx, cy - s*0.3); p.lineTo(cx - s*0.35, cy + s*0.1)
    p.close(); c.drawPath(p, fill=1, stroke=0)
# ─────────────────────────────────────────────────────────────────────────────

class DB:
    @staticmethod
    def execute(sql, params=None, fetch=False, commit=False):
        with get_session() as session:
            try:
                result = session.execute(text(sql), params or {})
                if fetch:
                    return [list(row) for row in result.fetchall()]
                if commit:
                    session.commit()
                return True 
            except Exception as exc:
                print(f"Database Error: {exc}")
                if commit: session.rollback()
                return False 

    @staticmethod
    def fetchone(sql, params=None):
        with get_session() as session:
            try:
                result = session.execute(text(sql), params or {})
                row = result.fetchone()
                return list(row) if row else None
            except Exception as exc:
                print(f"Fetch Failed: {exc}")
                return None


class ZEDScoreCardPage(QWidget):
    """PySide6 implementation of the ZED ScoreCard management tool."""
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        category_map = {
            "Swachh Workplace": "🧹",
            "Quality": "🏅",
            "Safety": "🛡️",
            "Energy Management": "⚡",
            "Delivery": "🚚",
            "Maintenance": "🛠️",
            "Legal": "⚖️"
        }
        for cat_name, icon in category_map.items():
            self.tabs.addTab(ParameterWorkspaceWidget(cat_name), f"{icon} {cat_name}")
            
        layout.addWidget(self.tabs)


class ParameterWorkspaceWidget(QWidget):
    """An individual category workspace for ZED ScoreCard parameters."""
    def __init__(self, category_name):
        super().__init__()
        self.category_name = category_name
        self.editing_record_id = None
        self.setup_ui()
        self.refresh_kpis()
        self.refresh_grid()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Left Panel: Form Operations
        form_group = QGroupBox(f"Manage {self.category_name} Records")
        form_layout = QFormLayout(form_group)
        
        self.cb_metric = QComboBox()
        self.cb_metric.currentTextChanged.connect(self.on_form_kpi_selected)
        
        self.cb_sub = QComboBox()
        self.cb_sub.setEditable(True)
        
        self.ent_month = QLineEdit(datetime.now().strftime("%Y-%m"))
        self.ent_value = QLineEdit()
        self.txt_remarks = QTextEdit()
        self.txt_remarks.setMaximumHeight(80)
        
        self.btn_save = QPushButton("💾 Save Data Entry")
        self.btn_save.clicked.connect(self.save_record)
        self.btn_save.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        
        self.btn_cancel = QPushButton("❌ Cancel Edit")
        self.btn_cancel.clicked.connect(self.clear_form_fields)
        self.btn_cancel.hide()

        form_layout.addRow("KPI / Parameter:", self.cb_metric)
        form_layout.addRow("Area / Zone / Customer:", self.cb_sub)
        form_layout.addRow("Target Month (YYYY-MM):", self.ent_month)
        form_layout.addRow("Actual Value:", self.ent_value)
        form_layout.addRow("Remarks:", self.txt_remarks)
        form_layout.addRow(self.btn_save)
        form_layout.addRow(self.btn_cancel)
        
        # Right Panel: Filters and Data Grid
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Interactive Trend Filters
        filter_group = QGroupBox("Trend Filters")
        filter_layout = QHBoxLayout(filter_group)
        
        self.ent_start = QLineEdit("2025-04")
        self.ent_end = QLineEdit("2026-03")
        self.cb_filter_kpi = QComboBox()
        self.cb_filter_kpi.currentTextChanged.connect(self.on_filter_kpi_changed)
        
        self.cb_filter_zone = QComboBox()
        self.cb_filter_zone.currentTextChanged.connect(lambda: self.refresh_grid())
        
        btn_reset = QPushButton("🧹 Reset Filters")
        btn_reset.clicked.connect(self.reset_filters)
        
        filter_layout.addWidget(QLabel("From:"))
        filter_layout.addWidget(self.ent_start)
        filter_layout.addWidget(QLabel("To:"))
        filter_layout.addWidget(self.ent_end)
        filter_layout.addWidget(QLabel("KPI:"))
        filter_layout.addWidget(self.cb_filter_kpi)
        filter_layout.addWidget(QLabel("Zone:"))
        filter_layout.addWidget(self.cb_filter_zone)
        filter_layout.addWidget(btn_reset)
        
        # Trend Chart (Matplotlib)
        self.figure, self.ax = plt.subplots(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        self.figure.patch.set_facecolor('#ffffff')
        self.ax.set_facecolor('#ffffff')

        # Data Grid
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "KPI", "Zone/Area", "Month", "Value", "Remarks"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Splitter for Grid and Chart
        data_splitter = QSplitter(Qt.Vertical)
        data_splitter.addWidget(self.canvas)
        data_splitter.addWidget(self.table)
        
        # Action Bar
        action_layout = QHBoxLayout()
        btn_edit = QPushButton("✏️ Modify Selected")
        btn_edit.clicked.connect(self.load_selected_for_edit)

        btn_delete = QPushButton("🗑️ Delete Selected")
        btn_delete.clicked.connect(self.delete_selected_record)

        btn_export = QPushButton("📊 Export to CSV")
        btn_export.clicked.connect(self.export_to_csv)

        btn_pdf = QPushButton("📄 toPdf")
        btn_pdf.setStyleSheet(
            "background-color: #1565C0; color: white; font-weight: bold; padding: 6px 14px;"
        )
        btn_pdf.setToolTip("Save the current trend chart as a landscape PDF with SQV header")
        btn_pdf.clicked.connect(self.export_chart_to_pdf)

        action_layout.addWidget(btn_edit)
        action_layout.addWidget(btn_delete)
        action_layout.addWidget(btn_export)
        action_layout.addWidget(btn_pdf)
        action_layout.addStretch()
        
        right_layout.addWidget(filter_group)
        right_layout.addWidget(data_splitter)
        right_layout.addLayout(action_layout)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(form_group)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)

    def clear_form_fields(self):
        self.editing_record_id = None
        self.cb_metric.setCurrentIndex(-1)
        self.cb_sub.setCurrentText("")
        self.ent_value.clear()
        self.txt_remarks.clear()
        self.btn_save.setText("Save Data Entry")
        self.btn_cancel.hide()

    def refresh_kpis(self):
        query = """
            SELECT m.kpi_name FROM metrics m 
            JOIN categories c ON m.category_id = c.id 
            WHERE c.name = :name ORDER BY m.kpi_name
        """
        rows = DB.execute(query, {"name": self.category_name}, fetch=True)
        kpi_list = [row[0] for row in rows]
        self.cb_metric.clear()
        self.cb_metric.addItems(kpi_list)
        self.cb_filter_kpi.clear()
        self.cb_filter_kpi.addItem("- All Parameters -")
        self.cb_filter_kpi.addItems(kpi_list)

    def on_form_kpi_selected(self, kpi):
        if not kpi: return
        query = "SELECT DISTINCT s.sub_name FROM sub_targets s JOIN metrics m ON s.metric_id = m.id WHERE m.kpi_name = :kpi ORDER BY s.sub_name"
        rows = DB.execute(query, {"kpi": kpi}, fetch=True)
        zones = [row[0] for row in rows]
        self.cb_sub.clear()
        self.cb_sub.addItems(zones)

    def on_filter_kpi_changed(self, kpi):
        self.refresh_grid()

    def reset_filters(self):
        self.cb_filter_kpi.setCurrentIndex(0)
        self.cb_filter_zone.setCurrentIndex(-1)
        self.refresh_grid()

    def refresh_grid(self):
        self.table.setRowCount(0)
        start_str, end_str = self.ent_start.text().strip(), self.ent_end.text().strip()
        
        try:
            start_iso = datetime.strptime(start_str, "%Y-%m").strftime("%Y-%m-01")
            end_iso = datetime.strptime(end_str, "%Y-%m").strftime("%Y-%m-01")
        except ValueError:
            return

        query = """
            SELECT r.id, m.kpi_name, COALESCE(s.sub_name, '- Global -'), r.record_date, r.actual_value, COALESCE(r.remarks, '') 
            FROM monthly_records r 
            JOIN metrics m ON r.metric_id = m.id 
            JOIN categories c ON m.category_id = c.id 
            LEFT JOIN sub_targets s ON r.sub_target_id = s.id 
            WHERE c.name = :cat_name AND r.record_date BETWEEN :start AND :end
        """
        params = {"cat_name": self.category_name, "start": start_iso, "end": end_iso}
        
        fkpi = self.cb_filter_kpi.currentText()
        if fkpi and fkpi != "- All Parameters -":
            query += " AND m.kpi_name = :fkpi"
            params["fkpi"] = fkpi
            
        fzone = self.cb_filter_zone.currentText()
        if fzone and fzone != "- All Zones -":
            if fzone == "- Global -":
                query += " AND s.sub_name IS NULL"
            else:
                query += " AND s.sub_name = :fzone"
                params["fzone"] = fzone

        query += " ORDER BY r.record_date ASC"
        rows = DB.execute(query, params, fetch=True)
        
        self.table.setRowCount(len(rows))
        chart_data = []
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                if j == 3 and val:
                    item.setText(val.strftime("%b-%y"))
                self.table.setItem(i, j, item)
            chart_data.append((row[3].strftime("%b-%y"), row[4]))
        
        self.update_chart(chart_data, fkpi, fzone)

    def update_chart(self, data, kpi, zone):
        self.ax.clear()
        if not data:
            self.ax.text(0.5, 0.5, "No data for selected filters", ha='center', va='center')
        else:
            months, values = zip(*data)
            self.ax.plot(months, values, marker='o', color='#2e5a1c', linewidth=2)
            self.ax.set_title(f"Trend: {kpi} ({zone})", fontsize=10)
            self.ax.grid(True, linestyle='--', alpha=0.6)
            self.figure.autofmt_xdate()
        self.canvas.draw()

    # ── PDF EXPORT ─────────────────────────────────────────────────────────────
    def export_chart_to_pdf(self):
        """Save the current trend chart as a landscape A4 PDF with the SQV header."""
        # Set default PDF filename to match the currently selected KPI
        selected_kpi = self.cb_filter_kpi.currentText()
        pdf_filename = selected_kpi if selected_kpi != "- All Parameters -" else self.category_name

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Chart as PDF",
            f"{pdf_filename}_Trend_Report.pdf",
            "PDF Files (*.pdf)"
        )
        if not path:
            return

        tmp_path = None
        try:
            # 1. Render chart to a high-res temp PNG
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name

            export_fig, export_ax = plt.subplots(figsize=(13, 5))
            export_fig.patch.set_facecolor('#ffffff')
            export_ax.set_facecolor('#ffffff')

            lines = self.ax.get_lines()
            if lines:
                line = lines[0]
                export_ax.plot(line.get_xdata(), line.get_ydata(),
                               marker='o', color='#2e5a1c', linewidth=2)
                export_ax.set_title(self.ax.get_title(), fontsize=12, fontweight='bold')
                export_ax.grid(True, linestyle='--', alpha=0.6)
                export_fig.autofmt_xdate()
            else:
                export_ax.text(0.5, 0.5, "No data for selected filters",
                               ha='center', va='center', fontsize=14)

            export_fig.savefig(tmp_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(export_fig)

            # 2. Build landscape A4 PDF
            page_w, page_h = landscape(A4)
            c = rl_canvas.Canvas(path, pagesize=landscape(A4))

            # Draw the SQV header; get y where body starts
            content_y = draw_sqv_header(c, page_w, page_h,
                                         doc_number="SVEE/DOC/ZED1/001",
                                         page_no=1, total_pages=1)

            # Display KPI name in place of Category label when a filter is active
            c.setFont("Helvetica-Bold", 11)
            c.setFillColor(rl_colors.black)
            display_label = f"KPI:  {selected_kpi}" if selected_kpi != "- All Parameters -" else f"Category:  {self.category_name}"
            c.drawString(10 * mm, content_y, display_label)
            content_y -= 6 * mm

            # Chart image — fills remaining space above footer
            margin      = 10 * mm
            chart_bottom = 12 * mm
            chart_h     = content_y - chart_bottom
            chart_w     = page_w - 2 * margin

            c.drawImage(
                ImageReader(tmp_path),
                x=margin, y=chart_bottom,
                width=chart_w, height=chart_h,
                preserveAspectRatio=True
            )

            # Footer rule
            c.setStrokeColor(rl_colors.HexColor("#cccccc"))
            c.setLineWidth(0.5)
            c.line(margin, 10 * mm, page_w - margin, 10 * mm)
            c.setFont("Helvetica-Oblique", 7)
            c.setFillColor(rl_colors.HexColor("#888888"))
            c.drawCentredString(page_w / 2, 5 * mm, "Generated by ZED ScoreCard System")

            c.save()

        except Exception as e:
            QMessageBox.critical(self, "PDF Export Error", str(e))
            return
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

        QMessageBox.information(self, "PDF Saved", f"Chart exported successfully:\n{path}")
    # ── END PDF EXPORT ─────────────────────────────────────────────────────────

    def save_record(self):
        kpi = self.cb_metric.currentText()
        sub = self.cb_sub.currentText().strip()
        month_str = self.ent_month.text().strip()
        val_str = self.ent_value.text().strip()
        rem = self.txt_remarks.toPlainText().strip()

        if not all([kpi, month_str, val_str]):
            QMessageBox.warning(self, "Input Error", "Please fill in KPI, Month, and Value.")
            return

        try:
            val_num = float(val_str)
            iso_date = datetime.strptime(month_str, "%Y-%m").strftime("%Y-%m-01")
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid numeric value or date format (YYYY-MM).")
            return

        with get_session() as session:
            try:
                cat_id = session.execute(text("SELECT id FROM categories WHERE name = :name"), {"name": self.category_name}).scalar()
                metric_id = session.execute(text("SELECT id FROM metrics WHERE category_id = :cat_id AND kpi_name = :kpi"), {"cat_id": cat_id, "kpi": kpi}).scalar()

                sub_id = None
                if sub and sub != "- Global -":
                    res = session.execute(text("SELECT id FROM sub_targets WHERE metric_id = :mid AND sub_name = :sub"), {"mid": metric_id, "sub": sub}).fetchone()
                    if not res:
                        session.execute(text("INSERT INTO sub_targets (metric_id, sub_name) VALUES (:mid, :sub)"), {"mid": metric_id, "sub": sub})
                        session.commit()
                        sub_id = session.execute(text("SELECT id FROM sub_targets WHERE metric_id = :mid AND sub_name = :sub"), {"mid": metric_id, "sub": sub}).scalar()
                    else:
                        sub_id = res[0]

                if self.editing_record_id:
                    session.execute(text("UPDATE monthly_records SET actual_value=:val, remarks=:rem, record_date=:date, sub_target_id=:sid WHERE id=:id"), 
                                 {"val": val_num, "rem": rem, "date": iso_date, "sid": sub_id, "id": self.editing_record_id})
                else:
                    session.execute(text("INSERT INTO monthly_records (metric_id, sub_target_id, record_date, actual_value, remarks) VALUES (:mid, :sid, :date, :val, :rem)"),
                                 {"mid": metric_id, "sid": sub_id, "date": iso_date, "val": val_num, "rem": rem})
                
                session.commit()
                QMessageBox.information(self, "Success", "Record saved to cloud database.")
                self.clear_form_fields()
                self.refresh_grid()
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Database Error", str(e))

    def load_selected_for_edit(self):
        row = self.table.currentRow()
        if row < 0: return
        self.editing_record_id = self.table.item(row, 0).text()
        self.cb_metric.setCurrentText(self.table.item(row, 1).text())
        zone_val = self.table.item(row, 2).text()
        self.cb_sub.setCurrentText("" if zone_val == "- Global -" else zone_val)
        try:
            dt = datetime.strptime(self.table.item(row, 3).text(), "%b-%y")
            self.ent_month.setText(dt.strftime("%Y-%m"))
        except: pass
        self.ent_value.setText(self.table.item(row, 4).text())
        self.txt_remarks.setText(self.table.item(row, 5).text())
        self.btn_save.setText("Update Saved Record")
        self.btn_cancel.show()

    def delete_selected_record(self):
        row = self.table.currentRow()
        if row < 0: return
        if QMessageBox.question(self, "Delete", "Remove this record?") == QMessageBox.Yes:
            record_id = int(self.table.item(row, 0).text())
            DB.execute("DELETE FROM monthly_records WHERE id = :id", {"id": record_id}, commit=True)
            self.refresh_grid()

    def export_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Report", "", "CSV Files (*.csv)")
        if not path: return
        try:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "KPI", "Zone", "Month", "Value", "Remarks"])
                for row in range(self.table.rowCount()):
                    writer.writerow([self.table.item(row, col).text() for col in range(6)])
            QMessageBox.information(self, "Success", "Export complete.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
