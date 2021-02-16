import os
import globals
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

harvester.scraper()
