from sqlalchemy import text

from app.config.database import get_session # Assuming get_session is now a context manager


class BaseRepository:
    def __init__(self, table_name):
        self.table_name = table_name
        pass # Session will be acquired per method

    def get_all(self):
        with get_session() as session:
            query = text(f"SELECT * FROM {self.table_name}")
            result = session.execute(query)
            return result.fetchall(), result.keys()

    def delete(self, record_id):
        with get_session() as session:
            query = text(
                f"DELETE FROM {self.table_name} WHERE id=:id"
            )

            session.execute(query, {"id": record_id})
            session.commit()