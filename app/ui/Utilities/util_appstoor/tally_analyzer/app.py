import http.server
import socketserver
import json
import urllib.parse
import sqlite3
import os
import sys
import webbrowser
from pathlib import Path
from datetime import datetime

# Define paths
APP_DIR = Path(__file__).parent.resolve()
DB_PATH = APP_DIR / "tally.db"
DEFAULT_EXCEL_PATH = r"G:\My Drive\SVEE2\03 FY25-26\05 Accounts\05 TallyExport\Tally.xlsx"

# ----------------- Database Operations -----------------

def init_db():
    """Initializes the SQLite database and settings table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tally_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        particular TEXT NOT NULL,
        voucher_no TEXT NOT NULL,
        voucher_type TEXT NOT NULL,
        contra REAL DEFAULT 0.0,
        sales REAL DEFAULT 0.0,
        receipt REAL DEFAULT 0.0,
        payment REAL DEFAULT 0.0,
        debit_note REAL DEFAULT 0.0,
        credit_note REAL DEFAULT 0.0,
        journal REAL DEFAULT 0.0,
        purchase REAL DEFAULT 0.0,
        amount REAL DEFAULT 0.0,
        UNIQUE(date, particular, voucher_no)
    )
    """)
    
    # Seed default excel path if not present
    cursor.execute("SELECT value FROM settings WHERE key = 'excel_file_path'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO settings (key, value) VALUES ('excel_file_path', ?)", (DEFAULT_EXCEL_PATH,))
        
    conn.commit()
    conn.close()

