import sqlite3

DATABASE = 'store.db'

def get_connection():
    try:
        conn = sqlite3.connect(DATABASE)
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
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
        name TEXT,
        code TEXT PRIMARY KEY,
        price INTEGER,
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