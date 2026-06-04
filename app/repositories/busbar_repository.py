from sqlalchemy import text
from app.config.database import get_session # Assuming get_session is now a context manager

class BusbarRepository:
    def __init__(self):
        pass # Session will be acquired per method

    def get_all_busbars(self):
        query = text('''
            SELECT 
                l."ID",
                l."Run",
                l."Width",
                l."Thick",
                mp.metal,
                mp.metaldensity,
                mp.unitkgcost,
                s.sleevewidth,
                s.specialrate,
                s.normalrate,
                l."MetalPropID",
                l."SlevID"
            FROM "tbl_bb_List" l
            JOIN tbl_bb_metalproperties mp ON l."MetalPropID" = mp.id
            JOIN tbl_bb_sleeves s ON l."SlevID" = s.id
            ORDER BY l."ID"
        ''')
        with get_session() as session:
            result = session.execute(query)
            return result.fetchall()

    def get_busbar_by_id(self, bb_id):
        query = text('''
            SELECT l.*, mp.metal, mp.metaldensity, mp.unitkgcost, s.sleevewidth, s.normalrate
            FROM "tbl_bb_List" l
            JOIN tbl_bb_metalproperties mp ON l."MetalPropID" = mp.id
            JOIN tbl_bb_sleeves s ON l."SlevID" = s.id
            WHERE l."ID" = :id
        ''')
        with get_session() as session:
            return session.execute(query, {"id": bb_id}).fetchone()

    def create_busbar(self, run, width, thick, metal_id, sleeve_id):
        query = text('''
            INSERT INTO "tbl_bb_List" ("Run", "Width", "Thick", "MetalPropID", "SlevID")
            VALUES (:run, :width, :thick, :metal_id, :sleeve_id)
        ''')
        with get_session() as session:
            session.execute(query, {"run": run, "width": width, "thick": thick, "metal_id": metal_id, "sleeve_id": sleeve_id})
            session.commit()

    def update_busbar(self, bb_id, run, width, thick, metal_id, sleeve_id):
        query = text('''
            UPDATE "tbl_bb_List"
            SET "Run" = :run, "Width" = :width, "Thick" = :thick, 
                "MetalPropID" = :metal_id, "SlevID" = :sleeve_id
            WHERE "ID" = :id
        ''')
        with get_session() as session:
            session.execute(query, {"run": run, "width": width, "thick": thick, "metal_id": metal_id, "sleeve_id": sleeve_id, "id": bb_id})
            session.commit()

    def delete_busbar(self, bb_id):
        with get_session() as session:
            session.execute(text('DELETE FROM "tbl_bb_List" WHERE "ID" = :id'), {"id": bb_id})
            session.commit()

    # Metal Properties Lookups
    def get_all_metals(self):
        with get_session() as session:
            return session.execute(text("SELECT * FROM tbl_bb_metalproperties ORDER BY metal")).fetchall()

    def create_metal(self, metal, density, curr_density, cost):
        query = text('''
            INSERT INTO tbl_bb_metalproperties (metal, metaldensity, currentdensity, unitkgcost)
            VALUES (:metal, :density, :curr_density, :cost)
        ''')
        with get_session() as session:
            session.execute(query, {"metal": metal, "density": density, "curr_density": curr_density, "cost": cost})
            session.commit()

    def update_metal(self, metal_id, metal, density, curr_density, cost):
        query = text('''
            UPDATE tbl_bb_metalproperties
            SET metal = :metal, unitkgcost = :cost
            WHERE id = :id
        ''')
        with get_session() as session:
            session.execute(query, {"metal": metal, "cost": cost, "id": metal_id})
            session.commit()

    def delete_metal(self, metal_id):
        with get_session() as session:
            session.execute(text("DELETE FROM tbl_bb_metalproperties WHERE id = :id"), {"id": metal_id})
            session.commit()

    # Sleeve Lookups
    def get_all_sleeves(self):
        with get_session() as session:
            return session.execute(text("SELECT * FROM tbl_bb_sleeves ORDER BY bb_width, bb_thick")).fetchall()

    def create_sleeve(self, b_width, b_thick, s_width, s_rate, n_rate):
        query = text('''
            INSERT INTO tbl_bb_sleeves (bb_width, bb_thick, sleevewidth, specialrate, normalrate)
            VALUES (:b_width, :b_thick, :s_width, :s_rate, :n_rate)
        ''')
        with get_session() as session:
            session.execute(query, {"b_width": b_width, "b_thick": b_thick, "s_width": s_width, "s_rate": s_rate, "n_rate": n_rate})
            session.commit()

    def update_sleeve(self, sleeve_id, b_width, b_thick, s_width, s_rate, n_rate):
        query = text('''
            UPDATE tbl_bb_sleeves
            SET bb_width = :b_width, bb_thick = :b_thick, sleevewidth = :s_width, 
                specialrate = :s_rate, normalrate = :n_rate
            WHERE id = :id
        ''')
        with get_session() as session:
            session.execute(query, {"b_width": b_width, "b_thick": b_thick, "s_width": s_width, "s_rate": s_rate, "n_rate": n_rate, "id": sleeve_id})
            session.commit()

    def delete_sleeve(self, sleeve_id):
        with get_session() as session:
            session.execute(text("DELETE FROM tbl_bb_sleeves WHERE id = :id"), {"id": sleeve_id})
            session.commit()

    # Analytics Queries
    def get_material_usage_summary(self):
        query = text('''
            SELECT mp.metal, COUNT(*) AS total_jobs
            FROM "tbl_bb_List" l
            JOIN tbl_bb_metalproperties mp ON l."MetalPropID" = mp.id
            GROUP BY mp.metal
        ''')
        with get_session() as session:
            return session.execute(query).fetchall()

    def get_metal_cost_analysis(self):
        query = text('''
            SELECT mp.metal, mp.unitkgcost, COUNT(*) AS jobs
            FROM "tbl_bb_List" l
            JOIN tbl_bb_metalproperties mp ON l."MetalPropID" = mp.id
            GROUP BY mp.metal, mp.unitkgcost
            ORDER BY mp.unitkgcost DESC
        ''')
        with get_session() as session:
            return session.execute(query).fetchall()

    def get_sleeve_usage_report(self):
        query = text('''
            SELECT s.bb_width, s.bb_thick, s.sleevewidth, COUNT(*) AS usage_count
            FROM "tbl_bb_List" l
            JOIN tbl_bb_sleeves s ON l."SlevID" = s.id
            GROUP BY s.bb_width, s.bb_thick, s.sleevewidth
            ORDER BY usage_count DESC
        ''')
        with get_session() as session:
            return session.execute(query).fetchall()

    def get_busbar_summary(self, filters=None):
        base_query = 'SELECT * FROM public."vwBB_Summary"'
        where_clauses = []
        params = {}
        
        if filters:
            if filters.get('run'):
                where_clauses.append('"Run" = :run')
                params['run'] = filters['run']
            if filters.get('metal'):
                where_clauses.append('metal ILIKE :metal')
                params['metal'] = f"%{filters['metal']}%"
            if filters.get('width'):
                where_clauses.append('"Width" = :width')
                params['width'] = filters['width']
            if filters.get('thick'):
                where_clauses.append('"Thick" = :thick')
                params['thick'] = filters['thick']
            if filters.get('min_amps'):
                where_clauses.append('"CalAmps" >= :min_amps')
                params['min_amps'] = filters['min_amps']
            if filters.get('max_amps'):
                where_clauses.append('"CalAmps" <= :max_amps')
                params['max_amps'] = filters['max_amps']
                
        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)
            
        query = text(base_query)
        with get_session() as session:
            result = session.execute(query, params)
            return result.fetchall()