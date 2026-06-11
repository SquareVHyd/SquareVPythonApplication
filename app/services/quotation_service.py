import pyodbc
from datetime import datetime

class QuotationService:
    def __init__(self):
        self.dsn = "PostgreSQLLH"

    def get_db_connection(self):
        try:
            return pyodbc.connect(f"DSN={self.dsn};")
        except Exception as e:
            print(f"Connection Error: {e}")
            return None

    def get_all_quotations(self):
        """Fetches quotations with joined customer and contact names."""
        conn = self.get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            # Resolving IDs to names as requested
            query = """
                SELECT 
                    q."ID",
                    q."CustomerId", 
                    c."CustomerName", 
                    q."DateOfRequest", q."Date_Quote", q."QuoteRereceNo",
                    q."QuoteSubject", q."QuoteProjectName",
                    cc."CustomerContactName",
                    q."PreparedBy", q."QuoteStatus"
                FROM public."tbl_QuoteMain" q
                LEFT JOIN public."tblCustomers" c ON q."CustomerId" = c."ID"
                LEFT JOIN public."tblCustomerContacts" cc ON q."CustomerContactID" = cc."ID"
                ORDER BY q."ID" DESC
            """
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"Query Error: {e}")
            return []
        finally:
            conn.close()

    def get_panels_by_quote(self, quote_id):
        """Fetches all panels associated with a specific quotation."""
        conn = self.get_db_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            # Explicitly naming columns is faster and prevents issues if table schema changes.
            # Ensure public."tbl_Panels"("QuoteID") has an INDEX in your database for speed.
            query = """
                SELECT "ID", "QuoteID", "PanelCategory", "PanelSerial", "PanelName", "PanelQty",
                       "LengthXmm", "HeightYmm", "DepthZmm", "AddWaste", "PanelKARating",
                       "EarthRuns", "StandRequired", "BusbarMaterial"
                FROM public."tbl_Panels" 
                WHERE "QuoteID" = ? ORDER BY "ID"
            """
            cursor.execute(query, (quote_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching panels: {e}")
            return []
        finally:
            conn.close()

    def create_panel(self, **kwargs):
        """Inserts a new panel record linked to a quotation."""
        conn = self.get_db_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO public."tbl_Panels" (
                    "QuoteID", "PanelCategory", "PanelSerial", "PanelName", "PanelQty",
                    "LengthXmm", "HeightYmm", "DepthZmm", "AddWaste", "PanelKARating",
                    "EarthRuns", "StandRequired", "BusbarMaterial"
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                kwargs.get('quote_id'), kwargs.get('category'), kwargs.get('serial'),
                kwargs.get('name'), kwargs.get('qty'), kwargs.get('length'),
                kwargs.get('height'), kwargs.get('depth'), kwargs.get('waste'),
                kwargs.get('ka_rating'), kwargs.get('earth_runs'),
                kwargs.get('stand'), kwargs.get('busbar')
            )
            cursor.execute(query, params)
            conn.commit()
        finally:
            conn.close()

    def update_panel(self, panel_id, **kwargs):
        """Updates an existing panel record."""
        conn = self.get_db_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            query = """
                UPDATE public."tbl_Panels" SET 
                    "PanelCategory" = ?, "PanelSerial" = ?, "PanelName" = ?, "PanelQty" = ?,
                    "LengthXmm" = ?, "HeightYmm" = ?, "DepthZmm" = ?, "AddWaste" = ?, 
                    "PanelKARating" = ?, "EarthRuns" = ?, "StandRequired" = ?, "BusbarMaterial" = ?
                WHERE "ID" = ?
            """
            params = (
                kwargs.get('category'), kwargs.get('serial'), kwargs.get('name'), kwargs.get('qty'),
                kwargs.get('length'), kwargs.get('height'), kwargs.get('depth'), kwargs.get('waste'),
                kwargs.get('ka_rating'), kwargs.get('earth_runs'), kwargs.get('stand'), 
                kwargs.get('busbar'), panel_id
            )
            cursor.execute(query, params)
            conn.commit()
        finally:
            conn.close()

    def delete_panel(self, panel_id):
        """Deletes a panel record by its ID."""
        conn = self.get_db_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM public."tbl_Panels" WHERE "ID" = ?', (panel_id,))
            conn.commit()
        finally:
            conn.close()

    def get_all_customers(self):
        """Fetches ID and Name from tblCustomers for dropdowns."""
        conn = self.get_db_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            # Using exact column names from your provided schema
            cursor.execute('SELECT "ID", "CustomerName" FROM public."tblCustomers" ORDER BY "CustomerName"')
            return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching customers: {e}")
            return []
        finally:
            conn.close()

    def create_customer_quick(self, name):
        """Quickly inserts a new customer and returns the generated ID."""
        conn = self.get_db_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO public."tblCustomers" ("CustomerName") VALUES (?) RETURNING "ID"', (name,))
            new_id = cursor.fetchone()[0]
            conn.commit()
            return new_id
        finally:
            conn.close()

    def create_quotation(self, **kwargs):
        """Inserts a new quotation record into tbl_QuoteMain."""
        conn = self.get_db_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO public."tbl_QuoteMain" (
                    "CustomerId", "DateOfRequest", "Date_Quote", "QuoteRereceNo", 
                    "QuoteSubject", "QuoteProjectName", "PreparedBy", "QuoteStatus"
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                kwargs.get('customer_id'), kwargs.get('req_date'), kwargs.get('quote_date'),
                kwargs.get('ref_no'), kwargs.get('subject'), kwargs.get('project'),
                kwargs.get('prepared_by'), kwargs.get('status')
            )
            cursor.execute(query, params)
            conn.commit()
        finally:
            conn.close()

    def update_quotation(self, quot_id, **kwargs):
        """Updates an existing quotation record."""
        conn = self.get_db_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            query = """
                UPDATE public."tbl_QuoteMain" SET 
                    "CustomerId" = ?, "DateOfRequest" = ?, "Date_Quote" = ?, 
                    "QuoteRereceNo" = ?, "QuoteSubject" = ?, "QuoteProjectName" = ?, 
                    "PreparedBy" = ?, "QuoteStatus" = ?
                WHERE "ID" = ?
            """
            params = (
                kwargs.get('customer_id'), kwargs.get('req_date'), kwargs.get('quote_date'),
                kwargs.get('ref_no'), kwargs.get('subject'), kwargs.get('project'),
                kwargs.get('prepared_by'), kwargs.get('status'), quot_id
            )
            cursor.execute(query, params)
            conn.commit()
        finally:
            conn.close()

    def delete_quotation(self, quot_id):
        """Deletes a quotation by ID."""
        conn = self.get_db_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM public."tbl_QuoteMain" WHERE "ID" = ?', (quot_id,))
            conn.commit()
        finally:
            conn.close()

    def get_panel_modules_by_panel_id(self, panel_id):
        """
        Fetches all modules for a specific panel.
        Includes module type name from tbl_PnlModuleCost.
        """
        conn = self.get_db_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT 
                    pm."ID", pm."PanelID", pm."IngOg", pm."PanelModQty", 
                    pm."ModuleTypeID", mc."SwgType", pm."ModPole", pm."ModKa", 
                    pm."Release", pm."Protection", pm."Remark"
                FROM public."tbl_PanelModules" pm
                LEFT JOIN public."tbl_PnlModuleCost" mc ON pm."ModuleTypeID" = mc."ID"
                WHERE pm."PanelID" = ?
                ORDER BY pm."ID"
            """
            cursor.execute(query, (panel_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching panel modules by panel ID: {e}")
            return []
        finally:
            conn.close()

    def get_all_modules_by_quote(self, quote_id):
        """Fetches all modules for all panels belonging to a quotation."""
        conn = self.get_db_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT 
                    pm."ID", pm."PanelID", p."PanelName", pm."IngOg", 
                    pm."PanelModQty", pm."ModuleTypeID", mc."SwgType",
                    pm."ModPole", pm."ModKa", pm."Release", 
                    pm."Protection", pm."Remark"
                FROM public."tbl_PanelModules" pm
                JOIN public."tbl_Panels" p ON pm."PanelID" = p."ID"
                LEFT JOIN public."tbl_PnlModuleCost" mc ON pm."ModuleTypeID" = mc."ID"
                WHERE p."QuoteID" = ?
                ORDER BY p."ID", pm."ID"
            """
            cursor.execute(query, (quote_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching quote modules: {e}")
            return []
        finally:
            conn.close()

    def get_module_costs_lookup(self):
        """Fetches module types from tbl_PnlModuleCost for selection."""
        conn = self.get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT "ID", "SwgType" FROM public."tbl_PnlModuleCost" ORDER BY "SwgType"')
            return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching module costs: {e}")
            return []
        finally:
            conn.close()

    def create_panel_module(self, **kwargs):
        """Inserts a new panel module record."""
        conn = self.get_db_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO public."tbl_PanelModules" (
                    "PanelID", "IngOg", "PanelModQty", "ModuleTypeID", "ModPole",
                    "ModKa", "Release", "Protection", "Remark"
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                kwargs.get('panel_id'), kwargs.get('ing_og'), kwargs.get('qty'),
                kwargs.get('type_id'), kwargs.get('pole'), kwargs.get('ka'),
                kwargs.get('release'), kwargs.get('protection'), kwargs.get('remark')
            )
            cursor.execute(query, params)
            conn.commit()
        finally:
            conn.close()

    def update_panel_module(self, pm_id, **kwargs):
        """Updates an existing panel module record."""
        conn = self.get_db_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            query = """
                UPDATE public."tbl_PanelModules" SET 
                    "PanelID" = ?, "IngOg" = ?, "PanelModQty" = ?, "ModuleTypeID" = ?, 
                    "ModPole" = ?, "ModKa" = ?, "Release" = ?, "Protection" = ?, "Remark" = ?
                WHERE "ID" = ?
            """
            params = (
                kwargs.get('panel_id'), kwargs.get('ing_og'), kwargs.get('qty'),
                kwargs.get('type_id'), kwargs.get('pole'), kwargs.get('ka'),
                kwargs.get('release'), kwargs.get('protection'), kwargs.get('remark'), pm_id
            )
            cursor.execute(query, params)
            conn.commit()
        finally:
            conn.close()

    def delete_panel_module(self, pm_id):
        """Deletes a panel module by ID."""
        conn = self.get_db_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM public."tbl_PanelModules" WHERE "ID" = ?', (pm_id,))
            conn.commit()
        finally:
            conn.close()

    def update_panel_field(self, panel_id, column_name, new_value):
        """
        Updates a single field for a panel record.
        Used for inline editing in the PanelPage.
        """
        conn = self.get_db_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            # Ensure column_name is properly quoted for PostgreSQL case-sensitivity
            query = f'UPDATE public."tbl_Panels" SET "{column_name}" = ? WHERE "ID" = ?'
            cursor.execute(query, (new_value, panel_id))
            conn.commit()
        except Exception as e:
            print(f"Error updating panel field {column_name} for ID {panel_id}: {e}")
        finally:
            conn.close()

    def get_steel_configs_by_panel(self, panel_id):
        """Fetches steel records for a specific panel."""
        conn = self.get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM public."tbl_PanelSteel" WHERE "PanelID" = ? ORDER BY "ID" DESC', (panel_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching steel configs: {e}")
            return []
        finally:
            conn.close()

    def ensure_steel_configs_for_panels(self, panel_ids):
        """Ensures every panel in the list has a corresponding steel config with defaults."""
        conn = self.get_db_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            for pid in panel_ids:
                cursor.execute('SELECT 1 FROM public."tbl_PanelSteel" WHERE "PanelID" = ?', (pid,))
                if not cursor.fetchone():
                    query = """
                        INSERT INTO public."tbl_PanelSteel" (
                            "PanelID", "FrontBackQty", "FrontBackSteelSize", "SidesQty", "SidesSteelSize",
                            "BottomTopQty", "BottomSteelSize", "TypeOfSeating", "Canopy", "CableEntry",
                            "Mounting", "DoubleDoor", "DrawoutFixed", "IndoorOutdoor", "PanelFace", "ProtectionClass",
                            "SeatStand", "StandMetalSize"
                        ) VALUES (?, 0, 'CRCA 1.2 mm', 0, 'CRCA 1.2 mm', 0, 'CRCA 1.2 mm', 'ISMC', 'No', 'Top',
                                  'free stand', 'No', 'No', 'Indoor', 'single', 'IP 44', 'No', '0')
                    """
                    cursor.execute(query, (pid,))
            conn.commit()
        except Exception as e:
            print(f"Error ensuring steel configs: {e}")
        finally:
            conn.close()

    def create_steel_config(self, panel_id):
        """Creates a steel config with defaults for a specific panel."""
        conn = self.get_db_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO public."tbl_PanelSteel" (
                    "PanelID", "FrontBackQty", "FrontBackSteelSize", "SidesQty", "SidesSteelSize",
                    "BottomTopQty", "BottomSteelSize", "TypeOfSeating", "Canopy", "CableEntry",
                    "Mounting", "DoubleDoor", "DrawoutFixed", "IndoorOutdoor", "PanelFace", "ProtectionClass",
                    "SeatStand", "StandMetalSize"
                ) VALUES (?, 0, 'CRCA 1.2 mm', 0, 'CRCA 1.2 mm', 0, 'CRCA 1.2 mm', 'ISMC', 'No', 'Top',
                          'free stand', 'No', 'No', 'Indoor', 'single', 'IP 44', 'No', '0')
            """
            cursor.execute(query, (panel_id,))
            conn.commit()
        finally:
            conn.close()

    def update_steel_field(self, steel_id, column_name, new_value):
        """Updates a single field for a steel record."""
        conn = self.get_db_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            query = f'UPDATE public."tbl_PanelSteel" SET "{column_name}" = ? WHERE "ID" = ?'
            cursor.execute(query, (new_value, steel_id))
            conn.commit()
            #print(f"DEBUG: attach_steel_to_panel: Successfully attached steel_id {steel_id} to panel_id {panel_id}.")
            if cursor.rowcount == 0:
                print(f"WARNING: attach_steel_to_panel: Update query for steel_id {steel_id} affected 0 rows.")
        except Exception as e:
            print(f"Error updating steel field: {e}")
        finally:
            conn.close()

    def delete_steel_config(self, steel_id):
        """Deletes a specific steel configuration."""
        conn = self.get_db_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM public."tbl_PanelSteel" WHERE "ID" = ?', (steel_id,))
            conn.commit()
        finally:
            conn.close()

    def attach_steel_to_panel(self, panel_id, steel_id):
        """Updates the PanelID for a specific PanelSteel record to link it to a panel."""
        conn = self.get_db_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute('UPDATE public."tbl_PanelSteel" SET "PanelID" = ? WHERE "ID" = ?', (panel_id, steel_id))
            conn.commit()
            #print(f"DEBUG: attach_steel_to_panel: Successfully attached steel_id {steel_id} to panel_id {panel_id}.")
        except Exception as e:
            print(f"Error attaching steel to panel: {e}")
            # Re-raise to ensure it's caught by the UI if needed
            raise
        finally:
            conn.close()

    def update_full_steel_config(self, steel_id, data):
        """Updates all fields for a steel record at once with provided data dictionary."""
        conn = self.get_db_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
                        
            # 1. Fetch current data to check for changes
            cursor.execute('SELECT * FROM public."tbl_PanelSteel" WHERE "ID" = ?', (steel_id,))
            current_record_tuple = cursor.fetchone()

            if not current_record_tuple:
                #print(f"DEBUG: update_full_steel_config: No existing record found for steel_id {steel_id}. Cannot update.")
                return

            # Get column names from cursor description
            col_names = [desc[0] for desc in cursor.description]
            current_data_db = dict(zip(col_names, current_record_tuple))

            # 2. Prepare parameters for comparison and update
            # Define the order of columns as they appear in the UPDATE query and 'data' dict
            update_columns_order = [
                "FrontBackQty", "FrontBackSteelSize", "SidesQty", "SidesSteelSize",
                "BottomTopQty", "BottomSteelSize", "TypeOfSeating", "Canopy",
                "IndoorOutdoor", "PanelFace", "DoubleDoor", "DrawoutFixed",
                "ProtectionClass", "CableEntry", "Mounting", "SeatStand",
                "StandMetalSize"
            ]

            has_changed = False
            for col_name in update_columns_order:
                # Get new value from the 'data' dictionary (which already has defaults applied)
                new_val = data.get(col_name)
                # Get current value from the database record
                current_val_db = current_data_db.get(col_name)

                # Convert both to string for robust comparison, handling None/empty string consistently
                str_new_val = str(new_val).strip() if new_val is not None else ""
                str_current_val_db = str(current_val_db).strip() if current_val_db is not None else ""

                # Special handling for numeric fields where UI might send '0' and DB might store 0 (int)
                # or vice-versa, ensuring '0' == 0
                if isinstance(new_val, (int, float)) and isinstance(current_val_db, (int, float)):
                    if new_val != current_val_db:
                        has_changed = True
                        break
                elif str_new_val != str_current_val_db:
                    has_changed = True
                    break

            if not has_changed:
                #print(f"DEBUG: update_full_steel_config: No changes detected for steel_id {steel_id}. Skipping update.")
                return

            # If changes are detected, proceed with the update
            query = """
                UPDATE public."tbl_PanelSteel" SET 
                    "FrontBackQty" = ?, "FrontBackSteelSize" = ?, "SidesQty" = ?, "SidesSteelSize" = ?,
                    "BottomTopQty" = ?, "BottomSteelSize" = ?, "TypeOfSeating" = ?, "Canopy" = ?,
                    "IndoorOutdoor" = ?, "PanelFace" = ?, "DoubleDoor" = ?, "DrawoutFixed" = ?,
                    "ProtectionClass" = ?, "CableEntry" = ?, "Mounting" = ?, "SeatStand" = ?,
                    "StandMetalSize" = ?
                WHERE "ID" = ?
            """
            params = (
                data.get("FrontBackQty"), data.get("FrontBackSteelSize"), 
                data.get("SidesQty"), data.get("SidesSteelSize"),
                data.get("BottomTopQty"), data.get("BottomSteelSize"), 
                data.get("TypeOfSeating"), data.get("Canopy"),
                data.get("IndoorOutdoor"), data.get("PanelFace"), 
                data.get("DoubleDoor"), data.get("DrawoutFixed"),
                data.get("ProtectionClass"), data.get("CableEntry"), 
                data.get("Mounting"), data.get("SeatStand"),
                data.get("StandMetalSize"), steel_id
            )
            #print(f"DEBUG: update_full_steel_config: Executing query for steel_id {steel_id}: {query}")
            #print(f"DEBUG: update_full_steel_config: With params: {params}")
            cursor.execute(query, params)
            conn.commit()           
            # Check if any rows were affected
            if cursor.rowcount == 0:
                print(f"WARNING: update_full_steel_config: Update query for steel_id {steel_id} affected 0 rows. Record might not exist or ID is incorrect.")
            else:
                #print(f"DEBUG: update_full_steel_config: Commit successful for steel_id {steel_id}. Rows affected: {cursor.rowcount}.")
        except Exception as e:
            print(f"Error updating full steel config: {e}")
            # Re-raise to ensure it's caught by the UI and shown in QMessageBox
            raise
        finally:
            conn.close()