import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog as fd
import pyodbc
import csv
import os
import webbrowser
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


DSN_NAME = "PostgreSQLLH"

# ──────────────────────────────────────────────
# DATABASE LAYER (Strict Commit Protocol)
# ──────────────────────────────────────────────
class DB:
    @staticmethod
    def connect():
        # Added autocommit=True at the driver level
        return pyodbc.connect(f"DSN={DSN_NAME};", autocommit=True)

    @staticmethod
    def execute(sql, params=(), fetch=False):
        conn = None
        try:
            conn = DB.connect()
            cur = conn.cursor()
            cur.execute(sql, params)
            if fetch:
                result = [tuple(row) for row in cur.fetchall()]
                return result
            # Hard commit to force the insert through the ODBC driver
            conn.commit() 
            return True 
        except Exception as exc:
            messagebox.showerror("Database Error", f"Query Failed:\n{str(exc)}")
            return False 
        finally:
            if conn:
                try: conn.close()
                except: pass

    @staticmethod
    def fetchone(sql, params=()):
        conn = None
        try:
            conn = DB.connect()
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()
            return tuple(row) if row else None
        except Exception as exc:
            messagebox.showerror("Database Error", f"Fetch Failed:\n{str(exc)}")
            return None
        finally:
            if conn:
                try: conn.close()
                except: pass

# --- Utility: Date & FY Parser ---
def get_date_obj(month_str):
    try:
        return datetime.strptime(month_str, "%b-%y")
    except ValueError:
        return datetime.min

def get_fy_from_month(month_str):
    dt = get_date_obj(month_str)
    if dt == datetime.min: return "Unknown FY"
    if dt.month < 4:
        start_year = dt.year - 1
    else:
        start_year = dt.year
    return f"FY{start_year}-{str(start_year+1)[-2:]}"

# Mapped explicitly to your Supabase schema
ALL_COLS = "id, billing_month, eb_kvah_old, eb_kvah_new, eb_charged_units, eb_pf, unit_rate, total_bill_amount, derived_fixed_charges, sri_old, sri_new, sri_units, sri_pct, sri_total, sq_old, sq_new, sq_units, sq_pct, sq_total, excess_units, eb_kwh_old, eb_kwh_new"

class EnterpriseBillApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SVEE Electricity Management - Supabase Edition")
        self.root.geometry("1100x800")
        
        self.current_edit_id = None 

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        self.tab_entry = ttk.Frame(self.notebook)
        self.tab_list = ttk.Frame(self.notebook)
        self.tab_graph = ttk.Frame(self.notebook)
        self.tab_pf_graph = ttk.Frame(self.notebook)
        self.tab_report = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_entry, text="1. New/Edit Entry")
        self.notebook.add(self.tab_list, text="2. Bill History")
        self.notebook.add(self.tab_graph, text="3. Financial Trends")
        self.notebook.add(self.tab_pf_graph, text="4. PF Trend")
        self.notebook.add(self.tab_report, text="5. Monthly Report (Print)")

        self.build_entry_tab()
        self.build_list_tab()
        self.build_graph_tab()
        self.build_pf_graph_tab()
        self.build_report_tab()
        
        self.update_global_dropdowns()

    # ========================== GLOBAL DATA / DATE LOGIC ==========================
    def update_global_dropdowns(self):
        rows = DB.execute('SELECT DISTINCT billing_month FROM public."tbl_EBbillR1"', fetch=True)
        if not rows: rows = []
        
        raw_months = [row[0] for row in rows if row[0]]
        sorted_months = sorted(raw_months, key=get_date_obj)
        
        fys = sorted(list(set([get_fy_from_month(m) for m in sorted_months if get_fy_from_month(m) != "Unknown FY"])))
        fys.insert(0, "All Data") 

        if sorted_months:
            self.list_fy_combo['values'] = fys
            if not self.list_fy_combo.get(): self.list_fy_combo.set("All Data")

            self.graph_fy_combo['values'] = fys
            if not self.graph_fy_combo.get(): self.graph_fy_combo.set("All Data")

            self.report_month_combo['values'] = sorted_months
            if not self.report_month_combo.get(): self.report_month_combo.set(sorted_months[-1])

        self.load_list_data()
        self.plot_dynamic_graph()
        self.plot_pf()
        self.fetch_latest_readings()

    def filter_data_by_fy(self, data, target_fy):
        if target_fy == "All Data" or not target_fy: return data
        return [row for row in data if get_fy_from_month(row[1]) == target_fy]

    # ========================== TAB 1: DATA ENTRY ==========================
    def build_entry_tab(self):
        frame_eb = tk.LabelFrame(self.tab_entry, text="EB Main Bill Details", padx=15, pady=10)
        frame_eb.pack(fill="x", padx=20, pady=5)
        
        tk.Label(frame_eb, text="Billing Month (e.g., Mar-26):").grid(row=0, column=0, sticky="w")
        self.ent_month = ttk.Entry(frame_eb, width=15); self.ent_month.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(frame_eb, text="Unit Rate (Rs):").grid(row=0, column=2, sticky="w", padx=10)
        self.ent_rate = ttk.Entry(frame_eb, width=15); self.ent_rate.insert(0, "7.7"); self.ent_rate.grid(row=0, column=3, padx=5, pady=5)
        tk.Label(frame_eb, text="Total Bill (Rs):").grid(row=0, column=4, sticky="w", padx=10)
        self.ent_total_bill = ttk.Entry(frame_eb, width=15); self.ent_total_bill.grid(row=0, column=5, padx=5, pady=5)
        
        tk.Label(frame_eb, text="KVAH Old Reading:").grid(row=1, column=0, sticky="w")
        self.ent_kvah_old = ttk.Entry(frame_eb, width=15); self.ent_kvah_old.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(frame_eb, text="KVAH New Reading:").grid(row=1, column=2, sticky="w", padx=10)
        self.ent_kvah_new = ttk.Entry(frame_eb, width=15); self.ent_kvah_new.grid(row=1, column=3, padx=5, pady=5)
        tk.Label(frame_eb, text="Charged Units:").grid(row=1, column=4, sticky="w", padx=10)
        self.ent_eb_units = ttk.Entry(frame_eb, width=15); self.ent_eb_units.grid(row=1, column=5, padx=5, pady=5)
        
        self.lbl_eb_kvah_hint = tk.Label(frame_eb, text="Prev: --", fg="gray", font=("Arial", 8))
        self.lbl_eb_kvah_hint.grid(row=2, column=1, sticky="w", padx=5)

        tk.Label(frame_eb, text="KWH Old Reading:").grid(row=3, column=0, sticky="w")
        self.ent_kwh_old = ttk.Entry(frame_eb, width=15); self.ent_kwh_old.grid(row=3, column=1, padx=5, pady=5)
        tk.Label(frame_eb, text="KWH New Reading:").grid(row=3, column=2, sticky="w", padx=10)
        self.ent_kwh_new = ttk.Entry(frame_eb, width=15); self.ent_kwh_new.grid(row=3, column=3, padx=5, pady=5)
        tk.Label(frame_eb, text="Calculated PF:").grid(row=3, column=4, sticky="w", padx=10)
        self.ent_eb_pf = ttk.Entry(frame_eb, width=15, state="readonly"); self.ent_eb_pf.grid(row=3, column=5, padx=5, pady=5)
        
        self.lbl_eb_kwh_hint = tk.Label(frame_eb, text="Prev: --", fg="gray", font=("Arial", 8))
        self.lbl_eb_kwh_hint.grid(row=4, column=1, sticky="w", padx=5)

        frame_local = tk.LabelFrame(self.tab_entry, text="Local Sub-Meters Detail", padx=15, pady=10)
        frame_local.pack(fill="x", padx=20, pady=5)
        tk.Label(frame_local, text="SRINIVAS (MF: 20)", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky="w", pady=(5,0))
        tk.Label(frame_local, text="Old Reading:").grid(row=1, column=0, sticky="w")
        self.sri_old = ttk.Entry(frame_local); self.sri_old.grid(row=1, column=1, padx=5)
        self.lbl_sri_hint = tk.Label(frame_local, text="Prev: --", fg="gray", font=("Arial", 8)); self.lbl_sri_hint.grid(row=2, column=1, sticky="w", padx=5)
        tk.Label(frame_local, text="New Reading:").grid(row=1, column=2, sticky="w", padx=10)
        self.sri_new = ttk.Entry(frame_local); self.sri_new.grid(row=1, column=3, padx=5)
        tk.Label(frame_local, text="SQUARE V (MF: 1)", font=('Arial', 10, 'bold')).grid(row=3, column=0, sticky="w", pady=(15, 0))
        tk.Label(frame_local, text="Old Reading:").grid(row=4, column=0, sticky="w")
        self.sq_old = ttk.Entry(frame_local); self.sq_old.grid(row=4, column=1, padx=5)
        self.lbl_sq_hint = tk.Label(frame_local, text="Prev: --", fg="gray", font=("Arial", 8)); self.lbl_sq_hint.grid(row=5, column=1, sticky="w", padx=5)
        tk.Label(frame_local, text="New Reading:").grid(row=4, column=2, sticky="w", padx=10)
        self.sq_new = ttk.Entry(frame_local); self.sq_new.grid(row=4, column=3, padx=5)

        frame_actions = tk.Frame(self.tab_entry)
        frame_actions.pack(pady=20)
        self.btn_save = tk.Button(frame_actions, text="Calculate & Save Record", bg="#4CAF50", fg="white", font=('Arial', 11, 'bold'), width=30, command=self.process_logic)
        self.btn_save.pack(side=tk.LEFT, padx=10)
        tk.Button(frame_actions, text="Clear Form", bg="#f44336", fg="white", font=('Arial', 11, 'bold'), width=15, command=self.clear_form).pack(side=tk.LEFT, padx=10)

    def fetch_latest_readings(self):
        row = DB.fetchone('SELECT eb_kvah_new, sri_new, sq_new, eb_kwh_new FROM public."tbl_EBbillR1" ORDER BY id DESC LIMIT 1')
        if row:
            self.lbl_eb_kvah_hint.config(text=f"Prev: {row[0]}")
            self.lbl_sri_hint.config(text=f"Prev: {row[1]}")
            self.lbl_sq_hint.config(text=f"Prev: {row[2]}")
            self.lbl_eb_kwh_hint.config(text=f"Prev: {row[3] if row[3] else 0}")

    def clear_form(self):
        self.current_edit_id = None
        self.btn_save.config(text="Calculate & Save NEW Record", bg="#4CAF50")
        
        self.ent_eb_pf.config(state="normal") 
        for entry in [self.ent_month, self.ent_rate, self.ent_total_bill, self.ent_kvah_old, self.ent_kvah_new, 
                   self.ent_eb_units, self.ent_eb_pf, self.ent_kwh_old, self.ent_kwh_new, self.sri_old, self.sri_new, self.sq_old, self.sq_new]:
            entry.delete(0, tk.END)
        self.ent_eb_pf.config(state="readonly")
            
        self.ent_rate.insert(0, "7.7")
        self.fetch_latest_readings()

    def process_logic(self):
        try:
            month = self.ent_month.get()
            rate = float(self.ent_rate.get())
            total_bill = float(self.ent_total_bill.get())
            eb_units = float(self.ent_eb_units.get())
            
            kvah_old = int(self.ent_kvah_old.get()) if self.ent_kvah_old.get() else 0
            kvah_new = int(self.ent_kvah_new.get()) if self.ent_kvah_new.get() else 0
            kwh_old = int(self.ent_kwh_old.get()) if self.ent_kwh_old.get() else 0
            kwh_new = int(self.ent_kwh_new.get()) if self.ent_kwh_new.get() else 0

            sri_old_val, sri_new_val = int(self.sri_old.get()), int(self.sri_new.get())
            sq_old_val, sq_new_val = int(self.sq_old.get()), int(self.sq_new.get())

            kwh_diff = kwh_new - kwh_old
            kvah_diff = kvah_new - kvah_old
            eb_pf = round(kwh_diff / kvah_diff, 4) if kvah_diff > 0 else 0.0

            self.ent_eb_pf.config(state="normal")
            self.ent_eb_pf.delete(0, tk.END)
            self.ent_eb_pf.insert(0, str(eb_pf))
            self.ent_eb_pf.config(state="readonly")

            units_charge_total = eb_units * rate
            derived_fixed_charges = total_bill - units_charge_total
            half_fixed = derived_fixed_charges / 2

            sri_units = (sri_new_val - sri_old_val) * 20
            sq_units = (sq_new_val - sq_old_val) * 1
            total_local = sri_units + sq_units
            excess_units = eb_units - total_local

            sri_pct = sri_units / total_local if total_local > 0 else 0
            sq_pct = sq_units / total_local if total_local > 0 else 0

            sri_shared_amt = (excess_units * sri_pct) * rate
            sq_shared_amt = (excess_units * sq_pct) * rate

            sri_final = (sri_units * rate) + half_fixed + sri_shared_amt
            sq_final = (sq_units * rate) + half_fixed + sq_shared_amt

            data_tuple = (month, kvah_old, kvah_new, eb_units, eb_pf, rate, total_bill, derived_fixed_charges,
                          sri_old_val, sri_new_val, sri_units, sri_pct, sri_final,
                          sq_old_val, sq_new_val, sq_units, sq_pct, sq_final, excess_units, kwh_old, kwh_new)

            if self.current_edit_id:
                query = """UPDATE public."tbl_EBbillR1" SET 
                            billing_month=?, eb_kvah_old=?, eb_kvah_new=?, eb_charged_units=?, eb_pf=?, unit_rate=?, 
                            total_bill_amount=?, derived_fixed_charges=?, 
                            sri_old=?, sri_new=?, sri_units=?, sri_pct=?, sri_total=?, 
                            sq_old=?, sq_new=?, sq_units=?, sq_pct=?, sq_total=?, excess_units=?,
                            eb_kwh_old=?, eb_kwh_new=?
                            WHERE id=?"""
                result = DB.execute(query, data_tuple + (self.current_edit_id,))
            else:
                query = """INSERT INTO public."tbl_EBbillR1" 
                            (billing_month, eb_kvah_old, eb_kvah_new, eb_charged_units, eb_pf, unit_rate, 
                            total_bill_amount, derived_fixed_charges, 
                            sri_old, sri_new, sri_units, sri_pct, sri_total, 
                            sq_old, sq_new, sq_units, sq_pct, sq_total, excess_units, eb_kwh_old, eb_kwh_new) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                result = DB.execute(query, data_tuple)

            if result is False: return # Prevents fake success message if DB fails

            messagebox.showinfo("Success", f"Record Successfully Saved!\nCalculated PF: {eb_pf}\nSrinivas: ₹{sri_final:.2f}\nSquare V: ₹{sq_final:.2f}")
            self.clear_form()
            self.update_global_dropdowns() 
        except Exception as e:
            messagebox.showerror("Input Error", f"Ensure all fields are valid numbers.\nError: {e}")

    # ========================== TAB 2: HISTORY & EXPORT ==========================
    def build_list_tab(self):
        frame_filter = tk.Frame(self.tab_list, pady=5)
        frame_filter.pack(fill="x", padx=10)
        
        tk.Label(frame_filter, text="Select Financial Year (FY):", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.list_fy_combo = ttk.Combobox(frame_filter, state="readonly", width=15)
        self.list_fy_combo.pack(side=tk.LEFT, padx=10)
        tk.Button(frame_filter, text="Apply Filter", command=self.load_list_data, bg="#e0e0e0").pack(side=tk.LEFT)
        
        tk.Button(frame_filter, text="📥 Export Visible to Excel", bg="gold", command=self.export_to_excel).pack(side=tk.RIGHT)
        
        columns = ('id', 'month', 'total_bill', 'excess', 'kwh', 'pf', 'sri_total', 'sq_total')
        self.tree = ttk.Treeview(self.tab_list, columns=columns, show='headings', height=16)
        self.tree.bind('<Double-1>', self.load_record_for_edit)
        
        for col, text in zip(columns, ['ID', 'Month', 'Total Bill (₹)', 'Excess (KVAH)', 'Diff (KWH)', 'PF', 'Srinivas (₹)', 'Square V (₹)']):
            self.tree.heading(col, text=text)
        self.tree.column('id', width=40)
        self.tree.pack(fill='both', expand=True, padx=10, pady=5)

    def load_list_data(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        
        rows = DB.execute(f'SELECT {ALL_COLS} FROM public."tbl_EBbillR1"', fetch=True)
        if not rows: return
        
        rows = sorted(rows, key=lambda x: get_date_obj(x[1]))
        filtered_rows = self.filter_data_by_fy(rows, self.list_fy_combo.get())
        
        for r in reversed(filtered_rows):
            kwh_diff = (r[21] - r[20]) if (r[21] is not None and r[20] is not None) else 0
            formatted = (r[0], r[1], f"{r[7]:.2f}", f"{r[19]:.1f}", f"{kwh_diff}", f"{r[5]}", f"{r[13]:.2f}", f"{r[18]:.2f}")
            self.tree.insert('', tk.END, values=formatted)

    def load_record_for_edit(self, event):
        selected = self.tree.selection()
        if not selected: return
        item = self.tree.item(selected[0])
        record_id = item['values'][0]

        row = DB.fetchone(f'SELECT {ALL_COLS} FROM public."tbl_EBbillR1" WHERE id=?', (record_id,))

        if row:
            self.clear_form()
            self.current_edit_id = record_id
            self.btn_save.config(text=f"UPDATE Record #{record_id}", bg="#ff9800")
            
            self.ent_month.insert(0, str(row[1]))
            self.ent_kvah_old.insert(0, str(row[2])); self.ent_kvah_new.insert(0, str(row[3]))
            self.ent_eb_units.insert(0, str(row[4]))
            
            self.ent_eb_pf.config(state="normal")
            self.ent_eb_pf.insert(0, str(row[5]))
            self.ent_eb_pf.config(state="readonly")
            
            self.ent_rate.delete(0, tk.END); self.ent_rate.insert(0, str(row[6]))
            self.ent_total_bill.insert(0, str(row[7]))
            self.sri_old.insert(0, str(row[9])); self.sri_new.insert(0, str(row[10]))
            self.sq_old.insert(0, str(row[14])); self.sq_new.insert(0, str(row[15]))
            
            if len(row) > 20 and row[20] is not None: self.ent_kwh_old.insert(0, str(row[20]))
            if len(row) > 21 and row[21] is not None: self.ent_kwh_new.insert(0, str(row[21]))
            
            self.notebook.select(self.tab_entry)

    def export_to_excel(self):
        visible_ids = [self.tree.item(item)['values'][0] for item in self.tree.get_children()]
        if not visible_ids: return
        
        filepath = fd.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], title="Export Visible Bill History")
        if not filepath: return
        
        try:
            placeholders = ','.join('?' for _ in visible_ids)
            query = f'SELECT * FROM public."tbl_EBbillR1" WHERE id IN ({placeholders}) ORDER BY id ASC'
            
            with DB.connect() as conn:
                cur = conn.cursor()
                cur.execute(query, visible_ids)
                rows = cur.fetchall()
                column_names = [description[0] for description in cur.description]

            with open(filepath, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(column_names)
                writer.writerows(rows)
            messagebox.showinfo("Success", f"Data exported to:\n{filepath}")
        except Exception as e: messagebox.showerror("Failed", str(e))

    # ========================== TAB 3 & 4: GRAPHS ==========================
    def build_graph_tab(self):
        frame_controls = tk.Frame(self.tab_graph, pady=10, padx=10); frame_controls.pack(fill="x")
        tk.Label(frame_controls, text="Trend:").pack(side=tk.LEFT)
        self.graph_combo = ttk.Combobox(frame_controls, values=["Financial Billed (Rs)", "Units Consumed", "Excess Units Trend", "KWH vs KVAH Units"], state="readonly", width=25)
        self.graph_combo.set("Financial Billed (Rs)"); self.graph_combo.pack(side=tk.LEFT, padx=5)
        
        tk.Label(frame_controls, text="| FY Filter:").pack(side=tk.LEFT)
        self.graph_fy_combo = ttk.Combobox(frame_controls, state="readonly", width=15); self.graph_fy_combo.pack(side=tk.LEFT, padx=5)
        tk.Button(frame_controls, text="Generate Trend", command=self.plot_dynamic_graph, bg="lightblue").pack(side=tk.LEFT, padx=10)

        self.graph_frame = tk.Frame(self.tab_graph); self.graph_frame.pack(fill="both", expand=True)

    def plot_dynamic_graph(self):
        for widget in self.graph_frame.winfo_children(): widget.destroy()
        
        data = DB.execute(f'SELECT {ALL_COLS} FROM public."tbl_EBbillR1"', fetch=True)
        if not data: return

        data = sorted(data, key=lambda x: get_date_obj(x[1]))
        data = self.filter_data_by_fy(data, self.graph_fy_combo.get())
        if not data: return

        months, selection = [row[1] for row in data], self.graph_combo.get()
        fig, ax = plt.subplots(figsize=(8, 4))

        if selection == "Financial Billed (Rs)":
            ax.plot(months, [row[7] for row in data], marker='D', label='Total EB Bill', color='black', linestyle='--')
            ax.plot(months, [row[13] for row in data], marker='o', label='Srinivas (₹)', color='blue')
            ax.plot(months, [row[18] for row in data], marker='s', label='Square V (₹)', color='orange')
            ax.set_ylabel('Amount (Rs)')
        elif selection == "Units Consumed":
            ax.plot(months, [row[4] for row in data], marker='D', label='Total Main Units', color='black', linestyle='--')
            ax.plot(months, [row[11] for row in data], marker='o', label='Srinivas Units', color='blue')
            ax.plot(months, [row[16] for row in data], marker='s', label='Square V Units', color='orange')
            ax.set_ylabel('Units')
        elif selection == "Excess Units Trend":
            ax.plot(months, [row[19] for row in data], marker='^', label='Excess Units (Overhead)', color='red')
            ax.set_ylabel('Excess Units')
        elif selection == "KWH vs KVAH Units":
            kvah_diffs = [(r[3]-r[2]) if r[3] and r[2] else 0 for r in data]
            kwh_diffs = [(r[21]-r[20]) if r[21] and r[20] else 0 for r in data]
            ax.plot(months, kvah_diffs, marker='o', label='KVAH Units (Billed)', color='orange', linewidth=2)
            ax.plot(months, kwh_diffs, marker='^', label='KWH Units (Actual Power)', color='green', linewidth=2)
            ax.fill_between(months, kwh_diffs, kvah_diffs, color='red', alpha=0.1, label="System Loss Gap")
            ax.set_ylabel('Units')

        ax.set_title(f'{selection} ({self.graph_fy_combo.get()})'); ax.grid(True, linestyle='--', alpha=0.6); ax.legend()
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame); canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        toolbar = NavigationToolbar2Tk(canvas, self.graph_frame); toolbar.update()

    def build_pf_graph_tab(self):
        tk.Button(self.tab_pf_graph, text="Refresh PF Trend", command=self.plot_pf).pack(pady=10)
        self.pf_frame = tk.Frame(self.tab_pf_graph); self.pf_frame.pack(fill="both", expand=True)

    def plot_pf(self):
        for widget in self.pf_frame.winfo_children(): widget.destroy()
        
        data = DB.execute('SELECT billing_month, eb_pf FROM public."tbl_EBbillR1"', fetch=True)
        if not data: return

        data = sorted(data, key=lambda x: get_date_obj(x[0]))
        data = self.filter_data_by_fy(data, self.graph_fy_combo.get()) 
        if not data: return

        months, pfs = [row[0] for row in data], [row[1] for row in data]
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(months, pfs, marker='^', label='Actual PF', color='purple', linewidth=2)
        ax.axhline(y=0.99, color='green', linestyle=':', label='Ideal (0.99)')
        ax.axhline(y=0.90, color='red', linestyle=':', label='Warning (0.90)')
        ax.set_ylabel('Power Factor'); ax.set_title(f'Efficiency Trend ({self.graph_fy_combo.get()})'); ax.grid(True, linestyle='--', alpha=0.6); ax.legend(loc='lower right')

        canvas = FigureCanvasTkAgg(fig, master=self.pf_frame); canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        toolbar = NavigationToolbar2Tk(canvas, self.pf_frame); toolbar.update()

    # ========================== TAB 5: PRINTABLE REPORT ==========================
    def build_report_tab(self):
        frame_top = tk.Frame(self.tab_report, pady=20)
        frame_top.pack()
        
        tk.Label(frame_top, text="Select Month to Generate Official Invoice:", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=10)
        self.report_month_combo = ttk.Combobox(frame_top, state="readonly", width=15, font=("Arial", 12))
        self.report_month_combo.pack(side=tk.LEFT, padx=10)
        
        tk.Button(frame_top, text="📄 Preview Report Details", font=("Arial", 11), bg="#2196F3", fg="white", command=self.preview_report).pack(side=tk.LEFT, padx=10)
        tk.Button(frame_top, text="🖨️ Print / Save as PDF", font=("Arial", 11, "bold"), bg="#ff5722", fg="white", command=self.generate_html_report).pack(side=tk.LEFT, padx=10)

        self.report_preview = tk.Text(self.tab_report, height=25, width=90, font=("Courier", 11), bg="#f5f5f5")
        self.report_preview.pack(pady=10)

    def preview_report(self):
        month = self.report_month_combo.get()
        if not month: return
        row = DB.fetchone(f'SELECT {ALL_COLS} FROM public."tbl_EBbillR1" WHERE billing_month=?', (month,))
        
        self.report_preview.delete(1.0, tk.END)
        if not row:
            self.report_preview.insert(tk.END, "No data found for this month.")
            return

        preview_text = f"""
        ===================================================================
                        MONTHLY ELECTRICITY REPORT: {row[1]}
        ===================================================================
        
        >> UTILITY BILL SUMMARY
        -------------------------------------------------------------------
        Total Bill Amount Paid : Rs {row[7]:.2f}
        Total Charged Units    : {row[4]}
        Unit Rate              : Rs {row[6]:.2f}
        System Power Factor    : {row[5]}
        Derived Fixed Charges  : Rs {row[8]:.2f}
        System Loss (Excess)   : {row[19]:.1f} Units
        
        >> SRINIVAS ACCOUNT (MF: 20)
        -------------------------------------------------------------------
        Meter Readings         : Old {row[9]} -> New {row[10]}
        Units Consumed         : {row[11]}
        Proportional Usage     : {row[12]*100:.1f}%
        Allocated Fixed Charge : Rs {row[8]/2:.2f}
        FINAL INVOICE AMOUNT   : Rs {row[13]:.2f}
        
        >> SQUARE V ACCOUNT (MF: 1)
        -------------------------------------------------------------------
        Meter Readings         : Old {row[14]} -> New {row[15]}
        Units Consumed         : {row[16]}
        Proportional Usage     : {row[17]*100:.1f}%
        Allocated Fixed Charge : Rs {row[8]/2:.2f}
        FINAL INVOICE AMOUNT   : Rs {row[18]:.2f}
        
        ===================================================================
        Note: The sum of sub-meter invoices matches the Total Utility Bill.
        """
        self.report_preview.insert(tk.END, preview_text)

    def generate_html_report(self):
        month = self.report_month_combo.get()
        if not month: messagebox.showerror("Error", "Select a month first."); return
        row = DB.fetchone(f'SELECT {ALL_COLS} FROM public."tbl_EBbillR1" WHERE billing_month=?', (month,))
        if not row: return

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Helvetica Neue', Arial, sans-serif; padding: 40px; color: #333; max-width: 800px; margin: auto; }}
                .header {{ border-bottom: 3px solid #004d99; padding-bottom: 20px; margin-bottom: 30px; text-align: center; }}
                h1 {{ color: #004d99; margin: 0; font-size: 28px; }}
                h3 {{ color: #666; margin-top: 5px; }}
                .section-title {{ background-color: #f2f2f2; padding: 10px; font-weight: bold; border-left: 5px solid #004d99; margin-top: 30px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                th, td {{ padding: 12px 15px; border-bottom: 1px solid #ddd; text-align: left; }}
                th {{ background-color: #f9f9f9; font-weight: bold; color: #555; }}
                .right {{ text-align: right; }}
                .total-row {{ font-weight: bold; background-color: #e6f2ff; font-size: 1.1em; }}
                .grand-total {{ font-size: 1.4em; color: #d32f2f; }}
                .footer {{ margin-top: 50px; font-size: 12px; color: #888; text-align: center; border-top: 1px solid #eee; padding-top: 20px; }}
                @media print {{ body {{ padding: 0; }} .no-print {{ display: none; }} }}
            </style>
        </head>
        <body>
            <div class="no-print" style="text-align:center; margin-bottom:20px;">
                <button onclick="window.print()" style="padding:10px 20px; font-size:16px; background:#4CAF50; color:white; border:none; cursor:pointer;">🖨️ Click to Print Document</button>
            </div>
            
            <div class="header">
                <h1>SVEE Electricity Bill Allocation</h1>
                <h3>Billing Period: {row[1]}</h3>
            </div>

            <div class="section-title">Utility Board Summary (Main Meter)</div>
            <table>
                <tr><th>Total Billed Amount</th><td class="right grand-total">₹{row[7]:,.2f}</td></tr>
                <tr><th>Main Meter Units Charged</th><td class="right">{row[4]:,.0f} Units</td></tr>
                <tr><th>Unit Rate Applied</th><td class="right">₹{row[6]:.2f} / Unit</td></tr>
                <tr><th>System Power Factor (PF)</th><td class="right">{row[5]}</td></tr>
                <tr><th>Total Derived Fixed Charges</th><td class="right">₹{row[8]:,.2f}</td></tr>
                <tr><th>System Loss / Shared Excess</th><td class="right">{row[19]:,.1f} Units</td></tr>
            </table>

            <div class="section-title">Tenant Invoice Breakdown</div>
            <table>
                <tr>
                    <th>Tenant</th>
                    <th>Readings (Old &rarr; New)</th>
                    <th>Actual Units</th>
                    <th>Usage Ratio</th>
                    <th class="right">Total Allocation (₹)</th>
                </tr>
                <tr>
                    <td><strong>Srinivas</strong> (MF: 20)</td>
                    <td>{row[9]} &rarr; {row[10]}</td>
                    <td>{row[11]:.0f}</td>
                    <td>{row[12]*100:.1f}%</td>
                    <td class="right total-row">₹{row[13]:,.2f}</td>
                </tr>
                <tr>
                    <td><strong>Square V</strong> (MF: 1)</td>
                    <td>{row[14]} &rarr; {row[15]}</td>
                    <td>{row[16]:.0f}</td>
                    <td>{row[17]*100:.1f}%</td>
                    <td class="right total-row">₹{row[18]:,.2f}</td>
                </tr>
            </table>

            <div class="footer">
                <p>Generated by SVEE Management System</p>
            </div>
        </body>
        </html>
        """
        
        filepath = os.path.abspath("temp_bill_report.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        webbrowser.open('file://' + filepath)

if __name__ == "__main__":
    # Ensure Tkinter starts normally
    root = tk.Tk()
    app = EnterpriseBillApp(root)
    root.mainloop()