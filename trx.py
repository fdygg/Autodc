import sqlite3
import json
import logging
from discord import File
from database import get_connection

# Baca konfigurasi dari config.json
with open('config.json') as config_file:
    config = json.load(config_file)

ID_LOG_PURCH = config['id_log_purch']  # Channel ID untuk log pembelian
ID_HISTORY_BUY = config['id_history_buy']  # Channel ID untuk riwayat pembelian

DATABASE = 'store.db'

def add_stock_from_file(product_code: str):
    try:
        with open(f'{product_code}.txt', 'r') as file:
            count = int(file.read().strip())
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET stock = stock + ? WHERE code = ?", (count, product_code))
            conn.commit()
            conn.close()
            return f"Added {count} to stock of product with code {product_code}."
    except Exception as e:
        logging.error(f'Error in add_stock_from_file: {e}')
        return f"An error occurred: {e}"

async def process_purchase(bot, user, product_code, quantity):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT stock, price FROM products WHERE code = ?", (product_code,))
        product_info = cursor.fetchone()
        if not product_info:
            return "Product not found."

        stock, price = product_info
        total_price = price * quantity

        cursor.execute("SELECT growid FROM user_growid WHERE user_id = ?", (user.id,))
        growid = cursor.fetchone()
        if growid:
            cursor.execute("SELECT balance_wl FROM users WHERE growid = ?", (growid[0],))
            user_balance = cursor.fetchone()
            if not user_balance or user_balance[0] < total_price:
                return "Insufficient balance."

            if stock < quantity:
                return "Not enough stock."

            cursor.execute("UPDATE products SET stock = stock - ? WHERE code = ?", (quantity, product_code))
            cursor.execute("UPDATE users SET balance_wl = balance_wl - ? WHERE growid = ?", (total_price, growid[0]))
            cursor.execute("INSERT OR REPLACE INTO purchases (user_id, product, quantity) VALUES (?, ?, COALESCE((SELECT quantity FROM purchases WHERE user_id = ? AND product = ?), 0) + ?)", 
                           (user.id, product_code, user.id, product_code, quantity))
            conn.commit()
            conn.close()

            await log_purchase(bot, user, product_code, quantity)
            await log_history(bot, user, product_code, quantity)

            return f"Successfully purchased {quantity} of product with code {product_code} for {total_price} WL."
        else:
            return "No GrowID found for your account."
    except Exception as e:
        logging.error(f'Error in process_purchase: {e}')
        return f"An error occurred: {e}"

async def log_purchase(bot, user, product_code, quantity):
    channel = bot.get_channel(ID_LOG_PURCH)
    if channel:
        file = File(f'{product_code}.txt')
        await channel.send(content=f"{user.mention} purchased {quantity} of product with code {product_code}.", file=file)

async def log_history(bot, user, product_code, quantity):
    channel = bot.get_channel(ID_HISTORY_BUY)
    if channel:
        await channel.send(content=f"{user.mention} purchased {quantity} of product with code {product_code}.")