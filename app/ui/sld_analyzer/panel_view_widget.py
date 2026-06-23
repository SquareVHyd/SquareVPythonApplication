from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QRect

class PanelDrawingWidget(QWidget):
    def __init__(self, length, height, depth, title):
        super().__init__()
        self.length = float(length) if length else 0.0
        self.height_val = float(height) if height else 0.0
        self.depth = float(depth) if depth else 0.0
        self.title = title
        self.setMinimumSize(250, 300)
        self.setStyleSheet("border: none; background: transparent;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate scaling to fit the widget, leaving room for labels
        w = self.width() - 60
        h = self.height() - 60
        
        if self.length <= 0 or self.height_val <= 0 or self.depth <= 0:
            painter.drawText(self.rect(), Qt.AlignCenter, "Invalid Dimensions")
            return

        # Determine which dimensions we are plotting for this view
        if self.title == "Front View":
            real_w, real_h = self.length, self.height_val
            label_w, label_h = f"L: {self.length} mm", f"H: {self.height_val} mm"
        elif self.title == "Side View":
            real_w, real_h = self.depth, self.height_val
            label_w, label_h = f"D: {self.depth} mm", f"H: {self.height_val} mm"
        else: # Bottom View
            real_w, real_h = self.length, self.depth
            label_w, label_h = f"L: {self.length} mm", f"D: {self.depth} mm"

        # Scale
        scale_x = w / real_w
        scale_y = h / real_h
        scale = min(scale_x, scale_y)

        draw_w = real_w * scale
        draw_h = real_h * scale
        
        start_x = 30 + (w - draw_w) / 2
        start_y = 40 + (h - draw_h) / 2

        # Draw Title
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.setPen(QColor("#0f172a"))
        painter.drawText(0, 10, self.width(), 20, Qt.AlignHCenter | Qt.AlignTop, self.title)

        # Draw Rectangle
        painter.setPen(QPen(QColor("#334155"), 2))
        painter.setBrush(QColor("#f8fafc"))
        painter.drawRect(QRect(int(start_x), int(start_y), int(draw_w), int(draw_h)))

        # Draw Dimensions
        painter.setFont(QFont("Arial", 10))
        painter.setPen(QColor("#b91c1c"))
        
        # Bottom label for width dimension
        painter.drawText(int(start_x), int(start_y + draw_h + 5), int(draw_w), 20, Qt.AlignHCenter | Qt.AlignTop, label_w)
        
        # Right label for height dimension
        painter.save()
        painter.translate(start_x + draw_w + 5, start_y + draw_h / 2)
        painter.rotate(-90)
        painter.drawText(int(-draw_h/2), 0, int(draw_h), 20, Qt.AlignCenter, label_h)
        painter.restore()

class PanelCardWidget(QFrame):
    def __init__(self, panel_data):
        super().__init__()
        self.setStyleSheet("QFrame { background-color: white; border: 1px solid #cbd5e1; border-radius: 8px; margin-bottom: 10px; }")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        p_id, p_name, p_qty, p_len, p_hgt, p_dep = panel_data
        
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #f1f5f9; border: none; border-bottom: 1px solid #cbd5e1; border-top-left-radius: 8px; border-top-right-radius: 8px;")
        header_layout = QHBoxLayout(header_widget)
        
        title_lbl = QLabel(f"<b>{p_name}</b> (Qty: {p_qty})")
        title_lbl.setStyleSheet("font-size: 16px; color: #1e293b; border: none;")
        
        dims_lbl = QLabel(f"L: {p_len} mm  |  H: {p_hgt} mm  |  D: {p_dep} mm")
        dims_lbl.setStyleSheet("font-size: 14px; color: #475569; border: none;")
        
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(dims_lbl)
        
        layout.addWidget(header_widget)
        
        # Views Layout
        views_widget = QWidget()
        views_widget.setStyleSheet("border: none; background: transparent;")
        views_layout = QHBoxLayout(views_widget)
        views_layout.setContentsMargins(10, 10, 10, 10)
        
        views_layout.addWidget(PanelDrawingWidget(p_len, p_hgt, p_dep, "Front View"))
        views_layout.addWidget(PanelDrawingWidget(p_len, p_hgt, p_dep, "Side View"))
        views_layout.addWidget(PanelDrawingWidget(p_len, p_hgt, p_dep, "Bottom View"))
        
        layout.addWidget(views_widget)
