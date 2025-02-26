from database import get_connection

# Fungsi untuk menambahkan saldo
def add_balance(growid, wl=0, dl=0, bgl=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO users (growid, balance_wl, balance_dl, balance_bgl)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(growid) DO UPDATE SET
    balance_wl = balance_wl + ?,
    balance_dl = balance_dl + ?,
    balance_bgl = balance_bgl + ?
    ''', (growid, wl, dl, bgl, wl, dl, bgl))
    conn.commit()
    conn.close()

# Fungsi untuk mengurangi saldo
def subtract_balance(growid, wl=0, dl=0, bgl=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE users
    SET balance_wl = balance_wl - ?,
        balance_dl = balance_dl - ?,
        balance_bgl = balance_bgl - ?
    WHERE growid = ?
    ''', (wl, dl, bgl, growid))
    conn.commit()
    conn.close()

# Fungsi untuk mendapatkan saldo
def get_balance(growid):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT balance_wl, balance_dl, balance_bgl
    FROM users
    WHERE growid = ?
    ''', (growid,))
    balance = cursor.fetchone()
    conn.close()
    return balance

# Fungsi konversi saldo
def convert_balance(growid, from_currency, to_currency, amount):
    balance = get_balance(growid)
    if not balance:
        return "User not found"
    
    balance_wl, balance_dl, balance_bgl = balance

    if from_currency == 'WL' and to_currency == 'DL':
        if balance_wl >= amount:
            subtract_balance(growid, wl=amount)
            add_balance(growid, dl=amount // 100)
        else:
            return "Insufficient WL balance"
    elif from_currency == 'DL' and to_currency == 'WL':
        if balance_dl >= amount:
            subtract_balance(growid, dl=amount)
            add_balance(growid, wl=amount * 100)
        else:
            return "Insufficient DL balance"
    elif from_currency == 'DL' and to_currency == 'BGL':
        if balance_dl >= amount:
            subtract_balance(growid, dl=amount)
            add_balance(growid, bgl=amount // 100)
        else:
            return "Insufficient DL balance"
    elif from_currency == 'BGL' and to_currency == 'DL':
        if balance_bgl >= amount:
            subtract_balance(growid, bgl=amount)
            add_balance(growid, dl=amount * 100)
        else:
            return "Insufficient BGL balance"
    else:
        return "Invalid conversion"

    return "Conversion successful"

# Fungsi untuk mendapatkan saldo WL dengan konversi dari DL dan BGL
def get_total_wl_balance(growid):
    balance = get_balance(growid)
    if not balance:
        return "User not found"
    
    balance_wl, balance_dl, balance_bgl = balance
    total_wl = balance_wl + (balance_dl * 100) + (balance_bgl * 10000)
    return total_wl

if __name__ == "__main__":
    from database import init_db
    init_db()
    growid = "user123"
    add_balance(growid, wl=150, dl=2, bgl=1)
    print(get_balance(growid))
    print(convert_balance(growid, 'WL', 'DL', 100))
    print(get_balance(growid))
    print(convert_balance(growid, 'DL', 'BGL', 1))
    print(get_balance(growid))
    print(convert_balance(growid, 'BGL', 'DL', 1))
    print(get_balance(growid))
    print(f"Total WL balance for {growid} (including DL and BGL converted to WL): {get_total_wl_balance(growid)}")