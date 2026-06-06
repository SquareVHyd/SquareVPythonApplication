import os
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QFrame,
    QSizePolicy,
    QSpacerItem,
    QGraphicsDropShadowEffect
)

from PySide6.QtGui import QPixmap, Qt, QFont
from PySide6.QtCore import Signal, QSize, QTimer

from app.services.auth_service import AuthService
from app.ui.main_window import MainWindow
from app.ui.auth.register_window import RegisterWindow


class MarqueeLabel(QLabel):
    def __init__(self, text):
        super().__init__(text)

        self.full_text = text + "     "
        self.offset = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.scroll_text)
        self.timer.start(120)

    def scroll_text(self):
        self.offset += 1

        if self.offset >= len(self.full_text):
            self.offset = 0

        display = (
            self.full_text[self.offset:]
            + self.full_text[:self.offset]
        )

        self.setText(display)


class StaffCard(QFrame):
    def __init__(self, name, designation, image_filename):
        super().__init__()

        self.image_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "Images",
            image_filename
        )

        self.setFixedSize(180, 140)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.image_lbl = QLabel()
        self.image_lbl.setFixedSize(80, 80)
        self.image_lbl.setAlignment(Qt.AlignCenter)
        self.image_lbl.hide()

        self.name_lbl = QLabel(name.replace("Mr. ", ""))
        self.name_lbl.setAlignment(Qt.AlignCenter)
        self.name_lbl.setStyleSheet("font-weight: 600; color: #0f172a; font-size: 14px; background: transparent;")

        self.role_lbl = QLabel(designation)
        self.role_lbl.setAlignment(Qt.AlignCenter)
        self.role_lbl.setStyleSheet("color: #64748b; font-size: 12px; background: transparent;")

        self.layout.addWidget(self.image_lbl, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.name_lbl)
        self.layout.addWidget(self.role_lbl)

        self.setStyleSheet("""
            QFrame {
                border-radius: 10px;
                background: transparent;
                border: none;
            }

            QFrame:hover {
                background: #f1f5f9;
            }
        """)

    def enterEvent(self, event):
        if os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)

            self.image_lbl.setPixmap(
                pixmap.scaled(
                    80,
                    80,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )

            self.image_lbl.show()

        super().enterEvent(event)

    def leaveEvent(self, event):
        self.image_lbl.hide()
        super().leaveEvent(event)


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Square V Engineering - Login")
        self.setStyleSheet("background-color: #f8fafc;")
       #self.showMaximized()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- HEADER SECTION (15-20% of screen) ---
        info_panel = QFrame()
        info_panel.setStyleSheet("background-color: #ffffff; border: none;")
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(30, 40, 30, 25)
        info_layout.setSpacing(8)

        # Company Details
        self.logo_lbl = QLabel("SQUARE V ENGINEERING")
        self.logo_lbl.setAlignment(Qt.AlignCenter)
        self.logo_lbl.setStyleSheet("font-weight: 800; color: #1e3a8a; border: none;font-size: 30px;")
        info_layout.addWidget(self.logo_lbl)

        address_text = (
            "Survey No:298/P, Road No 14, Pipe Line Road, "
            "Phase-I, IDA, Jeedimetla, Hyderabad - 500055, TS, India"
        )

        addr_lbl = MarqueeLabel(address_text)
        addr_lbl.setStyleSheet("color: #64748b; font-size: 13px; padding: 2px; border: none;")
        addr_lbl.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(addr_lbl)
        
        contact_details = QLabel("📱 +91-9182830625   •   ✉️ info.squarev@gmail.com")
        contact_details.setStyleSheet("color: #2563eb; font-weight: 600; font-size: 18px; border: none;")
        contact_details.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(contact_details)
        
        info_layout.addSpacing(20)
        login_title = QLabel("Login Page")
        login_title.setAlignment(Qt.AlignCenter)
        login_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #0f172a;
            border: none;
            font-size: 20px;
        """)
        info_layout.addWidget(login_title)

        main_layout.addWidget(info_panel, 1) # Header stretch

        # --- MAIN SECTION: Login Form centered ---
        content_area = QWidget()
        content_area.setStyleSheet("background-color: #f8fafc;")
        content_layout = QVBoxLayout(content_area)
        
        login_panel = QFrame()
        login_panel.setMaximumWidth(420)
        login_panel.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 12px;")
        login_layout = QVBoxLayout(login_panel)
        login_layout.setContentsMargins(60, 40, 60, 40)
        login_layout.setAlignment(Qt.AlignCenter)

        welcome_title = QLabel("Enterprise Portal")
        welcome_title.setStyleSheet("font-size: 28px; font-weight: bold; color: #0f172a;")
        login_layout.addWidget(welcome_title)

        # Form Fields
        input_style = """
            QLineEdit { border: 1px solid #d1d5db; border-radius: 6px; padding: 10px; background: white; color: #111827; }
            QLineEdit:focus { border: 2px solid #3b82f6; }
        """
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(45)
        self.username_input.setStyleSheet(input_style)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(45)
        self.password_input.setStyleSheet(input_style)
        self.password_input.returnPressed.connect(self.login)

        login_layout.addWidget(self.username_input)
        login_layout.addSpacing(10)
        login_layout.addWidget(self.password_input)
        login_layout.addSpacing(30)

        # Buttons layout
        button_layout = QHBoxLayout()
        self.login_button = QPushButton("🔑 LOGIN")
        self.login_button.setMinimumHeight(45)
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.setStyleSheet("""
            QPushButton { background-color: #2563eb; color: white; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        self.login_button.clicked.connect(self.login)

        self.register_button = QPushButton("👤+ NEW USER?")
        self.register_button.setMinimumHeight(45)
        self.register_button.setCursor(Qt.PointingHandCursor)
        self.register_button.setStyleSheet("""
            QPushButton { background-color: #64748b; color: white; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background-color: #475569; }
        """)
        self.register_button.clicked.connect(self.open_register)

        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.register_button)
        login_layout.addLayout(button_layout)

        content_layout.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(login_panel)
        main_layout.addWidget(content_area, 4) # Content area stretch (80%)

    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username:
            QMessageBox.warning(self, "Validation", "Username required")
            return

        if not password:
            QMessageBox.warning(self, "Validation", "Password required")
            return

        valid = self.auth_service.login(username, password)

        if valid:
            self.main_window = MainWindow()
            self.main_window.show()
            self.close()
        else:
            QMessageBox.critical(self, "Login Failed", "Invalid username or password")
            self.password_input.clear()

    def open_register(self):
        """Open the registration window."""
        self.register_window = RegisterWindow(self)
        self.register_window.show()