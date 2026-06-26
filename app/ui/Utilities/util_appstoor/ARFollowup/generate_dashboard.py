import os
import re
import json
import webbrowser
from collections import defaultdict
import pdfplumber

# File Paths
pdf_path = r"G:\My Drive\SVEE2\05 FY26-27\05 Accounts\APAR\AR.pdf"
output_dir = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(output_dir, "AR_Dashboard.html")

def clean_amount(val_str):
    return float(val_str.replace(",", ""))

def parse_pdf(path):
    customers = []
    
    if not os.path.exists(path):
        print(f"Error: PDF file not found at {path}")
        return []
        
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            words = page.extract_words()
            
            # Group words by top coordinate
            lines = defaultdict(list)
            for w in words:
                matched = False
                for t in lines:
                    if abs(w['top'] - t) < 2:
                        lines[t].append(w)
                        matched = True
                        break
                if not matched:
                    lines[w['top']].append(w)
            
            sorted_tops = sorted(lines.keys())
            start_parsing = False
            
            for top in sorted_tops:
                line_words = sorted(lines[top], key=lambda x: x['x0'])
                line_text = " ".join([w['text'] for w in line_words])
                
                if "Particulars" in line_text and "Closing" in line_text:
                    continue
                if "Debit" in line_text and "Credit" in line_text:
                    start_parsing = True
                    continue
                if "Grand Total" in line_text:
                    start_parsing = False
                    break
                    
                if start_parsing:
                    if not line_words:
                        continue
                    
                    amount_word = line_words[-1]
                    # Validate that the last word is a valid currency amount
                    if re.match(r'^\d{1,3}(,\d{2,3})*\.\d{2}$', amount_word['text']):
                        val = clean_amount(amount_word['text'])
                        x1 = amount_word['x1']
                        
                        customer_name = " ".join([w['text'] for w in line_words[:-1]])
                        
                        # Column detection based on x-coordinate
                        if x1 < 520:
                            debit = val
                            credit = None
                        else:
                            debit = None
                            credit = val
                            
                        customers.append({
                            "name": customer_name.strip(),
                            "debit": debit,
                            "credit": credit
                        })
    return customers

