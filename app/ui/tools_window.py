from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, 
    QStackedWidget, QFrame
)
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import Qt
from app.ui.capacitor_page import CapacitorPage
from app.ui.file_creator_page import FileCreatorPage
from app.ui.file_viewer_page import FileViewerPage
from app.ui.whatsapp_sender_page import WhatsAppSenderPage

class ToolsWindow(QMainWindow):
    """A dedicated window for tools with a sidebar layout consistent with UtilitiesWindow."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tools")
        self.resize(1200, 800)
        
        main_container = QWidget()
        main_layout = QHBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar setup matching ERP style
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("sidebar")
        sidebar_frame.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(12)

        title = QLabel("Tools")
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

        self.capacitor_btn = QPushButton("🔋 Capacitor R1")
        self.capacitor_btn.clicked.connect(self.show_capacitor)
        self.capacitor_btn.setToolTip(self.shortcuts_tip)

        self.file_creator_btn = QPushButton("📁 File Creator")
        self.file_creator_btn.clicked.connect(self.show_file_creator)
        self.file_creator_btn.setToolTip(self.shortcuts_tip)

        self.file_viewer_btn = QPushButton("🔍 File Viewer")
        self.file_viewer_btn.clicked.connect(self.show_file_viewer)
        self.file_viewer_btn.setToolTip(self.shortcuts_tip)

        self.whatsapp_btn = QPushButton("📱 WhatsApp Msg")
        self.whatsapp_btn.clicked.connect(self.show_whatsapp)
        self.whatsapp_btn.setToolTip(self.shortcuts_tip)

        sidebar_layout.addWidget(title)
        sidebar_layout.addWidget(self.capacitor_btn)
        sidebar_layout.addWidget(self.file_creator_btn)
        sidebar_layout.addWidget(self.file_viewer_btn)
        sidebar_layout.addWidget(self.whatsapp_btn)
        sidebar_layout.addStretch()
        
        self.close_btn = QPushButton("↩️ Back to ERP")
        self.close_btn.clicked.connect(self.close)
        sidebar_layout.addWidget(self.close_btn)

        # Content pages
        self.pages = QStackedWidget()
        
        self.welcome_page = QLabel("Welcome to Tools\n\nSelect a tool from the sidebar to begin.")
        self.welcome_page.setAlignment(Qt.AlignCenter)
        self.welcome_page.setWordWrap(True)
        
        self.capacitor_page = CapacitorPage()
        self.file_creator_page = FileCreatorPage()
        self.file_viewer_page = FileViewerPage()
        self.whatsapp_page = WhatsAppSenderPage()

        self.pages.addWidget(self.welcome_page)
        self.pages.addWidget(self.capacitor_page)
        self.pages.addWidget(self.file_creator_page)
        self.pages.addWidget(self.file_viewer_page)
        self.pages.addWidget(self.whatsapp_page)

        main_layout.addWidget(sidebar_frame)
        main_layout.addWidget(self.pages, 1)

        self.setCentralWidget(main_container)
        self.setStyleSheet(
            "#sidebar { background-color: #f0f2f5; } "
            "#appTitle { font-size: 20px; font-weight: bold; margin-bottom: 16px; }"
        )
        
        self.esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.esc_shortcut.activated.connect(self.close)

    def show_capacitor(self):
        """Navigates to the Capacitor R1 tool page."""
        self.pages.setCurrentIndex(1)

    def show_file_creator(self):
        """Navigates to the File Creator tool page."""
        self.pages.setCurrentIndex(2)

    def show_file_viewer(self):
        """Navigates to the File Viewer tool page."""
        self.pages.setCurrentIndex(3)

    def show_whatsapp(self):
        """Navigates to the WhatsApp Auto Messenger page."""
        self.pages.setCurrentIndex(4)