from sqlalchemy import text
from app.config.database import get_session # Assuming get_session is now a context manager


class StateRepository:
    def __init__(self):
        pass # Session will be acquired per method

    def get_states(self):
        query = text(
            '''
            SELECT "ID", "StateCode", "StateName"
            FROM "tblState"
            ORDER BY "StateName"
            '''
        )

        with get_session() as session:
            try:
                result = session.execute(query)
            except Exception: # The rollback is handled by the context manager
                result = session.execute(query)
            return result.fetchall(), result.keys()

    def get_state_by_id(self, state_id):
        query = text(
            '''
            SELECT "ID", "StateCode", "StateName"
            FROM "tblState"
            WHERE "ID" = :state_id
            '''
        )
        with get_session() as session:
            result = session.execute(query, {"state_id": state_id})
            return result.fetchone()

    def search_states(self, keyword):
        query = text(
            '''
            SELECT "ID", "StateCode", "StateName"
            FROM "tblState"
            WHERE ("ID" = :id_exact)
               OR LOWER(CAST("StateCode" AS TEXT)) LIKE LOWER(:keyword)
               OR LOWER("StateName") LIKE LOWER(:keyword)
            ORDER BY "StateName"
            '''
        )

        id_exact = int(keyword) if keyword.isdigit() else None
        params = {
            "keyword": f"%{keyword}%",
            "id_exact": id_exact,
        }
        with get_session() as session:
            try:
                result = session.execute(query, params)
            except Exception:
                result = session.execute(query, params)
            return result.fetchall(), result.keys()

    def create_state(self, state_code, state_name):
        query = text(
            '''
            INSERT INTO "tblState"
            ("StateCode", "StateName")
            VALUES
            (:state_code, :state_name)
            '''
        )
        with get_session() as session:
            session.execute(
                query,
                {
                    "state_code": state_code,
                    "state_name": state_name,
                }
            )
            session.commit()

    def update_state(self, state_id, state_code, state_name):
        query = text(
            '''
            UPDATE "tblState"
            SET "StateCode" = :state_code,
                "StateName" = :state_name
            WHERE "ID" = :state_id
            '''
        )
        with get_session() as session:
            session.execute(
                query,
                {
                    "state_id": state_id,
                    "state_code": state_code,
                    "state_name": state_name,
                }
            )
            session.commit()

    def delete_state(self, state_id):
        query = text(
            '''
            DELETE FROM "tblState"
            WHERE "ID" = :state_id
            '''
        )
        with get_session() as session:
            session.execute(query, {"state_id": state_id})
            session.commit()
