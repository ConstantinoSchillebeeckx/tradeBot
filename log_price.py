#!/usr/bin/env python

import lib.tradeBot as tb

freq = 15 # frequency in seconds to log prices
user = 'matatu' # database user
password = 'password' # password for database user

bot = tb.tradeBot(freq=freq, user=user, password=password)
bot.log_price()
