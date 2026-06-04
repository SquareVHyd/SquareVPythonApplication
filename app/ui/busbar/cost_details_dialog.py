from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QGridLayout, QFrame
from PySide6.QtCore import Qt

class CostDetailsDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Metal-Cost Details")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        grid = QGridLayout()

        # Inputs
        run = float(data[1] or 0)
        width = float(data[2] or 0)
        thick = float(data[3] or 0)
        density = float(data[7] or 0)
        kg_cost = float(data[8] or 0)
        s_rate = float(data[10] or 0)

        # Calculations (Density Factor: 0.000001 converts mm3 to kg)
        weight = round(run * width * thick * density * 0.000001, 3)
        m_cost = round(weight * kg_cost, 2)
        s_cost = round(run * s_rate, 2)
        total = round(m_cost + s_cost, 2)

        # UI Generation
        rows = [
            ("Run Length:", f"{run}"),
            ("Busbar Size:", f"{width} x {thick}"),
            ("Metal:", f"{data[6]}"),
            ("", ""),
            ("Estimated Weight:", f"<b>{weight} Kg</b>"),
            ("Metal Cost:", f"${m_cost}"),
            ("Sleeve Cost:", f"${s_cost}"),
            ("", ""),
            ("TOTAL COST:", f"<font color='blue' size='5'>${total}</font>")
        ]

        for i, (lbl, val) in enumerate(rows):
            if not lbl and not val:
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                grid.addWidget(line, i, 0, 1, 2)
                continue
            
            grid.addWidget(QLabel(lbl), i, 0)
            v_lbl = QLabel(val)
            v_lbl.setAlignment(Qt.AlignRight)
            grid.addWidget(v_lbl, i, 1)

        layout.addLayout(grid)
        
        info = QLabel("<br><i>Note: Total Cost = (Weight * Cost/Kg) + (Run * Normal Rate)</i>")
        info.setWordWrap(True)
        info.setStyleSheet("color: gray;")
        layout.addWidget(info)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

from PySide6.QtWidgets import QPushButton