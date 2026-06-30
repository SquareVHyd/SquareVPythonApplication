from app.repositories.price_list_repository import PriceListRepository


class PriceListService:
    def __init__(self):
        self.repository = PriceListRepository()

    def get_all_price_items(self):
        return self.repository.get_all_price_items()

    def get_price_item(self, item_id):
        return self.repository.get_price_item(item_id)

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
        return self.repository.create_price_item(
            item_description,
            model,
            list_price,
            discount_percent,
            net_price,
            used_qty,
            total_amount,
            category_id,
            make_id,
        )

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
        return self.repository.update_price_item(
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
        )

    def delete_price_item(self, item_id):
        return self.repository.delete_price_item(item_id)

    def get_all_categories(self):
        return self.repository.get_all_categories()

    def get_all_makes(self):
        return self.repository.get_all_makes()

    def create_category(self, category_name):
        return self.repository.create_category(category_name)

    def create_make(self, make_name):
        return self.repository.create_make(make_name)

    def get_pricelist_view_data(self):
        """Pass-through to repository to fetch data from vwPriceList."""
        return self.repository.get_pricelist_view_data()

    def get_price_revisions(self, price_list_id):
        """Returns price revision history (oldest first) for a specific item."""
        return self.repository.get_price_revisions(price_list_id)

    def get_all_price_revisions(self):
        """Returns all revision records joined with item description."""
        return self.repository.get_all_price_revisions()

    def get_updated_items_revisions(self):
        """Returns only items with more than one revision entry (price was changed)."""
        return self.repository.get_updated_items_revisions()