def generate_html(customers):
    # Calculate statistics
    total_debit = sum(c['debit'] for c in customers if c['debit'] is not None)
    total_credit = sum(c['credit'] for c in customers if c['credit'] is not None)
    actionable_count = sum(1 for c in customers if c['debit'] is not None)
    
    customers_json = json.dumps(customers, indent=2)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AR Invoice Dashboard & Email Generator</title>
    
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- FontAwesome Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <style>
        :root {{
            --bg-primary: #0b0f19;
            --bg-secondary: #131b2e;
            --bg-card: #1e293b;
            --accent-indigo: #6366f1;
            --accent-indigo-hover: #4f46e5;
            --accent-purple: #a855f7;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --debit-color: #f43f5e;
            --credit-color: #10b981;
            --border-color: #334155;
            --font-family: 'Plus Jakarta Sans', sans-serif;
            --header-font: 'Outfit', sans-serif;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            transition: all 0.2s ease;
        }}

        body {{
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-family: var(--font-family);
            padding: 2.5rem 1.5rem;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        /* Header Layout */
        header {{
            margin-bottom: 2.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        h1 {{
            font-family: var(--header-font);
            font-weight: 700;
            font-size: 2.25rem;
            background: linear-gradient(135deg, var(--text-primary) 30%, #a5b4fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}

        header p {{
            color: var(--text-secondary);
            font-size: 1rem;
        }}

        .refresh-btn {{
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.75rem 1.25rem;
            border-radius: 12px;
            cursor: pointer;
            font-family: var(--font-family);
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .refresh-btn:hover {{
            background-color: var(--border-color);
            transform: translateY(-2px);
        }}

        /* Stats Cards */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2.5rem;
        }}

        .stat-card {{
            background: linear-gradient(145deg, var(--bg-secondary) 0%, rgba(30, 41, 59, 0.4) 100%);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
            overflow: hidden;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        }}

        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: var(--accent-indigo);
            opacity: 0.8;
        }}

        .stat-card.debit-card::before {{
            background: var(--debit-color);
        }}

        .stat-card.credit-card::before {{
            background: var(--credit-color);
        }}

        .stat-card .icon {{
            position: absolute;
            right: 1.25rem;
            top: 1.25rem;
            font-size: 2rem;
            opacity: 0.15;
            color: var(--text-primary);
        }}

        .stat-title {{
            color: var(--text-secondary);
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }}

        .stat-value {{
            font-size: 1.75rem;
            font-weight: 700;
            font-family: var(--header-font);
            margin-bottom: 0.25rem;
        }}

        .stat-desc {{
            color: var(--text-muted);
            font-size: 0.75rem;
        }}

        /* Control Bar (Search & Filter) */
        .control-bar {{
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            align-items: center;
            justify-content: space-between;
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            padding: 1rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}

        .search-wrapper {{
            position: relative;
            flex: 1;
            min-width: 280px;
        }}

        .search-wrapper i {{
            position: absolute;
            left: 1rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
        }}

        .search-input {{
            width: 100%;
            background-color: var(--bg-primary);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.75rem 1rem 0.75rem 2.5rem;
            border-radius: 10px;
            font-family: var(--font-family);
            font-size: 0.95rem;
        }}

        .search-input:focus {{
            outline: none;
            border-color: var(--accent-indigo);
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
        }}

        .filter-tabs {{
            display: flex;
            gap: 0.5rem;
        }}

        .filter-tab {{
            background: transparent;
            border: 1px solid transparent;
            color: var(--text-secondary);
            padding: 0.6rem 1.2rem;
            border-radius: 10px;
            cursor: pointer;
            font-family: var(--font-family);
            font-weight: 600;
            font-size: 0.9rem;
        }}

        .filter-tab:hover {{
            background-color: rgba(255, 255, 255, 0.05);
            color: var(--text-primary);
        }}

        .filter-tab.active {{
            background-color: var(--accent-indigo);
            color: var(--text-primary);
        }}

        /* Table CSS */
        .table-container {{
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.4);
            margin-bottom: 2rem;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}

        th {{
            background-color: rgba(30, 41, 59, 0.6);
            color: var(--text-secondary);
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 1.1rem 1.5rem;
            border-bottom: 1px solid var(--border-color);
        }}

        td {{
            padding: 1.2rem 1.5rem;
            border-bottom: 1px solid rgba(51, 65, 85, 0.4);
            vertical-align: middle;
            font-size: 0.95rem;
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        tr:hover td {{
            background-color: rgba(255, 255, 255, 0.02);
        }}

        .customer-name {{
            font-weight: 600;
            color: var(--text-primary);
        }}

        .balance-val {{
            font-weight: 700;
            font-family: var(--header-font);
        }}

        .balance-debit {{
            color: var(--debit-color);
        }}

        .balance-credit {{
            color: var(--credit-color);
        }}

        .btn-action {{
            background: linear-gradient(135deg, var(--accent-indigo) 0%, var(--accent-purple) 100%);
            border: none;
            color: var(--text-primary);
            padding: 0.6rem 1.1rem;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.85rem;
            font-family: var(--font-family);
            box-shadow: 0 4px 10px rgba(99, 102, 241, 0.3);
        }}

        .btn-action:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(99, 102, 241, 0.45);
        }}

        .credit-badge {{
            color: var(--text-muted);
            font-style: italic;
            font-size: 0.85rem;
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
        }}

        /* Modal / Drawer Panel */
        .drawer-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(11, 15, 25, 0.7);
            backdrop-filter: blur(8px);
            z-index: 1000;
            opacity: 0;
            pointer-events: none;
        }}

        .drawer-overlay.active {{
            opacity: 1;
            pointer-events: all;
        }}

        .drawer {{
            position: fixed;
            top: 0;
            right: -500px;
            width: 500px;
            max-width: 90%;
            height: 100%;
            background-color: var(--bg-secondary);
            border-left: 1px solid var(--border-color);
            z-index: 1001;
            padding: 2rem;
            box-shadow: -10px 0 30px rgba(0, 0, 0, 0.5);
            display: flex;
            flex-direction: column;
            border-radius: 24px 0 0 24px;
        }}

        .drawer.active {{
            right: 0;
        }}

        .drawer-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1rem;
        }}

        .drawer-title {{
            font-family: var(--header-font);
            font-size: 1.4rem;
            font-weight: 700;
        }}

        .btn-close {{
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-size: 1.25rem;
            cursor: pointer;
        }}

        .btn-close:hover {{
            color: var(--text-primary);
        }}

        .form-group {{
            margin-bottom: 1.5rem;
        }}

        .form-label {{
            display: block;
            color: var(--text-secondary);
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .form-input {{
            width: 100%;
            background-color: var(--bg-primary);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.75rem 1rem;
            border-radius: 10px;
            font-family: var(--font-family);
            font-size: 0.95rem;
        }}

        .form-input:focus {{
            outline: none;
            border-color: var(--accent-indigo);
        }}

        .message-textarea {{
            width: 100%;
            height: 180px;
            background-color: var(--bg-primary);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 1rem;
            border-radius: 12px;
            font-family: var(--font-family);
            font-size: 0.95rem;
            resize: none;
            line-height: 1.5;
        }}

        .message-textarea:focus {{
            outline: none;
            border-color: var(--accent-indigo);
        }}

        .drawer-footer {{
            margin-top: auto;
            display: grid;
            grid-template-columns: 1fr;
            gap: 0.75rem;
        }}

        .btn-launch {{
            padding: 0.9rem;
            border-radius: 12px;
            font-weight: 600;
            font-family: var(--font-family);
            font-size: 0.95rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            border: none;
        }}

        .btn-launch-gmail {{
            background: linear-gradient(135deg, #ea4335 0%, #c5221f 100%);
            color: white;
            box-shadow: 0 4px 12px rgba(234, 67, 53, 0.3);
        }}

        .btn-launch-gmail:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 18px rgba(234, 67, 53, 0.45);
        }}

        .btn-launch-default {{
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
        }}

        .btn-launch-default:hover {{
            background-color: rgba(255, 255, 255, 0.1);
        }}

        .btn-launch-copy {{
            background-color: rgba(99, 102, 241, 0.1);
            border: 1px solid rgba(99, 102, 241, 0.3);
            color: #c7d2fe;
        }}

        .btn-launch-copy:hover {{
            background-color: rgba(99, 102, 241, 0.2);
        }}

        .toast {{
            position: fixed;
            bottom: 2rem;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background-color: var(--accent-indigo);
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 10px;
            font-weight: 600;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
            opacity: 0;
            pointer-events: none;
            z-index: 2000;
        }}

        .toast.show {{
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }}

        /* Empty State */
        .empty-state {{
            padding: 3rem;
            text-align: center;
            color: var(--text-muted);
        }}

        .empty-state i {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header>
            <div>
                <h1>AR Invoice Assistant</h1>
                <p>Generated from <code>AR.pdf</code> &bull; Survey No:298(P), IDA, Jeedimetla</p>
            </div>
            <button class="refresh-btn" onclick="window.location.reload()"><i class="fa-solid fa-arrows-rotate"></i> Reload PDF Data</button>
        </header>

        <!-- Stats Cards -->
        <div class="stats-grid">
            <div class="stat-card debit-card">
                <i class="fa-solid fa-money-bill-trend-up icon"></i>
                <div class="stat-title">Outstanding Debit</div>
                <div class="stat-value" id="outstanding-val">&#8377; {total_debit:,.2f}</div>
                <div class="stat-desc">Awaiting payments from customers</div>
            </div>
            
            <div class="stat-card credit-card">
                <i class="fa-solid fa-wallet icon"></i>
                <div class="stat-title">Total Credit</div>
                <div class="stat-value" id="credit-val">&#8377; {total_credit:,.2f}</div>
                <div class="stat-desc">Credit balances of customers</div>
            </div>

            <div class="stat-card">
                <i class="fa-solid fa-bell icon"></i>
                <div class="stat-title">Follow-ups Pending</div>
                <div class="stat-value">{actionable_count}</div>
                <div class="stat-desc">Customers with outstanding debit</div>
            </div>

            <div class="stat-card">
                <i class="fa-solid fa-users icon"></i>
                <div class="stat-title">Total Accounts</div>
                <div class="stat-value">{len(customers)}</div>
                <div class="stat-desc">Active ledger accounts</div>
            </div>
        </div>

        <!-- Controls -->
        <div class="control-bar">
            <div class="search-wrapper">
                <i class="fa-solid fa-magnifying-glass"></i>
                <input type="text" class="search-input" id="search" placeholder="Search customer name..." oninput="filterData()">
            </div>
            <div class="filter-tabs">
                <button class="filter-tab active" onclick="setFilter('all', this)">All</button>
                <button class="filter-tab" onclick="setFilter('debit', this)">Debit Only</button>
                <button class="filter-tab" onclick="setFilter('credit', this)">Credit Only</button>
            </div>
        </div>

        <!-- Table -->
        <div class="table-container">
            <table id="customer-table">
                <thead>
                    <tr>
                        <th>Customer Name</th>
                        <th style="text-align: right;">Debit (Outstanding)</th>
                        <th style="text-align: right;">Credit</th>
                        <th style="text-align: center; width: 220px;">Action</th>
                    </tr>
                </thead>
                <tbody id="table-body">
                    <!-- Dynamic Rows -->
                </tbody>
            </table>
            <div class="empty-state" id="empty-state" style="display: none;">
                <i class="fa-solid fa-box-open"></i>
                <p>No customers match your filters.</p>
            </div>
        </div>
    </div>

    <!-- Drawer Component -->
    <div class="drawer-overlay" id="drawer-overlay" onclick="closeDrawer()"></div>
    <div class="drawer" id="drawer">
        <div class="drawer-header">
            <div class="drawer-title" id="drawer-cust-name">Customer Name</div>
            <button class="btn-close" onclick="closeDrawer()"><i class="fa-solid fa-xmark"></i></button>
        </div>
        
        <div class="form-group">
            <label class="form-label">To (Customer Email/Contact)</label>
            <input type="email" class="form-input" id="email-to" placeholder="enter-customer-email@example.com">
        </div>
        
        <div class="form-group">
            <label class="form-label">Reminder Stage</label>
            <select class="form-input" id="reminder-type" onchange="updateMessageTemplate()" style="background-color: var(--bg-primary); color: var(--text-primary); cursor: pointer;">
                <option value="Gentle Reminder">Gentle Reminder</option>
                <option value="Payment Reminder #1">Payment Reminder #1</option>
                <option value="Payment Reminder #2">Payment Reminder #2</option>
                <option value="Payment Reminder #3">Payment Reminder #3</option>
            </select>
        </div>

        <div class="form-group">
            <label class="form-label">Subject</label>
            <input type="text" class="form-input" id="email-subject" value="">
        </div>

        <div class="form-group">
            <label class="form-label">Message Template</label>
            <textarea class="message-textarea" id="email-body" style="height: 320px;"></textarea>
        </div>

        <div class="drawer-footer">
            <button class="btn-launch btn-launch-gmail" onclick="launchGmail()"><i class="fa-solid fa-envelope"></i> Compose in Gmail Web</button>
            <button class="btn-launch btn-launch-default" onclick="launchDefaultMail()"><i class="fa-solid fa-paper-plane"></i> Send via Mail App (mailto)</button>
            <button class="btn-launch btn-launch-copy" onclick="copyMessage()"><i class="fa-solid fa-copy"></i> Copy Message to Clipboard</button>
        </div>
    </div>

    <!-- Toast -->
    <div class="toast" id="toast">Copied to clipboard!</div>

    <script>
        // Inject customer list from python
        const customers = {customers_json};

        let currentFilter = 'all';
        let activeCustomerIndex = null;

        function formatCurrency(val) {{
            if (val === null || val === undefined) return '-';
            return val.toLocaleString('en-IN', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
        }}

        function setFilter(filterType, element) {{
            document.querySelectorAll('.filter-tab').forEach(tab => tab.classList.remove('active'));
            element.classList.add('active');
            currentFilter = filterType;
            filterData();
        }}

        function filterData() {{
            const searchVal = document.getElementById('search').value.toLowerCase();
            const tbody = document.getElementById('table-body');
            tbody.innerHTML = '';
            
            let filtered = customers.filter(c => {{
                const matchesSearch = c.name.toLowerCase().includes(searchVal);
                if (!matchesSearch) return false;
                
                if (currentFilter === 'debit') return c.debit !== null;
                if (currentFilter === 'credit') return c.credit !== null;
                return true;
            }});

            if (filtered.length === 0) {{
                document.getElementById('empty-state').style.display = 'block';
                document.getElementById('customer-table').style.display = 'none';
            }} else {{
                document.getElementById('empty-state').style.display = 'none';
                document.getElementById('customer-table').style.display = 'table';
                
                filtered.forEach((c, idx) => {{
                    const originalIdx = customers.findIndex(orig => orig.name === c.name);
                    const tr = document.createElement('tr');
                    
                    const tdName = document.createElement('td');
                    tdName.className = 'customer-name';
                    tdName.textContent = c.name;
                    
                    const tdDebit = document.createElement('td');
                    tdDebit.style.textAlign = 'right';
                    tdDebit.className = 'balance-val balance-debit';
                    tdDebit.textContent = c.debit !== null ? formatCurrency(c.debit) : '-';
                    
                    const tdCredit = document.createElement('td');
                    tdCredit.style.textAlign = 'right';
                    tdCredit.className = 'balance-val balance-credit';
                    tdCredit.textContent = c.credit !== null ? formatCurrency(c.credit) : '-';
                    
                    const tdAction = document.createElement('td');
                    tdAction.style.textAlign = 'center';
                    
                    if (c.debit !== null) {{
                        const btn = document.createElement('button');
                        btn.className = 'btn-action';
                        btn.innerHTML = '<i class="fa-solid fa-envelope-open-text"></i> Send Request';
                        btn.onclick = () => openDrawer(originalIdx);
                        tdAction.appendChild(btn);
                    }} else {{
                        const creditBadge = document.createElement('span');
                        creditBadge.className = 'credit-badge';
                        creditBadge.innerHTML = '<i class="fa-solid fa-circle-check"></i> Credit Balance';
                        tdAction.appendChild(creditBadge);
                    }}
                    
                    tr.appendChild(tdName);
                    tr.appendChild(tdDebit);
                    tr.appendChild(tdCredit);
                    tr.appendChild(tdAction);
                    tbody.appendChild(tr);
                }});
            }}
        }}

        function getPresentDate() {{
            const today = new Date();
            return today.toLocaleDateString('en-IN', {{ day: '2-digit', month: 'short', year: 'numeric' }});
        }}

        function updateMessageTemplate() {{
            if (activeCustomerIndex === null) return;
            const customer = customers[activeCustomerIndex];
            const reminderType = document.getElementById('reminder-type').value;
            const formattedVal = formatCurrency(customer.debit);
            const presentDate = getPresentDate();
            
            // Format subject
            const subjectText = `${{reminderType}}: Payment Request for Outstanding Invoice ₹${{formattedVal}}`;
            document.getElementById('email-subject').value = subjectText;
            
            // Format body based on selected reminder type
            let reminderIntroText = "";
            if (reminderType === "Gentle Reminder") {{
                reminderIntroText = "This is a gentle reminder that payment for Balance amounting to ₹" + formattedVal + " is currently outstanding.";
            }} else {{
                reminderIntroText = "This is " + reminderType.toLowerCase() + " that payment for Balance amounting to ₹" + formattedVal + " is currently outstanding.";
            }}
            
            const bodyText = `Dear ${{customer.name}},\nSquare V Engineering Enterprises\n\nI hope this message finds you well. We truly value our business relationship and appreciate the trust you place in us.\n\n${{reminderIntroText}} As per our agreed terms, the due date was ${{presentDate}}.\n\nWe kindly request you to arrange the payment at the earliest convenience to avoid any disruption in services. Please find the payment details below for your reference:\n\nBank Details:\nICICI Bank\nCurrent Account Number: 130405002630\nIFSC Code: ICIC0001304\nBranch: Shapurnagar-500055\n\nIf you have already processed the payment, please disregard this notice. Otherwise, we would appreciate it if you could confirm the expected date of settlement.\n\nThank you for your prompt attention to this matter. Should you have any questions or require clarification, please feel free to reach out.`;
            
            document.getElementById('email-body').value = bodyText;
        }}

        function openDrawer(index) {{
            activeCustomerIndex = index;
            document.getElementById('reminder-type').value = 'Gentle Reminder'; // Reset to gentle reminder
            
            const customer = customers[index];
            document.getElementById('drawer-cust-name').textContent = customer.name;
            document.getElementById('email-to').value = ''; // User can fill this in
            
            updateMessageTemplate();
            
            document.getElementById('drawer-overlay').classList.add('active');
            document.getElementById('drawer').classList.add('active');
        }}

        function closeDrawer() {{
            document.getElementById('drawer-overlay').classList.remove('active');
            document.getElementById('drawer').classList.remove('active');
        }}

        function showToast() {{
            const toast = document.getElementById('toast');
            toast.classList.add('show');
            setTimeout(() => {{
                toast.classList.remove('show');
            }}, 2500);
        }}

        function copyMessage() {{
            const text = document.getElementById('email-body').value;
            navigator.clipboard.writeText(text).then(() => {{
                showToast();
            }});
        }}

        function launchGmail() {{
            const to = document.getElementById('email-to').value;
            const subject = encodeURIComponent(document.getElementById('email-subject').value);
            const body = encodeURIComponent(document.getElementById('email-body').value);
            const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=${{to}}&su=${{subject}}&body=${{body}}`;
            window.open(gmailUrl, '_blank');
        }}

        function launchDefaultMail() {{
            const to = document.getElementById('email-to').value;
            const subject = encodeURIComponent(document.getElementById('email-subject').value);
            const body = encodeURIComponent(document.getElementById('email-body').value);
            window.location.href = `mailto:${{to}}?subject=${{subject}}&body=${{body}}`;
        }}

        // Initial rendering
        filterData();
    </script>
</body>
</html>
"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Success: Interactive dashboard generated at: {html_path}")
    return html_path

def main():
    print("Parsing PDF and extracting customer records...")
    records = parse_pdf(pdf_path)
    if not records:
        print("No records extracted. Ensure the PDF path is correct.")
        return
        
    print(f"Extracted {len(records)} customer records.")
    html_file = generate_html(records)
    
    # Auto-open the file in user browser
    webbrowser.open(f"file:///{html_file.replace(chr(92), '/')}")
    print("Dashboard launched in browser.")

if __name__ == "__main__":
    main()
