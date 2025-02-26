import discord
from discord.ext import commands
import logging
from main import is_admin  # Import is_admin function from main.py
from database import get_connection

DATABASE = 'store.db'

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def db_connect(self):
        return get_connection()

    @commands.command()
    @is_admin()
    async def addProduct(self, ctx, name: str, code: str, price: int, description: str):
        logging.info(f'addProduct command invoked by {ctx.author}')
        try:
            conn = self.db_connect()
            if conn is None:
                await ctx.send("Database connection failed.")
                return
            cursor = conn.cursor()
            cursor.execute("INSERT INTO products (name, code, price, stock, description) VALUES (?, ?, ?, 0, ?)", (name, code, price, description))
            conn.commit()
            conn.close()
            await ctx.send(f"Product {name} with code {code} added with price {price}.")
        except Exception as e:
            logging.error(f'Error in addProduct: {e}')
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    @is_admin()
    async def addStock(self, ctx, product_code: str):
        logging.info(f'addStock command invoked by {ctx.author}')
        try:
            with open(f'{product_code}.txt', 'r') as file:
                count = int(file.read().strip())
                conn = self.db_connect()
                if conn is None:
                    await ctx.send("Database connection failed.")
                    return
                cursor = conn.cursor()
                cursor.execute("UPDATE products SET stock = stock + ? WHERE code = ?", (count, product_code))
                conn.commit()
                conn.close()
                await ctx.send(f"Added {count} to stock of product with code {product_code}.")
        except Exception as e:
            logging.error(f'Error in addStock: {e}')
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    @is_admin()
    async def deleteProduct(self, ctx, code: str):
        logging.info(f'deleteProduct command invoked by {ctx.author}')
        try:
            conn = self.db_connect()
            if conn is None:
                await ctx.send("Database connection failed.")
                return
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE code = ?", (code,))
            conn.commit()
            conn.close()
            await ctx.send(f"Product with code {code} deleted.")
        except Exception as e:
            logging.error(f'Error in deleteProduct: {e}')
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    @is_admin()
    async def changePrice(self, ctx, code: str, new_price: int):
        logging.info(f'changePrice command invoked by {ctx.author}')
        try:
            conn = self.db_connect()
            if conn is None:
                await ctx.send("Database connection failed.")
                return
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET price = ? WHERE code = ?", (new_price, code))
            conn.commit()
            conn.close()
            await ctx.send(f"Price of product with code {code} changed to {new_price}.")
        except Exception as e:
            logging.error(f'Error in changePrice: {e}')
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    @is_admin()
    async def setDescription(self, ctx, code: str, *, description: str):
        logging.info(f'setDescription command invoked by {ctx.author}')
        try:
            conn = self.db_connect()
            if conn is None:
                await ctx.send("Database connection failed.")
                return
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET description = ? WHERE code = ?", (description, code))
            conn.commit()
            conn.close()
            await ctx.send(f"Description of product with code {code} set.")
        except Exception as e:
            logging.error(f'Error in setDescription: {e}')
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    @is_admin()
    async def setWorld(self, ctx, world: str, owner: str, bot_name: str):
        logging.info(f'setWorld command invoked by {ctx.author}')
        try:
            conn = self.db_connect()
            if conn is None:
                await ctx.send("Database connection failed.")
                return
            cursor = conn.cursor()
            cursor.execute("SELECT world, owner, bot FROM world_info WHERE id = 1")
            existing_world_info = cursor.fetchone()
            
            if existing_world_info:
                if existing_world_info == (world, owner, bot_name):
                    await ctx.send(f"World info is already set to {world} with owner {owner} and bot {bot_name}.")
                    conn.close()
                    return

            cursor.execute("INSERT OR REPLACE INTO world_info (id, world, owner, bot) VALUES (1, ?, ?, ?)", (world, owner, bot_name))
            conn.commit()
            conn.close()
            await ctx.send(f"World set to {world} with owner {owner} and bot {bot_name}.")
        except Exception as e:
            logging.error(f'Error in setWorld: {e}')
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    @is_admin()
    async def send(self, ctx, user: discord.User, code: str, count: int):
        logging.info(f'send command invoked by {ctx.author}')
        try:
            conn = self.db_connect()
            if conn is None:
                await ctx.send("Database connection failed.")
                return
            cursor = conn.cursor()

            cursor.execute("SELECT stock FROM products WHERE code = ?", (code,))
            stock = cursor.fetchone()
            if not stock or stock[0] < count:
                await ctx.send("Not enough stock.")
                conn.close()
                return

            cursor.execute("UPDATE products SET stock = stock - ? WHERE code = ?", (count, code))
            cursor.execute("INSERT OR REPLACE INTO user_products (user_id, product, count) VALUES (?, ?, COALESCE((SELECT count FROM user_products WHERE user_id = ? AND product = ?), 0) + ?)", (user.id, code, user.id, code, count))
            conn.commit()
            conn.close()
            await ctx.send(f"Successfully sent {count} of product with code {code} to {user.name}.")
        except Exception as e:
            logging.error(f'Error in send: {e}')
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    @is_admin()
    async def addBal(self, ctx, growid: str, wl: int = 0, dl: int = 0, bgl: int = 0):
        logging.info(f'addBal command invoked by {ctx.author}')
        try:
            add_balance(growid, wl, dl, bgl)
            await ctx.send(f"Added {wl} WL, {dl} DL, {bgl} BGL to {growid}'s balance.")
        except Exception as e:
            logging.error(f'Error in addBal: {e}')
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    @is_admin()
    async def reduceBal(self, ctx, growid: str, wl: int = 0, dl: int = 0, bgl: int = 0):
        logging.info(f'reduceBal command invoked by {ctx.author}')
        try:
            subtract_balance(growid, wl, dl, bgl)
            await ctx.send(f"Reduced {wl} WL, {dl} DL, {bgl} BGL from {growid}'s balance.")
        except Exception as e:
            logging.error(f'Error in reduceBal: {e}')
            await ctx.send(f"An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
