import discord
from discord.ext import tasks, commands
from discord.ui import Button, View, Modal, TextInput
import sqlite3
import logging
from datetime import datetime
from main import LIVE_STOCK_CHANNEL_ID  # Import the config value from main
from ext.balance_manager import get_balance  # Import functions from balance_manager
from database import get_connection  # Import the get_connection function from database
from ext.trx import process_purchase  # Import process_purchase function

DATABASE = 'store.db'

class LiveStock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_id = None  # Store the ID of the live stock message

    def db_connect(self):
        return get_connection()

    @tasks.loop(minutes=1)
    async def live_stock(self):
        channel = self.bot.get_channel(LIVE_STOCK_CHANNEL_ID)
        if not channel:
            logging.error('Live stock channel not found')
            return

        conn = self.db_connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name, code, stock, price FROM products")
        products = cursor.fetchall()
        conn.close()

        embed = discord.Embed(title="Current Stock", color=discord.Color.blue())
        if products:
            for name, code, stock, price in products:
                embed.add_field(
                    name=f"🔸 {name} 🔸",
                    value=f"- Code: {code}\n- Stock: {stock}\n- Price: {price}",
                    inline=False
                )
        else:
            embed.description = "No products available."

        last_update = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        embed.set_footer(text=f"Last Update: {last_update}")

        # Buat tombol
        button_balance = Button(label="Check Balance", style=discord.ButtonStyle.secondary)
        button_buy = Button(label="Buy", style=discord.ButtonStyle.primary)
        button_set_growid = Button(label="Set GrowID", style=discord.ButtonStyle.success)
        button_check_growid = Button(label="Check GrowID", style=discord.ButtonStyle.secondary)  # Tambahkan tombol baru
        button_world = Button(label="World Info", style=discord.ButtonStyle.secondary)  # Tambahkan tombol baru untuk world info

        async def button_balance_callback(interaction):
            conn = self.db_connect()
            cursor = conn.cursor()
            cursor.execute("SELECT growid FROM user_growid WHERE user_id = ?", (interaction.user.id,))
            growid = cursor.fetchone()
            conn.close()
            if growid:
                balance = get_balance(growid[0])
                if balance:
                    balance_wl, balance_dl, balance_bgl = balance
                    await interaction.response.send_message(f"Your balance is: {balance_wl} WL, {balance_dl} DL, {balance_bgl} BGL", ephemeral=True)
                else:
                    logging.warning(f"No balance found for GrowID {growid[0]}")
                    await interaction.response.send_message("No balance found for your account.", ephemeral=True)
            else:
                logging.warning(f"No GrowID found for user ID {interaction.user.id}")
                await interaction.response.send_message("No GrowID found for your account.", ephemeral=True)

        async def button_buy_callback(interaction):
            modal = BuyModal(self.bot)
            await interaction.response.send_modal(modal)

        async def button_set_growid_callback(interaction):
            modal = SetGrowIDModal(self.bot)
            await interaction.response.send_modal(modal)

        async def button_check_growid_callback(interaction):  # Tambahkan callback baru
            conn = self.db_connect()
            cursor = conn.cursor()
            cursor.execute("SELECT growid FROM user_growid WHERE user_id = ?", (interaction.user.id,))
            growid = cursor.fetchone()
            conn.close()
            if growid:
                await interaction.response.send_message(f"Your GrowID is: {growid[0]}", ephemeral=True)
            else:
                logging.warning(f"No GrowID found for user ID {interaction.user.id}")
                await interaction.response.send_message("No GrowID found for your account.", ephemeral=True)

        async def button_world_callback(interaction):  # Tambahkan callback baru untuk world info
            conn = self.db_connect()
            cursor = conn.cursor()
            cursor.execute("SELECT world, owner, bot FROM world_info WHERE id = 1")
            world_info = cursor.fetchone()
            conn.close()
            if world_info:
                world, owner, bot = world_info
                await interaction.response.send_message(f"World: {world}\nOwner: {owner}\nBot: {bot}", ephemeral=True)
            else:
                logging.warning("No world info set")
                await interaction.response.send_message("No world info set.", ephemeral=True)

        button_balance.callback = button_balance_callback
        button_buy.callback = button_buy_callback
        button_set_growid.callback = button_set_growid_callback
        button_check_growid.callback = button_check_growid_callback  # Tambahkan callback ke tombol
        button_world.callback = button_world_callback  # Tambahkan callback ke tombol world info
        view = View()
        view.add_item(button_balance)
        view.add_item(button_buy)
        view.add_item(button_set_growid)
        view.add_item(button_check_growid)  # Tambahkan tombol ke view
        view.add_item(button_world)  # Tambahkan tombol ke view

        if self.message_id:
            try:
                message = await channel.fetch_message(self.message_id)
                await message.edit(embed=embed, view=view)
            except discord.NotFound:
                # If the message is not found, send a new message
                message = await channel.send(embed=embed, view=view)
                self.message_id = message.id
        else:
            message = await channel.send(embed=embed, view=view)
            self.message_id = message.id

    @live_stock.before_loop
    async def before_live_stock(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        self.live_stock.start()  # Start the task when the bot is ready

class SetGrowIDModal(Modal):
    def __init__(self, bot):
        super().__init__(title="Set GrowID")
        self.bot = bot
        self.add_item(TextInput(label="GrowID", placeholder="Enter your GrowID here"))

    async def on_submit(self, interaction):
        growid = self.children[0].value
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO user_growid (user_id, growid) VALUES (?, ?)", (interaction.user.id, growid))
            conn.commit()
            conn.close()
            await interaction.response.send_message(f"GrowID {growid} has been set for user {interaction.user.name}.", ephemeral=True)
        except Exception as e:
            logging.error(f'Error in setgrowid: {e}')
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

class BuyModal(Modal):
    def __init__(self, bot):
        super().__init__(title="Buy Product")
        self.bot = bot
        self.add_item(TextInput(label="Product Code", placeholder="Enter the product code"))
        self.add_item(TextInput(label="Quantity", placeholder="Enter the quantity", style=discord.TextStyle.short))

    async def on_submit(self, interaction):
        product_code = self.children[0].value
        quantity = int(self.children[1].value)
        result = await process_purchase(self.bot, interaction.user, product_code, quantity)
        await interaction.response.send_message(result, ephemeral=True)

async def setup(bot):
    await bot.add_cog(LiveStock(bot))