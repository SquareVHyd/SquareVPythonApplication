from app.repositories.user_repository import (
    UserRepository
)

from app.security.password_hash import (
    hash_password
)

repository = UserRepository()

hashed_password = hash_password("admin")

repository.create_user(
    username="admin",
    password_hash=hashed_password,
    full_name="System Administrator",
    role="admin"
)

print("ADMIN USER CREATED SUCCESSFULLY")