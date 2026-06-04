from app.repositories.user_repository import (
    UserRepository
)

from app.security.password_hash import (
    verify_password,
    hash_password
)

from app.security.session_manager import (
    SessionManager
)


class AuthService:

    def __init__(self):

        self.repository = UserRepository()

    def login(
        self,
        username,
        password
    ):

        user = (
            self.repository.get_user_by_username(
                username
            )
        )

        if not user:
            return False

        if not user.is_active:
            return False

        valid = verify_password(
            password,
            user.password_hash
        )

        if not valid:
            return False

        SessionManager.login(user)

        return True

    def register(
        self,
        username,
        password,
        full_name,
        role="user"
    ):
        """Register a new user."""

        # Check if username already exists
        existing_user = (
            self.repository.get_user_by_username(
                username
            )
        )

        if existing_user:
            return {
                "success": False,
                "message": "Username already exists"
            }

        try:
            # Hash password
            password_hash = hash_password(password)

            # Create user
            user = self.repository.create_user(
                username=username,
                password_hash=password_hash,
                full_name=full_name,
                role=role
            )

            return {
                "success": True,
                "message": "Registration successful",
                "user": user
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Registration error: {str(e)}"
            }

    def logout(self):
        """Logout the current user."""
        SessionManager.logout()

    def get_current_user(self):
        """Get the currently logged-in user."""
        return SessionManager.get_user()