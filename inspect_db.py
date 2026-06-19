from app.config.database import get_session
from sqlalchemy import text

def inspect_tables():
    tables = ["tbl_QuoteMain", "tbl_Panels", "tbl_PanelSteel", "tbl_PanelBB", "tbl_PanelModules", "tbl_PnlModuleType", "tbl_ModuleItems"]
    with get_session() as session:
        for t in tables:
            print(f"--- {t} ---")
            query = text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{t}'")
            for row in session.execute(query).fetchall():
                print(row)

if __name__ == "__main__":
    inspect_tables()
