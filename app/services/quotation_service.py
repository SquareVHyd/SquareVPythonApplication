from datetime import datetime
from sqlalchemy import text
from app.config.database import get_session

class QuotationService:
    clipboard = {"type": None, "id": None, "name": None}

    def __init__(self):
        pass

    def get_all_quotations(self):
        """Fetches quotations with joined customer and contact names."""
        query = text("""
                SELECT 
                    q."ID",
                    q."CustomerId", 
                    c."CustomerName", 
                    q."DateOfRequest", q."Date_Quote", q."QuoteRereceNo",
                    q."QuoteSubject", q."QuoteProjectName",
                    cc."CustomerContactName",
                    q."PreparedBy", q."QuoteStatus",
                    q."UnitSteelCost", q."UnitAluminiumCost", q."UnitCopperCost"
                FROM public."tbl_QuoteMain" q
                LEFT JOIN public."tblCustomers" c ON q."CustomerId" = c."ID"
                LEFT JOIN public."tblCustomerContacts" cc ON q."CustomerContactID" = cc."ID"
                ORDER BY q."ID" DESC
        """)
        with get_session() as session:
            try:
                result = session.execute(query)
                # Convert to list of tuples for thread safety and predictable indexing in the UI
                return [tuple(row) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching quotations: {e}")
                return []

    def get_panels_by_quote(self, quote_id):
        """Fetches all panels associated with a specific quotation."""
        query = text("""
                SELECT "ID", "QuoteID", "PanelCategory", "PanelSerial", "PanelName", "PanelQty",
                       "LengthXmm", "HeightYmm", "DepthZmm", "AddWaste", "PanelKARating",
                       "EarthRuns", "StandRequired", "BusbarMaterial"
                FROM public."tbl_Panels" 
                WHERE "QuoteID" = :quote_id ORDER BY "ID"
        """)
        with get_session() as session:
            try:
                result = session.execute(query, {"quote_id": quote_id})
                return [tuple(row) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching panels: {e}")
                return []

    def create_panel(self, **kwargs):
        """Inserts a new panel record linked to a quotation."""
        query = text("""
                INSERT INTO public."tbl_Panels" (
                    "QuoteID", "PanelCategory", "PanelSerial", "PanelName", "PanelQty",
                    "LengthXmm", "HeightYmm", "DepthZmm", "AddWaste", "PanelKARating",
                    "EarthRuns", "StandRequired", "BusbarMaterial"
                ) VALUES (:quote_id, :category, :serial, :name, :qty, :length, :height, :depth, :waste, :ka_rating, :earth_runs, :stand, :busbar)
        """)
        params = {
            "quote_id": kwargs.get('quote_id'), "category": kwargs.get('category'), "serial": kwargs.get('serial'),
            "name": kwargs.get('name'), "qty": kwargs.get('qty'), "length": kwargs.get('length'),
            "height": kwargs.get('height'), "depth": kwargs.get('depth'), "waste": kwargs.get('waste'),
            "ka_rating": kwargs.get('ka_rating'), "earth_runs": kwargs.get('earth_runs'),
            "stand": kwargs.get('stand'), "busbar": kwargs.get('busbar')
        }
        with get_session() as session:
            try:
                session.execute(query, params)
                session.commit()
            except Exception:
                session.rollback()
                raise

    def update_panel(self, panel_id, **kwargs):
        """Updates an existing panel record."""
        query = text("""
                UPDATE public."tbl_Panels" SET 
                    "PanelCategory" = :category, "PanelSerial" = :serial, "PanelName" = :name, "PanelQty" = :qty,
                    "LengthXmm" = :length, "HeightYmm" = :height, "DepthZmm" = :depth, "AddWaste" = :waste, 
                    "PanelKARating" = :ka_rating, "EarthRuns" = :earth_runs, "StandRequired" = :stand, "BusbarMaterial" = :busbar
                WHERE "ID" = :panel_id
        """)
        params = {
            "category": kwargs.get('category'), "serial": kwargs.get('serial'), "name": kwargs.get('name'), "qty": kwargs.get('qty'),
            "length": kwargs.get('length'), "height": kwargs.get('height'), "depth": kwargs.get('depth'), "waste": kwargs.get('waste'),
            "ka_rating": kwargs.get('ka_rating'), "earth_runs": kwargs.get('earth_runs'), "stand": kwargs.get('stand'), 
            "busbar": kwargs.get('busbar'), "panel_id": panel_id
        }
        with get_session() as session:
            try:
                session.execute(query, params)
                session.commit()
            except Exception:
                session.rollback()
                raise

    def delete_panel(self, panel_id):
        """Deletes a panel record by its ID."""
        with get_session() as session:
            try:
                session.execute(text('DELETE FROM public."tbl_Panels" WHERE "ID" = :id'), {"id": panel_id})
                session.commit()
            except Exception:
                session.rollback()
                raise

    def get_all_customers(self):
        """Fetches ID and Name from tblCustomers for dropdowns."""
        with get_session() as session:
            try:
                result = session.execute(text('SELECT "ID", "CustomerName" FROM public."tblCustomers" ORDER BY "CustomerName"'))
                return result.fetchall()
            except Exception as e:
                print(f"Error fetching customers: {e}")
                return []

    def create_customer_quick(self, name):
        """Quickly inserts a new customer and returns the generated ID."""
        with get_session() as session:
            try:
                result = session.execute(text('INSERT INTO public."tblCustomers" ("CustomerName") VALUES (:name) RETURNING "ID"'), {"name": name})
                new_id = result.fetchone()[0]
                session.commit()
                return new_id
            except Exception:
                session.rollback()
                raise

    def create_quotation(self, **kwargs):
        """Inserts a new quotation record into tbl_QuoteMain and auto-fills initial metal costs."""
        with get_session() as session:
            try:
                # Fetch initial metal costs
                def get_cost(metal_name):
                    res = session.execute(
                        text("SELECT unitkgcost FROM public.tbl_bb_metalproperties WHERE LOWER(metal) LIKE :m LIMIT 1"),
                        {"m": f"%{metal_name.lower()}%"}
                    ).fetchone()
                    return float(res[0]) if res and res[0] is not None else 0.0

                steel_cost = get_cost("steel")
                alum_cost = get_cost("aluminium")
                copper_cost = get_cost("copper")

                query = text("""
                        INSERT INTO public."tbl_QuoteMain" (
                            "CustomerId", "DateOfRequest", "Date_Quote", "QuoteRereceNo", 
                            "QuoteSubject", "QuoteProjectName", "PreparedBy", "QuoteStatus",
                            "UnitSteelCost", "UnitAluminiumCost", "UnitCopperCost"
                        ) VALUES (:customer_id, :req_date, :quote_date, :ref_no, :subject, :project, :prepared_by, :status,
                                  :steel_cost, :alum_cost, :copper_cost)
                """)
                params = {
                    "customer_id": kwargs.get('customer_id'), "req_date": kwargs.get('req_date'), "quote_date": kwargs.get('quote_date'),
                    "ref_no": kwargs.get('ref_no'), "subject": kwargs.get('subject'), "project": kwargs.get('project'),
                    "prepared_by": kwargs.get('prepared_by'), "status": kwargs.get('status'),
                    "steel_cost": steel_cost, "alum_cost": alum_cost, "copper_cost": copper_cost
                }
                session.execute(query, params)
                session.commit()
            except Exception:
                session.rollback()
                raise

    def update_quotation(self, quot_id, **kwargs):
        """Updates an existing quotation record."""
        query = text("""
                UPDATE public."tbl_QuoteMain" SET 
                    "CustomerId" = :customer_id, "DateOfRequest" = :req_date, "Date_Quote" = :quote_date, 
                    "QuoteRereceNo" = :ref_no, "QuoteSubject" = :subject, "QuoteProjectName" = :project, 
                    "PreparedBy" = :prepared_by, "QuoteStatus" = :status
                WHERE "ID" = :quot_id
        """)
        params = {
            "customer_id": kwargs.get('customer_id'), "req_date": kwargs.get('req_date'), "quote_date": kwargs.get('quote_date'),
            "ref_no": kwargs.get('ref_no'), "subject": kwargs.get('subject'), "project": kwargs.get('project'),
            "prepared_by": kwargs.get('prepared_by'), "status": kwargs.get('status'), "quot_id": quot_id
        }
        with get_session() as session:
            try:
                session.execute(query, params)
                session.commit()
            except Exception:
                session.rollback()
                raise

    def delete_quotation(self, quot_id):
        """Deletes a quotation by ID."""
        with get_session() as session:
            try:
                session.execute(text('DELETE FROM public."tbl_QuoteMain" WHERE "ID" = :id'), {"id": quot_id})
                session.commit()
            except Exception:
                session.rollback()
                raise

    def get_panel_modules_by_panel_id(self, panel_id):
        """
        Fetches all modules for a specific panel.
        Includes module type name from tbl_PnlModuleType.
        """
        query = text("""
                SELECT 
                    pm."ID", pm."PanelID", p."PanelName", p."PanelQty", pm."IngOg", 
                    pm."PanelModQty", pm."ModuleTypeID", mc."Pnl_Module_Type", pm."ModPole", pm."ModKa", 
                    pm."Release", pm."Protection", pm."Remark"
                FROM public."tbl_PanelModules" pm
                JOIN public."tbl_Panels" p ON pm."PanelID" = p."ID"
                LEFT JOIN public."tbl_PnlModuleType" mc ON pm."ModuleTypeID" = mc."ID"
                WHERE pm."PanelID" = :panel_id
                ORDER BY pm."ID"
        """)
        with get_session() as session:
            try:
                result = session.execute(query, {"panel_id": panel_id})
                return [tuple(row) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching panel modules: {e}")
                return []

    def get_all_modules_by_quote(self, quote_id):
        """Fetches all modules for all panels belonging to a quotation."""
        query = text("""
                SELECT 
                    pm."ID", pm."PanelID", p."PanelName", p."PanelQty", pm."IngOg", 
                    pm."PanelModQty", pm."ModuleTypeID", mc."Pnl_Module_Type",
                    pm."ModPole", pm."ModKa", pm."Release", 
                    pm."Protection", pm."Remark"
                FROM public."tbl_PanelModules" pm
                JOIN public."tbl_Panels" p ON pm."PanelID" = p."ID"
                LEFT JOIN public."tbl_PnlModuleType" mc ON pm."ModuleTypeID" = mc."ID"
                WHERE p."QuoteID" = :quote_id
                ORDER BY p."ID", pm."ID"
        """)
        with get_session() as session:
            try:
                result = session.execute(query, {"quote_id": quote_id})
                return [tuple(row) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching quote modules: {e}")
                return []

    def get_quotation_by_id(self, quote_id):
        """Fetches a single quotation record by its ID, including customer and contact names."""
        query = text("""
                SELECT 
                    q."ID", q."CustomerId", c."CustomerName", q."DateOfRequest", q."Date_Quote", 
                    q."QuoteRereceNo", q."QuoteSubject", q."QuoteProjectName",
                    cc."CustomerContactName", q."PreparedBy", q."QuoteStatus"
                FROM public."tbl_QuoteMain" q
                LEFT JOIN public."tblCustomers" c ON q."CustomerId" = c."ID"
                LEFT JOIN public."tblCustomerContacts" cc ON q."CustomerContactID" = cc."ID"
                WHERE q."ID" = :quote_id
        """)
        with get_session() as session:
            try:
                result = session.execute(query, {"quote_id": quote_id})
                row = result.fetchone()
                return dict(row._mapping) if row else None
            except Exception as e:
                print(f"Error fetching quotation by ID: {e}")
                return None

    def get_module_costs_lookup(self):
        """Fetches module types from tbl_PnlModuleType for selection."""
        with get_session() as session:
            try:
                result = session.execute(text('SELECT "ID", "Pnl_Module_Type" FROM public."tbl_PnlModuleType" ORDER BY "Pnl_Module_Type"'))
                return result.fetchall()
            except Exception as e:
                print(f"Error fetching module costs: {e}")
                return []

    def create_module_type_quick(self, name):
        """Quickly inserts a new module type and returns the generated ID."""
        with get_session() as session:
            try:
                result = session.execute(text('INSERT INTO public."tbl_PnlModuleType" ("Pnl_Module_Type") VALUES (:name) RETURNING "ID"'), {"name": name})
                new_id = result.fetchone()[0]
                session.commit()
                return new_id
            except Exception:
                session.rollback()
                raise

    def create_panel_module(self, **kwargs):
        """Inserts a new panel module record."""
        query = text("""
                INSERT INTO public."tbl_PanelModules" (
                    "PanelID", "IngOg", "PanelModQty", "ModuleTypeID", "ModPole",
                    "ModKa", "Release", "Protection", "Remark"
                ) VALUES (:panel_id, :ing_og, :qty, :type_id, :pole, :ka, :release, :protection, :remark)
        """)
        params = {
            "panel_id": kwargs.get('panel_id'), "ing_og": kwargs.get('ing_og'), "qty": kwargs.get('qty'),
            "type_id": kwargs.get('type_id'), "pole": kwargs.get('pole'), "ka": kwargs.get('ka'),
            "release": kwargs.get('release'), "protection": kwargs.get('protection'), "remark": kwargs.get('remark')
        }
        with get_session() as session:
            try:
                session.execute(query, params)
                session.commit()
            except Exception:
                session.rollback()
                raise

    def get_module_items_by_module_type_id(self, module_type_id):
        """
        Fetches all items from tbl_ModuleItems for a specific ModuleTypeID.
        """
        query = text("""
                SELECT 
                    mi."ID", mi."DriveDescription", mi."BOM", mi."LP", mi."%Discount",

                    pl."Make",
                    (CAST(mi."BOM" AS NUMERIC) * CAST(mi."LP" AS NUMERIC) * (1 - CAST(mi."%Discount" AS NUMERIC))) as "Amount"
                FROM public."tbl_ModuleItems" mi
                LEFT JOIN public."vwPriceList" pl ON mi."DriveDescription" = pl."ItemDescription"
                WHERE mi."ID" = :module_type_id
                ORDER BY mi."DriveDescription"
        """)
        with get_session() as session:
            try:
                result = session.execute(query, {"module_type_id": module_type_id})
                return [tuple(row) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching module items: {e}")
                return []

    def create_module_item(self, module_type_id, drive_description, bom, lp, discount, selection, sequence_number=None):
        """Inserts a new module item record."""
        query = text("""
                INSERT INTO public."tbl_ModuleItems" (
                    "ID", "DriveDescription", "BOM", "LP", "%Discount"
                ) VALUES (:module_type_id, :drive_description, :bom, :lp, :discount)
        """)
        params = {
            "module_type_id": module_type_id,
            "drive_description": drive_description,
            "bom": bom,
            "lp": lp,
            "discount": discount,
            "discount": discount
        }
        with get_session() as session:
            try:
                session.execute(query, params)
                session.commit()
            except Exception:
                session.rollback()
                raise

    def update_panel_module(self, pm_id, **kwargs):
        """Updates an existing panel module record."""
        query = text("""
                UPDATE public."tbl_PanelModules" SET 
                    "PanelID" = :panel_id, "IngOg" = :ing_og, "PanelModQty" = :qty, "ModuleTypeID" = :type_id, 
                    "ModPole" = :pole, "ModKa" = :ka, "Release" = :release, "Protection" = :protection, "Remark" = :remark
                WHERE "ID" = :pm_id
        """)
        params = {
            "panel_id": kwargs.get('panel_id'), "ing_og": kwargs.get('ing_og'), "qty": kwargs.get('qty'),
            "type_id": kwargs.get('type_id'), "pole": kwargs.get('pole'), "ka": kwargs.get('ka'),
            "release": kwargs.get('release'), "protection": kwargs.get('protection'), "remark": kwargs.get('remark'), "pm_id": pm_id
        }
        with get_session() as session:
            try:
                session.execute(query, params)
                session.commit()
            except Exception:
                session.rollback()
                raise

    def update_module_item(self, old_module_type_id, old_drive_description, module_type_id, drive_description, bom, lp, discount, selection, sequence_number=None):
        """Updates an existing module item record using its composite primary key.
        Handles cases where DriveDescription (part of PK) might change by deleting old and inserting new.
        """
        with get_session() as session:
            try:
                if drive_description != old_drive_description:
                    # If DriveDescription (part of PK) changes, delete old and insert new
                    session.execute(text('DELETE FROM public."tbl_ModuleItems" WHERE "ID" = :old_mt_id AND "DriveDescription" = :old_desc'),
                                    {"old_mt_id": old_module_type_id, "old_desc": old_drive_description})
                    
                    session.execute(text("""
                        INSERT INTO public."tbl_ModuleItems" (
                            "ID", "DriveDescription", "BOM", "LP", "%Discount"
                        ) VALUES (:module_type_id, :drive_description, :bom, :lp, :discount)
                    """), {
                        "module_type_id": module_type_id,
                        "drive_description": drive_description,
                        "bom": bom,
                        "lp": lp,
                        "discount": discount,
                        "discount": discount
                    })
                else:
                    # Only update non-PK fields
                    query = text("""
                            UPDATE public."tbl_ModuleItems" SET 
                                "BOM" = :bom, "LP" = :lp, "%Discount" = :discount
                            WHERE "ID" = :module_type_id AND "DriveDescription" = :drive_description
                    """)
                    params = {
                        "module_type_id": module_type_id,
                        "drive_description": drive_description,
                        "bom": bom,
                        "lp": lp,
                        "discount": discount,
                        "discount": discount
                    }
                    session.execute(query, params)
                session.commit()
            except Exception:
                session.rollback()
                raise

    def delete_module_item(self, module_type_id, drive_description):
        """Deletes a module item record by its composite primary key."""
        with get_session() as session:
            try:
                session.execute(text('DELETE FROM public."tbl_ModuleItems" WHERE "ID" = :mt_id AND "DriveDescription" = :desc'),
                                {"mt_id": module_type_id, "desc": drive_description})
                session.commit()
            except Exception:
                session.rollback()
                raise

    def get_vw_modules_full_makes(self):
        """Fetches distinct makes from vwModulesFull."""
        query = text('SELECT DISTINCT "Make" FROM public."vwmodulesfull" WHERE "Make" IS NOT NULL ORDER BY "Make"')
        with get_session() as session:
            return [row[0] for row in session.execute(query).fetchall()]

    def get_vw_modules_full_types(self, make):
        """Fetches distinct module types for a specific make."""
        query = text('SELECT DISTINCT "ModuleType" FROM public."vwmodulesfull" WHERE "Make" = :make ORDER BY "ModuleType"')
        with get_session() as session:
            return [row[0] for row in session.execute(query, {"make": make}).fetchall()]

    def get_vw_modules_full_items(self, make, module_type):
        """Fetches all items for a specific make and module type."""
        query = text('SELECT * FROM public."vwmodulesfull" WHERE "Make" = :make AND "ModuleType" = :mt ORDER BY "SEQNo"')
        with get_session() as session:
            return [dict(row._mapping) for row in session.execute(query, {"make": make, "mt": module_type}).fetchall()]

    def bulk_add_module_items_from_vw(self, items, target_mt_id):
        """Handles logic: Resolve ID -> Price Lookup -> Dup Check -> Insert."""
        added, skipped = 0, 0
        with get_session() as session:
            for item in items:
                desc = item.get("ItemDescription")
                qty_from_mod = item.get("Qty")

                # 1. Duplicate Prevention for this specific Module Type Instance
                exists = session.execute(
                    text('SELECT 1 FROM public."tbl_ModuleItems" WHERE "ID" = :id AND "DriveDescription" = :desc'),
                    {"id": target_mt_id, "desc": desc}
                ).scalar()
                if exists:
                    skipped += 1; continue

                # 2. Price List Lookup from vwPriceList View
                price = session.execute(
                    text('SELECT "ListPrice", "DiscountPercent", "UsedQty" FROM public."vwPriceList" WHERE "ItemDescription" = :desc'),
                    {"desc": desc}
                ).fetchone()
                
                lp = float(price[0]) if price and price[0] else 0.0
                disc = float(price[1]) if price and price[1] else 0.0
                
                # Logic: Use Qty from the template (vwmodulesfull) if available, 
                # else fall back to the Price List UsedQty, else default to 1.0
                if qty_from_mod is not None:
                    bom = float(qty_from_mod)
                elif price and price[2] is not None:
                    bom = float(price[2])
                else:
                    bom = 1.0

                # 3. Insert into tbl_ModuleItems
                try:
                    session.execute(
                        text("""INSERT INTO public."tbl_ModuleItems" ("ID", "DriveDescription", "BOM", "LP", "%Discount") 
                                VALUES (:id, :desc, :bom, :lp, :disc)"""),
                        {"id": target_mt_id, "desc": desc, "bom": bom, "lp": lp, "disc": disc}
                    )
                    added += 1
                except Exception:
                    skipped += 1
            session.commit()
        return added, skipped

    def update_panel_module_field(self, pm_id, column_name, new_value):
        """Updates a single field for a panel module record."""
        with get_session() as session:
            try:
                # Ensure column_name is properly quoted for PostgreSQL case-sensitivity
                query = text(f'UPDATE public."tbl_PanelModules" SET "{column_name}" = :val WHERE "ID" = :id')
                session.execute(query, {"val": new_value, "id": pm_id})
                session.commit()
            except Exception:
                session.rollback()
                raise

    def delete_panel_module(self, pm_id):
        """Deletes a panel module by ID."""
        with get_session() as session:
            try:
                session.execute(text('DELETE FROM public."tbl_PanelModules" WHERE "ID" = :id'), {"id": pm_id})
                session.commit()
            except Exception:
                session.rollback()
                raise

    def update_panel_field(self, panel_id, column_name, new_value):
        """
        Updates a single field for a panel record.
        Used for inline editing in the PanelPage.
        """
        with get_session() as session:
            try:
                # Ensure column_name is properly quoted for PostgreSQL case-sensitivity
                query = text(f'UPDATE public."tbl_Panels" SET "{column_name}" = :val WHERE "ID" = :id')
                session.execute(query, {"val": new_value, "id": panel_id})
                session.commit()
            except Exception:
                session.rollback()
                raise

    def get_steel_configs_by_panel(self, panel_id):
        """Fetches steel records for a specific panel."""
        with get_session() as session:
            try:
                result = session.execute(text('SELECT * FROM public."tbl_PanelSteel" WHERE "PanelID" = :id ORDER BY "ID" DESC'), {"id": panel_id})
                return result.fetchall()
            finally:
                pass

    def ensure_steel_configs_for_panels(self, panel_ids):
        """Ensures every panel in the list has a corresponding steel config with defaults."""
        with get_session() as session:
            try:
                for pid in panel_ids:
                    res = session.execute(text('SELECT 1 FROM public."tbl_PanelSteel" WHERE "PanelID" = :pid'), {"pid": pid})
                    if not res.fetchone():
                        query = text("""
                        INSERT INTO public."tbl_PanelSteel" (
                            "PanelID", "FrontBackQty", "FrontBackSteelSize", "SidesQty", "SidesSteelSize",
                            "BottomTopQty", "BottomSteelSize", "TypeOfSeating", "Canopy", "CableEntry",
                            "Mounting", "DoubleDoor", "DrawoutFixed", "IndoorOutdoor", "PanelFace", "ProtectionClass",
                            "SeatStand", "StandMetalSize"
                        ) VALUES (:pid, 0, 'CRCA 1.2 mm', 0, 'CRCA 1.2 mm', 0, 'CRCA 1.2 mm', 'ISMC', 'No', 'Top',
                                    'free stand', 'No', 'No', 'Indoor', 'single', 'IP 44', 'No', '0')
                        """)
                        session.execute(query, {"pid": pid})
                session.commit()
            except Exception:
                session.rollback()
                raise

    def create_steel_config(self, panel_id):
        """Creates a steel config with defaults for a specific panel."""
        query = text("""
                INSERT INTO public."tbl_PanelSteel" (
                    "PanelID", "FrontBackQty", "FrontBackSteelSize", "SidesQty", "SidesSteelSize",
                    "BottomTopQty", "BottomSteelSize", "TypeOfSeating", "Canopy", "CableEntry",
                    "Mounting", "DoubleDoor", "DrawoutFixed", "IndoorOutdoor", "PanelFace", "ProtectionClass",
                    "SeatStand", "StandMetalSize"
                ) VALUES (:panel_id, 0, 'CRCA 1.2 mm', 0, 'CRCA 1.2 mm', 0, 'CRCA 1.2 mm', 'ISMC', 'No', 'Top',
                          'free stand', 'No', 'No', 'Indoor', 'single', 'IP 44', 'No', '0')
        """)
        with get_session() as session:
            try:
                session.execute(query, {"panel_id": panel_id})
                session.commit()
            except Exception:
                session.rollback()
                raise

    def update_steel_field(self, steel_id, column_name, new_value):
        """Updates a single field for a steel record."""
        with get_session() as session:
            try:
                query = text(f'UPDATE public."tbl_PanelSteel" SET "{column_name}" = :val WHERE "ID" = :id')
                res = session.execute(query, {"val": new_value, "id": steel_id})
                session.commit()
                if res.rowcount == 0:
                    print(f"WARNING: update_steel_field: Update query for steel_id {steel_id} affected 0 rows.")
            except Exception:
                session.rollback()
                raise

    def delete_steel_config(self, steel_id):
        """Deletes a specific steel configuration."""
        with get_session() as session:
            try:
                session.execute(text('DELETE FROM public."tbl_PanelSteel" WHERE "ID" = :id'), {"id": steel_id})
                session.commit()
            except Exception:
                session.rollback()
                raise

    def attach_steel_to_panel(self, panel_id, steel_id):
        """Updates the PanelID for a specific PanelSteel record to link it to a panel."""
        with get_session() as session:
            try:
                session.execute(text('UPDATE public."tbl_PanelSteel" SET "PanelID" = :pid WHERE "ID" = :sid'), {"pid": panel_id, "sid": steel_id})
                session.commit()
            except Exception:
                session.rollback()
                raise

    def update_full_steel_config(self, steel_id, data):
        """Updates all fields for a steel record at once with provided data dictionary."""
        with get_session() as session:
            try:
                # 1. Fetch current data to check for changes
                result = session.execute(text('SELECT * FROM public."tbl_PanelSteel" WHERE "ID" = :id'), {"id": steel_id})
                row = result.fetchone()

                if not row:
                    return

                current_data_db = row._mapping

                # 2. Prepare parameters for comparison and update
                update_columns_order = [
                    "FrontBackQty", "FrontBackSteelSize", "SidesQty", "SidesSteelSize",
                    "BottomTopQty", "BottomSteelSize", "TypeOfSeating", "Canopy",
                    "IndoorOutdoor", "PanelFace", "DoubleDoor", "DrawoutFixed",
                    "ProtectionClass", "CableEntry", "Mounting", "SeatStand",
                    "StandMetalSize"
                ]

                has_changed = False
                for col_name in update_columns_order:
                    new_val = data.get(col_name)
                    current_val_db = current_data_db.get(col_name)

                    str_new_val = str(new_val).strip() if new_val is not None else ""
                    str_current_val_db = str(current_val_db).strip() if current_val_db is not None else ""

                    if isinstance(new_val, (int, float)) and isinstance(current_val_db, (int, float)):
                        if new_val != current_val_db:
                            has_changed = True
                            break
                    elif str_new_val != str_current_val_db:
                        has_changed = True
                        break

                if not has_changed:
                    return

                # If changes are detected, proceed with the update
                query = text("""
                UPDATE public."tbl_PanelSteel" SET 
                    "FrontBackQty" = :FrontBackQty, "FrontBackSteelSize" = :FrontBackSteelSize, "SidesQty" = :SidesQty, "SidesSteelSize" = :SidesSteelSize,
                    "BottomTopQty" = :BottomTopQty, "BottomSteelSize" = :BottomSteelSize, "TypeOfSeating" = :TypeOfSeating, "Canopy" = :Canopy,
                    "IndoorOutdoor" = :IndoorOutdoor, "PanelFace" = :PanelFace, "DoubleDoor" = :DoubleDoor, "DrawoutFixed" = :DrawoutFixed,
                    "ProtectionClass" = :ProtectionClass, "CableEntry" = :CableEntry, "Mounting" = :Mounting, "SeatStand" = :SeatStand,
                    "StandMetalSize" = :StandMetalSize
                WHERE "ID" = :steel_id
                """)
                params = {col: data.get(col) for col in update_columns_order}
                params["steel_id"] = steel_id

                res = session.execute(query, params)
                session.commit()           
                if res.rowcount == 0:
                    print(f"WARNING: update_full_steel_config: Update query for steel_id {steel_id} affected 0 rows.")
            except Exception:
                session.rollback()
                raise

    def get_quote_ctc_list(self, quote_id=None):
        """Fetches CTC records for a specific quotation as list of tuples for table display."""
        query_str = 'SELECT * FROM public."tbl_QuoteCTC"'
        params = {}
        if quote_id:
            query_str += ' WHERE "QuoteID" = :quote_id'
            params['quote_id'] = quote_id
        query_str += ' ORDER BY "ID" DESC'
        
        query = text(query_str)
        with get_session() as session:
            try:
                result = session.execute(query, params)
                return [tuple(row) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching Quote CTC list: {e}")
                return []

    def update_quote_ctc_field(self, ctc_id, column_name, new_value):
        """Updates a single field in tbl_QuoteCTC for inline table editing."""
        with get_session() as session:
            try:
                query = text(f'UPDATE public."tbl_QuoteCTC" SET "{column_name}" = :val WHERE "ID" = :id')
                session.execute(query, {"val": new_value, "id": ctc_id})
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error updating CTC field {column_name}: {e}")
                raise

    def get_quote_ctc(self, quote_id):
        """Fetches the commercial terms and conditions for a specific quotation."""
        query = text('SELECT * FROM public."tbl_QuoteCTC" WHERE "QuoteID" = :quote_id')
        with get_session() as session:
            try:
                result = session.execute(query, {"quote_id": quote_id})
                row = result.fetchone()
                return dict(row._mapping) if row else None
            except Exception as e:
                print(f"Error fetching Quote CTC: {e}")
                return None

    def save_quote_ctc(self, **kwargs):
        """Inserts or updates CTC details for a quotation."""
        quote_id = kwargs.get('QuoteID')
        existing = self.get_quote_ctc(quote_id)
        
        columns = [
            "GSTTax", "FreightAndInsurance", "Payment", "Warranty", "Validity", 
            "Packing", "Inspection", "Delivery", "BankDetails", "Notes"
        ]
        
        if existing:
            set_clause = ", ".join([f'"{col}" = :{col}' for col in columns])
            query = text(f'UPDATE public."tbl_QuoteCTC" SET {set_clause} WHERE "QuoteID" = :QuoteID')
        else:
            cols_str = ", ".join([f'"{c}"' for c in (["QuoteID"] + columns)])
            vals_str = ", ".join([f':{c}' for c in (["QuoteID"] + columns)])
            query = text(f'INSERT INTO public."tbl_QuoteCTC" ({cols_str}) VALUES ({vals_str})')

        # Ensure all keys exist in params
        params = {col: kwargs.get(col, "") for col in columns}
        params["QuoteID"] = quote_id

        with get_session() as session:
            try:
                session.execute(query, params)
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error saving Quote CTC: {e}")
                raise

    def get_common_specs_list(self, quote_id):
        """Fetches common specs for a quotation as a list for table display."""
        query = text('SELECT * FROM public."tbl_QuoteCommonSpecs" WHERE "QuoteID" = :quote_id')
        with get_session() as session:
            try:
                result = session.execute(query, {"quote_id": quote_id})
                return [tuple(row) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching Common Specs: {e}")
                return []

    def save_common_specs(self, quote_id):
        """Ensures a common specs record exists for the quote."""
        with get_session() as session:
            try:
                check = session.execute(text('SELECT 1 FROM public."tbl_QuoteCommonSpecs" WHERE "QuoteID" = :id'), {"id": quote_id}).fetchone()
                if not check:
                    session.execute(text('INSERT INTO public."tbl_QuoteCommonSpecs" ("QuoteID") VALUES (:id)'), {"id": quote_id})
                    session.commit()
            except Exception:
                session.rollback()
                raise

    def update_common_specs_field(self, spec_id, column, value):
        """Updates a specific field in common specs."""
        with get_session() as session:
            try:
                query = text(f'UPDATE public."tbl_QuoteCommonSpecs" SET "{column}" = :val WHERE "ID" = :id')
                session.execute(query, {"val": value, "id": spec_id})
                session.commit()
            except Exception:
                session.rollback()
                raise

    def get_revisions_list(self, quote_id):
        """Fetches all revisions for a quotation."""
        query = text('SELECT * FROM public."tbl_QuoteRev" WHERE "QuoteID" = :quote_id ORDER BY "RevisionNo" DESC')
        with get_session() as session:
            try:
                result = session.execute(query, {"quote_id": quote_id})
                return [tuple(row) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching revisions: {e}")
                return []

    def create_revision(self, quote_id):
        """Creates a new revision entry."""
        with get_session() as session:
            try:
                query = text("""
                    INSERT INTO public."tbl_QuoteRev" ("QuoteID", "RevisionNo", "QuoteRevisionDate")
                    VALUES (:id, (SELECT COALESCE(MAX("RevisionNo"), 0) + 1 FROM public."tbl_QuoteRev" WHERE "QuoteID" = :id), CURRENT_TIMESTAMP)
                """)
                session.execute(query, {"id": quote_id})
                session.commit()
            except Exception:
                session.rollback()
                raise

    def update_revision_field(self, rev_id, column, value):
        """Updates a specific field in a revision record."""
        with get_session() as session:
            try:
                query = text(f'UPDATE public."tbl_QuoteRev" SET "{column}" = :val WHERE "ID" = :id')
                session.execute(query, {"val": value, "id": rev_id})
                session.commit()
            except Exception:
                session.rollback()
                raise

    def get_panel_bb_configs_by_panel(self, panel_id):
        """Fetches busbar records for a specific panel."""
        query = text('SELECT * FROM public."tbl_PanelBB" WHERE "PanelID" = :id ORDER BY "ID" DESC')
        with get_session() as session:
            try:
                result = session.execute(query, {"id": panel_id})
                return [tuple(row) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching panel BB configs: {e}")
                return []

    def ensure_panel_bb_configs_for_panels(self, panel_ids):
        """Ensures every panel in the list has a corresponding busbar config with defaults."""
        with get_session() as session:
            try:
                for pid in panel_ids:
                    res = session.execute(text('SELECT 1 FROM public."tbl_PanelBB" WHERE "PanelID" = :pid'), {"pid": pid})
                    if not res.fetchone():
                        query = text("""
                        INSERT INTO public."tbl_PanelBB" (
                            "PanelID", "NeutralRating", "BusSection", "BusSectionQty", "AmpsRequested",
                            "AmpsSelected", "BusbarClearence", "BB_QtyPH", "BB_QtyNu", "BB_QtyEarth",
                            "Select_BB_Phase", "Select_BB_Neutral", "Select_BB_Earth"
                        ) VALUES (:pid, 100, 'Main', 1, 0, '0', 'Standard', 1, 1, 1, '', '', '')
                        """)
                        session.execute(query, {"pid": pid})
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error ensuring panel BB configs: {e}")

    def update_full_panel_bb_config(self, bb_id, data):
        """Updates all fields for a busbar record at once with provided data dictionary."""
        with get_session() as session:
            try:
                update_columns_order = [
                    "NeutralRating", "BusSection", "BusSectionQty", "AmpsRequested",
                    "AmpsSelected", "BusbarClearence", "BB_QtyPH", "BB_QtyNu", "BB_QtyEarth",
                    "Select_BB_Phase", "Select_BB_Neutral", "Select_BB_Earth"
                ]
                set_clause = ", ".join([f'"{col}" = :{col}' for col in update_columns_order])
                query = text(f'UPDATE public."tbl_PanelBB" SET {set_clause} WHERE "ID" = :bb_id')
                params = {col: data.get(col) for col in update_columns_order}
                params["bb_id"] = bb_id
                session.execute(query, params)
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error updating full panel BB config: {e}")
                raise

    def get_steel_unit_cost(self):
        """Fetches the unit cost for steel from tbl_bb_metalproperties."""
        query = text("SELECT unitkgcost FROM public.tbl_bb_metalproperties WHERE LOWER(metal) LIKE '%steel%' LIMIT 1")
        with get_session() as session:
            try:
                result = session.execute(query)
                row = result.fetchone()
                return float(row[0]) if row and row[0] is not None else 0.0
            except Exception as e:
                print(f"Error fetching steel unit cost: {e}")
                return 0.0

    def get_bb_metal_unit_cost(self, metal_name):
        """Fetches the unit cost for a specific metal from tbl_bb_metalproperties."""
        query = text('SELECT unitkgcost FROM public.tbl_bb_metalproperties WHERE LOWER(metal) = LOWER(:metal) LIMIT 1')
        with get_session() as session:
            try:
                result = session.execute(query, {"metal": metal_name})
                row = result.fetchone()
                return float(row[0]) if row and row[0] is not None else 0.0
            except Exception as e:
                print(f"Error fetching metal unit cost for {metal_name}: {e}")
                return 0.0

    def get_metal_cost_from_quote(self, quote_id, metal_name):
        """Fetches the specific frozen unit cost for a metal from a specific quote."""
        query = text('SELECT "UnitSteelCost", "UnitAluminiumCost", "UnitCopperCost" FROM public."tbl_QuoteMain" WHERE "ID" = :id')
        with get_session() as session:
            try:
                row = session.execute(query, {"id": quote_id}).fetchone()
                if row:
                    m_lower = metal_name.lower()
                    if "steel" in m_lower: return float(row[0] or 0.0)
                    if "aluminium" in m_lower: return float(row[1] or 0.0)
                    if "copper" in m_lower: return float(row[2] or 0.0)
                return 0.0
            except Exception as e:
                print(f"Error fetching metal cost from quote {quote_id} for {metal_name}: {e}")
                return 0.0

    def update_metal_cost_in_quote(self, quote_id, metal_name, new_val):
        """Updates a specific metal's unit cost in a quotation."""
        col_name = None
        m_lower = metal_name.lower()
        if "steel" in m_lower: col_name = "UnitSteelCost"
        elif "aluminium" in m_lower: col_name = "UnitAluminiumCost"
        elif "copper" in m_lower: col_name = "UnitCopperCost"
        
        if not col_name: return
        
        query = text(f'UPDATE public."tbl_QuoteMain" SET "{col_name}" = :val WHERE "ID" = :id')
        with get_session() as session:
            try:
                session.execute(query, {"val": new_val, "id": quote_id})
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error updating metal cost {col_name} for quote {quote_id}: {e}")
                raise

    def copy_module_items(self, old_module_type_id, new_module_type_id, session=None):
        def _execute(sess):
            result = sess.execute(
                text('SELECT * FROM public."tbl_ModuleItems" WHERE "ID" = :old_id'),
                {"old_id": old_module_type_id}
            )
            items = [dict(r._mapping) for r in result.fetchall()]
            
            for item in items:
                desc = item.get("DriveDescription")
                old_bom = item.get("BOM")
                selection = item.get("Selection", "Selected")
                
                price_res = sess.execute(
                    text('SELECT "ListPrice", "DiscountPercent" FROM public."vwPriceList" WHERE "ItemDescription" = :desc'),
                    {"desc": desc}
                ).fetchone()
                
                lp = float(price_res[0]) if price_res and price_res[0] else float(item.get("LP", 0))
                disc = float(price_res[1]) if price_res and price_res[1] else float(item.get("%Discount", 0))
                
                sess.execute(
                    text("""INSERT INTO public."tbl_ModuleItems" 
                            ("ID", "DriveDescription", "BOM", "LP", "%Discount") 
                            VALUES (:id, :desc, :bom, :lp, :disc)"""),
                    {"id": new_module_type_id, "desc": desc, "bom": old_bom, "lp": lp, "disc": disc}
                )

        if session:
            _execute(session)
        else:
            with get_session() as new_session:
                try:
                    _execute(new_session)
                    new_session.commit()
                except Exception as e:
                    new_session.rollback()
                    raise e

    def copy_panel_module(self, module_id, target_panel_id, session=None):
        def _execute(sess):
            old_mod = sess.execute(
                text('SELECT * FROM public."tbl_PanelModules" WHERE "ID" = :id'),
                {"id": module_id}
            ).fetchone()
            if not old_mod: return
            old_mod = dict(old_mod._mapping)
            
            old_type_id = old_mod.get("ModuleTypeID")
            new_type_id = None
            if old_type_id:
                old_type_name_res = sess.execute(
                    text('SELECT "Pnl_Module_Type" FROM public."tbl_PnlModuleType" WHERE "ID" = :id'),
                    {"id": old_type_id}
                ).fetchone()
                old_type_name = old_type_name_res[0] if old_type_name_res else "Copied Module"
                new_type_name = f"{old_type_name} (Copy)"
                
                new_type_res = sess.execute(
                    text('INSERT INTO public."tbl_PnlModuleType" ("Pnl_Module_Type") VALUES (:name) RETURNING "ID"'), 
                    {"name": new_type_name}
                )
                new_type_id = new_type_res.fetchone()[0]
                
                self.copy_module_items(old_type_id, new_type_id, sess)
            
            query = text("""
                INSERT INTO public."tbl_PanelModules" (
                    "PanelID", "IngOg", "PanelModQty", "ModuleTypeID", "ModPole",
                    "ModKa", "Release", "Protection", "Remark"
                ) VALUES (:pid, :ingog, :qty, :typeid, :pole, :ka, :release, :prot, :rem) RETURNING "ID"
            """)
            sess.execute(query, {
                "pid": target_panel_id,
                "ingog": old_mod.get("IngOg"),
                "qty": old_mod.get("PanelModQty"),
                "typeid": new_type_id,
                "pole": old_mod.get("ModPole"),
                "ka": old_mod.get("ModKa"),
                "release": old_mod.get("Release"),
                "prot": old_mod.get("Protection"),
                "rem": old_mod.get("Remark")
            })

        if session:
            _execute(session)
        else:
            with get_session() as new_session:
                try:
                    _execute(new_session)
                    new_session.commit()
                except Exception as e:
                    new_session.rollback()
                    raise e

    def copy_panel(self, panel_id, target_quote_id, session=None):
        def _execute(sess):
            old_panel = sess.execute(text('SELECT * FROM public."tbl_Panels" WHERE "ID" = :id'), {"id": panel_id}).fetchone()
            if not old_panel: return
            old_panel = dict(old_panel._mapping)
            
            new_name = f"{old_panel.get('PanelName', 'Panel')}_copy"
            
            new_panel_res = sess.execute(text("""
                INSERT INTO public."tbl_Panels" (
                    "QuoteID", "PanelCategory", "PanelSerial", "PanelName", "PanelQty",
                    "LengthXmm", "HeightYmm", "DepthZmm", "AddWaste", "PanelKARating",
                    "EarthRuns", "StandRequired", "BusbarMaterial"
                ) VALUES (:qid, :cat, :ser, :name, :qty, :l, :h, :d, :w, :ka, :e, :st, :bb) RETURNING "ID"
            """), {
                "qid": target_quote_id, "cat": old_panel.get("PanelCategory"), "ser": old_panel.get("PanelSerial"),
                "name": new_name, "qty": old_panel.get("PanelQty"), "l": old_panel.get("LengthXmm"),
                "h": old_panel.get("HeightYmm"), "d": old_panel.get("DepthZmm"), "w": old_panel.get("AddWaste"),
                "ka": old_panel.get("PanelKARating"), "e": old_panel.get("EarthRuns"), "st": old_panel.get("StandRequired"),
                "bb": old_panel.get("BusbarMaterial")
            })
            new_panel_id = new_panel_res.fetchone()[0]
            
            old_steel = sess.execute(text('SELECT * FROM public."tbl_PanelSteel" WHERE "PanelID" = :id'), {"id": panel_id}).fetchone()
            if old_steel:
                old_s = dict(old_steel._mapping)
                sess.execute(text("""
                    INSERT INTO public."tbl_PanelSteel" (
                        "PanelID", "FrontBackQty", "FrontBackSteelSize", "SidesQty", "SidesSteelSize",
                        "BottomTopQty", "BottomSteelSize", "TypeOfSeating", "Canopy", "CableEntry",
                        "Mounting", "DoubleDoor", "DrawoutFixed", "IndoorOutdoor", "PanelFace", "ProtectionClass",
                        "SeatStand", "StandMetalSize"
                    ) VALUES (:pid, :fbq, :fbs, :sq, :ss, :btq, :bts, :tos, :c, :ce, :m, :dd, :df, :io, :pf, :pc, :sts, :sms)
                """), {
                    "pid": new_panel_id, "fbq": old_s.get("FrontBackQty"), "fbs": old_s.get("FrontBackSteelSize"),
                    "sq": old_s.get("SidesQty"), "ss": old_s.get("SidesSteelSize"), "btq": old_s.get("BottomTopQty"),
                    "bts": old_s.get("BottomSteelSize"), "tos": old_s.get("TypeOfSeating"), "c": old_s.get("Canopy"),
                    "ce": old_s.get("CableEntry"), "m": old_s.get("Mounting"), "dd": old_s.get("DoubleDoor"),
                    "df": old_s.get("DrawoutFixed"), "io": old_s.get("IndoorOutdoor"), "pf": old_s.get("PanelFace"),
                    "pc": old_s.get("ProtectionClass"), "sts": old_s.get("SeatStand"), "sms": old_s.get("StandMetalSize")
                })
                
            old_bb = sess.execute(text('SELECT * FROM public."tbl_PanelBB" WHERE "PanelID" = :id'), {"id": panel_id}).fetchone()
            if old_bb:
                old_b = dict(old_bb._mapping)
                sess.execute(text("""
                    INSERT INTO public."tbl_PanelBB" (
                        "PanelID", "NeutralRating", "BusSection", "BusSectionQty", "AmpsRequested",
                        "AmpsSelected", "BusbarClearence", "BB_QtyPH", "BB_QtyNu", "BB_QtyEarth",
                        "Select_BB_Phase", "Select_BB_Neutral", "Select_BB_Earth"
                    ) VALUES (:pid, :nr, :bs, :bsq, :ar, :ase, :bc, :qp, :qn, :qe, :sp, :sn, :se)
                """), {
                    "pid": new_panel_id, "nr": old_b.get("NeutralRating"), "bs": old_b.get("BusSection"),
                    "bsq": old_b.get("BusSectionQty"), "ar": old_b.get("AmpsRequested"), "ase": old_b.get("AmpsSelected"),
                    "bc": old_b.get("BusbarClearence"), "qp": old_b.get("BB_QtyPH"), "qn": old_b.get("BB_QtyNu"),
                    "qe": old_b.get("BB_QtyEarth"), "sp": old_b.get("Select_BB_Phase"), "sn": old_b.get("Select_BB_Neutral"),
                    "se": old_b.get("Select_BB_Earth")
                })

            modules = sess.execute(text('SELECT "ID" FROM public."tbl_PanelModules" WHERE "PanelID" = :id'), {"id": panel_id}).fetchall()
            
            for mod in modules:
                self.copy_panel_module(mod[0], new_panel_id, sess)

        if session:
            _execute(session)
        else:
            with get_session() as new_session:
                try:
                    _execute(new_session)
                    new_session.commit()
                except Exception as e:
                    new_session.rollback()
                    raise e

    def copy_quotation(self, quote_id, session=None):
        def _execute(sess):
            old_quote = sess.execute(text('SELECT * FROM public."tbl_QuoteMain" WHERE "ID" = :id'), {"id": quote_id}).fetchone()
            if not old_quote: return
            old_q = dict(old_quote._mapping)
            
            new_project_name = f"{old_q.get('QuoteProjectName', 'Project')}_copy"
            
            res = sess.execute(text("""
                INSERT INTO public."tbl_QuoteMain" (
                    "CustomerId", "DateOfRequest", "Date_Quote", "QuoteRereceNo", 
                    "QuoteSubject", "QuoteProjectName", "CustomerContactID", "PreparedBy", "QuoteStatus"
                ) VALUES (:cid, :dr, :dq, :qr, :qs, :qp, :ccid, :pb, :stat) RETURNING "ID"
            """), {
                "cid": old_q.get("CustomerId"), "dr": old_q.get("DateOfRequest"), "dq": old_q.get("Date_Quote"),
                "qr": old_q.get("QuoteRereceNo"), "qs": old_q.get("QuoteSubject"), "qp": new_project_name,
                "ccid": old_q.get("CustomerContactID"), "pb": old_q.get("PreparedBy"), "stat": old_q.get("QuoteStatus")
            })
            new_quote_id = res.fetchone()[0]
            
            old_ctc = sess.execute(text('SELECT * FROM public."tbl_QuoteCTC" WHERE "QuoteID" = :id'), {"id": quote_id}).fetchone()
            if old_ctc:
                old_c = dict(old_ctc._mapping)
                sess.execute(text("""
                    INSERT INTO public."tbl_QuoteCTC" (
                        "QuoteID", "GSTTax", "FreightAndInsurance", "Payment", "Warranty", "Validity", 
                        "Packing", "Inspection", "Delivery", "BankDetails", "Notes"
                    ) VALUES (:qid, :g, :f, :p, :w, :v, :pack, :i, :d, :b, :n)
                """), {
                    "qid": new_quote_id, "g": old_c.get("GSTTax"), "f": old_c.get("FreightAndInsurance"),
                    "p": old_c.get("Payment"), "w": old_c.get("Warranty"), "v": old_c.get("Validity"),
                    "pack": old_c.get("Packing"), "i": old_c.get("Inspection"), "d": old_c.get("Delivery"),
                    "b": old_c.get("BankDetails"), "n": old_c.get("Notes")
                })
            
            old_specs = sess.execute(text('SELECT * FROM public."tbl_QuoteCommonSpecs" WHERE "QuoteID" = :id'), {"id": quote_id}).fetchone()
            if old_specs:
                old_s = dict(old_specs._mapping)
                cols = [c for c in old_s.keys() if c != "ID" and c != "QuoteID"]
                if cols:
                    col_str = ", ".join([f'"{c}"' for c in cols])
                    val_str = ", ".join([f':{c}' for c in cols])
                    sess.execute(text(f"""
                        INSERT INTO public."tbl_QuoteCommonSpecs" ("QuoteID", {col_str})
                        VALUES (:qid, {val_str})
                    """), {**old_s, "qid": new_quote_id})
            
            panels = sess.execute(text('SELECT "ID" FROM public."tbl_Panels" WHERE "QuoteID" = :id'), {"id": quote_id}).fetchall()
            
            for p in panels:
                self.copy_panel(p[0], new_quote_id, sess)

        if session:
            _execute(session)
        else:
            with get_session() as new_session:
                try:
                    _execute(new_session)
                    new_session.commit()
                except Exception as e:
                    new_session.rollback()
                    raise e

    def get_bb_sizes_by_amps_and_metal(self, amps_req, metal):
        """Fetches BB sizes from vwBB_Summary within +/- 25% of amps_req and matching metal."""
        min_amps = amps_req * 0.75
        max_amps = amps_req * 1.25
        query = text('SELECT "ID", "BBSize" FROM public."vwBB_Summary" WHERE "CalAmps" >= :min AND "CalAmps" <= :max AND "metal" = :metal ORDER BY "CalAmps" ASC')
        with get_session() as session:
            try:
                result = session.execute(query, {"min": min_amps, "max": max_amps, "metal": metal})
                return [(row[0], row[1]) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching BB sizes by amps and metal: {e}")
                return []

    def get_bb_size_by_id(self, bb_id):
        query = text('SELECT "BBSize" FROM public."vwBB_Summary" WHERE "ID" = :id')
        with get_session() as session:
            try:
                res = session.execute(query, {"id": bb_id}).fetchone()
                return res[0] if res else str(bb_id)
            except Exception:
                return str(bb_id)

    def get_bb_metal_kg_per_meter(self, bb_id):
        query = text('SELECT "MetalKgPerMeter" FROM public."vwBB_Summary" WHERE "ID" = :id')
        with get_session() as session:
            try:
                res = session.execute(query, {"id": bb_id}).fetchone()
                return float(res[0]) if res else 0.0
            except Exception:
                return 0.0

    def get_bb_run_length(self, bb_id):
        query = text('SELECT "Run" FROM public."vwBB_Summary" WHERE "ID" = :id')
        with get_session() as session:
            try:
                res = session.execute(query, {"id": bb_id}).fetchone()
                return float(res[0]) if res else 0.0
            except Exception:
                return 0.0

    def get_panel_by_id(self, panel_id):
        """Fetches a panel by its ID."""
        query = text('SELECT * FROM public."tbl_Panels" WHERE "ID" = :id')
        with get_session() as session:
            try:
                result = session.execute(query, {"id": panel_id})
                row = result.fetchone()
                return dict(row._mapping) if row else None
            except Exception as e:
                print(f"Error fetching panel: {e}")
                return None

    def get_panel_bb_configs_by_panel(self, panel_id):
        """Fetches busbar records for a specific panel."""
        query = text('SELECT * FROM public."tbl_PanelBB" WHERE "PanelID" = :id ORDER BY "ID" DESC')
        with get_session() as session:
            try:
                result = session.execute(query, {"id": panel_id})
                return [tuple(row) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching panel BB configs: {e}")
                return []

    def ensure_panel_bb_configs_for_panels(self, panel_ids):
        """Ensures every panel has a busbar config. Fetches panel length for ReqLength default."""
        with get_session() as session:
            try:
                for pid in panel_ids:
                    res = session.execute(
                        text('SELECT 1 FROM public."tbl_PanelBB" WHERE "PanelID" = :pid'), {"pid": pid}
                    )
                    if not res.fetchone():
                        # Get panel length for ReqLength default
                        p_row = session.execute(
                            text('SELECT "LengthXmm" FROM public."tbl_Panels" WHERE "ID" = :pid'), {"pid": pid}
                        ).fetchone()
                        req_len = float(p_row[0]) if p_row and p_row[0] is not None else 0.0
                        session.execute(text("""
                            INSERT INTO public."tbl_PanelBB" (
                                "PanelID", "NeutralRating", "BusSection", "BusSectionQty", "AmpsRequested",
                                "AmpsSelected", "BusbarClearence", "BB_QtyPH", "BB_QtyNu", "BB_QtyEarth",
                                "Select_BB_Phase", "Select_BB_Neutral", "Select_BB_Earth", "ReqLength"
                            ) VALUES (:pid, 100, 'Main', 1, 0, '0', 'Standard', 1, 1, 1, '', '', '', :req_len)
                        """), {"pid": pid, "req_len": req_len})
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error ensuring panel BB configs: {e}")

    def add_panel_bb_config(self, panel_id, req_length=0.0):
        """Adds a new busbar config row with defaults (ReqLength defaults to panel length)."""
        with get_session() as session:
            try:
                query = text("""
                INSERT INTO public."tbl_PanelBB" (
                    "PanelID", "NeutralRating", "BusSection", "BusSectionQty", "AmpsRequested",
                    "AmpsSelected", "BusbarClearence", "BB_QtyPH", "BB_QtyNu", "BB_QtyEarth",
                    "Select_BB_Phase", "Select_BB_Neutral", "Select_BB_Earth", "ReqLength"
                ) VALUES (:pid, 100, 'Main', 1, 0, '0', 'Standard', 1, 1, 1, '', '', '', :req_len)
                RETURNING "ID"
                """)
                res = session.execute(query, {"pid": panel_id, "req_len": req_length})
                new_id = res.fetchone()[0]
                session.commit()
                return new_id
            except Exception as e:
                session.rollback()
                print(f"Error adding panel BB config: {e}")
                raise

    def delete_panel_bb_config(self, bb_id):
        """Deletes a busbar config record by ID."""
        with get_session() as session:
            try:
                query = text('DELETE FROM public."tbl_PanelBB" WHERE "ID" = :bb_id')
                session.execute(query, {"bb_id": bb_id})
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error deleting panel BB config: {e}")
                raise

    def update_full_panel_bb_config(self, bb_id, data):
        """Updates all fields for a busbar record at once with provided data dictionary."""
        with get_session() as session:
            try:
                update_columns_order = [
                    "NeutralRating", "BusSection", "BusSectionQty", "AmpsRequested",
                    "AmpsSelected", "BusbarClearence", "BB_QtyPH", "BB_QtyNu", "BB_QtyEarth",
                    "Select_BB_Phase", "Select_BB_Neutral", "Select_BB_Earth", "ReqLength"
                ]
                set_clause = ", ".join([f'"{col}" = :{col}' for col in update_columns_order])
                query = text(f'UPDATE public."tbl_PanelBB" SET {set_clause} WHERE "ID" = :bb_id')
                params = {col: data.get(col) for col in update_columns_order}
                params["bb_id"] = bb_id
                session.execute(query, params)
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error updating full panel BB config: {e}")
                raise

    def get_busbar_summary_by_quote(self, quote_id):
        """
        Returns a summary of unique busbar IDs used across all panels in a quotation,
        along with the summed quantities from BB_QtyPH, BB_QtyNu, and BB_QtyEarth.
        Joins vwBB_Summary to resolve the busbar size label (BBSize column).
        Returns list of tuples: (bb_id, bb_size, total_qty)
        """
        query = text("""
            SELECT
                bb_usage.bb_id,
                COALESCE(vs."BBSize", CAST(bb_usage.bb_id AS TEXT)) AS bb_size,
                SUM(bb_usage.qty) AS total_qty
            FROM (
                SELECT
                    CAST(pb."Select_BB_Phase" AS INTEGER) AS bb_id,
                    SUM(COALESCE(pb."BB_QtyPH", 0)) AS qty
                FROM public."tbl_PanelBB" pb
                JOIN public."tbl_Panels" p ON pb."PanelID" = p."ID"
                WHERE p."QuoteID" = :quote_id
                  AND pb."Select_BB_Phase" IS NOT NULL
                  AND pb."Select_BB_Phase" <> ''
                GROUP BY pb."Select_BB_Phase"

                UNION ALL

                SELECT
                    CAST(pb."Select_BB_Neutral" AS INTEGER) AS bb_id,
                    SUM(COALESCE(pb."BB_QtyNu", 0)) AS qty
                FROM public."tbl_PanelBB" pb
                JOIN public."tbl_Panels" p ON pb."PanelID" = p."ID"
                WHERE p."QuoteID" = :quote_id
                  AND pb."Select_BB_Neutral" IS NOT NULL
                  AND pb."Select_BB_Neutral" <> ''
                GROUP BY pb."Select_BB_Neutral"

                UNION ALL

                SELECT
                    CAST(pb."Select_BB_Earth" AS INTEGER) AS bb_id,
                    SUM(COALESCE(pb."BB_QtyEarth", 0)) AS qty
                FROM public."tbl_PanelBB" pb
                JOIN public."tbl_Panels" p ON pb."PanelID" = p."ID"
                WHERE p."QuoteID" = :quote_id
                  AND pb."Select_BB_Earth" IS NOT NULL
                  AND pb."Select_BB_Earth" <> ''
                GROUP BY pb."Select_BB_Earth"
            ) bb_usage
            LEFT JOIN public."vwBB_Summary" vs ON vs."ID" = bb_usage.bb_id
            GROUP BY bb_usage.bb_id, vs."BBSize"
            ORDER BY bb_usage.bb_id
        """)
        with get_session() as session:
            try:
                result = session.execute(query, {"quote_id": quote_id})
                return [tuple(row) for row in result.fetchall()]
            except Exception as e:
                print(f"Error fetching busbar summary: {e}")
                return []

    def calculate_panel_process_cost(self, panel_id):
        """Calculates total module & item cost for a panel."""
        modules = self.get_panel_modules_by_panel_id(panel_id)
        panel_total = 0.0
        for m_row in modules:
            m_qty = m_row[5]
            mt_id = m_row[6]
            m_items = self.get_module_items_by_module_type_id(mt_id)
            total_items_amount = sum(float(item[6] or 0) for item in m_items)
            panel_total += float(m_qty or 0) * total_items_amount
        return panel_total

    def get_panel_dimensions(self, panel_id):
        """Returns the length, height, and depth of a panel in mm as a tuple (L, H, D)."""
        panel = self.get_panel_by_id(panel_id)
        if not panel: return (0.0, 0.0, 0.0)
        
        l = float(panel.get("LengthXmm") or 0)
        h = float(panel.get("HeightYmm") or 0)
        d = float(panel.get("DepthZmm") or 0)
        return (l, h, d)

    def calculate_panel_steel_cost(self, panel_id, quote_id):
        """Calculates total steel cost for a panel using the locked unit cost."""
        panel = self.get_panel_by_id(panel_id)
        if not panel: return 0.0
        
        p_len = float(panel.get("LengthXmm") or 0)
        p_hgt = float(panel.get("HeightYmm") or 0)
        p_dep = float(panel.get("DepthZmm") or 0)
        p_waste = float(panel.get("AddWaste") or 0)
        
        query = text('SELECT * FROM public."tbl_PanelSteel" WHERE "PanelID" = :id')
        with get_session() as session:
            steel = session.execute(query, {"id": panel_id}).fetchone()
            
        if not steel: return 0.0
        s = dict(steel._mapping)
        
        fb_qty = float(s.get("FrontBackQty") or 0)
        fb_size = str(s.get("FrontBackSteelSize") or "")
        sides_qty = float(s.get("SidesQty") or 0)
        sides_size = str(s.get("SidesSteelSize") or "")
        bt_qty = float(s.get("BottomTopQty") or 0)
        bt_size = str(s.get("BottomSteelSize") or "")
        
        import re
        def get_thick(s):
            m = re.search(r"(\d+(\.\d+)?)", s)
            return float(m.group(1)) if m else 0.0

        fb_t = get_thick(fb_size)
        bt_t = get_thick(bt_size)
        sides_t = get_thick(sides_size)
        
        density = 7850
        fb_wt = fb_t * p_len * p_hgt * density * 1e-9 * fb_qty
        bt_wt = bt_t * p_len * p_dep * density * 1e-9 * bt_qty
        sides_wt = sides_t * p_dep * p_hgt * density * 1e-9 * sides_qty
        
        panel_wt = fb_wt + bt_wt + sides_wt
        if 0 < p_waste < 100:
            total_wt = panel_wt * 100.0 / (100.0 - p_waste)
        else:
            total_wt = panel_wt
            
        unit_cost = self.get_metal_cost_from_quote(quote_id, "steel")
        return total_wt * unit_cost

    def calculate_panel_busbar_cost(self, panel_id, quote_id):
        """Calculates total busbar cost for a panel using the locked unit cost."""
        panel = self.get_panel_by_id(panel_id)
        if not panel: return 0.0
        
        metal = panel.get("BusbarMaterial", "Aluminium")
        if not metal: metal = "Aluminium"
        
        unit_cost = self.get_metal_cost_from_quote(quote_id, metal)
        
        query = text('SELECT * FROM public."tbl_PanelBB" WHERE "PanelID" = :id')
        with get_session() as session:
            bb_rows = session.execute(query, {"id": panel_id}).fetchall()
            
        total_weight = 0.0
        for bb in bb_rows:
            b = dict(bb._mapping)
            for role, qty_col in [("Select_BB_Phase", "BB_QtyPH"), 
                                  ("Select_BB_Neutral", "BB_QtyNu"), 
                                  ("Select_BB_Earth", "BB_QtyEarth")]:
                bb_id_str = b.get(role)
                if bb_id_str:
                    try:
                        bb_id = int(bb_id_str)
                        qty = int(b.get(qty_col) or 0)
                        kg_m = self.get_bb_metal_kg_per_meter(bb_id)
                        total_weight += qty * kg_m
                    except ValueError:
                        pass
        return total_weight * unit_cost