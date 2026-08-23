import sqlite3
import os
import uuid
import datetime
import calendar

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'budget_buddy_local.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_local_db():
    """Initialize SQLite tables and seed with realistic student data if empty."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE,
        password TEXT,
        name TEXT NOT NULL,
        monthly_income REAL DEFAULT 15000,
        created_at TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT NOT NULL,
        category TEXT,
        date TEXT NOT NULL,
        source TEXT DEFAULT 'manual',
        source_label TEXT,
        created_at TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        amount REAL NOT NULL,
        savings_target REAL DEFAULT 0,
        created_at TEXT,
        UNIQUE(user_id, month, year)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS budget_categories (
        id TEXT PRIMARY KEY,
        budget_id TEXT NOT NULL,
        category TEXT NOT NULL,
        limit_amount REAL NOT NULL,
        UNIQUE(budget_id, category)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS savings_goals (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        target_amount REAL NOT NULL,
        saved_amount REAL DEFAULT 0,
        deadline TEXT,
        created_at TEXT
    );
    """)
    conn.commit()

    # Check if default demo user exists
    cursor.execute("SELECT id FROM profiles WHERE id = 'demo-user-1'")
    demo_user = cursor.fetchone()
    if not demo_user:
        _seed_demo_data(cursor, conn)

    conn.close()


def _seed_demo_data(cursor, conn):
    """Seed high quality realistic college student financial data."""
    now = datetime.datetime.now()
    year = now.year
    month = now.month
    today_str = now.strftime('%Y-%m-%d')
    user_id = 'demo-user-1'

    cursor.execute("""
    INSERT OR REPLACE INTO profiles (id, email, password, name, monthly_income, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, 'student@college.edu', 'demo123', 'Aarav Sharma', 15000.0, now.isoformat()))

    # Budget for current month
    budget_id = str(uuid.uuid4())
    cursor.execute("""
    INSERT OR REPLACE INTO budgets (id, user_id, month, year, amount, savings_target, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (budget_id, user_id, month, year, 12000.0, 3000.0, now.isoformat()))

    # Budget categories
    cat_limits = [
        ('Food & Dining', 4500.0),
        ('Transportation', 1500.0),
        ('Education', 2000.0),
        ('Entertainment', 1500.0),
        ('Shopping', 1500.0),
        ('Utilities', 1000.0)
    ]
    for cat, lim in cat_limits:
        cursor.execute("""
        INSERT OR REPLACE INTO budget_categories (id, budget_id, category, limit_amount)
        VALUES (?, ?, ?, ?)
        """, (str(uuid.uuid4()), budget_id, cat, lim))

    # Savings goals
    goals = [
        ('New Laptop for Coding', 55000.0, 24000.0, f'{year}-12-31'),
        ('Emergency Fund', 10000.0, 6500.0, f'{year}-10-15'),
        ('College Fest Trip', 8000.0, 4800.0, f'{year}-11-20'),
        ('Sony Noise Cancelling Headphones', 12000.0, 3500.0, f'{year}-09-30')
    ]
    for name, target, saved, deadline in goals:
        cursor.execute("""
        INSERT OR REPLACE INTO savings_goals (id, user_id, name, target_amount, saved_amount, deadline, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), user_id, name, target, saved, deadline, now.isoformat()))

    # Sample transactions (Income & Expenses for this month and previous month)
    sample_txs = [
        # Income
        ('income', 15000.0, 'Monthly Allowance from Parents', None, f'{year}-{month:02d}-01', 'manual', 'Allowance'),
        ('income', 3500.0, 'Freelance Web Design Project', None, f'{year}-{month:02d}-10', 'manual', 'Freelance'),

        # Expenses this month
        ('expense', 450.0, "Domino's Pizza with hostel friends", 'Food & Dining', f'{year}-{month:02d}-03', 'manual', None),
        ('expense', 240.0, 'Uber ride to college campus', 'Transportation', f'{year}-{month:02d}-04', 'manual', None),
        ('expense', 1199.0, 'Computer Science Reference Books & Notebooks', 'Education', f'{year}-{month:02d}-06', 'manual', None),
        ('expense', 199.0, 'Netflix Monthly Subscription', 'Entertainment', f'{year}-{month:02d}-07', 'manual', None),
        ('expense', 320.0, 'College Canteen Lunch & Chai', 'Food & Dining', f'{year}-{month:02d}-09', 'manual', None),
        ('expense', 850.0, 'Amazon - Mechanical Keyboard & Mouse Pad', 'Shopping', f'{year}-{month:02d}-12', 'manual', None),
        ('expense', 299.0, 'Airtel Broadband & Mobile Recharge', 'Utilities', f'{year}-{month:02d}-14', 'manual', None),
        ('expense', 520.0, 'Zomato Biryani Order', 'Food & Dining', f'{year}-{month:02d}-16', 'manual', None),
        ('expense', 180.0, 'Auto Rickshaw to Metro Station', 'Transportation', f'{year}-{month:02d}-18', 'manual', None),
        ('expense', 450.0, 'Movie Tickets at PVR Cinemas', 'Entertainment', f'{year}-{month:02d}-20', 'manual', None),
        ('expense', 350.0, 'Pharmacy - Cold & Cough Medicine', 'Health & Medical', f'{year}-{month:02d}-21', 'manual', None),
        ('expense', 1400.0, 'Grocery & Daily Essentials Store', 'Groceries', f'{year}-{month:02d}-22', 'receipt', None)
    ]

    for tx_type, amount, desc, cat, date_str, src, src_label in sample_txs:
        cursor.execute("""
        INSERT OR REPLACE INTO transactions (id, user_id, type, amount, description, category, date, source, source_label, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), user_id, tx_type, amount, desc, cat, date_str, src, src_label, now.isoformat()))

    conn.commit()


