from app.repositories.busbar_repository import BusbarRepository

class BusbarService:
    def __init__(self):
        self.repository = BusbarRepository()

    def get_all_busbars(self):
        return self.repository.get_all_busbars()

    def get_busbar(self, bb_id):
        return self.repository.get_busbar_by_id(bb_id)

    def create_busbar(self, data):
        return self.repository.create_busbar(data['run'], data['width'], data['thick'], data['metal_id'], data['sleeve_id'])

    def update_busbar(self, bb_id, data):
        return self.repository.update_busbar(bb_id, data['run'], data['width'], data['thick'], data['metal_id'], data['sleeve_id'])

    def delete_busbar(self, bb_id):
        return self.repository.delete_busbar(bb_id)

    def get_metals(self):
        return self.repository.get_all_metals()

    def create_metal(self, metal, density, curr_density, cost):
        return self.repository.create_metal(metal, density, curr_density, cost)

    def update_metal(self, metal_id, metal, density, curr_density, cost):
        return self.repository.update_metal(metal_id, metal, density, curr_density, cost)

    def delete_metal(self, metal_id):
        return self.repository.delete_metal(metal_id)

    def get_sleeves(self):
        return self.repository.get_all_sleeves()

    def create_sleeve(self, b_width, b_thick, s_width, s_rate, n_rate):
        return self.repository.create_sleeve(b_width, b_thick, s_width, s_rate, n_rate)

    def update_sleeve(self, sleeve_id, b_width, b_thick, s_width, s_rate, n_rate):
        return self.repository.update_sleeve(sleeve_id, b_width, b_thick, s_width, s_rate, n_rate)

    def delete_sleeve(self, sleeve_id):
        return self.repository.delete_sleeve(sleeve_id)

    # Analytics
    def get_analytics(self):
        return {
            "usage": self.repository.get_material_usage_summary(),
            "costs": self.repository.get_metal_cost_analysis(),
            "sleeves": self.repository.get_sleeve_usage_report()
        }

    def get_summary_view(self, filters=None):
        return self.repository.get_busbar_summary(filters)