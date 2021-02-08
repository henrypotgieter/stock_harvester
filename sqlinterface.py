import sqlite3

class Sqlconn(object):
    def __init__(self, db_conn=None):
        self.db_conn = sqlite3.connect('symbols.db')
        self.c = self.db_conn.cursor()

    def sql_read(self, query):
        self.c.execute(query)
        data = self.c.fetchall()
        return data

    def sql_write(self, query):
        data = self.c.execute(query)
        self.db_conn.commit()
        return data

    def symbol_ignore_read(self):
        symbol_ignore_tuples = self.sql_read('SELECT symbol from ignore')

        # Detouple symbol_ignore
        symbol_ignore = []
        for symbol_ignore_entries in symbol_ignore_tuples:
            symbol_ignore.append(symbol_ignore_entries[0])
        return symbol_ignore

    def common_words_read(self):
        common_words_tuples = self.sql_read('SELECT words from common_words')

        # Detouple common words
        common_words = []
        for words in common_words_tuples:
            common_words.append(words[0])
        return common_words

    def channels_read(self):
        channels_tuples = self.sql_read('SELECT * from channels')

        # Detouple channel words
        channels = []
        for channel in channels_tuples:
            channels.append(channel[0])
        return channels

    def symbols_read(self):
        symbol_tuples = self.sql_read('SELECT * from symbols')

        # Detouple symbols
        symbols = []
        for symbol in symbol_tuples:
            symbols.append(symbol[0])
        return symbols

    def symbols_ignore_write(self, symbol_name):
        self.sql_write("INSERT INTO ignore VALUES('" + symbol_name +"')")

    def channel_write(self, channel_name):
        self.sql_write("INSERT INTO channels VALUES ('" + channel_name + "')")

    def channel_del(self, channel_name):
        self.sql_write("DELETE FROM channels where channel = ('" + channel_name + "')")

    def symbols_ignore_remove(self, symbol_name):
        self.sql_write("DELETE FROM ignore WHERE symbol = ('" + symbol_name + "')")

    def curr_data_read(self):
        curr_data = self.sql_read('SELECT * from curr_data order by count desc')
        return curr_data

    def context_data_read(self, symbol):
        curr_data = self.sql_read("SELECT * from context where symbol = '" + symbol + "'")
        return curr_data

    def context_purge(self):
        self.sql_write("DELETE FROM context")

    def context_data_write(self, symbol, comment):
        comment_escaped = comment.replace("'", "")
        self.sql_write("INSERT INTO context VALUES ('" + symbol + "', '" + comment_escaped + "')")

    def curr_data_purge(self):
        self.sql_write("DELETE FROM curr_data")

    def curr_data_write(self, symbol, qty):
        self.sql_write("INSERT INTO curr_data values ('" + symbol + "', '" + str(qty) + "');")
