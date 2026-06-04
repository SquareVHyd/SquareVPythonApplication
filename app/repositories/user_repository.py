from sqlalchemy import text
from app.config.database import (
    get_session
)


class UserRepository:
    def __init__(self):
        pass # Session will be acquired per method

    def get_user_by_username(
        self,
        username
    ):

        query = text(
            '''
            SELECT *
            FROM users
            WHERE username=:username
            '''
        )

        with get_session() as session:
            result = session.execute(
                query,
                {
                    "username": username
                }
            )

            return result.fetchone()
        
    def create_user(
        self,
        username,
        password_hash,
        full_name,
        role
    ):

        query = text(
            '''
            INSERT INTO users
            (
                username,
                password_hash,
                full_name,
                role,
                is_active
            )
            VALUES
            (
                :username,
                :password_hash,
                :full_name,
                :role,
                :is_active
            )
            '''
        )

        with get_session() as session:
            session.execute(
                query,
                {
                    "username": username,
                    "password_hash": password_hash,
                    "full_name": full_name,
                    "role": role,
                    "is_active": True,
                }
            )

            session.commit()

    def get_all_users(self):
        """Get all users from the database."""

        query = text( # This query is missing the session context manager
            '''
            SELECT id, username, full_name, role, is_active
            FROM users
            ORDER BY id DESC
            '''
        )

        with get_session() as session:
            result = session.execute(query)

            return result.fetchall()