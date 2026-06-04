from sqlalchemy import text

from app.config.database import get_session # Assuming get_session is now a context manager


class CustomerRepository:
    def __init__(self):
        pass # Session will be acquired per method

    def get_customers(self):
        query = text(
            '''
            SELECT "ID", "CustomerName", "Mail", "CustomerPhone",
                   "CustomerAddress", "CustomerCity", "CustomerStateID",
                   "CustomerPIN", "CustomerNotes", "CustomerGSTNCode",
                   "Attachments", "SysDateOfEntry"
            FROM "tblCustomers"
            ORDER BY "CustomerName"
            '''
        )

        with get_session() as session:
            result = session.execute(query)
            return result.fetchall(), result.keys()
        
    def get_customer_by_id(self, customer_id):
        query = text(
            '''
            SELECT "ID", "CustomerName", "Mail", "CustomerPhone",
                   "CustomerAddress", "CustomerCity", "CustomerStateID",
                   "CustomerPIN", "CustomerNotes", "CustomerGSTNCode",
                   "Attachments", "SysDateOfEntry"
            FROM "tblCustomers"
            WHERE "ID" = :customer_id
            '''
        )

        with get_session() as session:
            result = session.execute(
                query,
                {"customer_id": customer_id}
            )
            return result.fetchone()
        
    def search_customers(self, keyword):
        query = text(
            '''
            SELECT c."ID", c."CustomerName", c."Mail", c."CustomerPhone",
                   c."CustomerAddress", c."CustomerCity", c."CustomerStateID",
                   s."StateName" AS "CustomerStateName", c."CustomerPIN",
                   c."CustomerNotes", c."CustomerGSTNCode",
                   c."Attachments", c."SysDateOfEntry"
            FROM "tblCustomers" c
            LEFT JOIN "tblState" s ON c."CustomerStateID" = s."ID"
            WHERE (c."ID" = :id_exact)
               OR LOWER(c."CustomerName") LIKE LOWER(:keyword)
               OR LOWER(c."Mail") LIKE LOWER(:keyword)
               OR LOWER(CAST(c."CustomerPhone" AS TEXT)) LIKE LOWER(:keyword)
               OR LOWER(c."CustomerAddress") LIKE LOWER(:keyword)
               OR LOWER(c."CustomerCity") LIKE LOWER(:keyword)
               OR LOWER(CAST(c."CustomerStateID" AS TEXT)) LIKE LOWER(:keyword)
               OR LOWER(CAST(c."CustomerPIN" AS TEXT)) LIKE LOWER(:keyword)
               OR LOWER(c."CustomerNotes") LIKE LOWER(:keyword)
               OR LOWER(c."CustomerGSTNCode") LIKE LOWER(:keyword)
               OR LOWER(COALESCE(c."Attachments", '')) LIKE LOWER(:keyword)
               OR LOWER(CAST(c."SysDateOfEntry" AS TEXT)) LIKE LOWER(:keyword)
               OR LOWER(COALESCE(s."StateName", '')) LIKE LOWER(:keyword)
            ORDER BY c."CustomerName"
            '''
        )

        id_exact = int(keyword) if keyword.isdigit() else None
        with get_session() as session:
            result = session.execute(
                query,
                {
                    "keyword": f"%{keyword}%",
                    "id_exact": id_exact,
                }
            )
            return result.fetchall(), result.keys()
        
    def create_customer(
        self,
        customer_name,
        mail,
        phone,
        address,
        city,
        state_id,
        pin,
        notes,
        gstn_code,
        attachments
    ):
        query = text(
            '''
            INSERT INTO "tblCustomers"
            ("CustomerName", "Mail", "CustomerPhone", "CustomerAddress",
             "CustomerCity", "CustomerStateID", "CustomerPIN", "CustomerNotes",
             "CustomerGSTNCode", "Attachments")
            VALUES
            (:customer_name, :mail, :phone, :address,
             :city, :state_id, :pin, :notes,
             :gstn_code, :attachments)
            '''
        )

        with get_session() as session:
            session.execute(
                query,
                {
                    "customer_name": customer_name,
                    "mail": mail,
                    "phone": phone,
                    "address": address,
                    "city": city,
                    "state_id": state_id,
                    "pin": pin,
                    "notes": notes,
                    "gstn_code": gstn_code,
                    "attachments": attachments,
                }
            )
            session.commit()
        
    def update_customer(
        self,
        customer_id,
        customer_name,
        mail,
        phone,
        address,
        city,
        state_id,
        pin,
        notes,
        gstn_code,
        attachments
    ):
        query = text(
            '''
            UPDATE "tblCustomers"
            SET "CustomerName" = :customer_name,
                "Mail" = :mail,
                "CustomerPhone" = :phone,
                "CustomerAddress" = :address,
                "CustomerCity" = :city,
                "CustomerStateID" = :state_id,
                "CustomerPIN" = :pin,
                "CustomerNotes" = :notes,
                "CustomerGSTNCode" = :gstn_code,
                "Attachments" = :attachments
            WHERE "ID" = :customer_id
            '''
        )

        with get_session() as session:
            session.execute(
                query,
                {
                    "customer_id": customer_id,
                    "customer_name": customer_name,
                    "mail": mail,
                    "phone": phone,
                    "address": address,
                    "city": city,
                    "state_id": state_id,
                    "pin": pin,
                    "notes": notes,
                    "gstn_code": gstn_code,
                    "attachments": attachments,
                }
            )
            session.commit()

    def delete_customer(self, customer_id):
        query = text(
            '''
            DELETE FROM "tblCustomers"
            WHERE "ID" = :customer_id
            '''
        )

        self.session.execute(
            query,
            {"customer_id": customer_id}
        )
        self.session.commit()
    

    def create_contact(
        self,
        customer_id,
        name,
        title,
        designation,
        mobile1,
        mobile2,
    ):

        query = text(
            '''
            INSERT INTO "tblCustomerContacts"
            (
                "CustomerID",
                "CustomerContactName",
                "CustomerContactTitle",
                "CustomerContactDesignation",
                "CustomerMobile1",
                "CustomerMobile2"
            )
            VALUES
            (
                :customer_id,
                :name,
                :title,
                :designation,
                :mobile1,
                :mobile2
            )
            '''
        )

        with get_session() as session:
            session.execute(
                query,
                {
                    "customer_id": customer_id,
                    "name": name,
                    "title": title,
                    "designation": designation,
                    "mobile1": mobile1,
                    "mobile2": mobile2,
                }
            )

            session.commit()

    def update_contact(
        self,
        contact_id,
        name,
        title,
        designation,
        mobile1,
        mobile2,
    ):

        query = text(
            '''
            UPDATE "tblCustomerContacts"
            SET
                "CustomerContactName"=:name,
                "CustomerContactTitle"=:title,
                "CustomerContactDesignation"=:designation,
                "CustomerMobile1"=:mobile1,
                "CustomerMobile2"=:mobile2
            WHERE "ID"=:contact_id
            '''
        )

        with get_session() as session:
            session.execute(
                query,
                {
                    "contact_id": contact_id,
                    "name": name,
                    "title": title,
                    "designation": designation,
                    "mobile1": mobile1,
                    "mobile2": mobile2,
                }
            )

            session.commit()

    def delete_contact(self, contact_id):
        query = text(
            '''
            DELETE FROM "tblCustomerContacts"
            WHERE "ID"=:contact_id
            '''
        )

        with get_session() as session:
            session.execute(
                query,
                {
                    "contact_id": contact_id
                }
            )

            session.commit()