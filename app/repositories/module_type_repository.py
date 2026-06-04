from sqlalchemy import text

from app.config.database import get_session # Assuming get_session is now a context manager


class ModuleTypeRepository:
    def __init__(self):
        pass # Session will be acquired per method

    def get_all_module_types(self):
        query = text(
            '''
            SELECT 
                mt."ID", 
                mt."ModuleType", 
                mm."ModuleMake"
            FROM "tblModuleType" mt
            LEFT JOIN "tblModuleMake" mm ON mt."ModuleMakeID" = mm."ID"
            ORDER BY mt."ModuleType"
            '''
        )
        with get_session() as session:
            result = session.execute(query)
            return result.fetchall()

    def get_module_type(self, module_type_id):
        query = text(
            '''
            SELECT
                "ID",
                "ModuleType",
                "ModuleMakeID",
                "ModSwgID"
            FROM "tblModuleType"
            WHERE "ID" = :id
            '''
        )
        with get_session() as session:
            result = session.execute(query, {"id": module_type_id})
            return result.fetchone()

    def create_module_type(self, module_type, module_make_id, mod_swg_id):
        query = text(
            '''
            INSERT INTO "tblModuleType" ("ModuleType", "ModuleMakeID", "ModSwgID")
            VALUES (:module_type, :module_make_id, :mod_swg_id)
            RETURNING "ID"
            '''
        )
        with get_session() as session:
            res = session.execute(
                query, {"module_type": module_type, "module_make_id": module_make_id, "mod_swg_id": mod_swg_id}
            )
            session.commit()
            row = res.fetchone()
            return row[0] if row else None

    def update_module_type(self, module_type_id, module_type, module_make_id, mod_swg_id):
        query = text(
            '''
            UPDATE "tblModuleType"
            SET "ModuleType" = :module_type,
                "ModuleMakeID" = :module_make_id,
                "ModSwgID" = :mod_swg_id
            WHERE "ID" = :id
            '''
        )
        with get_session() as session:
            session.execute(
                query,
                {
                    "id": module_type_id,
                    "module_type": module_type,
                    "module_make_id": module_make_id,
                    "mod_swg_id": mod_swg_id,
                },
            )
            session.commit()

    def delete_module_type(self, module_type_id):
        query = text(
            '''
            DELETE FROM "tblModuleType"
            WHERE "ID" = :id
            '''
        )
        with get_session() as session:
            session.execute(query, {"id": module_type_id})
            session.commit()

    def get_all_module_makes(self):
        query = text(
            '''
            SELECT "ID", "ModuleMake"
            FROM "tblModuleMake"
            ORDER BY "ModuleMake"
            '''
        )
        with get_session() as session:
            result = session.execute(query)
            return result.fetchall()

    def get_all_swgs(self):
        query = text('SELECT "ID", "CatModSwg" FROM "tblModSwg" ORDER BY "CatModSwg"')
        with get_session() as session:
            result = session.execute(query)
            return result.fetchall()

    def create_module_make(self, module_make):
        query = text(
            '''
            INSERT INTO "tblModuleMake" ("ModuleMake")
            VALUES (:module_make)
            RETURNING "ID"
            '''
        )
        with get_session() as session:
            res = session.execute(query, {"module_make": module_make})
            session.commit()
            row = res.fetchone()
            return row[0] if row else None
