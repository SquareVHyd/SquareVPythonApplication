from app.config.database import get_session
from sqlalchemy import text

def check_db():
    with get_session() as session:
        result = session.execute(text("SELECT id, metal, unitkgcost FROM public.tbl_bb_metalproperties"))
        rows = result.fetchall()
        for row in rows:
            print(row)

if __name__ == "__main__":
    check_db()
