from sqlalchemy import text

from app.config.database import get_session # Assuming get_session is now a context manager


class ModuleRepository:
    def __init__(self):
        pass # Session will be acquired per method

    def get_all_modules(self):
        query = text(
            '''
            SELECT DISTINCT
                mt."ID" AS ModuleTypeID,
                mt."ModuleType" AS ModuleType,
                mm."ModuleMake" AS ModuleMake,
                ms."CatModSwg" AS SWG
            FROM "tblModuleType" mt
            INNER JOIN "tblModuleMake" mm
                ON mt."ModuleMakeID" = mm."ID"
            INNER JOIN "tblModSwg" ms
                ON mt."ModSwgID" = ms."ID"
            ORDER BY mt."ModuleType"
            '''
        )
        with get_session() as session:
            result = session.execute(query)
            return result.fetchall()

    def get_items_by_module_type(self, module_type_id):
        query = text(
            '''
            SELECT
                m."SEQNo",
                m."ItemID",
                pl."ItemDescription",
                m."Qty",
                m."ID" AS ModuleItemID
            FROM "tblModules" m
            JOIN "tblPriceList" pl ON m."ItemID" = pl."ID"
            WHERE m."ModuleTypeID" = :module_type_id
            ORDER BY m."SEQNo"
            '''
        )
        with get_session() as session:
            result = session.execute(query, {"module_type_id": module_type_id})
            return result.fetchall()

    def get_module(self, module_id):
        query = text(
            '''
            SELECT
                m."ID",
                m."ModuleTypeID",
                m."ItemID",
                mt."ModuleType" AS "ModuleType",
                mm."ModuleMake" AS "ModuleMake",
                pl."ItemDescription" AS "ItemDescription",
                pl."Model" AS "Model",
                cat."Category" AS "Category",
                pm."Make" AS "PriceMake",
                pl."ListPrice" AS "ListPrice",
                pl."DiscountPercent" AS "DiscountPercent",
                pl."NetPrice" AS "NetPrice",
                m."Qty",
                m."SEQNo"
            FROM "tblModules" m
            LEFT JOIN "tblModuleType" mt ON m."ModuleTypeID" = mt."ID"
            LEFT JOIN "tblModuleMake" mm ON mt."ModuleMakeID" = mm."ID"
            LEFT JOIN "tblPriceList" pl ON m."ItemID" = pl."ID"
            LEFT JOIN "tblCategory" cat ON pl."CategoryID" = cat."CategoryID"
            LEFT JOIN "tblMake" pm ON pl."MakeID" = pm."MakeID"
            WHERE m."ID" = :id
            '''
        )
        with get_session() as session:
            result = session.execute(query, {"id": module_id})
            return result.fetchone()

    def create_module(self, module_type_id, item_id, qty, seqno):
        query = text(
            '''
            INSERT INTO "tblModules"
                ("ModuleTypeID", "ItemID", "Qty", "SEQNo")
            VALUES
                (:module_type_id, :item_id, :qty, :seqno)
            RETURNING "ID"
            '''
        )
        with get_session() as session:
            res = session.execute(
                query,
                {
                    "module_type_id": module_type_id,
                    "item_id": item_id,
                    "qty": qty,
                    "seqno": seqno,
                },
            )
            row = res.fetchone()
            new_id = row[0] if row else None

            # Update related tblPriceList UsedQty and TotalAmount aggregate fields
            sync_query = text(
            '''
            UPDATE "tblPriceList"
            SET "UsedQty" = sub.total_qty,
                "TotalAmount" = sub.total_qty * "NetPrice"
            FROM (
                SELECT COALESCE(SUM("Qty"), 0) as total_qty
                FROM "tblModules"
                WHERE "ItemID" = :item_id
            ) AS sub
            WHERE "ID" = :item_id
            '''
            )
            session.execute(sync_query, {"item_id": item_id})
            session.commit()
            
            return new_id

    def update_module(self, module_id, module_type_id, item_id, qty, seqno):
        # Fetch old item_id to handle item change consistency
        old_module = self.get_module(module_id)
        old_item_id = old_module[2] if old_module else None

        query = text(
            '''
            UPDATE "tblModules"
            SET
                "ModuleTypeID" = :module_type_id,
                "ItemID" = :item_id,
                "Qty" = :qty,
                "SEQNo" = :seqno
            WHERE "ID" = :module_id
            '''
        )
        with get_session() as session:
            session.execute(
                query,
                {
                    "module_id": module_id,
                    "module_type_id": module_type_id,
                    "item_id": item_id,
                    "qty": qty,
                    "seqno": seqno,
                },
            )

            # Sync queries for Price List consistency
            sync_query = text(
            '''
            UPDATE "tblPriceList"
            SET "UsedQty" = sub.total_qty,
                "TotalAmount" = sub.total_qty * "NetPrice"
            FROM (
                SELECT COALESCE(SUM("Qty"), 0) as total_qty
                FROM "tblModules"
                WHERE "ItemID" = :item_id
            ) AS sub
            WHERE "ID" = :item_id
            '''
            )
            
            # Update current item
            session.execute(sync_query, {"item_id": item_id})
            
            # Update old item if the ItemID was changed in this update
            if old_item_id and old_item_id != item_id:
                session.execute(sync_query, {"item_id": old_item_id})
            session.commit()

    def delete_module(self, module_id):
        # Fetch item_id before deletion to sync price list afterwards
        old_module = self.get_module(module_id)
        item_id = old_module[2] if old_module else None

        query = text(
            '''
            DELETE FROM "tblModules"
            WHERE "ID" = :module_id
            '''
        )
        with get_session() as session:
            session.execute(query, {"module_id": module_id})

            if item_id:
                sync_query = text(
                '''
                UPDATE "tblPriceList"
                SET "UsedQty" = sub.total_qty,
                    "TotalAmount" = sub.total_qty * "NetPrice"
                FROM (
                    SELECT COALESCE(SUM("Qty"), 0) as total_qty
                    FROM "tblModules"
                    WHERE "ItemID" = :item_id
                ) AS sub
                WHERE "ID" = :item_id
                '''
                )
                session.execute(sync_query, {"item_id": item_id})
            session.commit()