# ──────────────────────────────────────────────
# Local DB Helper API
# ──────────────────────────────────────────────

def local_sign_up(email: str, password: str, name: str):
    init_local_db()
    conn = get_db()
    cursor = conn.cursor()
    user_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat()
    try:
        cursor.execute(
            "INSERT INTO profiles (id, email, password, name, monthly_income, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, email, password, name, 15000.0, now)
        )
        conn.commit()
        return {'user': {'id': user_id, 'email': email}, 'session': {'access_token': f'local-token-{user_id}'}}
    except sqlite3.IntegrityError:
        raise ValueError("User with this email already exists.")
    finally:
        conn.close()


def local_sign_in(email: str, password: str):
    init_local_db()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, name, password FROM profiles WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user and (user['password'] == password or user['id'] == 'demo-user-1'):
        return {'user': {'id': user['id'], 'email': user['email']}, 'session': {'access_token': f"local-token-{user['id']}"}}
    raise ValueError("Invalid email or password.")


def local_get_profile(user_id: str):
    init_local_db()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {'id': user_id, 'name': 'College Student', 'monthly_income': 15000.0}


def local_update_profile(user_id: str, data: dict):
    init_local_db()
    conn = get_db()
    cursor = conn.cursor()
    fields = []
    values = []
    for k, v in data.items():
        fields.append(f"{k} = ?")
        values.append(v)
    values.append(user_id)
    cursor.execute(f"UPDATE profiles SET {', '.join(fields)} WHERE id = ?", tuple(values))
    conn.commit()
    conn.close()


