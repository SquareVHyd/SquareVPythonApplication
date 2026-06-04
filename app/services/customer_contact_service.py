from app.repositories.customer_contact_repository import (
    CustomerContactRepository
)


class CustomerContactService:

    def __init__(self):
        self.repository = CustomerContactRepository()

    def get_contacts_by_customer(self, customer_id):
        return self.repository.get_contacts_by_customer_id(
            customer_id
        )
    def create_contact(
        self,
        customer_id,
        name,
        title,
        designation,
        mobile1,
        mobile2,
    ):
        return self.repository.create_contact(
            customer_id,
            name,
            title,
            designation,
            mobile1,
            mobile2,
        )


    def update_contact(
        self,
        contact_id,
        name,
        title,
        designation,
        mobile1,
        mobile2,
    ):
        return self.repository.update_contact(
            contact_id,
            name,
            title,
            designation,
            mobile1,
            mobile2,
        )


    def delete_contact(self, contact_id):
        return self.repository.delete_contact(contact_id)