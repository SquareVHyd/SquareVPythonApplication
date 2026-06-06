import os
import re
import time
import urllib.parse
import webbrowser
import pandas as pd
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
    QLabel, QGroupBox, QFormLayout, QTextEdit, QRadioButton,
    QFileDialog, QMessageBox, QProgressBar, QComboBox, QCheckBox,
    QSlider, QDialog, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QTextCursor

class WhatsAppWorker(QThread):
    progress = Signal(int)
    status = Signal(str, str) # message, color
    finished = Signal()

    def __init__(self, valid_links, delay):
        super().__init__()
        self.valid_links = valid_links
        self.delay = delay
        self.is_running = True

    def run(self):
        total = len(self.valid_links)
        for i, (name, num, url) in enumerate(self.valid_links):
            if not self.is_running:
                break
            
            self.status.emit(f"🚀 Sending {i+1}/{total}: {name}", "cyan")
            webbrowser.open(url)
            self.status.emit(f"✅ Sent: {name}", "lime")
            
            self.progress.emit(int(((i+1)/total)*100))
            
            if i < total - 1:
                for r in range(self.delay, 0, -1):
                    if not self.is_running:
                        break
                    self.status.emit(f"⏳ Next in {r}s...", "white")
                    time.sleep(1)
        
        self.finished.emit()

    def stop(self):
        self.is_running = False

