import discord
from discord.ext import commands
import os
import json
import logging
import asyncio
from database import init_db

# Setup logging
logging.basicConfig(level=logging.INFO)

# Load config
with open('config.json') as config_file:
    config = json.load(config_file)

TOKEN = config['token']
GUILD_ID = config['guild_id']
ADMIN_ID = int(config['admin_id'])  # Make sure to convert admin_id to integer
LIVE_STOCK_CHANNEL_ID = int(config['id_live_stock'])
LOG_PURCHASE_CHANNEL_ID = int(config['id_log_purch'])
DONATION_LOG_CHANNEL_ID = int(config['id_donation_log'])

intents = discord.Intents.default()
intents.messages = True  # Enable message intents to listen to messages
intents.message_content = True  # Enable reading of message content
bot = commands.Bot(command_prefix='!', intents=intents)

def is_admin():
    async def predicate(ctx):
        logging.info(f'Checking admin for {ctx.author.id}')
        return ctx.author.id == ADMIN_ID
    return commands.check(predicate)

@bot.event
async def on_ready():
    logging.info(f'Bot {bot.user.name} sudah online!')

@bot.event
async def on_message(message):
    logging.info(f'Message from {message.author}: {message.content}')
    await bot.process_commands(message)

async def main():
    init_db()
    
    # Load Cogs from cogs folder
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            logging.info(f'Loading cog: {filename}')
            await bot.load_extension(f'cogs.{filename[:-3]}')

    # Load Cogs from ext folder
    for filename in os.listdir('./ext'):
        if filename.endswith('.py') and filename != 'balance_manager.py':
            logging.info(f'Loading ext: {filename}')
            await bot.load_extension(f'ext.{filename[:-3]}')
# Muat semua ekstensi (cogs)
async def load_extensions():
    for filename in os.listdir('./ext'):
        if filename.endswith('.py') and filename != 'trx.py':
            await bot.load_extension(f'ext.{filename[:-3]}')
            
    await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())