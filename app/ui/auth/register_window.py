"""User registration window."""

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QFrame,
    QComboBox,
)

from PySide6.QtCore import Qt

from app.services.auth_service import AuthService


class RegisterWindow(QWidget):
    """Registration window for new users."""

    def __init__(self, parent=None):
        super().__init__()

        self.parent_window = parent
        self.auth_service = AuthService()

        self.setup_ui()

    def setup_ui(self):

        self.setWindowTitle("Enterprise ERP - Register New User")

        self.resize(450, 480)

        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-size: 14px;
            }

            QFrame {
                background: white;
                border-radius: 10px;
            }

            QLabel {
                color: #333333;
            }

            QLineEdit {
                padding: 10px;
                border: 1px solid #cccccc;
                border-radius: 5px;
                background: white;
            }

            QComboBox {
                padding: 10px;
                border: 1px solid #cccccc;
                border-radius: 5px;
                background: white;
            }

            QPushButton {
                background-color: #1976d2;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #1565c0;
            }

            #cancelBtn {
                background-color: #757575;
            }

            #cancelBtn:hover {
                background-color: #616161;
            }
        """)

        main_layout = QVBoxLayout(self)

        main_layout.setAlignment(Qt.AlignCenter)

        frame = QFrame()

        frame.setFixedWidth(380)

        frame_layout = QVBoxLayout(frame)

        frame_layout.setSpacing(10)

        # Title
        title = QLabel("Create Account")

        title.setAlignment(Qt.AlignCenter)

        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        """)

        subtitle = QLabel("Please fill in your details to register")

        subtitle.setAlignment(Qt.AlignCenter)

        subtitle.setStyleSheet("""
            color: gray;
            font-size: 12px;
            margin-bottom: 10px;
        """)

        # Full Name
        frame_layout.addWidget(QLabel("Full Name:"))

        self.full_name_input = QLineEdit()

        self.full_name_input.setPlaceholderText("Enter your full name")

        frame_layout.addWidget(self.full_name_input)

        # Username
        frame_layout.addWidget(QLabel("Username:"))

        self.username_input = QLineEdit()

        self.username_input.setPlaceholderText("Choose a unique username")

        self.username_input.returnPressed.connect(self.register)


        frame_layout.addWidget(self.username_input)

        # Password
        frame_layout.addWidget(QLabel("Password:"))

        self.password_input = QLineEdit()

        self.password_input.setPlaceholderText("Enter password (minimum 6 characters)")

        self.password_input.setEchoMode(QLineEdit.Password)

        self.password_input.returnPressed.connect(self.register)


        frame_layout.addWidget(self.password_input)

        # Confirm Password
        frame_layout.addWidget(QLabel("Confirm Password:"))

        self.confirm_password_input = QLineEdit()

        self.confirm_password_input.setPlaceholderText("Confirm your password")

        self.confirm_password_input.setEchoMode(QLineEdit.Password)

        self.confirm_password_input.returnPressed.connect(self.register)


        frame_layout.addWidget(self.confirm_password_input)

        # Role Selection
        frame_layout.addWidget(QLabel("Role:"))

        self.role_combo = QComboBox()

        self.role_combo.addItem("User", "user")

        self.role_combo.addItem("Manager", "manager")

        # Note: Admin role is not available for self-registration

        frame_layout.addWidget(self.role_combo)

        # Info label
        info_label = QLabel("Admin accounts can only be created by administrators")

        info_label.setStyleSheet("""
            color: #ff9800;
            font-size: 11px;
            font-style: italic;
            margin-bottom: 10px;
        """)

        frame_layout.addWidget(info_label)

        frame_layout.addWidget(QLabel(""))  # Spacer

        # Buttons layout
        button_layout = QHBoxLayout()

        self.register_button = QPushButton("📝 REGISTER")

        self.register_button.clicked.connect(self.register)

        self.cancel_button = QPushButton("❌ CANCEL")

        self.cancel_button.setObjectName("cancelBtn")

        self.cancel_button.clicked.connect(self.cancel)

        button_layout.addWidget(self.register_button)
        button_layout.addWidget(self.cancel_button)

        frame_layout.addLayout(button_layout)

        # Add frame to main layout
        frame_layout.insertWidget(0, title)
        frame_layout.insertWidget(1, subtitle)

        main_layout.addWidget(frame)

    def validate_inputs(self):
        """Validate registration form inputs."""

        full_name = self.full_name_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()

        if not full_name:
            QMessageBox.warning(
                self,
                "Validation",
                "Full name is required"
            )
            return False

        if len(full_name) < 2:
            QMessageBox.warning(
                self,
                "Validation",
                "Full name must be at least 2 characters"
            )
            return False

        if not username:
            QMessageBox.warning(
                self,
                "Validation",
                "Username is required"
            )
            return False

        if len(username) < 3:
            QMessageBox.warning(
                self,
                "Validation",
                "Username must be at least 3 characters"
            )
            return False

        if not password:
            QMessageBox.warning(
                self,
                "Validation",
                "Password is required"
            )
            return False

        if len(password) < 6:
            QMessageBox.warning(
                self,
                "Validation",
                "Password must be at least 6 characters"
            )
            return False

        if password != confirm_password:
            QMessageBox.warning(
                self,
                "Validation",
                "Passwords do not match"
            )
            return False

        return True

    def register(self):
        """Handle user registration."""

        if not self.validate_inputs():
            return

        full_name = self.full_name_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_combo.currentData()

        # Call auth service to register
        result = self.auth_service.register(
            username=username,
            password=password,
            full_name=full_name,
            role=role
        )

        if result["success"]:
            QMessageBox.information(
                self,
                "Success",
                f"Registration successful! Welcome {full_name}.\n\nYou can now login with your credentials."
            )

            self.close()

        else:
            QMessageBox.critical(
                self,
                "Registration Failed",
                result["message"]
            )

    def cancel(self):
        """Close registration window."""
        self.close()
