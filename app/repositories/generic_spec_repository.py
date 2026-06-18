from sqlalchemy import text
from app.config.database import get_session

class GenericSpecRepository:
    def __init__(self):
        pass

    def initialize_tables(self):
        """Creates tblGenericSpecItems and updates tblPriceList with the foreign key if they do not exist."""
        with get_session() as session:
            try:
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS public."tblGenericSpecItems" (
                        "ID" SERIAL PRIMARY KEY,
                        "ItemDescription" TEXT NOT NULL UNIQUE,
                        "Remark/Makes" TEXT
                    );
                """))
                session.execute(text("""
                    ALTER TABLE public."tblGenericSpecItems"
                    ADD COLUMN IF NOT EXISTS "Remark/Makes" TEXT;
                """))
                
                # 2. Add GenericSpecItemID foreign key column to tblPriceList
                session.execute(text("""
                    ALTER TABLE public."tblPriceList" 
                    ADD COLUMN IF NOT EXISTS "GenericSpecItemID" INTEGER;
                """))
                
                # 3. Add FK constraint if it doesn't exist
                session.execute(text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.table_constraints 
                            WHERE constraint_name = 'fk_price_list_generic_spec' 
                            AND table_name = 'tblPriceList'
                        ) THEN
                            ALTER TABLE public."tblPriceList"
                            ADD CONSTRAINT fk_price_list_generic_spec
                            FOREIGN KEY ("GenericSpecItemID")
                            REFERENCES public."tblGenericSpecItems"("ID")
                            ON DELETE SET NULL;
                        END IF;
                    END
                    $$;
                """))

                # 4. Add index for performance on GenericSpecItemID
                session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_pricelist_generic_spec_id 
                    ON public."tblPriceList"("GenericSpecItemID");
                """))
                
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error initializing generic spec tables: {e}")

    def get_all_generic_items(self):
        """Retrieves all generic specification items ordered by description."""
        query = text("""
            SELECT "ID", "ItemDescription", "Remark/Makes"
            FROM public."tblGenericSpecItems"
            ORDER BY "ItemDescription" ASC
        """)
        with get_session() as session:
            result = session.execute(query)
            return result.fetchall(), result.keys()

    def create_generic_item(self, item_description, remark_makes=None):
        """Creates a new generic item description. Returns new ID."""
        query = text("""
            INSERT INTO public."tblGenericSpecItems" ("ItemDescription", "Remark/Makes")
            VALUES (:desc, :remark)
            RETURNING "ID"
        """)
        with get_session() as session:
            try:
                res = session.execute(query, {"desc": item_description, "remark": remark_makes})
                row = res.fetchone()
                new_id = row[0] if row else None
                session.commit()
                return new_id
            except Exception as e:
                session.rollback()
                raise e

    def update_generic_item(self, item_id, item_description, remark_makes=None):
        """Updates a generic item's description."""
        query = text("""
            UPDATE public."tblGenericSpecItems"
            SET "ItemDescription" = :desc, "Remark/Makes" = :remark
            WHERE "ID" = :id
        """)
        with get_session() as session:
            try:
                session.execute(query, {"desc": item_description, "remark": remark_makes, "id": item_id})
                session.commit()
            except Exception as e:
                session.rollback()
                raise e

    def delete_generic_item(self, item_id):
        """Deletes a generic item."""
        query = text("""
            DELETE FROM public."tblGenericSpecItems"
            WHERE "ID" = :id
        """)
        with get_session() as session:
            try:
                session.execute(query, {"id": item_id})
                session.commit()
            except Exception as e:
                session.rollback()
                raise e

    def count_linked_price_items(self, item_id):
        """Checks the number of tblPriceList records linked to this generic item."""
        query = text("""
            SELECT COUNT(*)
            FROM public."tblPriceList"
            WHERE "GenericSpecItemID" = :id
        """)
        with get_session() as session:
            result = session.execute(query, {"id": item_id})
            return result.scalar()

    def get_price_list_items(self):
        """Fetches all price list items including category, make names, and GenericSpecItemID."""
        query = text("""
            SELECT
                p."ID",
                p."ItemDescription",
                p."Model",
                c."Category",
                m."Make",
                p."ListPrice",
                p."DiscountPercent",
                p."NetPrice",
                p."UsedQty",
                p."TotalAmount",
                p."CategoryID",
                p."MakeID",
                p."GenericSpecItemID"
            FROM public."tblPriceList" p
            LEFT JOIN public."tblCategory" c ON c."CategoryID" = p."CategoryID"
            LEFT JOIN public."tblMake" m ON m."MakeID" = p."MakeID"
            ORDER BY p."ItemDescription" ASC
        """)
        with get_session() as session:
            result = session.execute(query)
            return result.fetchall(), result.keys()

    def assign_generic_item_to_price_items(self, generic_id, price_item_ids):
        """Maps multiple price list records to a generic item ID."""
        if not price_item_ids:
            return
        
        # Build SQL with dynamic IN clause to ensure maximum compatibility
        placeholders = ", ".join(f":id_{i}" for i in range(len(price_item_ids)))
        query = text(f"""
            UPDATE public."tblPriceList"
            SET "GenericSpecItemID" = :generic_id
            WHERE "ID" IN ({placeholders})
        """)
        
        params = {"generic_id": generic_id}
        for i, pid in enumerate(price_item_ids):
            params[f"id_{i}"] = pid

        with get_session() as session:
            try:
                session.execute(query, params)
                session.commit()
            except Exception as e:
                session.rollback()
                raise e

    def remove_generic_item_mapping(self, price_item_ids):
        """Removes the generic item link from selected price list records."""
        if not price_item_ids:
            return
            
        placeholders = ", ".join(f":id_{i}" for i in range(len(price_item_ids)))
        query = text(f"""
            UPDATE public."tblPriceList"
            SET "GenericSpecItemID" = NULL
            WHERE "ID" IN ({placeholders})
        """)
        
        params = {}
        for i, pid in enumerate(price_item_ids):
            params[f"id_{i}"] = pid

        with get_session() as session:
            try:
                session.execute(query, params)
                session.commit()
            except Exception as e:
                session.rollback()
                raise e