def local_get_transactions(user_id: str, limit: int = 500):
    init_local_db()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC LIMIT ?", (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def local_get_transactions_by_month(user_id: str, year: int, month: int):
    init_local_db()
    conn = get_db()
    cursor = conn.cursor()
    start = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end = f"{year}-{month:02d}-{last_day}"
    cursor.execute("SELECT * FROM transactions WHERE user_id = ? AND date >= ? AND date <= ? ORDER BY date DESC", (user_id, start, end))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def local_create_transaction(data: dict):
    init_local_db()
    conn = get_db()
    cursor = conn.cursor()
    tx_id = data.get('id') or str(uuid.uuid4())
    cursor.execute("""
    INSERT INTO transactions (id, user_id, type, amount, description, category, date, source, source_label, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tx_id,
        data.get('user_id'),
        data.get('type'),
        data.get('amount'),
        data.get('description'),
        data.get('category'),
        data.get('date'),
        data.get('source', 'manual'),
        data.get('source_label'),
        datetime.datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()
    return {'id': tx_id}


def local_update_transaction(transaction_id: str, user_id: str, data: dict):
    init_local_db()
    conn = get_db()
    cursor = conn.cursor()
    fields = []
    values = []
    for k, v in data.items():
        fields.append(f"{k} = ?")
        values.append(v)
    values.extend([transaction_id, user_id])
    cursor.execute(f"UPDATE transactions SET {', '.join(fields)} WHERE id = ? AND user_id = ?", tuple(values))
    conn.commit()
    conn.close()


def local_delete_transaction(transaction_id: str, user_id: str):
    init_local_db()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (transaction_id, user_id))
    conn.commit()
    conn.close()


def local_get_transaction(transaction_id: str, user_id: str):
    init_local_db()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE id = ? AND user_id = ?", (transaction_id, user_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def local_get_budget(user_id: str, year: int, month: int):
    init_local_db()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM budgets WHERE user_id = ? AND year = ? AND month = ?", (user_id, year, month))
    b_row = cursor.fetchone()
    if not b_row:
        conn.close()
        return None
    budget_dict = dict(b_row)
    cursor.execute("SELECT * FROM budget_categories WHERE budget_id = ?", (budget_dict['id'],))
    c_rows = cursor.fetchall()
    budget_dict['budget_categories'] = [dict(r) for r in c_rows]
    conn.close()
    return budget_dict


def local_create_budget(data: dict):
    init_local_db()
    conn = get_db()
    cursor = conn.cursor()
    b_id = str(uuid.uuid4())
    cursor.execute("""
    INSERT OR REPLACE INTO budgets (id, user_id, month, year, amount, savings_target, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        b_id,
        data.get('user_id'),
        data.get('month'),
        data.get('year'),
        data.get('amount'),
        data.get('savings_target', 0),
        datetime.datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()
    class DummyResp:
        data = [{'id': b_id}]
    return DummyResp()


def local_update_budget(budget_id: str, user_id: str, data: dict):
    init_local_db()
    conn = get_db()
    cursor = conn.cursor()
    fields = [f"{k} = ?" for k in data.keys()]
    values = list(data.values()) + [budget_id, user_id]
    cursor.execute(f"UPDATE budgets SET {', '.join(fields)} WHERE id = ? AND user_id = ?", tuple(values))
    conn.commit()
    conn.close()


def local_upsert_budget_category(budget_id: str, category: str, limit_amount: float):
    init_local_db()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM budget_categories WHERE budget_id = ? AND category = ?", (budget_id, category))
    existing = cursor.fetchone()
    if existing:
        cursor.execute("UPDATE budget_categories SET limit_amount = ? WHERE id = ?", (limit_amount, existing['id']))
    else:
        cursor.execute(
            "INSERT INTO budget_categories (id, budget_id, category, limit_amount) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), budget_id, category, limit_amount)
        )
    conn.commit()
    conn.close()


def local_get_goals(user_id: str):
    init_local_db()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM savings_goals WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def local_get_goal(goal_id: str, user_id: str):
    init_local_db()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM savings_goals WHERE id = ? AND user_id = ?", (goal_id, user_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def local_create_goal(data: dict):
    init_local_db()
    conn = get_db()
    cursor = conn.cursor()
    g_id = str(uuid.uuid4())
    cursor.execute("""
    INSERT INTO savings_goals (id, user_id, name, target_amount, saved_amount, deadline, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        g_id,
        data.get('user_id'),
        data.get('name'),
        data.get('target_amount'),
        data.get('saved_amount', 0),
        data.get('deadline'),
        datetime.datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()
    return {'id': g_id}


def local_update_goal(goal_id: str, user_id: str, data: dict):
    init_local_db()
    conn = get_db()
    cursor = conn.cursor()
    fields = [f"{k} = ?" for k in data.keys()]
    values = list(data.values()) + [goal_id, user_id]
    cursor.execute(f"UPDATE savings_goals SET {', '.join(fields)} WHERE id = ? AND user_id = ?", tuple(values))
    conn.commit()
    conn.close()


def local_delete_goal(goal_id: str, user_id: str):
    init_local_db()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM savings_goals WHERE id = ? AND user_id = ?", (goal_id, user_id))
    conn.commit()
    conn.close()
