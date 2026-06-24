import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem,
    QInputDialog
)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF
from PySide6.QtCore import Qt, QRectF, QPointF

class ModuleItem(QGraphicsRectItem):
    def __init__(self, x, y, w, h, text, scale_factor=0.5):
        super().__init__(0, 0, w, h)
        self.scale_factor = scale_factor
        self.physical_w = w / scale_factor
        self.physical_h = h / scale_factor
        
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setPen(QPen(QColor("#000000"), 1))
        
        # Modules need a white background so they occlude things behind them when dragged
        self.setBrush(QColor("#ffffff"))
        
        self.txt_item = QGraphicsTextItem(self)
        self.module_name = text
        self.update_text()
        
    def update_text(self):
        w = self.rect().width()
        self.txt_item.setTextWidth(max(10, w - 10))
        # Center text alignment using HTML
        dim_str = f"{int(self.physical_w)}x{int(self.physical_h)} mm"
        self.txt_item.setHtml(f"<div align='center' style='font-family: Arial; font-size: 13px;'><b>{self.module_name}</b><br>{dim_str}</div>")
        self.txt_item.setPos(5, 5)

class GAGraphicsView(QGraphicsView):
    def __init__(self, panel_data, modules):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setStyleSheet("border: none; background-color: #f8fafc;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # panel_data = ("ID", "PanelName", "PanelQty", "LengthXmm", "HeightYmm", "DepthZmm", "StandRequired")
        self.length = float(panel_data[3]) if panel_data[3] else 0.0
        self.height_val = float(panel_data[4]) if panel_data[4] else 0.0
        self.depth = float(panel_data[5]) if panel_data[5] else 0.0
        self.stand_required = str(panel_data[6]).lower() in ['yes', 'true', '1', 'y'] if len(panel_data) > 6 else False
        
        self.modules = modules
        self.build_scene()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'paper_rect') and not self.paper_rect.isEmpty():
            if self.viewport().width() > 0 and self.viewport().height() > 0:
                self.fitInView(self.paper_rect, Qt.KeepAspectRatio)

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, 'paper_rect') and not self.paper_rect.isEmpty():
            if self.viewport().width() > 0 and self.viewport().height() > 0:
                self.fitInView(self.paper_rect, Qt.KeepAspectRatio)

    def wheelEvent(self, event):
        """Allow zooming in and out with Mouse Wheel"""
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        self.scale(zoom_factor, zoom_factor)

    def draw_dimension(self, x1, y1, x2, y2, text, offset_x=0, offset_y=0):
        pen = QPen(QColor("#000000"), 1)
        font = QFont("Arial", 15, QFont.Bold)
        
        ext_len = 10
        self.scene.addLine(x1, y1, x1 + offset_x + (ext_len if offset_x else 0), y1 + offset_y + (ext_len if offset_y else 0), pen)
        self.scene.addLine(x2, y2, x2 + offset_x + (ext_len if offset_x else 0), y2 + offset_y + (ext_len if offset_y else 0), pen)
        
        ax1 = x1 + offset_x
        ay1 = y1 + offset_y
        ax2 = x2 + offset_x
        ay2 = y2 + offset_y
        self.scene.addLine(ax1, ay1, ax2, ay2, pen)
        
        arrow_size = 5
        if ax1 == ax2: # Vertical
            self.scene.addLine(ax1, ay1, ax1 - arrow_size, ay1 + arrow_size, pen)
            self.scene.addLine(ax1, ay1, ax1 + arrow_size, ay1 + arrow_size, pen)
            self.scene.addLine(ax2, ay2, ax2 - arrow_size, ay2 - arrow_size, pen)
            self.scene.addLine(ax2, ay2, ax2 + arrow_size, ay2 - arrow_size, pen)
            
            txt = self.scene.addText(text, font)
            txt.setRotation(-90)
            br = txt.boundingRect()
            txt.setPos(ax1 - 15 - br.height(), (ay1 + ay2)/2 + br.width()/2)
        else: # Horizontal
            self.scene.addLine(ax1, ay1, ax1 + arrow_size, ay1 - arrow_size, pen)
            self.scene.addLine(ax1, ay1, ax1 + arrow_size, ay1 + arrow_size, pen)
            self.scene.addLine(ax2, ay2, ax2 - arrow_size, ay2 - arrow_size, pen)
            self.scene.addLine(ax2, ay2, ax2 - arrow_size, ay2 + arrow_size, pen)
            
            txt = self.scene.addText(text, font)
            br = txt.boundingRect()
            txt.setPos((ax1+ax2)/2 - br.width()/2, ay1 - 25 - br.height()/2)

    def build_scene(self):
        if self.length <= 0 or self.height_val <= 0 or self.depth <= 0:
            self.scene.addText("Invalid Dimensions for G.A. Drawing")
            return
            
        scale = 0.5 
        def sc(val): return val * scale
        
        stand_h = 400.0 if self.stand_required else 0.0
        main_h = max(0.0, self.height_val - stand_h)
        
        spacing_x = 800.0
        spacing_y = 800.0
        
        # Calculate physical layout
        total_physical_w = self.depth + spacing_x + self.length + spacing_x + self.depth
        total_physical_h = self.height_val + spacing_y + self.depth
        
        # A4 Landscape ratio
        a4_ratio = 297.0 / 210.0
        
        # Use a tight margin so the drawing takes up as much of the paper as possible
        margin = 250.0
        
        content_w = total_physical_w + margin * 2
        content_h = total_physical_h + margin * 2
        
        if content_w / content_h > a4_ratio:
            paper_w = content_w
            paper_h = content_w / a4_ratio
        else:
            paper_h = content_h
            paper_w = content_h * a4_ratio
            
        pw = sc(paper_w)
        ph = sc(paper_h)
        self.paper_rect = QRectF(0, 0, pw, ph)
        paper_item = self.scene.addRect(self.paper_rect, QPen(QColor("#cbd5e1"), 2), QColor("#ffffff"))
        paper_item.setZValue(-100)
        
        start_x = (pw - sc(total_physical_w)) / 2
        start_y = (ph - sc(total_physical_h)) / 2
        
        pen_thick = QPen(QColor("#000000"), 2)
        pen_thin = QPen(QColor("#000000"), 1)
        font = QFont("Arial", 14, QFont.Bold)
        
        def add_text_center(x, y, w, h, text):
            txt = self.scene.addText(text, font)
            br = txt.boundingRect()
            txt.setPos(x + w/2 - br.width()/2, y + h/2 - br.height()/2)
            
        # --- LEFT SIDE VIEW ---
        lx = start_x
        ly = start_y
        
        self.scene.addRect(lx, ly, sc(self.depth), sc(main_h), pen_thick)
        if stand_h > 0:
            self.scene.addRect(lx, ly + sc(main_h), sc(self.depth), sc(stand_h), pen_thick)
            self.scene.addRect(lx + sc(self.depth)*0.2, ly + sc(main_h) + sc(stand_h)*0.1, sc(self.depth)*0.6, sc(stand_h)*0.8, pen_thick)
            
        add_text_center(lx, ly + sc(self.height_val) + 20, sc(self.depth), 20, "SIDE VIEW (LH)")
        
        self.draw_dimension(lx, ly - sc(10), lx + sc(self.depth), ly - sc(10), str(int(self.depth)), offset_y=-50)
        self.draw_dimension(lx - sc(10), ly, lx - sc(10), ly + sc(self.height_val), str(int(self.height_val)), offset_x=-60)
        
        # --- FRONT VIEW ---
        fx = lx + sc(self.depth) + sc(spacing_x)
        fy = start_y
        
        self.scene.addRect(fx, fy, sc(self.length), sc(main_h), pen_thick)
        
        bb_h = 300.0 if main_h > 400 else 0
        if bb_h > 0:
            self.scene.addLine(fx, fy + sc(bb_h), fx + sc(self.length), fy + sc(bb_h), pen_thick)
            add_text_center(fx, fy, sc(self.length), sc(bb_h), "BUSBAR CHAMBER")
            self.draw_dimension(fx - sc(10), fy, fx - sc(10), fy + sc(bb_h), str(int(bb_h)), offset_x=-40)
            
        if stand_h > 0:
            self.scene.addLine(fx, fy + sc(main_h), fx, fy + sc(self.height_val), pen_thick)
            self.scene.addLine(fx + sc(self.length), fy + sc(main_h), fx + sc(self.length), fy + sc(self.height_val), pen_thick)
            self.scene.addLine(fx, fy + sc(self.height_val), fx + sc(self.length), fy + sc(self.height_val), pen_thick)
            self.scene.addLine(fx + sc(self.length/2), fy + sc(main_h), fx + sc(self.length/2), fy + sc(self.height_val), pen_thick)
            
            txt = self.scene.addText("STAND", font)
            txt.setPos(fx + 20, fy + sc(main_h) + 20)
            
        add_text_center(fx, fy + sc(self.height_val) + 20, sc(self.length), 20, "FRONT VIEW")
        
        # Modules
        comps_y = fy + sc(bb_h)
        comps_h = sc(main_h - bb_h)
        
        flattened_modules = []
        for m in self.modules:
            qty = m[1] or 1
            for _ in range(qty):
                flattened_modules.append(m[0] or "Unknown")
        
        flattened_modules = flattened_modules[:16]
        n_mods = len(flattened_modules)
        
        if n_mods > 0:
            cols = max(1, round(self.length / 500.0))
            rows = math.ceil(n_mods / cols)
            comp_w = sc(self.length) / cols
            comp_h = comps_h / rows
            
            comp_w_val = self.length / cols
            comp_h_val = (main_h - bb_h) / rows
            
            idx = 0
            for r in range(rows):
                for c in range(cols):
                    cx = fx + c * comp_w
                    cy = comps_y + r * comp_h
                    
                    if idx < n_mods:
                        # Draw interactive, selectable module
                        mod_item = ModuleItem(cx, cy, comp_w, comp_h, flattened_modules[idx], scale_factor=scale)
                        self.scene.addItem(mod_item)
                        idx += 1
                    else:
                        # Empty slot
                        self.scene.addRect(cx, cy, comp_w, comp_h, pen_thin)
                        
                    if c == 0:
                        self.draw_dimension(fx - sc(10), cy, fx - sc(10), cy + comp_h, str(int(comp_h_val)), offset_x=-40)
                    if r == 0:
                        self.draw_dimension(cx, fy - sc(10), cx + comp_w, fy - sc(10), str(int(comp_w_val)), offset_y=-30)
                        
        self.draw_dimension(fx, fy - sc(10), fx + sc(self.length), fy - sc(10), str(int(self.length)), offset_y=-70)
        
        # --- RIGHT SIDE VIEW ---
        rx = fx + sc(self.length) + sc(spacing_x)
        ry = start_y
        
        self.scene.addRect(rx, ry, sc(self.depth), sc(main_h), pen_thick)
        if stand_h > 0:
            self.scene.addRect(rx, ry + sc(main_h), sc(self.depth), sc(stand_h), pen_thick)
            self.scene.addRect(rx + sc(self.depth)*0.2, ry + sc(main_h) + sc(stand_h)*0.1, sc(self.depth)*0.6, sc(stand_h)*0.8, pen_thick)
            
        add_text_center(rx, ry + sc(self.height_val) + 20, sc(self.depth), 20, "SIDE VIEW (RH)")
        
        self.draw_dimension(rx, ry - sc(10), rx + sc(self.depth), ry - sc(10), str(int(self.depth)), offset_y=-50)
        self.draw_dimension(rx + sc(self.depth) + sc(10), ry, rx + sc(self.depth) + sc(10), ry + sc(self.height_val), str(int(self.height_val)), offset_x=60)
        
        # --- BOTTOM VIEW ---
        bx = fx
        by = start_y + sc(self.height_val) + sc(spacing_y)
        
        self.scene.addRect(bx, by, sc(self.length), sc(self.depth), pen_thick)
        self.scene.addRect(bx + sc(100), by + sc(50), sc(self.length - 200), sc(self.depth - 100), pen_thick)
        
        add_text_center(bx, by + sc(self.depth) + 20, sc(self.length), 20, "CABLE ENTRY - BOTTOM")
        
        self.draw_dimension(bx, by - sc(10), bx + sc(self.length), by - sc(10), str(int(self.length)), offset_y=-50)
        self.draw_dimension(bx + sc(self.length) + sc(10), by, bx + sc(self.length) + sc(10), by + sc(self.depth), str(int(self.depth)), offset_x=60)

        # Ensure the scene sets its boundaries correctly to the paper
        self.scene.setSceneRect(self.paper_rect)


class PanelCardWidget(QFrame):
    def __init__(self, panel_data, modules):
        super().__init__()
        self.setStyleSheet("QFrame { background-color: white; border: 1px solid #cbd5e1; border-radius: 8px; margin-bottom: 10px; }")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # panel_data: ID, PanelName, PanelQty, LengthXmm, HeightYmm, DepthZmm, StandRequired
        p_name = panel_data[1]
        p_qty = panel_data[2]
        p_len = panel_data[3]
        p_hgt = panel_data[4]
        p_dep = panel_data[5]
        
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
        
        # New Interactive Graphics View!
        self.ga_widget = GAGraphicsView(panel_data, modules)
        # Fix a minimum height so it feels like a large canvas you can interact with
        self.ga_widget.setMinimumSize(1200, 900)
        layout.addWidget(self.ga_widget)