class WhatsAppSenderPage(QWidget):
    def __init__(self):
        super().__init__()
        self.is_sending = False
        self.valid_links = []
        self.worker = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("📱 WhatsApp Bulk Manager")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #1565C0; margin-bottom: 10px;")
        layout.addWidget(header)

        # Mode Selection
        mode_group = QGroupBox("Mode Selection")
        mode_layout = QHBoxLayout(mode_group)
        self.radio_csv = QRadioButton("📊 CSV (Bulk)")
        self.radio_manual = QRadioButton("✏️ Manual (Single)")
        self.radio_csv.setChecked(True)
        self.radio_csv.toggled.connect(self.toggle_mode)
        mode_layout.addWidget(self.radio_csv)
        mode_layout.addWidget(self.radio_manual)
        layout.addWidget(mode_group)

        # Input Section
        self.input_group = QGroupBox("Entry Details & Column Mapping")
        self.input_form = QFormLayout(self.input_group)

        # CSV Row
        csv_layout = QHBoxLayout()
        self.ent_csv_path = QLineEdit()

        self.btn_browse = QPushButton("📁 Browse")
        self.btn_browse.clicked.connect(self.browse_csv)
        csv_layout.addWidget(self.ent_csv_path)
        csv_layout.addWidget(self.btn_browse)
        self.input_form.addRow("CSV File:", csv_layout)

        # Manual Fields
        self.ent_prefix = QLineEdit("Dear")
        self.ent_name = QLineEdit()
        self.ent_suffix = QComboBox()
        self.ent_suffix.addItems(["", "Sir", "Madam", "Gaaru"])
        self.ent_suffix.setEditable(True)
        self.ent_num = QLineEdit()
        self.ent_company = QLineEdit()
        self.check_include_company = QCheckBox("Include Company Name")
        self.check_include_company.setChecked(True)

        manual_row = QHBoxLayout()
        manual_row.addWidget(QLabel("Prefix:"))
        manual_row.addWidget(self.ent_prefix, 1)
        manual_row.addWidget(QLabel("Name:"))
        manual_row.addWidget(self.ent_name, 2)
        manual_row.addWidget(QLabel("Suffix:"))
        manual_row.addWidget(self.ent_suffix, 1)
        self.input_form.addRow("Manual Data:", manual_row)
        
        self.input_form.addRow("Phone Number:", self.ent_num)
        self.input_form.addRow("Company (Manual):", self.ent_company)
        self.input_form.addRow("", self.check_include_company)
        
        layout.addWidget(self.input_group)

        # Message Template
        msg_group = QGroupBox("📝 Message Template")
        msg_layout = QVBoxLayout(msg_group)
        
        tool_bar = QHBoxLayout()
        formats = [
            ("Bold", lambda: self.wrap_text("*", "*")),
            ("Italic", lambda: self.wrap_text("_", "_")),
            ("Strike", lambda: self.wrap_text("~", "~")),
        ]
        for txt, cmd in formats:
            btn = QPushButton(txt)
            btn.clicked.connect(cmd)
            btn.setFixedWidth(60)
            tool_bar.addWidget(btn)
        
        tool_bar.addStretch()
        btn_preview = QPushButton("👁️ PREVIEW")
        btn_preview.clicked.connect(self.show_preview)
        btn_preview.setStyleSheet("background-color: #9C27B0; color: white;")
        tool_bar.addWidget(btn_preview)
        
        msg_layout.addLayout(tool_bar)
        self.msg_text = QTextEdit()
        self.msg_text.setPlaceholderText("Type your message here...")
        self.msg_text.setText("✅ *Panel Quote Attached*\n💬 We value your business!")
        msg_layout.addWidget(self.msg_text)
        
        layout.addWidget(msg_group)

        # Config & Logs
        bottom_row = QHBoxLayout()
        
        config_group = QGroupBox("Configuration")
        config_form = QFormLayout(config_group)
        self.ent_signature = QLineEdit("Square V Engineering Enterprises, Hyderabad")
        self.slider_delay = QSlider(Qt.Horizontal)
        self.slider_delay.setRange(5, 60)
        self.slider_delay.setValue(40)
        self.lbl_delay = QLabel("40s")
        self.slider_delay.valueChanged.connect(lambda v: self.lbl_delay.setText(f"{v}s"))
        
        config_form.addRow("Signature:", self.ent_signature)
        config_form.addRow("Delay:", self.slider_delay)
        config_form.addRow("", self.lbl_delay)
        bottom_row.addWidget(config_group, 1)

        log_group = QGroupBox("📊 Activity Log")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #1e1e1e; color: #00FF00; font-family: Consolas;")
        log_layout.addWidget(self.log_text)
        bottom_row.addWidget(log_group, 1)
        
        layout.addLayout(bottom_row)

        # Controls
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        self.lbl_status = QLabel("✅ Ready")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_status)

        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("🚀 START SENDING")
        self.btn_start.clicked.connect(self.process_contacts)
        self.btn_start.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 10px;")
        
        self.btn_stop = QPushButton("🛑 STOP")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_sending)
        self.btn_stop.setStyleSheet("background-color: #f44336; color: white;")

        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_stop)
        btn_row.addWidget(QPushButton("📋 Copy Links", clicked=self.copy_links))
        btn_row.addWidget(QPushButton("🧹 Clear", clicked=self.clear_all))
        layout.addLayout(btn_row)

        self.toggle_mode()

    def wrap_text(self, start_tag, end_tag):
        cursor = self.msg_text.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.insertText(f"{start_tag}{text}{end_tag}")

    def toggle_mode(self):
        is_bulk = self.radio_csv.isChecked()
        self.ent_csv_path.setEnabled(is_bulk)
        self.btn_browse.setEnabled(is_bulk)
        self.ent_name.setEnabled(not is_bulk)
        self.ent_num.setEnabled(not is_bulk)
        self.ent_company.setEnabled(not is_bulk)

    def browse_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if path:
            self.ent_csv_path.setText(path)
            self.log_text.append(f"📁 CSV Loaded: {os.path.basename(path)}")

    def clean_india_number(self, n):
        n = re.sub(r'[^\d+]', '', str(n).rstrip('.0'))
        if n.startswith('+91') and len(n) == 13: return n
        if len(n) == 10 and n[0] in '6789': return '+91' + n
        if len(n) == 12 and n.startswith('91'): return '+' + n
        return None

    def show_preview(self):
        if self.radio_csv.isChecked():
            name, comp = "John Doe", "Tech Corp Ltd"
        else:
            name = self.ent_name.text() or "John Doe"
            comp = self.ent_company.text() or "Tech Corp Ltd"
        
        greet = f"{self.ent_prefix.text()} {name} {self.ent_suffix.currentText()}".strip()
        comp_str = f"\nCompany: {comp}" if self.check_include_company.isChecked() else ""
        full_msg = f"{greet}{comp_str}\n\n{self.msg_text.toPlainText()}\n\n{self.ent_signature.text()}"
        
        dlg = QDialog(self)
        dlg.setWindowTitle("Message Preview")
        dlg.resize(400, 400)
        vbox = QVBoxLayout(dlg)
        preview = QTextEdit(full_msg)
        preview.setReadOnly(True)
        vbox.addWidget(preview)
        btn = QPushButton("Close")
        btn = QPushButton("❌ Close")
        btn.clicked.connect(dlg.accept)
        vbox.addWidget(btn)
        dlg.exec()

    def process_contacts(self):
        msg_tmpl = self.msg_text.toPlainText().strip()
        if not msg_tmpl:
            QMessageBox.warning(self, "Error", "Message is empty!")
            return

        contacts = []
        if self.radio_csv.isChecked():
            path = self.ent_csv_path.text()
            if not os.path.exists(path):
                QMessageBox.warning(self, "Error", "Select valid CSV!")
                return
            df = pd.read_csv(path, dtype=str).fillna('')
            if 'SendYN' in df.columns:
                df = df[df['SendYN'].str.strip().str.upper() != 'N']
            contacts = df.to_dict('records')
        else:
            n = self.ent_name.text().strip()
            num = self.ent_num.text().strip()
            if not n or not num:
                QMessageBox.warning(self, "Error", "Missing Name/Number!")
                return
            contacts = [{'Name': n, 'Number': num, 'Company': self.ent_company.text()}]

        self.valid_links = []
        prefix = self.ent_prefix.text().strip()
        suffix = self.ent_suffix.currentText().strip()
        signature = self.ent_signature.text().strip()

        for c in contacts:
            name = str(c.get('Name', '')).strip()
            comp = str(c.get('Company', '')).strip()
            num = self.clean_india_number(c.get('Number', ''))
            
            if num:
                greet = f"{prefix} {name} {suffix}".strip()
                comp_str = f"\nCompany: {comp}" if self.check_include_company.isChecked() and comp else ""
                full_msg = urllib.parse.quote(f"{greet}{comp_str}\n\n{msg_tmpl}\n\n{signature}")
                url = f"https://web.whatsapp.com/send?phone={num[1:]}&text={full_msg}"
                self.valid_links.append((name, num, url))

        if not self.valid_links:
            QMessageBox.information(self, "Finished", "No valid numbers found to send.")
            return

        self.is_sending = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        
        self.worker = WhatsAppWorker(self.valid_links, self.slider_delay.value())
        self.worker.progress.connect(self.progress.setValue)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.on_sending_finished)
        self.worker.start()

    def update_status(self, msg, color):
        self.lbl_status.setText(msg)
        self.lbl_status.setStyleSheet(f"color: {color};")
        if "Sent" in msg or "CSV" in msg:
            self.log_text.append(msg)

    def on_sending_finished(self):
        self.is_sending = False
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_status.setText("✅ Done")
        self.lbl_status.setStyleSheet("color: lime;")

    def stop_sending(self):
        if self.worker:
            self.worker.stop()
            self.lbl_status.setText("🛑 Stopped")

    def copy_links(self):
        if not self.valid_links: return
        txt = "\n".join([f"{n} ({p}): {u}" for n, p, u in self.valid_links])
        QApplication.clipboard().setText(txt)
        QMessageBox.information(self, "Copied", "Links copied to clipboard!")

    def clear_all(self):
        self.log_text.clear()
        self.progress.setValue(0)
        self.ent_name.clear()
        self.ent_num.clear()
        self.ent_company.clear()