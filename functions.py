import globals
import datetime
import json
import requests
from datetime import timezone
from sqlinterface import Sqlconn

sql_conn = Sqlconn()

''' All the supporting functions, keep the bot.py file clean '''

class Functions(object):
    def add_channel(self, channel_name):
        globals.channels.append(channel_name)
        sql_conn.channel_write(channel_name)

    def del_channel(self, channel_name):
        globals.channels.remove(channel_name)
        sql_conn.channel_del(channel_name)

    def add_ignore(self, symbol_add_ignore):
        print(symbol_add_ignore)
        for symbol in globals.symbols:
            if symbol_add_ignore == symbol:
                sql_conn.symbols_ignore_write(symbol_add_ignore)
                globals.symbol_ignore.append(symbol_add_ignore)
                return True
        return False

    def del_ignore(self, symbol_del_ignore):
        for symbol in globals.symbols:
            if symbol_del_ignore == symbol:
                globals.symbol_ignore.remove(symbol_del_ignore)
                sql_conn.symbols_ignore_remove(symbol_del_ignore)
                return True
        return False

    def pub_after_time(self, time_diff):
        '''Create timestamp to be passed to youtube api'''
        cur_time = datetime.datetime.now()
        utc_time = cur_time.replace(tzinfo = timezone.utc)
        utc_timestamp = utc_time.timestamp()
        final_time = int(utc_timestamp) - int(time_diff)
        return datetime.datetime.fromtimestamp(final_time).isoformat(timespec='seconds') + "Z"

    def too_old(self, time_limit, time_given):
        '''Compare timestamps to see if an entry is too old'''
        time_limit_nonepoch = datetime.datetime.strptime(time_limit, "%Y-%m-%dT%H:%M:%SZ")
        time_given_nonepoch = datetime.datetime.strptime(time_given, "%Y-%m-%dT%H:%M:%SZ")
        time_limit_epoch = (time_limit_nonepoch - datetime.datetime(1970, 1, 1)).total_seconds()
        time_given_epoch = (time_given_nonepoch - datetime.datetime(1970, 1, 1)).total_seconds()
        if time_given_epoch > time_limit_epoch:
            return True
        else:
            return False

    def is_ignored(self, symbol_ignored):
        if symbol_ignored[0] in globals.symbol_ignore:
            return True
        return False

    def scraper(self):
        # Generate empty comments list
        comments = []

        # Build a discoveries dictionary that we populate with symbols
        discoveries = {}
        for symbol in globals.symbols:
            if len(symbol) > 1:
                discoveries[symbol] = 0

        time_pub_after = self.pub_after_time(globals.TIME_SUB)

        # Primary loop to parse data from each channel
        for channel in globals.channels:
            # Build initial pull request and process json
            print(channel)
            you_pull = requests.get(globals.BASE_URL + channel + "&key=" + globals.API_KEY)
            data = you_pull.text
            json_data = json.loads(data)

            # Loop control flags, reset to false every time
            more = False
            dont_bother = False

            if not 'items' in json_data:
                print(data)
                continue
            # Append initial comments
            for item in json_data['items']:
                if self.too_old(item['snippet']['topLevelComment']['snippet']['publishedAt'], time_pub_after):
                    dont_bother = True
                else:
                    comments.append(" " + item['snippet']['topLevelComment']['snippet']['textOriginal'] + " ")

            # Check if there was a next page token, set it and then adjust loop control to True
            if 'nextPageToken' in json_data and dont_bother == False:
                next_page_token = json_data['nextPageToken']
                more = True
                # Loop until there is no more!
                while more:
                    # Grab data request again using page token and published after time
                    you_pull = requests.get(globals.BASE_URL + channel +"&pageToken=" + next_page_token + "&publishedAfter=" + time_pub_after +  "&key=" + globals.API_KEY)
                    data_sub = you_pull.text
                    json_data_sub = json.loads(data_sub)
                    # If no more next page then break the loop
                    if not 'nextPageToken' in json_data_sub:
                        more = False
                    else:
                        next_page_token = json_data_sub['nextPageToken']
                    # Append our comments list
                    for item in json_data_sub['items']:
                        if self.too_old(item['snippet']['topLevelComment']['snippet']['publishedAt'], time_pub_after):
                            more = False
                        else:
                            comments.append(" " + item['snippet']['topLevelComment']['snippet']['textOriginal'] + " ")

        # Process the comments discovered
        globals.current_results = []
        sql_conn.context_purge()
        for comment in comments:
            for symbol in globals.symbols:
                comment_context_limit = 20
                if symbol in globals.common_words:
                    if " $" + symbol + " " in comment:
                        if len(symbol) > 1:
                            discoveries[symbol] += 1
                            if comment_context_limit > 1:
                                sql_conn.context_data_write(symbol, comment)
                                comment_context_limit -= 1

                else:
                    if " " + symbol + " " in comment or " $" + symbol + " " in comment:
                        if len(symbol) > 1:
                            discoveries[symbol] += 1
                            if comment_context_limit > 1:
                                sql_conn.context_data_write(symbol, comment)
                                comment_context_limit -= 1

        # Sort the comments by highest and report the top 30, write to DB/memory
        sql_conn.curr_data_purge()
        sorted_tuples = sorted(discoveries.items(), key=lambda item: item[1])
        sorted_dict = {k: v for k, v in sorted_tuples}
        for symbol, qty in list(reversed(list(sorted_dict.items())))[0:50]:
            sql_conn.curr_data_write(symbol, qty)
            globals.current_results.append((symbol,qty))

