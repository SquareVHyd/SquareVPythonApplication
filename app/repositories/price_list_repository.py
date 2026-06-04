from sqlalchemy import text

from app.config.database import get_session


class PriceListRepository:
    def get_all_price_items(self):
        with get_session() as session:
            try:
                result = session.execute(
                    text(""" -- Added DISTINCT to ensure unique price list items
                    SELECT
                        DISTINCT p."ID",
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
                        p."MakeID"

                    FROM public."tblPriceList" p

                    LEFT JOIN public."tblCategory" c
                        ON c."CategoryID" = p."CategoryID"

                    LEFT JOIN public."tblMake" m
                        ON m."MakeID" = p."MakeID"

                    ORDER BY p."ItemDescription"
                """)
            )
                return result.fetchall(), result.keys()
            except Exception as e:
                session.rollback()
                raise e

    def get_price_item(self, item_id):
        with get_session() as session:
            query = text(
                '''
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
                p."MakeID"

            FROM public."tblPriceList" p
            LEFT JOIN public."tblCategory" c
                ON c."CategoryID" = p."CategoryID"
            LEFT JOIN public."tblMake" m
                ON m."MakeID" = p."MakeID"
            WHERE p."ID" = :id
            '''
        )
            result = session.execute(query, {"id": item_id})
            row = result.fetchone()
            return row


    def create_price_item(
        self,
        item_description,
        model,
        list_price,
        discount_percent,
        net_price,
        used_qty,
        total_amount,
        category_id,
        make_id,
    ):
        # Recalculate derived fields to maintain database consistency
        with get_session() as session:
            calc_net_price = float(list_price or 0) * (1 - float(discount_percent or 0) / 100)
            calc_total_amount = calc_net_price * int(used_qty or 0)

            query = text(
                '''
            INSERT INTO "tblPriceList"
                ("ItemDescription", "Model", "ListPrice", "DiscountPercent", "NetPrice", "UsedQty", "TotalAmount", "CategoryID", "MakeID")
            VALUES
                (:item_description, :model, :list_price, :discount_percent, :net_price, :used_qty, :total_amount, :category_id, :make_id)
            RETURNING "ID"
            '''
            )
            try:
                res = session.execute(
                    query,
                    {
                        "item_description": item_description,
                        "model": model,
                        "list_price": list_price,
                        "discount_percent": float(discount_percent or 0),
                        "net_price": calc_net_price,
                        "used_qty": int(used_qty or 0),
                        "total_amount": calc_total_amount,
                        "category_id": category_id,
                        "make_id": make_id,
                    },
                )
                row = res.fetchone()
                new_id = row[0] if row else None
                session.commit()
                return new_id
            except Exception as e:
                session.rollback()
                raise e

    def update_price_item(
        self,
        item_id,
        item_description,
        model,
        list_price,
        discount_percent,
        net_price,
        used_qty,
        total_amount,
        category_id,
        make_id,
    ):
        with get_session() as session:
            # Recalculate derived fields to maintain database consistency
            calc_net_price = float(list_price or 0) * (1 - float(discount_percent or 0) / 100)
            calc_total_amount = calc_net_price * int(used_qty or 0)

            query = text(
                '''
            UPDATE "tblPriceList"
            SET
                "ItemDescription" = :item_description,
                "Model" = :model,
                "ListPrice" = :list_price,
                "DiscountPercent" = :discount_percent,
                "NetPrice" = :calc_net_price,
                "UsedQty" = :used_qty,
                "TotalAmount" = :calc_total_amount,
                "CategoryID" = :category_id,
                "MakeID" = :make_id
            WHERE "ID" = :id
            '''
            )
            try:
                session.execute(
                    query,
                    {
                        "id": item_id,
                        "item_description": item_description,
                        "model": model,
                        "list_price": list_price,
                        "discount_percent": float(discount_percent or 0),
                        "calc_net_price": calc_net_price, # Changed from net_price to calc_net_price
                        "used_qty": int(used_qty or 0),
                        "calc_total_amount": calc_total_amount, # Changed from total_amount to calc_total_amount
                        "category_id": category_id,
                        "make_id": make_id,
                    },
                )
                session.commit()
            except Exception as e:
                session.rollback()
                raise e

    def delete_price_item(self, item_id):
        with get_session() as session:
            query = text(
                '''
            DELETE FROM "tblPriceList"
            WHERE "ID" = :id
            '''
            )
            try:
                session.execute(query, {"id": item_id})
                session.commit()
            except Exception as e:
                session.rollback()
                raise e

    def get_all_categories(self):
        with get_session() as session:
            query = text(
                '''
            SELECT "CategoryID", "Category"
            FROM public."tblCategory"
            ORDER BY "Category"
            '''
            )
            result = session.execute(query)
            return result.fetchall()

    def get_all_makes(self):
        with get_session() as session:
            query = text(
                '''
            SELECT "MakeID", "Make"
            FROM public."tblMake"
            ORDER BY "Make"
            '''
            )
            result = session.execute(query)
            return result.fetchall()

    def create_category(self, category_name):
        with get_session() as session:
            query = text(
                '''
            INSERT INTO public."tblCategory" ("Category")
            VALUES (:name)
            '''
            )
            try:
                session.execute(query, {"name": category_name})
                session.commit()
            except Exception as e:
                session.rollback()
                raise e

    def create_make(self, make_name):
        with get_session() as session:
            query = text(
                '''
            INSERT INTO public."tblMake" ("Make")
            VALUES (:name)
            '''
            )
            try:
                session.execute(query, {"name": make_name})
                session.commit()
            except Exception as e:
                session.rollback()
                raise e
