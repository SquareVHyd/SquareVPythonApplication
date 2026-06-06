"""User management administration page."""

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QTableWidget,
    QDialog,
    QLineEdit,
    QComboBox,
)

from PySide6.QtCore import Qt

from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.ui.searchable_table import NumericTableWidgetItem


class UserManagementPage(QWidget):
    """Administration page for managing users."""

    def __init__(self):
        super().__init__()

        self.auth_service = AuthService()
        self.user_repository = UserRepository()

        self.setup_ui()
        self.load_users()

    def setup_ui(self):

        self.setWindowTitle("User Management")

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("User Management")

        title.setStyleSheet("font-size: 20px; font-weight: bold;")

        layout.addWidget(title)

        # Users table
        self.users_table = QTableWidget()

        self.users_table.setColumnCount(5)

        self.users_table.setHorizontalHeaderLabels([
            "ID",
            "Username",
            "Full Name",
            "Role",
            "Status"
        ])

        self.users_table.setColumnWidth(0, 40)
        self.users_table.setColumnWidth(1, 120)
        self.users_table.setColumnWidth(2, 180)
        self.users_table.setColumnWidth(3, 80)
        self.users_table.setColumnWidth(4, 80)
        self.users_table.setSortingEnabled(True)

        layout.addWidget(self.users_table)

        # Buttons layout
        button_layout = QHBoxLayout()

        self.refresh_button = QPushButton("🔄 Refresh")

        self.refresh_button.clicked.connect(self.load_users)

        self.add_admin_button = QPushButton("🛡️ Create Admin")

        self.add_admin_button.clicked.connect(self.open_add_admin_dialog)

        self.edit_button = QPushButton("✏️ Edit User")

        self.edit_button.clicked.connect(self.edit_user)

        self.delete_button = QPushButton("🗑️ Delete User")

        self.delete_button.clicked.connect(self.delete_user)

        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.add_admin_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)

        layout.addLayout(button_layout)

    def load_users(self):
        """Load all users into the table."""

        try:
            users = self.user_repository.get_all_users()

            self.users_table.setRowCount(0)

            for user in users:
                row = self.users_table.rowCount()

                self.users_table.insertRow(row)

                self.users_table.setItem(row, 0, NumericTableWidgetItem(user[0]))
                self.users_table.setItem(row, 1, NumericTableWidgetItem(user[1]))
                self.users_table.setItem(row, 2, NumericTableWidgetItem(user[2]))
                self.users_table.setItem(row, 3, NumericTableWidgetItem(user[3]))

                is_active = "Active" if user[4] else "Inactive"

                self.users_table.setItem(row, 4, NumericTableWidgetItem(is_active))

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load users: {str(e)}"
            )

    def open_add_admin_dialog(self):
        """Open dialog to create a new admin user."""

        dialog = QDialog(self)

        dialog.setWindowTitle("Create Admin User")

        dialog.resize(400, 250)

        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Full Name:"))

        full_name_input = QLineEdit()

        layout.addWidget(full_name_input)

        layout.addWidget(QLabel("Username:"))

        username_input = QLineEdit()

        layout.addWidget(username_input)

        layout.addWidget(QLabel("Password:"))

        password_input = QLineEdit()

        password_input.setEchoMode(QLineEdit.Password)

        layout.addWidget(password_input)

        # Buttons
        button_layout = QHBoxLayout()

        create_button = QPushButton("✅ Create")

        cancel_button = QPushButton("❌ Cancel")

        button_layout.addWidget(create_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        def create_admin():
            full_name = full_name_input.text().strip()
            username = username_input.text().strip()
            password = password_input.text().strip()

            if not all([full_name, username, password]):
                QMessageBox.warning(
                    dialog,
                    "Validation",
                    "All fields are required"
                )
                return

            result = self.auth_service.register(
                username=username,
                password=password,
                full_name=full_name,
                role="admin"
            )

            if result["success"]:
                QMessageBox.information(
                    dialog,
                    "Success",
                    f"Admin user '{username}' created successfully"
                )

                self.load_users()

                dialog.close()

            else:
                QMessageBox.critical(
                    dialog,
                    "Error",
                    result["message"]
                )

        create_button.clicked.connect(create_admin)

        cancel_button.clicked.connect(dialog.close)

        dialog.exec()

    def edit_user(self):
        """Edit selected user."""

        selected_row = self.users_table.currentRow()

        if selected_row < 0:
            QMessageBox.warning(
                self,
                "Selection",
                "Please select a user to edit"
            )
            return

        QMessageBox.information(
            self,
            "Edit",
            "Edit functionality coming soon"
        )

    def delete_user(self):
        """Delete selected user."""

        selected_row = self.users_table.currentRow()

        if selected_row < 0:
            QMessageBox.warning(
                self,
                "Selection",
                "Please select a user to delete"
            )
            return

        user_id = int(self.users_table.item(selected_row, 0).text())

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this user?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                self.user_repository.delete_user(user_id)

                QMessageBox.information(
                    self,
                    "Success",
                    "User deleted successfully"
                )

                self.load_users()

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete user: {str(e)}"
                )
