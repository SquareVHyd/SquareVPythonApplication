from sqlalchemy import text
from app.config.database import get_session


class PriceListService:

    def get_all_items(self):

        session = get_session()

        try:

            result = session.execute(
                text("""
                    SELECT
                        "ID",
                        "ItemDescription",
                        "Model",
                        "ListPrice",
                        "DiscountPercent",
                        "NetPrice",
                        "UsedQty",
                        "TotalAmount",
                        "CategoryID",
                        "MakeID"
                    FROM public."tblPriceList"
                    ORDER BY "ID"
                """)
            )

            return result.fetchall(), None

        finally:
            session.close()

    def get_item(self, item_id):

        session = get_session()

        try:

            result = session.execute(
                text("""
                    SELECT *
                    FROM public."tblPriceList"
                    WHERE "ID"=:id
                """),
                {"id": item_id}
            )

            return result.fetchone()

        finally:
            session.close()

    def add_item(self, values):

        session = get_session()

        try:

            session.execute(
                text("""
                    INSERT INTO public."tblPriceList"
                    (
                        "ItemDescription",
                        "Model",
                        "ListPrice",
                        "DiscountPercent",
                        "NetPrice",
                        "UsedQty",
                        "TotalAmount",
                        "CategoryID",
                        "MakeID"
                    )
                    VALUES
                    (
                        :ItemDescription,
                        :Model,
                        :ListPrice,
                        :DiscountPercent,
                        :NetPrice,
                        :UsedQty,
                        :TotalAmount,
                        :CategoryID,
                        :MakeID
                    )
                """),
                values
            )

            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    def update_item(self, item_id, values):

        session = get_session()

        try:

            values["ID"] = item_id

            session.execute(
                text("""
                    UPDATE public."tblPriceList"
                    SET
                        "ItemDescription"=:ItemDescription,
                        "Model"=:Model,
                        "ListPrice"=:ListPrice,
                        "DiscountPercent"=:DiscountPercent,
                        "NetPrice"=:NetPrice,
                        "UsedQty"=:UsedQty,
                        "TotalAmount"=:TotalAmount,
                        "CategoryID"=:CategoryID,
                        "MakeID"=:MakeID
                    WHERE "ID"=:ID
                """),
                values
            )

            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    def delete_item(self, item_id):

        session = get_session()

        try:

            session.execute(
                text("""
                    DELETE
                    FROM public."tblPriceList"
                    WHERE "ID"=:id
                """),
                {"id": item_id}
            )

            session.commit()

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()