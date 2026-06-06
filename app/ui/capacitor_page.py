import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLineEdit, 
    QLabel, QGroupBox, QFormLayout, QMessageBox
)

class CapacitorPage(QWidget):
    """PySide6 implementation of the Capacitor R1 power factor correction tool."""
    STEPS = [5, 10, 15, 25, 50, 100]

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Inputs Section
        input_group = QGroupBox("Power Factor Correction Inputs")
        form_layout = QFormLayout(input_group)
        
        self.ent_kwh_start = QLineEdit(); self.ent_kwh_start.setPlaceholderText("Enter KWH Start")
        self.ent_kwh_end = QLineEdit(); self.ent_kwh_end.setPlaceholderText("Enter KWH End")
        self.ent_kvah_start = QLineEdit(); self.ent_kvah_start.setPlaceholderText("Enter KVAH Start")
        self.ent_kvah_end = QLineEdit(); self.ent_kvah_end.setPlaceholderText("Enter KVAH End")
        self.ent_days = QLineEdit(); self.ent_days.setPlaceholderText("Enter Days")
        self.ent_hp = QLineEdit(); self.ent_hp.setPlaceholderText("Enter Contracted Load (HP)")
        self.ent_md = QLineEdit(); self.ent_md.setPlaceholderText("Enter Recorded MD (kVA)")
        self.ent_voltage = QLineEdit("415")
        self.ent_freq = QLineEdit("50")
        self.ent_pf_target = QLineEdit("0.99")
        
        form_layout.addRow("KWH Start:", self.ent_kwh_start)
        form_layout.addRow("KWH End:", self.ent_kwh_end)
        form_layout.addRow("KVAH Start:", self.ent_kvah_start)
        form_layout.addRow("KVAH End:", self.ent_kvah_end)
        form_layout.addRow("Days:", self.ent_days)
        form_layout.addRow("Contracted Load (HP):", self.ent_hp)
        form_layout.addRow("Recorded MD (kVA):", self.ent_md)
        form_layout.addRow("Voltage (V):", self.ent_voltage)
        form_layout.addRow("Frequency (Hz):", self.ent_freq)
        form_layout.addRow("Target PF:", self.ent_pf_target)
        
        layout.addWidget(input_group)
        
        calc_btn = QPushButton("🧮 Calculate")
        calc_btn.clicked.connect(self.calculate)
        calc_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        layout.addWidget(calc_btn)
        
        # Outputs Section
        output_group = QGroupBox("Results")
        out_layout = QFormLayout(output_group)
        
        self.lbl_pf = QLabel("--")
        self.lbl_kw = QLabel("--")
        self.lbl_kva = QLabel("--")
        self.lbl_q_req = QLabel("--")
        self.lbl_c = QLabel("--")
        self.lbl_contracted = QLabel("--")
        self.lbl_md_out = QLabel("--")
        self.lbl_bank = QLabel("--")
        self.lbl_bank.setWordWrap(True)
        
        # Style labels for readability
        for lbl in [self.lbl_pf, self.lbl_kw, self.lbl_kva, self.lbl_q_req, self.lbl_c, 
                   self.lbl_contracted, self.lbl_md_out, self.lbl_bank]:
            lbl.setStyleSheet("font-weight: bold; color: #2c3e50;")
            
        out_layout.addRow("Existing PF:", self.lbl_pf)
        out_layout.addRow("Avg kW:", self.lbl_kw)
        out_layout.addRow("Avg kVA:", self.lbl_kva)
        out_layout.addRow("Required Correction:", self.lbl_q_req)
        out_layout.addRow("Capacitance (µF):", self.lbl_c)
        out_layout.addRow("Contracted kW:", self.lbl_contracted)
        out_layout.addRow("Recorded MD:", self.lbl_md_out)
        out_layout.addRow("Bank Options:", self.lbl_bank)
        
        layout.addWidget(output_group)
        layout.addStretch()

    def calculate(self):
        try:
            k_start = float(self.ent_kwh_start.text() or 0)
            k_end = float(self.ent_kwh_end.text() or 0)
            kv_start = float(self.ent_kvah_start.text() or 0)
            kv_end = float(self.ent_kvah_end.text() or 0)
            days = float(self.ent_days.text() or 1)
            hp = float(self.ent_hp.text() or 0)
            md = float(self.ent_md.text() or 0)
            v_ll = float(self.ent_voltage.text() or 415)
            freq = float(self.ent_freq.text() or 50)
            pf_target = float(self.ent_pf_target.text() or 0.99)

            kwh = k_end - k_start
            kvah = kv_end - kv_start
            pf_exist = (kwh / kvah) if kvah > 0 else 0.0
            hours = days * 24.0
            avg_kW = (kwh / hours) if hours > 0 else 0.0
            avg_kVA = (kvah / hours) if hours > 0 else 0.0
            kvar_exist = math.sqrt(max(avg_kVA**2 - avg_kW**2, 0.0))
            kvar_target = avg_kW * math.tan(math.acos(pf_target)) if 0 < pf_target <= 1 else 0.0
            kvar_required = max(kvar_exist - kvar_target, 0.0)
            c_uf = ((kvar_required * 1000) / (3 * (v_ll/math.sqrt(3))**2 * 2 * math.pi * freq)) * 1e6 if v_ll > 0 and freq > 0 else 0

            self.lbl_pf.setText(f"{pf_exist:.3f}"); self.lbl_kw.setText(f"{avg_kW:.2f} kW")
            self.lbl_kva.setText(f"{avg_kVA:.2f} kVA"); self.lbl_q_req.setText(f"{kvar_required:.2f} kVAR")
            self.lbl_c.setText(f"{c_uf:.0f} µF"); self.lbl_contracted.setText(f"{hp*0.746:.2f} kW (from {hp:.1f} HP)")
            self.lbl_md_out.setText(f"{md:.2f} kVA")

            lines = []
            for step in self.STEPS:
                units = math.ceil(kvar_required / step) if kvar_required > 0 else 0
                if units > 0: lines.append(f"{units} × {step} kVAR = {units*step} kVAR (overage {units*step - kvar_required:.2f})")
            self.lbl_bank.setText("\n".join(lines) if lines else "No correction needed.")

        except ValueError: QMessageBox.warning(self, "Input Error", "Please ensure all fields are valid numbers.")
        except Exception as e: QMessageBox.critical(self, "Calculation Error", str(e))