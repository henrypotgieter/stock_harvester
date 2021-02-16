import os
import globals
import discord
from sqlinterface import Sqlconn
from functions import Functions
from discord.ext import commands
from dotenv import load_dotenv

'''
Youtube Comment Harvester bot
'''
# Get environment variables
load_dotenv('.env')
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
globals.CONTROL_CHANNEL = os.getenv('CONTROL_CHANNEL')

# Instantiate functions class
harvester = Functions()

# Populate vars from db
sql_conn = Sqlconn()

# Populate data from DB into memory
globals.symbol_ignore = sql_conn.symbol_ignore_read()
globals.common_words = sql_conn.common_words_read()
globals.channels = sql_conn.channels_read()
globals.symbols = sql_conn.symbols_read()
globals.current_results = sql_conn.curr_data_read()

intents = discord.Intents.default()
intents.members = True
# Instantiate the BOT
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

extensions = ['cogs.botcommands']
if __name__ == "__main__":
    #globals.initialize()
    for extension in extensions:
        try:
            bot.load_extension(extension)
            extension = extension.replace("cogs.", "")
            print(f"Loaded extension '{extension}'")
        except Exception as e:
            exception = f"{type(e).__name__}: {e}"
            extension = extension.replace("cogs.", "")
            print(f"Failed to load extension {extension}\n{exception}")

bot.run(TOKEN)
