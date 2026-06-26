from sqlalchemy import text
from app.config.database import get_session

class POCustomerRepository:
    def get_pos_by_quote(self, quote_id):
        sql = text("""
            SELECT "ID", "Quotation_ID", "PO_No", "PO_Date"
            FROM public."po_Customer"
            WHERE "Quotation_ID" = :quote_id
            ORDER BY "ID" DESC
        """)
        with get_session() as session:
            result = session.execute(sql, {"quote_id": quote_id})
            return [dict(row._mapping) for row in result.fetchall()]

    def create_po(self, quote_id, po_no, po_date):
        sql = text("""
            INSERT INTO public."po_Customer" ("Quotation_ID", "PO_No", "PO_Date")
            VALUES (:quote_id, :po_no, :po_date)
            RETURNING "ID"
        """)
        with get_session() as session:
            result = session.execute(sql, {
                "quote_id": quote_id,
                "po_no": po_no,
                "po_date": po_date
            })
            session.commit()
            return result.scalar()

    def update_po(self, po_id, po_no, po_date):
        sql = text("""
            UPDATE public."po_Customer"
            SET "PO_No" = :po_no, "PO_Date" = :po_date
            WHERE "ID" = :po_id
        """)
        with get_session() as session:
            session.execute(sql, {
                "po_id": po_id,
                "po_no": po_no,
                "po_date": po_date
            })
            session.commit()

    def delete_po(self, po_id):
        sql = text("""
            DELETE FROM public."po_Customer"
            WHERE "ID" = :po_id
        """)
        with get_session() as session:
            session.execute(sql, {"po_id": po_id})
            session.commit()

    def get_items_by_po(self, po_id):
        sql = text("""
            SELECT "ID", "PO_Customer_ID", "Description", "Qty", "Price", "Amount", "Warranty"
            FROM public."po_Items"
            WHERE "PO_Customer_ID" = :po_id
            ORDER BY "ID" ASC
        """)
        with get_session() as session:
            result = session.execute(sql, {"po_id": po_id})
            return [dict(row._mapping) for row in result.fetchall()]

    def create_po_item(self, po_id, description, qty, price, amount, warranty):
        sql = text("""
            INSERT INTO public."po_Items" ("PO_Customer_ID", "Description", "Qty", "Price", "Amount", "Warranty")
            VALUES (:po_id, :description, :qty, :price, :amount, :warranty)
            RETURNING "ID"
        """)
        with get_session() as session:
            result = session.execute(sql, {
                "po_id": po_id,
                "description": description,
                "qty": qty,
                "price": price,
                "amount": amount,
                "warranty": warranty
            })
            session.commit()
            return result.scalar()

    def update_po_item(self, item_id, description, qty, price, amount, warranty):
        sql = text("""
            UPDATE public."po_Items"
            SET "Description" = :description, "Qty" = :qty, "Price" = :price, "Amount" = :amount, "Warranty" = :warranty
            WHERE "ID" = :item_id
        """)
        with get_session() as session:
            session.execute(sql, {
                "item_id": item_id,
                "description": description,
                "qty": qty,
                "price": price,
                "amount": amount,
                "warranty": warranty
            })
            session.commit()

    def delete_po_item(self, item_id):
        sql = text("""
            DELETE FROM public."po_Items"
            WHERE "ID" = :item_id
        """)
        with get_session() as session:
            session.execute(sql, {"item_id": item_id})
            session.commit()

    def get_quote_used_items(self, quote_id):
        sql = text("""
            SELECT 
                mi."DriveDescription" as "Description",
                SUM(
                    COALESCE(p."PanelQty", 1) * 
                    COALESCE(pm."PanelModQty", 1) *
                    CASE 
                        WHEN mi."BOM" IS NOT NULL AND mi."BOM" <> 0 THEN mi."BOM" 
                        ELSE 1
                    END
                ) as "TotalQty",
                MAX(mi."LP") as "UnitPrice"
            FROM public."tbl_Panels" p
            JOIN public."tbl_PanelModules" pm ON p."ID" = pm."PanelID"
            JOIN public."tbl_ModuleItems" mi ON pm."ID" = mi."ID"
            WHERE p."QuoteID" = :quote_id
            GROUP BY mi."DriveDescription"
            ORDER BY mi."DriveDescription"
        """)
        with get_session() as session:
            result = session.execute(sql, {"quote_id": quote_id})
            return [dict(row._mapping) for row in result.fetchall()]
