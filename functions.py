import os
import globals
import datetime
import json
import requests
from dotenv import load_dotenv
from datetime import timezone
from sqlinterface import Sqlconn


''' All the supporting functions, keep the bot.py file clean '''

class Functions(object):
    def __init__(self):
        load_dotenv('.env')
        self.API_KEY = os.getenv('API_KEY')
        self.BASE_URL = os.getenv('BASE_URL')
        self.TIME_SUB = os.getenv('TIME_SUB')
        self.sql_conn = Sqlconn()

    def add_channel(self, channel_name):
        globals.channels.append(channel_name)
        self.sql_conn.channel_write(channel_name)

    def del_channel(self, channel_name):
        globals.channels.remove(channel_name)
        self.sql_conn.channel_del(channel_name)

    def add_ignore(self, symbol_add_ignore):
        for symbol in globals.symbols:
            if symbol_add_ignore == symbol:
                self.sql_conn.symbols_ignore_write(symbol_add_ignore)
                globals.symbol_ignore.append(symbol_add_ignore)
                return True
        return False

    def get_current_utc_timestamp(self):
        cur_time = datetime.datetime.now(tz=timezone.utc)
        utc_timestamp = cur_time.timestamp()
        current_utc_int_timestamp = int(utc_timestamp)
        return current_utc_int_timestamp

    def scrape_write_time(self):
        current_utc_int_timestamp = self.get_current_utc_timestamp()
        self.sql_conn.last_ran_write(str(current_utc_int_timestamp))

    def del_ignore(self, symbol_del_ignore):
        for symbol in globals.symbols:
            if symbol_del_ignore == symbol:
                globals.symbol_ignore.remove(symbol_del_ignore)
                self.sql_conn.symbols_ignore_remove(symbol_del_ignore)
                return True
        return False

    def pub_after_time(self, time_diff):
        '''Create timestamp to be passed to youtube api'''
        cur_time = datetime.datetime.now(tz=timezone.utc)
        utc_timestamp = cur_time.timestamp()
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

    def last_run(self):
        last_ran_time = self.sql_conn.last_ran_read()
        return last_ran_time[0][0]

    def last_run_utc_print(self):
        last_ran_time = self.last_run()
        return datetime.datetime.utcfromtimestamp(last_ran_time).strftime('%Y-%m-%dT%H:%M:%SZ')


    def scraper(self):
        # Generate empty comments list
        comments = []

        # Get time from db
        last_ran_time = self.last_run()

        datetime.datetime.utcfromtimestamp

        # Get time now
        current_utc_int_timestamp = self.get_current_utc_timestamp()
        time_difference = current_utc_int_timestamp - last_ran_time

        # Check if we're past 1 hour from last time we ran the scraper
        if time_difference < 3600:
            # Return UTC timestamp of last execution + 1 hour to tell user when
            # they can run the command again
            return datetime.datetime.utcfromtimestamp(last_ran_time + 3600).strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            # Update timestamp
            self.scrape_write_time()
            print ("Conducting scraping event at " + datetime.datetime.utcfromtimestamp(current_utc_int_timestamp).strftime('%Y-%m-%dT%H:%M:%SZ'))

            # Build a discoveries dictionary that we populate with symbols
            discoveries = {}
            for symbol in globals.symbols:
                if len(symbol) > 1:
                    discoveries[symbol] = 0

            time_pub_after = self.pub_after_time(self.TIME_SUB)

            # Primary loop to parse data from each channel
            for channel in globals.channels:
                # Build initial pull request and process json
                you_pull = requests.get(self.BASE_URL + channel + "&key=" + self.API_KEY)
                data = you_pull.text
                json_data = json.loads(data)

                # Loop control flags, reset to false every time
                more = False
                dont_bother = False

                if not 'items' in json_data:
                    continue
                # Append initial comments
                for item in json_data['items']:
                    if self.too_old(item['snippet']['topLevelComment']['snippet']['publishedAt'], time_pub_after):
                        dont_bother = True
                    else:
                        comment_raw = item['snippet']['topLevelComment']['snippet']['textOriginal']
                        cleaned = lambda s: "".join(i for i in s if 31 < ord(i) < 127)
                        comments.append(" " + cleaned(comment_raw) + " ")

                # Check if there was a next page token, set it and then adjust loop control to True
                if 'nextPageToken' in json_data and dont_bother == False:
                    next_page_token = json_data['nextPageToken']
                    more = True
                    # Loop until there is no more!
                    while more:
                        # Grab data request again using page token and published after time
                        you_pull = requests.get(self.BASE_URL + channel +"&pageToken=" + next_page_token + "&publishedAfter=" + time_pub_after +  "&key=" + self.API_KEY)
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
                                comment_raw = item['snippet']['topLevelComment']['snippet']['textOriginal']
                                cleaned = lambda s: "".join(i for i in s if 31 < ord(i) < 127)
                                comments.append(" " + cleaned(comment_raw) + " ")

            # Process the comments discovered
            #globals.current_results = []
            self.sql_conn.context_purge()
            for comment in comments:
                for symbol in globals.symbols:
                    comment_context_limit = 20
                    if symbol in globals.common_words:
                        if " $" + symbol + " " in comment:
                            if len(symbol) > 1:
                                discoveries[symbol] += 1
                                if comment_context_limit > 1:
                                    self.sql_conn.context_data_write(symbol, comment)
                                    comment_context_limit -= 1

                    else:
                        if " " + symbol + " " in comment or " $" + symbol + " " in comment:
                            if len(symbol) > 1:
                                discoveries[symbol] += 1
                                if comment_context_limit > 1:
                                    self.sql_conn.context_data_write(symbol, comment)
                                    comment_context_limit -= 1

            # Sort the comments by highest and report the top 30, write to DB/memory
            self.sql_conn.curr_data_purge()
            sorted_tuples = sorted(discoveries.items(), key=lambda item: item[1])
            sorted_dict = {k: v for k, v in sorted_tuples}
            for symbol, qty in list(reversed(list(sorted_dict.items())))[0:50]:
                self.sql_conn.curr_data_write(symbol, qty)
                #globals.current_results.append((symbol,qty))
            return 1;

    def get_context(self, symbol):
        return self.sql_conn.context_data_read(symbol)

    def get_results(self):
        data = self.sql_conn.curr_data_read()
        return data
