from app.repositories.user_repository import (
    UserRepository
)

from app.security.password_hash import (
    hash_password
)

repository = UserRepository()

username = "testuser"

password = "1234"

hashed_password = hash_password(password)

repository.create_user(
    username=username,
    password_hash=hashed_password,
    full_name="Test User",
    role="operator"
)

print("TEST USER CREATED")