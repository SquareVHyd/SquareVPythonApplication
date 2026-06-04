from sqlalchemy import text
from app.config.database import get_session # Assuming get_session is now a context manager


class PanelRepository:
    def __init__(self):
        pass # Session will be acquired per method

    def get_all_panels(self):
        """Get all panels with related quote info"""
        query = text(
            """
            SELECT
                p."ID",
                p."PanelName",
                p."PanelSerial",
                p."PanelCategory",
                p."QuoteID",
                p."PanelQty",
                p."LengthXmm",
                p."HeightYmm",
                p."DepthZmm"
            FROM "tbl_Panels" p
            ORDER BY p."PanelName"
            """
        )
        try:
            with get_session() as session:
                result = session.execute(query)
                return result.fetchall(), result.keys()
        except Exception:
            return result.fetchall(), result.keys()

    def get_panel_by_id(self, panel_id):
        """Get panel details by ID"""
        query = text(
            """
            SELECT
                p."ID",
                p."PanelName",
                p."PanelSerial",
                p."PanelCategory",
                p."QuoteID",
                p."PanelQty",
                p."LengthXmm",
                p."HeightYmm",
                p."DepthZmm",
                p."AddWaste",
                p."PanelKARating",
                p."EarthRuns",
                p."StandRequired",
                p."BusbarMaterial"
            FROM "tbl_Panels" p
            WHERE p."ID" = :panel_id
            """
        )
        with get_session() as session:
            result = session.execute(query, {"panel_id": panel_id})
            return result.fetchone()

    def search_panels(self, keyword):
        """Search panels by name, serial, or category"""
        query = text(
            """
            SELECT
                p."ID",
                p."PanelName",
                p."PanelSerial",
                p."PanelCategory",
                p."QuoteID",
                p."PanelQty",
                p."LengthXmm",
                p."HeightYmm",
                p."DepthZmm"
            FROM "tbl_Panels" p
            WHERE LOWER(p."PanelName") LIKE LOWER(:keyword)
               OR LOWER(p."PanelSerial") LIKE LOWER(:keyword)
               OR LOWER(p."PanelCategory") LIKE LOWER(:keyword)
            ORDER BY p."PanelName"
            """
        )
        try:
            with get_session() as session:
                result = session.execute(query, {"keyword": f"%{keyword}%"})
                return result.fetchall(), result.keys()
        except Exception:
            return result.fetchall(), result.keys()

    def create_panel(self, panel_data):
        """Create a new panel"""
        query = text(
            """
            INSERT INTO "tbl_Panels" 
            ("PanelName", "PanelSerial", "PanelCategory", "QuoteID", "PanelQty",
             "LengthXmm", "HeightYmm", "DepthZmm", "AddWaste", "PanelKARating",
             "EarthRuns", "StandRequired", "BusbarMaterial")
            VALUES
            (:panel_name, :panel_serial, :panel_category, :quote_id, :panel_qty,
             :length, :height, :depth, :add_waste, :ka_rating,
             :earth_runs, :stand_required, :busbar_material)
            RETURNING "ID"
            """
        )
        with get_session() as session:
            result = session.execute(query, panel_data)
            session.commit()
            return result.scalar()

    def update_panel(self, panel_id, panel_data):
        """Update panel details"""
        query = text(
            """
            UPDATE "tbl_Panels"
            SET "PanelName" = :panel_name,
                "PanelSerial" = :panel_serial,
                "PanelCategory" = :panel_category,
                "QuoteID" = :quote_id,
                "PanelQty" = :panel_qty,
                "LengthXmm" = :length,
                "HeightYmm" = :height,
                "DepthZmm" = :depth,
                "AddWaste" = :add_waste,
                "PanelKARating" = :ka_rating,
                "EarthRuns" = :earth_runs,
                "StandRequired" = :stand_required,
                "BusbarMaterial" = :busbar_material
            WHERE "ID" = :panel_id
            """
        )
        with get_session() as session:
            panel_data["panel_id"] = panel_id
            session.execute(query, panel_data)
            session.commit()

    def delete_panel(self, panel_id):
        """Delete panel"""
        query = text(
            """
            DELETE FROM "tbl_Panels"
            WHERE "ID" = :panel_id
            """
        )        
        with get_session() as session:
            session.execute(query, {"panel_id": panel_id})
            session.commit()

    # Panel Modules methods
    def get_panel_modules(self, panel_id):
        """Get all modules for a panel"""
        query = text(
            """
            SELECT
                pm."ID",
                pm."IngOg",
                pm."PanelModQty",
                pm."ModuleTypeID",
                pm."ModPole",
                pm."ModKa",
                pm."Release",
                pm."Protection",
                pm."Remark"
            FROM "tbl_PanelModules" pm
            WHERE pm."PanelID" = :panel_id
            ORDER BY pm."ID"
            """
        )
        with get_session() as session:
            result = session.execute(query, {"panel_id": panel_id})
            return result.fetchall(), result.keys()

    def create_panel_module(self, module_data):
        """Create a new panel module"""
        query = text(
            """
            INSERT INTO "tbl_PanelModules"
            ("PanelID", "IngOg", "PanelModQty", "ModuleTypeID", "ModPole",
             "ModKa", "Release", "Protection", "Remark")
            VALUES
            (:panel_id, :ing_og, :panel_mod_qty, :module_type_id, :mod_pole,
             :mod_ka, :release, :protection, :remark)
            RETURNING "ID"
            """
        )
        with get_session() as session:
            result = session.execute(query, module_data)
            session.commit()
            return result.scalar()

    def update_panel_module(self, module_id, module_data):
        """Update panel module"""
        query = text(
            """
            UPDATE "tbl_PanelModules"
            SET "IngOg" = :ing_og,
                "PanelModQty" = :panel_mod_qty,
                "ModuleTypeID" = :module_type_id,
                "ModPole" = :mod_pole,
                "ModKa" = :mod_ka,
                "Release" = :release,
                "Protection" = :protection,
                "Remark" = :remark
            WHERE "ID" = :module_id
            """
        )
        with get_session() as session:
            module_data["module_id"] = module_id
            session.execute(query, module_data)
            session.commit()

    def delete_panel_module(self, module_id):
        """Delete panel module"""
        query = text(
            """
            DELETE FROM "tbl_PanelModules"
            WHERE "ID" = :module_id
            """
        )        
        with get_session() as session:
            session.execute(query, {"module_id": module_id})
            session.commit()

    # Panel Steel methods
    def get_panel_steel(self, panel_id):
        """Get steel configuration for a panel"""
        query = text(
            """
            SELECT *
            FROM "tbl_PanelSteel"
            WHERE "PanelID" = :panel_id
            """
        )
        with get_session() as session:
            result = session.execute(query, {"panel_id": panel_id})
            return result.fetchone()

    def create_panel_steel(self, steel_data):
        """Create or update panel steel"""
        query = text(
            """
            INSERT INTO "tbl_PanelSteel"
            ("PanelID", "FrontBackQty", "FrontBackSteelSize", "SidesQty",
             "SidesSteelSize", "BottomTopQty", "BottomSteelSize", "TypeOfSeating",
             "Canopy", "IndoorOutdoor", "PanelFace", "DoubleDoor", "DrawoutFixed",
             "ProtectionClass", "CableEntry", "Mounting", "SeatStand", "StandMetalSize")
            VALUES
            (:panel_id, :front_back_qty, :front_back_steel_size, :sides_qty,
             :sides_steel_size, :bottom_top_qty, :bottom_steel_size, :type_of_seating,
             :canopy, :indoor_outdoor, :panel_face, :double_door, :drawout_fixed,
             :protection_class, :cable_entry, :mounting, :seat_stand, :stand_metal_size)
            RETURNING "ID"
            """
        )
        result = self.session.execute(query, steel_data)
        self.session.commit()
        return result.scalar()

    def update_panel_steel(self, steel_id, steel_data):
        """Update panel steel"""
        query = text(
            """
            UPDATE "tbl_PanelSteel"
            SET "FrontBackQty" = :front_back_qty,
                "FrontBackSteelSize" = :front_back_steel_size,
                "SidesQty" = :sides_qty,
                "SidesSteelSize" = :sides_steel_size,
                "BottomTopQty" = :bottom_top_qty,
                "BottomSteelSize" = :bottom_steel_size,
                "TypeOfSeating" = :type_of_seating,
                "Canopy" = :canopy,
                "IndoorOutdoor" = :indoor_outdoor,
                "PanelFace" = :panel_face,
                "DoubleDoor" = :double_door,
                "DrawoutFixed" = :drawout_fixed,
                "ProtectionClass" = :protection_class,
                "CableEntry" = :cable_entry,
                "Mounting" = :mounting,
                "SeatStand" = :seat_stand,
                "StandMetalSize" = :stand_metal_size
            WHERE "ID" = :steel_id
            """
        )
        with get_session() as session:
            steel_data["steel_id"] = steel_id
            session.execute(query, steel_data)
            session.commit()

    # Panel Busbar methods
    def get_panel_busbar(self, panel_id):
        """Get busbar configuration for a panel"""
        query = text(
            """
            SELECT *
            FROM "tbl_PanelBB"
            WHERE "PanelID" = :panel_id
            """
        )
        with get_session() as session:
            result = session.execute(query, {"panel_id": panel_id})
            return result.fetchone()

    def create_panel_busbar(self, busbar_data):
        """Create busbar configuration"""
        query = text(
            """
            INSERT INTO "tbl_PanelBB"
            ("PanelID", "NeutralRating", "BusSection", "BusSectionQty",
             "AmpsRequested", "AmpsSelected", "BusbarClearence",
             "BB_QtyPH", "BB_QtyNu", "BB_QtyEarth",
             "Select_BB_Phase", "Select_BB_Neutral", "Select_BB_Earth")
            VALUES
            (:panel_id, :neutral_rating, :bus_section, :bus_section_qty,
             :amps_requested, :amps_selected, :busbar_clearence,
             :bb_qty_ph, :bb_qty_nu, :bb_qty_earth,
             :select_bb_phase, :select_bb_neutral, :select_bb_earth)
            RETURNING "ID"
            """
        )
        with get_session() as session:
            result = session.execute(query, busbar_data)
            session.commit()
            return result.scalar()

    def update_panel_busbar(self, busbar_id, busbar_data):
        """Update busbar configuration"""
        query = text(
            """
            UPDATE "tbl_PanelBB"
            SET "NeutralRating" = :neutral_rating,
                "BusSection" = :bus_section,
                "BusSectionQty" = :bus_section_qty,
                "AmpsRequested" = :amps_requested,
                "AmpsSelected" = :amps_selected,
                "BusbarClearence" = :busbar_clearence,
                "BB_QtyPH" = :bb_qty_ph,
                "BB_QtyNu" = :bb_qty_nu,
                "BB_QtyEarth" = :bb_qty_earth,
                "Select_BB_Phase" = :select_bb_phase,
                "Select_BB_Neutral" = :select_bb_neutral,
                "Select_BB_Earth" = :select_bb_earth
            WHERE "ID" = :busbar_id
            """
        )
        with get_session() as session:
            busbar_data["busbar_id"] = busbar_id
            session.execute(query, busbar_data)
            session.commit()

    # Panel Accessories methods
    def get_all_accessories(self):
        """Get all available accessories"""
        query = text(
            """
            SELECT "ID", "Description", "Unit", "Price"
            FROM "tbl_panelAccessories"
            ORDER BY "Description"
            """
        )
        with get_session() as session:
            result = session.execute(query)
            return result.fetchall(), result.keys()