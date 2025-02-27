import sqlite3
import json
import logging
from discord import File, Embed
from discord.ext import commands
from database import get_connection
import datetime
from datetime import datetime, timezone

# Baca konfigurasi dari config.json
with open('config.json') as config_file:
    config = json.load(config_file)

ID_LOG_PURCH = config['id_log_purch']  # Channel ID untuk log pembelian
ID_HISTORY_BUY = config['id_history_buy']  # Channel ID untuk riwayat pembelian

DATABASE = 'store.db'

async def process_purchase(bot, user, product_code, quantity):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Get current UTC time
        current_time = datetime.now(timezone.utc)
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

        # Get last order number
        cursor.execute("SELECT COUNT(*) FROM purchases")
        order_count = cursor.fetchone()[0] + 1

        # Cek produk dan harga
        cursor.execute("SELECT stock, price FROM products WHERE code = ?", (product_code,))
        product_info = cursor.fetchone()
        if not product_info:
            return "Product not found."

        stock, price = product_info
        total_price = price * quantity

        # Cek GrowID dan balance
        cursor.execute("SELECT growid FROM user_growid WHERE user_id = ?", (user.id,))
        growid = cursor.fetchone()
        if growid:
            cursor.execute("SELECT balance_wl FROM users WHERE growid = ?", (growid[0],))
            user_balance = cursor.fetchone()
            if not user_balance or user_balance[0] < total_price:
                return "Insufficient balance."

            # Cek stock yang tersedia
            cursor.execute("""
                SELECT id, content 
                FROM product_stock 
                WHERE product_code = ? AND used = 0 
                LIMIT ?
            """, (product_code, quantity))
            
            items = cursor.fetchall()
            if len(items) < quantity:
                return "Not enough stock available."

            # Update status items
            for item_id, _ in items:
                cursor.execute("""
                    UPDATE product_stock 
                    SET used = 1,
                        used_by = ?,
                        used_at = ?
                    WHERE id = ?
                """, (str(user), formatted_time, item_id))

            # Update stock dan balance
            cursor.execute("UPDATE products SET stock = stock - ? WHERE code = ?", 
                         (quantity, product_code))
            cursor.execute("UPDATE users SET balance_wl = balance_wl - ? WHERE growid = ?", 
                         (total_price, growid[0]))

            # Log ke database purchases
            cursor.execute("""
                INSERT INTO purchases (
                    order_number, user_id, product, quantity, purchase_date, total_price
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (order_count, user.id, product_code, quantity, formatted_time, total_price))

            # Prepare items content
            items_content = "\n".join([f"{i+1}. {item[1]}" for i, item in enumerate(items)])
            
            # Save to result file
            result_filename = f"result ({user.name}).txt"
            with open(result_filename, 'w', encoding='utf-8') as f:
                f.write(f"Current Date and Time (UTC - YYYY-MM-DD HH:MM:SS formatted): {formatted_time}\n")
                f.write(f"Current User's Login: {user.name}\n\n")
                f.write(f"Order #{order_count}\n")
                f.write(f"Product: {product_code}\n")
                f.write(f"Quantity: {quantity}\n")
                f.write(f"Total Price: {total_price} WL\n\n")
                f.write("Items:\n")
                f.write(items_content)

            # Send to log channel
            channel_log = bot.get_channel(ID_LOG_PURCH)
            if channel_log:
                file = File(result_filename)
                await channel_log.send(file=file)

            # Send to history channel
            channel_history = bot.get_channel(ID_HISTORY_BUY)
            if channel_history:
                await channel_history.send(
                    f"<a:Arrow:1152710828395593729>Buyer: **{user.mention}**\n"
                    f"<a:Arrow:1152710828395593729>Produk: **{product_code} ( {growid[0]} // {user.name} )**\n"
                    f"<a:Arrow:1152710828395593729>Jumlah: **{quantity}**\n"
                    f"<a:Arrow:1152710828395593729>Total Price: **{total_price} <:WL:1146360510888034356>**\n"
                    f"**Thanks For Purchasing Our Product**"
                )

            # Send to buyer via DM
            try:
                file_dm = File(result_filename)
                await user.send(
                    content=f"🛍️ Your Purchase (Order #{order_count})\n"
                            f"Time: `{formatted_time}`\n\n"
                            f"Product: **{product_code}**\n"
                            f"Quantity: **{quantity}**\n"
                            f"Total Price: **{total_price} WL**\n\n"
                            f"Your items are in the attached file:",
                    file=file_dm
                )
            except discord.Forbidden:
                logging.warning(f"Could not send DM to {user}")

            # Clean up file
            try:
                os.remove(result_filename)
            except:
                pass

            conn.commit()
            conn.close()
            return f"✅ Successfully purchased {quantity} of {product_code} for {total_price} WL."
        else:
            return "❌ No GrowID found for your account."
    except Exception as e:
        logging.error(f'Error in process_purchase: {e}')
        return f"❌ An error occurred: {e}"

class Trx(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def buy(self, ctx, product_code: str, quantity: int = 1):
        """
        Buy a product
        Usage: !buy <product_code> [quantity]
        """
        logging.info(f'Buy command invoked by {ctx.author}')
        if quantity < 1:
            await ctx.send("❌ Quantity must be at least 1.")
            return

        result = await process_purchase(self.bot, ctx.author, product_code, quantity)
        await ctx.send(result)

    @commands.command()
    async def check(self, ctx):
        """Check your GrowID and balance"""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT growid FROM user_growid WHERE user_id = ?", (ctx.author.id,))
            growid = cursor.fetchone()

            if growid:
                cursor.execute("""
                    SELECT balance_wl, balance_dl, balance_bgl 
                    FROM users 
                    WHERE growid = ?
                """, (growid[0],))
                balance = cursor.fetchone()

                if balance:
                    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    embed = Embed(title="Account Information", color=0x00ff00)
                    embed.add_field(name="GrowID", value=growid[0], inline=True)
                    embed.add_field(name="Balance (WL)", value=str(balance[0]), inline=True)
                    embed.add_field(name="Balance (DL)", value=str(balance[1]), inline=True)
                    embed.add_field(name="Balance (BGL)", value=str(balance[2]), inline=True)
                    embed.set_footer(text=f"Requested by {ctx.author} • {current_time}")
                    
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ No balance found for your GrowID.")
            else:
                await ctx.send("❌ No GrowID registered for your account.")

            conn.close()
        except Exception as e:
            logging.error(f'Error in check command: {e}')
            await ctx.send(f"❌ An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(Trx(bot))