from app.repositories.generic_spec_repository import GenericSpecRepository

class GenericSpecService:
    def __init__(self):
        self.repository = GenericSpecRepository()

    def get_all_generic_items(self):
        return self.repository.get_all_generic_items()

    def create_generic_item(self, item_description, remark_makes=None):
        return self.repository.create_generic_item(item_description, remark_makes)

    def update_generic_item(self, item_id, item_description, remark_makes=None):
        return self.repository.update_generic_item(item_id, item_description, remark_makes)

    def delete_generic_item(self, item_id):
        return self.repository.delete_generic_item(item_id)

    def count_linked_price_items(self, item_id):
        return self.repository.count_linked_price_items(item_id)

    def get_price_list_items(self):
        return self.repository.get_price_list_items()

    def assign_generic_item_to_price_items(self, generic_id, price_item_ids):
        return self.repository.assign_generic_item_to_price_items(generic_id, price_item_ids)

    def remove_generic_item_mapping(self, price_item_ids):
        return self.repository.remove_generic_item_mapping(price_item_ids)
