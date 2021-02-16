# Stock Comment Harvester - Discord Bot

Tallies up comments from Youtube videos on select channels that mention stock
ticker symbols to help gather information on potential new hot stocks.

Allows interaction from a Discord server so that community can benefit from the
data collected.

This is beta code but it is functional.  More features will be added in the
future but for now here we are!

# Config

Examine the .env-sample file, replace the values that need to be populated in
the file with the appropriate data.  Write it to .env instead.'

Create a MYSQL db and user credentials for the bot to access.

Populate the MYSQL db using the data found in the initialize.sql dump.

# Setup

Install the required packages as follows:

```
pip install discord
pip install python-dotenv
pip install tabulate
pip install simplejson
pip install mysql-connector-python
```

# Usage

Run the primary script as follows using Python V3:

python bot.py

You could run this inside a screen session or create a systemd service file to
run it instead.
