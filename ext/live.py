import discord
from discord.ext import commands, tasks
from discord.ui import Button, Modal, TextInput
import logging
from datetime import datetime
from database import get_connection, get_balance
import json

# Load config
with open('config.json') as config_file:
    config = json.load(config_file)

LIVE_STOCK_CHANNEL_ID = int(config['id_live_stock'])

class BuyModal(Modal):
    def __init__(self, bot):
        super().__init__(title="Buy Product")
        self.bot = bot
        
        self.product_code = TextInput(
            label="Product Code",
            placeholder="Enter product code",
            required=True
        )
        
        self.quantity = TextInput(
            label="Quantity",
            placeholder="Enter quantity",
            required=True
        )
        
        self.add_item(self.product_code)
        self.add_item(self.quantity)
    
    async def on_submit(self, interaction):
        try:
            quantity = int(self.quantity.value)
            if quantity <= 0:
                await interaction.response.send_message("Quantity must be positive.", ephemeral=True)
                return
                
            from ext.trx import process_purchase
            result = await process_purchase(self.bot, interaction.user, self.product_code.value, quantity)
            await interaction.response.send_message(result, ephemeral=True)
            
        except ValueError:
            await interaction.response.send_message("Invalid quantity.", ephemeral=True)

class SetGrowIDModal(Modal):
    def __init__(self, bot):
        super().__init__(title="Set GrowID")
        self.bot = bot
        
        self.growid = TextInput(
            label="GrowID",
            placeholder="Enter your GrowID",
            required=True
        )
        
        self.add_item(self.growid)
    
    async def on_submit(self, interaction):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO user_growid (user_id, growid) VALUES (?, ?)",
                         (interaction.user.id, self.growid.value))
            cursor.execute("INSERT OR IGNORE INTO users (growid) VALUES (?)",
                         (self.growid.value,))
            conn.commit()
            conn.close()
            await interaction.response.send_message(f"GrowID set to: {self.growid.value}", ephemeral=True)
        except Exception as e:
            logging.error(f'Error in SetGrowIDModal: {e}')
            await interaction.response.send_message("An error occurred while setting GrowID.", ephemeral=True)

class LiveStock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_id = None
        self.live_stock.start()

    def db_connect(self):
        return get_connection()

    def cog_unload(self):
        self.live_stock.cancel()

    @tasks.loop(minutes=1)
    async def live_stock(self):
        channel = self.bot.get_channel(LIVE_STOCK_CHANNEL_ID)
        if not channel:
            logging.error('Live stock channel not found')
            return

        conn = self.db_connect()
        cursor = conn.cursor()
        
        # Get stock information with available items count
        cursor.execute("""
            SELECT 
                p.name, 
                p.code, 
                COUNT(CASE WHEN ps.used = 0 THEN 1 END) as available_stock,
                p.price,
                p.description
            FROM products p
            LEFT JOIN product_stock ps ON p.code = ps.product_code
            GROUP BY p.code
            ORDER BY p.name
        """)
        products = cursor.fetchall()
        
        # Get world info
        cursor.execute("SELECT world, owner, bot FROM world_info WHERE id = 1")
        world_info = cursor.fetchone()
        
        conn.close()

        embed = discord.Embed(
            title="🏪 Store Stock Status",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )

        if world_info:
            world, owner, bot_name = world_info
            embed.add_field(
                name="🌍 World Information",
                value=f"World: `{world}`\nOwner: `{owner}`\nBot: `{bot_name}`",
                inline=False
            )

        if products:
            for name, code, stock, price, description in products:
                value = (
                    f"💎 Code: `{code}`\n"
                    f"📦 Stock: `{stock}`\n"
                    f"💰 Price: `{price} WL`\n"
                )
                if description:
                    value += f"📝 Info: {description}\n"
                
                embed.add_field(
                    name=f"🔸 {name} 🔸",
                    value=value,
                    inline=False
                )
        else:
            embed.description = "No products available."

        embed.set_footer(text=f"Last Update: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")

        # Create view with buttons
        view = discord.ui.View()
        
        # Add buttons
        button_balance = Button(label="Check Balance", style=discord.ButtonStyle.secondary, emoji="💰")
        button_buy = Button(label="Buy", style=discord.ButtonStyle.primary, emoji="🛒")
        button_set_growid = Button(label="Set GrowID", style=discord.ButtonStyle.success, emoji="📝")
        button_check_growid = Button(label="Check GrowID", style=discord.ButtonStyle.secondary, emoji="🔍")
        button_world = Button(label="World Info", style=discord.ButtonStyle.secondary, emoji="🌍")

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
                    embed = discord.Embed(
                        title="💰 Your Balance",
                        color=discord.Color.green(),
                        timestamp=datetime.utcnow()
                    )
                    embed.add_field(name="GrowID", value=growid[0], inline=False)
                    embed.add_field(name="World Locks", value=f"{balance_wl:,} WL", inline=True)
                    embed.add_field(name="Diamond Locks", value=f"{balance_dl:,} DL", inline=True)
                    embed.add_field(name="Blue Gem Locks", value=f"{balance_bgl:,} BGL", inline=True)
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message("❌ No balance found for your account.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ No GrowID found for your account.", ephemeral=True)

        async def button_buy_callback(interaction):
            modal = BuyModal(self.bot)
            await interaction.response.send_modal(modal)

        async def button_set_growid_callback(interaction):
            modal = SetGrowIDModal(self.bot)
            await interaction.response.send_modal(modal)

        async def button_check_growid_callback(interaction):
            conn = self.db_connect()
            cursor = conn.cursor()
            cursor.execute("SELECT growid FROM user_growid WHERE user_id = ?", (interaction.user.id,))
            growid = cursor.fetchone()
            conn.close()
            
            if growid:
                embed = discord.Embed(
                    title="🔍 GrowID Information",
                    description=f"Your registered GrowID: `{growid[0]}`",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("❌ No GrowID registered for your account.", ephemeral=True)

        async def button_world_callback(interaction):
            conn = self.db_connect()
            cursor = conn.cursor()
            cursor.execute("SELECT world, owner, bot FROM world_info WHERE id = 1")
            world_info = cursor.fetchone()
            conn.close()
            
            if world_info:
                world, owner, bot_name = world_info
                embed = discord.Embed(
                    title="🌍 World Information",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="World", value=world, inline=True)
                embed.add_field(name="Owner", value=owner, inline=True)
                embed.add_field(name="Bot", value=bot_name, inline=True)
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("❌ No world information available.", ephemeral=True)

        # Set button callbacks
        button_balance.callback = button_balance_callback
        button_buy.callback = button_buy_callback
        button_set_growid.callback = button_set_growid_callback
        button_check_growid.callback = button_check_growid_callback
        button_world.callback = button_world_callback

        # Add buttons to view
        view.add_item(button_balance)
        view.add_item(button_buy)
        view.add_item(button_set_growid)
        view.add_item(button_check_growid)
        view.add_item(button_world)

        # Update or send message
        try:
            if self.message_id:
                try:
                    message = await channel.fetch_message(self.message_id)
                    await message.edit(embed=embed, view=view)
                except discord.NotFound:
                    message = await channel.send(embed=embed, view=view)
                    self.message_id = message.id
            else:
                message = await channel.send(embed=embed, view=view)
                self.message_id = message.id
        except Exception as e:
            logging.error(f'Error updating live stock message: {e}')

    @live_stock.before_loop
    async def before_live_stock(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(LiveStock(bot))