import os
import sys

# Add project root to path if needed to run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.config.database import engine

def create_tables():
    sql = """
    CREATE TABLE IF NOT EXISTS public."po_Customer"
    (
        "ID" BIGSERIAL PRIMARY KEY,
        "Quotation_ID" BIGINT NOT NULL,
        "PO_No" TEXT NOT NULL,
        "PO_Date" DATE NOT NULL,

        CONSTRAINT fk_po_customer_quote
            FOREIGN KEY ("Quotation_ID")
            REFERENCES public."tbl_QuoteMain" ("ID")
            ON UPDATE CASCADE
            ON DELETE CASCADE
    );

    -- Customer PO Line Items Table
    CREATE TABLE IF NOT EXISTS public."po_Items"
    (
        "ID" BIGSERIAL PRIMARY KEY,
        "PO_Customer_ID" BIGINT NOT NULL,

        "Description" TEXT,
        "Qty" NUMERIC(18,2) DEFAULT 0,
        "Price" NUMERIC(18,2) DEFAULT 0,
        "Amount" NUMERIC(18,2) DEFAULT 0,

        -- Warranty in years
        "Warranty" NUMERIC(5,2) DEFAULT 0.00,

        CONSTRAINT fk_po_items_customer
            FOREIGN KEY ("PO_Customer_ID")
            REFERENCES public."po_Customer" ("ID")
            ON UPDATE CASCADE
            ON DELETE CASCADE
    );
    """
    try:
        with engine.begin() as conn:
            conn.execute(text(sql))
        print("Successfully created po_Customer and po_Items tables.")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    create_tables()
