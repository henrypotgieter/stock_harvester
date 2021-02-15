import re
import discord
import globals
from tabulate import tabulate
from discord.ext import commands
from functions import Functions

# Instantiate functions
harvester = Functions()


class botcommands(commands.Cog, name="General Commands"):
    bot = commands.Bot(command_prefix='!')

    def __init__(self, bot):
        self.bot = bot

    # Verify if the message is from a channel
    async def valid_channel(self, context):
        if hasattr(context.channel, 'name'):
            return True
        return False

    # Verify if the message is from a channel, and if it is the valid control channel
    async def valid_command_channel(self, context):
        if hasattr(context.channel, 'name'):
            if context.channel.name == globals.CONTROL_CHANNEL:
                return True
        return False

    @bot.command(name='scrape', help='Scrape channels and update stock ticker mentions')
    async def scrape_channels(self, context):
        if await self.valid_channel(context):
            await context.send("Scraping channels.. this will take some time!")
            harvester.scraper()
            await context.send("Done!")

    @bot.command(name='channellist', help='List channels being monitored')
    async def channellist(self, context):
        if await self.valid_command_channel(context):
            channel_list = "#--------------------\n"
            for channel in globals.channels:
                channel_list += channel+"\n"
            await context.send('```' + channel_list + '```')

    @bot.command(name='channeladd', help='Add channel to channel list.')
    async def channeladd(self, context, name = ''):
        if await self.valid_command_channel(context):
            # Check if we got input
            if len(name) == 0:
                await context.send('No input provided, please specify a channel')
                return

            for channel in globals.channels:
                if name == channel:
                    await context.send('Channel already present, unable to add')
                    return
            matched = re.search("[.'_\-A-Za-z0-9]{6,24}", name).group()
            if matched == name:
                harvester.add_channel(name)
                await context.send('Channel ' + name + ' has been added to the list.')
            else:
                await context.send('Channel name is not valid.')

    @bot.command(name='channeldel', help='Delete channel to channel list.')
    async def channeldel(self, context, name = ''):
        if await self.valid_command_channel(context):
            # Check if we got input
            if len(name) == 0:
                await context.send('No input provided, please specify a channel')
                return

            # Validate the input meets requirements
            matched = re.search("[-A-Za-z0-9]{1,6}", name).group()
            if not matched == name:
                await context.send('Input does appear valid')
                return

            if await self.valid_command_channel(context):
                for channel in globals.channels:
                    if name == channel:
                        harvester.del_channel(name)
                        await context.send('Channel ' + name + ' has been removed.')
                        return
                matched = re.search("[.'_\-A-Za-z0-9]{6,24}", name).group()
                if matched == name:
                    await context.send('Channel ' + name + ' is not on the list.')
                else:
                    await context.send('Channel name invalid.')

    @bot.command(name='ignorelist', help='Show ignored stock symbols')
    async def ignorelist(self, context):
        if await self.valid_command_channel(context):
            if len(globals.symbol_ignore) == 0:
                await context.send("Ignore list is currently empty.")
            else:
                ignore_list = "Ignore List:\n============\n"
                for symbol in globals.symbol_ignore:
                    ignore_list += symbol + "\n"
                await context.send(ignore_list)

    @bot.command(name='ignoreadd', help='Add symbol to ignore list.')
    async def ignoreadd(self, context, name = ''):
        if await self.valid_command_channel(context):
            # Check if we got input
            if len(name) == 0:
                await context.send('No input provided, please specify a ticker')
                return

            # Validate the input meets requirements
            matched = re.search("[-A-Za-z0-9]{1,6}", name).group()
            if not matched == name:
                await context.send('Input does appear valid')
                return

            if await self.valid_command_channel(context):
                if name in globals.symbol_ignore:
                    await context.send('Symbol ' + name + ' already on ignore list.')
                if name in globals.symbols:
                    added = harvester.add_ignore(name)
                    await context.send('Symbol ' + name + ' added to ignore list.')
                else:
                    await context.send('Invalid stock ticker symbol, try again')

    @bot.command(name='ignoredel', help='Remove symbol from ignore list.')
    async def ignoredel(self, context, name = ''):
        if await self.valid_command_channel(context):
            # Check if we got input
            if len(name) == 0:
                await context.send('No input provided, please specify a ticker')
                return

            # Validate the input meets requirements
            matched = re.search("[-A-Za-z0-9]{1,6}", name).group()
            if not matched == name:
                await context.send('Input does appear valid')
                return

            if await self.valid_command_channel(context):
                was_valid = False
                if globals.symbols.index(name):
                    # for symbol in symbols:
                    # if name == symbol:
                    was_valid = True
                    added = harvester.del_ignore(name)
                    if added == True:
                        await context.send('Symbol ' + name + ' removed from ignore list.')
                if was_valid == False:
                    await context.send('Invalid stock ticker symbol, try again')

    @bot.command(name='context', help='Show the comments context, help check for false positives.  Takes symbol ticker as argument.')
    async def context(self, context, name = ''):
        if await self.valid_channel(context):
            if hasattr(context.channel, 'name'):
                # Set some vars
                con_len = 20
                was_valid = False

                # Check if we got input
                if len(name) == 0:
                    await context.send('No input provided, please specify a ticker')
                    return

                # Validate the input meets requirements
                matched = re.search("[-A-Za-z0-9]{1,6}", name).group()
                if not matched == name:
                    await context.send('Input does appear valid')
                    return

                # Convert name to uppercase
                name = name.upper()

                # Check if the name provided is present in the global symbols var
                if name in globals.symbols:
                    print(name)
                    was_valid = True
                    context_data = harvester.get_context(name)
                    print(context_data)
                    big_string = "----------\n"
                    iterations = len(context_data[0:20])
                    for i in context_data[0:20]:
                        iterations -= 1
                        location = i[1].find(name)
                        if location < con_len:
                            con_len = location
                        if len(i[1]) < 40:
                            if iterations <= 0:
                                big_string += i[1]
                            else:
                                big_string += i[1] + "\n---------\n"
                        if len(i[1][location-con_len:location+con_len+len(name)]) >= 0:
                            if iterations <= 0:
                                big_string += i[1][location -
                                                    con_len:location+con_len+len(name)]
                            else:
                                big_string += i[1][location-con_len:location +
                                                    con_len+len(name)] + "\n---------\n"
                        con_len = 20
                    await context.send('```' + big_string + '```')
                if was_valid == False:
                    await context.send('Invalid stock ticker symbol, try again')

    @bot.command(name='table', help='Display results table')
    async def table(self, context):
        if await self.valid_channel(context):
            if hasattr(context.channel, 'name'):
                table = []
                for result in globals.current_results:
                    if not harvester.is_ignored(result):
                        table.append((result))
                await context.send('```\n' + tabulate(table[0:20]) + '```')


def setup(bot):
    bot.add_cog(botcommands(bot))
