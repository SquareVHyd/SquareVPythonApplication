from app.repositories.po_customer_repository import POCustomerRepository

class POCustomerService:
    def __init__(self):
        self.repository = POCustomerRepository()

    def get_pos_by_quote(self, quote_id):
        return self.repository.get_pos_by_quote(quote_id)

    def create_po(self, quote_id, po_no, po_date):
        if not po_no or not po_date:
            raise ValueError("PO Number and PO Date are required.")
        return self.repository.create_po(quote_id, po_no, po_date)

    def update_po(self, po_id, po_no, po_date):
        if not po_no or not po_date:
            raise ValueError("PO Number and PO Date are required.")
        self.repository.update_po(po_id, po_no, po_date)

    def delete_po(self, po_id):
        self.repository.delete_po(po_id)

    def get_items_by_po(self, po_id):
        return self.repository.get_items_by_po(po_id)

    def create_po_item(self, po_id, description, qty, price, warranty):
        qty = float(qty or 0)
        price = float(price or 0)
        amount = qty * price
        warranty = float(warranty or 0)
        return self.repository.create_po_item(po_id, description, qty, price, amount, warranty)

    def update_po_item(self, item_id, description, qty, price, warranty):
        qty = float(qty or 0)
        price = float(price or 0)
        amount = qty * price
        warranty = float(warranty or 0)
        self.repository.update_po_item(item_id, description, qty, price, amount, warranty)

    def delete_po_item(self, item_id):
        self.repository.delete_po_item(item_id)

    def get_quote_used_items(self, quote_id):
        return self.repository.get_quote_used_items(quote_id)
