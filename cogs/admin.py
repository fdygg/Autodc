import discord
from discord.ext import commands
import logging
import datetime
from main import is_admin  # Import is_admin function from main.py
from database import get_connection, add_balance, subtract_balance

DATABASE = 'store.db'

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_time = datetime.datetime.utcnow()

    def db_connect(self):
        return get_connection()

    @commands.command()
    @is_admin()
    async def addProduct(self, ctx, name: str, code: str, price: int, description: str = ""):
        logging.info(f'addProduct command invoked by {ctx.author}')
        try:
            conn = self.db_connect()
            if conn is None:
                await ctx.send("Database connection failed.")
                return
            cursor = conn.cursor()
            cursor.execute("INSERT INTO products (name, code, price, stock, description) VALUES (?, ?, ?, 0, ?)", 
                         (name, code, price, description))
            conn.commit()
            conn.close()
            await ctx.send(f"Product {name} with code {code} added with price {price}.")
        except Exception as e:
            logging.error(f'Error in addProduct: {e}')
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    @is_admin()
    async def addStock(self, ctx, product_code: str, *, file_path: str = None):
        """
        Menambahkan stock dari file
        Usage: !addStock <kode_produk> [file_path]
        """
        logging.info(f'addStock command invoked by {ctx.author} at {self.current_time}')
        try:
            # Handle file path
            if file_path is None:
                if len(ctx.message.attachments) > 0:
                    attachment = ctx.message.attachments[0]
                    await attachment.save(attachment.filename)
                    file_path = attachment.filename
                else:
                    file_path = f'{product_code}.txt'

            # Membaca dan memproses file
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                valid_lines = [line.strip() for line in lines if line.strip()]
                count = len(valid_lines)

                if count == 0:
                    await ctx.send("❌ File is empty or contains no valid content.")
                    return

                conn = self.db_connect()
                if conn is None:
                    await ctx.send("Database connection failed.")
                    return

                cursor = conn.cursor()

                # Create product_stock table if not exists
                cursor.execute("""
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
                """)

                # Verify product exists
                cursor.execute("SELECT code FROM products WHERE code = ?", (product_code,))
                if not cursor.fetchone():
                    await ctx.send(f"❌ Product with code {product_code} does not exist.")
                    conn.close()
                    return

                # Update stock count
                cursor.execute("UPDATE products SET stock = stock + ? WHERE code = ?", 
                             (count, product_code))

                # Insert stock items
                for content in valid_lines:
                    cursor.execute("""
                        INSERT INTO product_stock (
                            product_code, content, added_by, source_file
                        ) VALUES (?, ?, ?, ?)
                    """, (product_code, content, str(ctx.author), file_path))

                conn.commit()
                conn.close()

                # Send confirmation
                embed = discord.Embed(
                    title="Stock Added Successfully",
                    color=discord.Color.green(),
                    timestamp=self.current_time
                )
                embed.add_field(name="Product Code", value=product_code, inline=True)
                embed.add_field(name="Items Added", value=str(count), inline=True)
                embed.add_field(name="Source File", value=file_path, inline=True)
                embed.set_footer(text=f"Added by {ctx.author}")

                await ctx.send(embed=embed)

        except FileNotFoundError:
            logging.error(f'File not found: {file_path}')
            await ctx.send(f"❌ File not found: {file_path}")
        except Exception as e:
            logging.error(f'Error in addStock: {e}')
            await ctx.send(f"❌ An error occurred: {e}")

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
            cursor.execute("DELETE FROM product_stock WHERE product_code = ?", (code,))  # Delete related stock
            conn.commit()
            conn.close()
            await ctx.send(f"Product with code {code} and its stock deleted.")
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

            cursor.execute("INSERT OR REPLACE INTO world_info (id, world, owner, bot) VALUES (1, ?, ?, ?)", 
                         (world, owner, bot_name))
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

            # Get available stock items
            cursor.execute("""
                SELECT id, content 
                FROM product_stock 
                WHERE product_code = ? AND used = 0 
                LIMIT ?
            """, (code, count))
            
            items = cursor.fetchall()
            if not items or len(items) < count:
                await ctx.send("Not enough stock available.")
                conn.close()
                return

            # Update stock status
            current_time = self.current_time.strftime('%Y-%m-%d %H:%M:%S')
            for item_id, _ in items:
                cursor.execute("""
                    UPDATE product_stock 
                    SET used = 1, used_by = ?, used_at = ? 
                    WHERE id = ?
                """, (str(user), current_time, item_id))

            # Update product stock count
            cursor.execute("UPDATE products SET stock = stock - ? WHERE code = ?", (count, code))
            
            # Update user products
            cursor.execute("""
                INSERT OR REPLACE INTO user_products (user_id, product, count) 
                VALUES (?, ?, COALESCE((SELECT count FROM user_products WHERE user_id = ? AND product = ?), 0) + ?)
            """, (user.id, code, user.id, code, count))

            conn.commit()
            conn.close()

            # Send items to user
            try:
                content_message = f"You received {count} items of {code}:\n\n"
                for i, (_, content) in enumerate(items, 1):
                    content_message += f"{i}. {content}\n"

                if len(content_message) > 1900:
                    parts = [content_message[i:i+1900] for i in range(0, len(content_message), 1900)]
                    for part in parts:
                        await user.send(part)
                else:
                    await user.send(content_message)
                
                await ctx.send(f"✅ Successfully sent {count} of product with code {code} to {user.name}.")
            except discord.Forbidden:
                await ctx.send("❌ Could not send DM to user. Items were sent but user needs to enable DMs.")

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

    @commands.command()
    @is_admin()
    async def checkStock(self, ctx, product_code: str):
        logging.info(f'checkStock command invoked by {ctx.author}')
        try:
            conn = self.db_connect()
            if conn is None:
                await ctx.send("Database connection failed.")
                return
                
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN used = 0 THEN 1 END) as available,
                    COUNT(CASE WHEN used = 1 THEN 1 END) as used,
                    COUNT(*) as total,
                    MAX(added_at) as last_added,
                    MAX(used_at) as last_used
                FROM product_stock 
                WHERE product_code = ?
            """, (product_code,))
            
            stats = cursor.fetchone()
            if stats:
                available, used, total, last_added, last_used = stats
                
                embed = discord.Embed(
                    title=f"Stock Status: {product_code}",
                    color=discord.Color.blue(),
                    timestamp=self.current_time
                )
                
                embed.add_field(name="Available", value=f"`{available}`", inline=True)
                embed.add_field(name="Used", value=f"`{used}`", inline=True)
                embed.add_field(name="Total", value=f"`{total}`", inline=True)
                
                if last_added:
                    embed.add_field(name="Last Added", value=last_added, inline=False)
                if last_used:
                    embed.add_field(name="Last Used", value=last_used, inline=False)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No stock information found for product {product_code}")
            
            conn.close()
            
        except Exception as e:
            logging.error(f'Error in checkStock: {e}')
            await ctx.send(f"An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))