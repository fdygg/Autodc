import sqlite3

DATABASE = 'store.db'

def get_connection():
    try:
        conn = sqlite3.connect(DATABASE)
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def add_balance(growid, wl, dl, bgl):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance_wl = balance_wl + ?, balance_dl = balance_dl + ?, balance_bgl = balance_bgl + ? WHERE growid = ?", (wl, dl, bgl, growid))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error updating balance: {e}")

def subtract_balance(growid, wl, dl, bgl):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance_wl = balance_wl - ?, balance_dl = balance_dl - ?, balance_bgl = balance_bgl - ? WHERE growid = ?", (wl, dl, bgl, growid))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error updating balance: {e}")

# Inisialisasi database dan tabel jika belum ada
def init_db():
    conn = get_connection()
    if conn is None:
        print("Failed to initialize database connection.")
        return
    cursor = conn.cursor()
    
    # Buat tabel users
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        growid TEXT PRIMARY KEY,
        balance_wl INTEGER DEFAULT 0,
        balance_dl INTEGER DEFAULT 0,
        balance_bgl INTEGER DEFAULT 0
    )
    ''')

    # Buat tabel products
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT NOT NULL UNIQUE,
        price INTEGER NOT NULL,
        stock INTEGER DEFAULT 0,
        description TEXT
    )
    ''')

    # Buat tabel user_products
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_products (
        user_id INTEGER,
        product TEXT,
        count INTEGER,
        PRIMARY KEY (user_id, product)
    )
    ''')

    # Buat tabel world_info
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS world_info (
        id INTEGER PRIMARY KEY,
        world TEXT,
        owner TEXT,
        bot TEXT
    )
    ''')

    # Buat tabel user_growid
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_growid (
        user_id INTEGER PRIMARY KEY,
        growid TEXT
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()