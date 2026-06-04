from app.repositories.panel_repository import PanelRepository


class PanelService:
    def __init__(self):
        self.repository = PanelRepository()

    # Panel CRUD operations
    def get_all_panels(self):
        return self.repository.get_all_panels()

    def get_panel(self, panel_id):
        return self.repository.get_panel_by_id(panel_id)

    def search_panels(self, keyword):
        return self.repository.search_panels(keyword)

    def create_panel(self, panel_data):
        return self.repository.create_panel(panel_data)

    def update_panel(self, panel_id, panel_data):
        return self.repository.update_panel(panel_id, panel_data)

    def delete_panel(self, panel_id):
        return self.repository.delete_panel(panel_id)

    # Panel Modules operations
    def get_panel_modules(self, panel_id):
        return self.repository.get_panel_modules(panel_id)

    def create_panel_module(self, module_data):
        return self.repository.create_panel_module(module_data)

    def update_panel_module(self, module_id, module_data):
        return self.repository.update_panel_module(module_id, module_data)

    def delete_panel_module(self, module_id):
        return self.repository.delete_panel_module(module_id)

    # Panel Steel operations
    def get_panel_steel(self, panel_id):
        return self.repository.get_panel_steel(panel_id)

    def create_panel_steel(self, steel_data):
        return self.repository.create_panel_steel(steel_data)

    def update_panel_steel(self, steel_id, steel_data):
        return self.repository.update_panel_steel(steel_id, steel_data)

    # Panel Busbar operations
    def get_panel_busbar(self, panel_id):
        return self.repository.get_panel_busbar(panel_id)

    def create_panel_busbar(self, busbar_data):
        return self.repository.create_panel_busbar(busbar_data)

    def update_panel_busbar(self, busbar_id, busbar_data):
        return self.repository.update_panel_busbar(busbar_id, busbar_data)

    # Accessories operations
    def get_all_accessories(self):
        return self.repository.get_all_accessories()