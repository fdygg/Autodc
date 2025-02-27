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

def get_balance(growid):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT balance_wl, balance_dl, balance_bgl FROM users WHERE growid = ?", (growid,))
        balance = cursor.fetchone()
        conn.close()
        return balance
    except sqlite3.Error as e:
        print(f"Error getting balance: {e}")
        return None

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

    # Buat tabel purchases dengan struktur baru
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        product TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        total_price INTEGER NOT NULL,
        purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        buyer_growid TEXT,
        buyer_name TEXT,
        UNIQUE(order_number)
    )
    ''')

    # Buat tabel product_stock
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS product_stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_code TEXT,
        content TEXT,
        used INTEGER DEFAULT 0,
        used_by TEXT DEFAULT NULL,
        used_at TIMESTAMP DEFAULT NULL,
        added_by TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        source_file TEXT,
        FOREIGN KEY (product_code) REFERENCES products (code)
    )
    ''')

    conn.commit()
    conn.close()

# Fungsi untuk menghapus dan membuat ulang tabel purchases jika diperlukan
def reset_purchases_table():
    conn = get_connection()
    if conn is None:
        print("Failed to initialize database connection.")
        return
    cursor = conn.cursor()
    
    # Hapus tabel lama
    cursor.execute('DROP TABLE IF EXISTS purchases')
    
    # Buat tabel baru dengan struktur yang benar
    cursor.execute('''
    CREATE TABLE purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        product TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        total_price INTEGER NOT NULL,
        purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        buyer_growid TEXT,
        buyer_name TEXT,
        UNIQUE(order_number)
    )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    # Uncomment baris berikut jika ingin mereset tabel purchases
    # reset_purchases_table()