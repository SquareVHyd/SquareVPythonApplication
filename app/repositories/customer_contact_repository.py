from sqlalchemy import text

from app.config.database import get_session


class CustomerContactRepository:

    def __init__(self):
        self.session = get_session()

    def get_contacts_by_customer_id(self, customer_id):

        query = text(
            '''
            SELECT
                "ID",
                "CustomerID",
                "CustomerContactName",
                "CustomerContactTitle",
                "CustomerContactDesignation",
                "CustomerMobile1",
                "CustomerMobile2"
            FROM "tblCustomerContacts"
            WHERE "CustomerID" = :customer_id
            ORDER BY "CustomerContactName"
            '''
        )

        with get_session() as session:
            result = session.execute(
                query,
                {
                    "customer_id": customer_id
                }
            )

            return result.fetchall()

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