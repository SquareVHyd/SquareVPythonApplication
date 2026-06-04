from app.repositories.customer_repository import CustomerRepository


class CustomerService:
    def __init__(self):
        self.repository = CustomerRepository()

    def get_all_customers(self):
        return self.repository.get_customers()

    def get_customer(self, customer_id):
        return self.repository.get_customer_by_id(customer_id)

    def search(self, keyword):
        return self.repository.search_customers(keyword)

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
        attachments,
    ):
        return self.repository.create_customer(
            customer_name,
            mail,
            phone,
            address,
            city,
            state_id,
            pin,
            notes,
            gstn_code,
            attachments,
        )

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
        attachments,
    ):
        return self.repository.update_customer(
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
            attachments,
        )

    def delete_customer(self, customer_id):
        return self.repository.delete_customer(customer_id)