def get_setting(key):
    """Retrieve a configuration value by key."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    """Save or update a configuration key-value pair."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def sync_excel_to_db(excel_path):
    """Parses Excel data and performs a smart sync (insert, update, delete) on SQLite."""
    import pandas as pd
    
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Excel file not found at: {excel_path}")
        
    # Read sheet "Column Day Book", using Row 1 as headers (row 0 is title)
    df = pd.read_excel(excel_path, sheet_name="Column Day Book", header=1)
    
    # Drop rows where Date is null
    df = df.dropna(subset=['Date'])
    
    # Check required columns
    required_cols = ['Date', 'Particular', 'Voucher No', 'Voucher Type']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' is missing from the Excel sheet.")
            
    # Clean string columns
    df['Particular'] = df['Particular'].fillna('').astype(str).str.strip()
    df['Voucher No'] = df['Voucher No'].fillna('').astype(str).str.strip()
    df['Voucher Type'] = df['Voucher Type'].fillna('').astype(str).str.strip()
    
    # Drop empty particulars (removes spacing/formatting rows)
    df = df[df['Particular'] != '']
    
    # Convert date to string format 'YYYY-MM-DD'
    df['parsed_date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['parsed_date'])
    df['date_str'] = df['parsed_date'].dt.strftime('%Y-%m-%d')
    
    # Convert transaction value columns to numeric
    amount_cols = ['Contra', 'Sales', 'Receipt', 'Payment', 'Debit Note', 'Credit Note', 'Journal', 'Purchase']
    for col in amount_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        else:
            df[col] = 0.0
            
    # Calculate amount: match Voucher Type column value or fallback to max non-zero value
    def get_row_amount(row):
        vt = row['Voucher Type']
        if vt in amount_cols and row[vt] != 0.0:
            return float(abs(row[vt]))
        # Fallback: get largest non-zero value among all columns
        vals = [abs(float(row[c])) for c in amount_cols if row[c] != 0.0]
        return max(vals) if vals else 0.0

    df['amount_calc'] = df.apply(get_row_amount, axis=1)
    
    # Remove Excel duplicates of (Date, Particular, Voucher No) keeping first
    df = df.drop_duplicates(subset=['date_str', 'Particular', 'Voucher No'], keep='first')
    
    # Build list of dict records
    excel_records = []
    for _, row in df.iterrows():
        excel_records.append({
            'date': row['date_str'],
            'particular': row['Particular'],
            'voucher_no': row['Voucher No'],
            'voucher_type': row['Voucher Type'],
            'contra': float(row['Contra']),
            'sales': float(row['Sales']),
            'receipt': float(row['Receipt']),
            'payment': float(row['Payment']),
            'debit_note': float(row['Debit Note']),
            'credit_note': float(row['Credit Note']),
            'journal': float(row['Journal']),
            'purchase': float(row['Purchase']),
            'amount': float(row['amount_calc'])
        })
        
    # Open SQLite transaction
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Load all current DB rows to compare
    cursor.execute("""
        SELECT date, particular, voucher_no, amount, contra, sales, receipt, payment, 
               debit_note, credit_note, journal, purchase, voucher_type 
        FROM tally_transactions
    """)
    sqlite_rows = cursor.fetchall()
    
    sqlite_dict = {}
    for r in sqlite_rows:
        key = (r[0], r[1], r[2]) # (date, particular, voucher_no)
        sqlite_dict[key] = {
            'amount': r[3],
            'contra': r[4],
            'sales': r[5],
            'receipt': r[6],
            'payment': r[7],
            'debit_note': r[8],
            'credit_note': r[9],
            'journal': r[10],
            'purchase': r[11],
            'voucher_type': r[12]
        }
        
    excel_keys = { (r['date'], r['particular'], r['voucher_no']) for r in excel_records }
    sqlite_keys = set(sqlite_dict.keys())
    
    keys_to_insert = excel_keys - sqlite_keys
    keys_to_delete = sqlite_keys - excel_keys
    keys_to_check = excel_keys & sqlite_keys
    
    added_count = 0
    updated_count = 0
    deleted_count = 0
    
    # 1. Insert new records
    insert_data = [r for r in excel_records if (r['date'], r['particular'], r['voucher_no']) in keys_to_insert]
    if insert_data:
        cursor.executemany("""
            INSERT INTO tally_transactions (
                date, particular, voucher_no, voucher_type, contra, sales, receipt, payment, 
                debit_note, credit_note, journal, purchase, amount
            ) VALUES (
                :date, :particular, :voucher_no, :voucher_type, :contra, :sales, :receipt, :payment, 
                :debit_note, :credit_note, :journal, :purchase, :amount
            )
        """, insert_data)
        added_count = len(insert_data)
        
    # 2. Delete missing records
    if keys_to_delete:
        cursor.executemany("""
            DELETE FROM tally_transactions 
            WHERE date = ? AND particular = ? AND voucher_no = ?
        """, list(keys_to_delete))
        deleted_count = len(keys_to_delete)
        
    # 3. Update changed records
    update_data = []
    for r in excel_records:
        key = (r['date'], r['particular'], r['voucher_no'])
        if key in keys_to_check:
            existing = sqlite_dict[key]
            # Match check tolerance
            changed = (
                abs(r['amount'] - existing['amount']) > 1e-5 or
                abs(r['contra'] - existing['contra']) > 1e-5 or
                abs(r['sales'] - existing['sales']) > 1e-5 or
                abs(r['receipt'] - existing['receipt']) > 1e-5 or
                abs(r['payment'] - existing['payment']) > 1e-5 or
                abs(r['debit_note'] - existing['debit_note']) > 1e-5 or
                abs(r['credit_note'] - existing['credit_note']) > 1e-5 or
                abs(r['journal'] - existing['journal']) > 1e-5 or
                abs(r['purchase'] - existing['purchase']) > 1e-5 or
                r['voucher_type'] != existing['voucher_type']
            )
            if changed:
                update_data.append((
                    r['voucher_type'], r['contra'], r['sales'], r['receipt'], r['payment'],
                    r['debit_note'], r['credit_note'], r['journal'], r['purchase'], r['amount'],
                    r['date'], r['particular'], r['voucher_no']
                ))
                
    if update_data:
        cursor.executemany("""
            UPDATE tally_transactions 
            SET voucher_type = ?, contra = ?, sales = ?, receipt = ?, payment = ?, 
                debit_note = ?, credit_note = ?, journal = ?, purchase = ?, amount = ?
            WHERE date = ? AND particular = ? AND voucher_no = ?
        """, update_data)
        updated_count = len(update_data)
        
    # Save last refresh timestamp
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('last_refresh', ?)", (now_str,))
    
    conn.commit()
    conn.close()
    
    return added_count, updated_count, deleted_count, len(excel_records)

# ----------------- HTTP Request Handler -----------------

class TallyHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        # Prevent default log flooding, log errors or important events only
        pass

    def serve_file(self, relative_path, content_type):
        try:
            file_path = APP_DIR / relative_path
            if file_path.exists():
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, f"File {relative_path} not found")
        except Exception as e:
            self.send_error(500, str(e))
            
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)
        
        # Route static assets
        if path == '/':
            self.serve_file('templates/index.html', 'text/html')
        elif path == '/static/style.css':
            self.serve_file('static/style.css', 'text/css')
        elif path == '/static/main.js':
            self.serve_file('static/main.js', 'application/javascript')
            
        # Route APIs
        elif path == '/api/status':
            self.handle_api_status()
        elif path == '/api/data':
            self.handle_api_data(query)
        elif path == '/api/particulars':
            self.handle_api_particulars()
        elif path == '/api/trends':
            self.handle_api_trends(query)
        else:
            self.send_error(404, "Endpoint Not Found")

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        if path == '/api/select_file':
            self.handle_api_select_file()
        elif path == '/api/refresh':
            self.handle_api_refresh()
        else:
            self.send_error(404, "Endpoint Not Found")
            
    # API Handler Implementations
    
    def handle_api_status(self):
        try:
            file_path = get_setting('excel_file_path')
            last_refresh = get_setting('last_refresh')
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tally_transactions")
            row_count = cursor.fetchone()[0]
            conn.close()
            
            self.send_json({
                'status': 'success',
                'file_path': file_path,
                'last_refresh': last_refresh,
                'row_count': row_count
            })
        except Exception as e:
            self.send_json({'status': 'error', 'message': str(e)}, 500)
            
    def handle_api_select_file(self):
        try:
            # File dialog launcher using Tkinter
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            
            file_path = filedialog.askopenfilename(
                title="Select Tally Excel File",
                filetypes=[("Excel Files", "*.xlsx *.xls")]
            )
            root.destroy()
            
            if file_path:
                # Normalize file path slashes
                file_path = os.path.normpath(file_path)
                set_setting('excel_file_path', file_path)
                
            self.send_json({
                'status': 'success',
                'file_path': file_path if file_path else None
            })
        except Exception as e:
            self.send_json({'status': 'error', 'message': str(e)}, 500)
            
    def handle_api_refresh(self):
        try:
            excel_path = get_setting('excel_file_path')
            if not excel_path or not os.path.exists(excel_path):
                self.send_json({
                    'status': 'error', 
                    'message': 'No Excel file selected or selected file path does not exist.'
                }, 400)
                return
                
            added, updated, deleted, total = sync_excel_to_db(excel_path)
            self.send_json({
                'status': 'success',
                'added': added,
                'updated': updated,
                'deleted': deleted,
                'total': total
            })
        except Exception as e:
            self.send_json({'status': 'error', 'message': str(e)}, 500)

    def handle_api_data(self):
        # Deprecated: see handle_api_data with query parameters below
        pass

    def handle_api_data(self, query):
        try:
            # Parse params
            page = int(query.get('page', [1])[0])
            page_size = int(query.get('page_size', [20])[0])
            search = query.get('search', [''])[0].strip()
            voucher_type = query.get('voucher_type', [''])[0].strip()
            
            offset = (page - 1) * page_size
            
            # Setup SQL query components
            where_clauses = []
            sql_params = []
            
            if search:
                where_clauses.append("(particular LIKE ? OR voucher_no LIKE ?)")
                sql_params.append(f"%{search}%")
                sql_params.append(f"%{search}%")
            if voucher_type:
                where_clauses.append("voucher_type = ?")
                sql_params.append(voucher_type)
                
            where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            # Fetch data
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Total records in DB
            cursor.execute("SELECT COUNT(*) FROM tally_transactions")
            total_records = cursor.fetchone()[0]
            
            # Total filtered records
            cursor.execute(f"SELECT COUNT(*) FROM tally_transactions {where_sql}", sql_params)
            total_filtered = cursor.fetchone()[0]
            
            # Fetch paginated rows
            query_sql = f"""
                SELECT date, particular, voucher_no, voucher_type, amount 
                FROM tally_transactions 
                {where_sql} 
                ORDER BY date DESC, particular ASC, id ASC
                LIMIT ? OFFSET ?
            """
            cursor.execute(query_sql, sql_params + [page_size, offset])
            rows = cursor.fetchall()
            
            # Convert to list of dicts
            data = [dict(r) for r in rows]
            
            # Total pages
            pages = (total_filtered + page_size - 1) // page_size
            pages = max(1, pages)
            
            # Compute Overall stats for KPIs
            cursor.execute("""
                SELECT 
                    SUM(sales) as sales, 
                    SUM(purchase) as purchase, 
                    SUM(receipt) as receipt, 
                    SUM(payment) as payment 
                FROM tally_transactions
            """)
            kpis_row = cursor.fetchone()
            stats = {
                'sales': kpis_row['sales'] or 0.0,
                'purchase': kpis_row['purchase'] or 0.0,
                'receipt': kpis_row['receipt'] or 0.0,
                'payment': kpis_row['payment'] or 0.0
            }
            
            conn.close()
            
            self.send_json({
                'status': 'success',
                'data': data,
                'total_records': total_records,
                'total_filtered': total_filtered,
                'pages': pages,
                'stats': stats
            })
        except Exception as e:
            self.send_json({'status': 'error', 'message': str(e)}, 500)
            
    def handle_api_particulars(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT particular FROM tally_transactions ORDER BY particular ASC")
            particulars = [r[0] for r in cursor.fetchall()]
            conn.close()
            
            self.send_json({
                'status': 'success',
                'data': particulars
            })
        except Exception as e:
            self.send_json({'status': 'error', 'message': str(e)}, 500)

    def handle_api_trends(self, query):
        try:
            particular = query.get('particular', [''])[0].strip()
            voucher_type = query.get('voucher_type', [''])[0].strip()
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            result = {'status': 'success'}
            
            if particular:
                # 1. Parameter trend for specific Particular (Ledger)
                cursor.execute("""
                    SELECT strftime('%Y-%m', date) as month, 
                           SUM(amount) as total_amount,
                           COUNT(*) as tx_count
                    FROM tally_transactions
                    WHERE particular = ?
                    GROUP BY month
                    ORDER BY month ASC
                """, (particular,))
                rows = cursor.fetchall()
                result['particular'] = {
                    'months': [r[0] for r in rows],
                    'values': [r[1] for r in rows],
                    'counts': [r[2] for r in rows]
                }
            elif voucher_type:
                # 2. Parameter trend for specific Voucher Type
                cursor.execute("""
                    SELECT strftime('%Y-%m', date) as month, 
                           SUM(amount) as total_amount,
                           COUNT(*) as tx_count
                    FROM tally_transactions
                    WHERE voucher_type = ?
                    GROUP BY month
                    ORDER BY month ASC
                """, (voucher_type,))
                rows = cursor.fetchall()
                result['voucher'] = {
                    'months': [r[0] for r in rows],
                    'values': [r[1] for r in rows],
                    'counts': [r[2] for r in rows]
                }
            else:
                # 3. Default cashflow trends (Sales vs Purchase, Receipt vs Payment)
                cursor.execute("""
                    SELECT strftime('%Y-%m', date) as month, 
                           SUM(sales) as total_sales, 
                           SUM(purchase) as total_purchase, 
                           SUM(receipt) as total_receipt, 
                           SUM(payment) as total_payment
                    FROM tally_transactions
                    GROUP BY month
                    ORDER BY month ASC
                """)
                rows = cursor.fetchall()
                result['cashflow'] = {
                    'months': [r[0] for r in rows],
                    'sales': [r[1] or 0.0 for r in rows],
                    'purchases': [r[2] or 0.0 for r in rows],
                    'receipts': [r[3] or 0.0 for r in rows],
                    'payments': [r[4] or 0.0 for r in rows]
                }
                
            conn.close()
            self.send_json(result)
        except Exception as e:
            self.send_json({'status': 'error', 'message': str(e)}, 500)

# ----------------- Start Web Server -----------------

def run_server(port=8050):
    init_db()
    handler = TallyHTTPRequestHandler
    
    # Find next available port if 8050 is blocked
    for p in range(port, port + 10):
        try:
            with socketserver.TCPServer(("", p), handler) as httpd:
                print(f"Server started on port {p} (http://localhost:{p})")
                print("Press Ctrl+C to stop.")
                
                # Open browser
                webbrowser.open(f"http://localhost:{p}")
                
                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    print("\nStopping server...")
                break
        except OSError:
            print(f"Port {p} in use, trying next...")
            continue

if __name__ == "__main__":
    run_server()
