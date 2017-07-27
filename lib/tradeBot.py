import bitstamp.client
import threading, psycopg2
import datetime, threading, time
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from coinbase.wallet.client import Client
import urllib3
urllib3.disable_warnings()

class tradeBot(object):
    '''
    A watcher that queries bitstamp for the current
    bitcoin price and stores it in the database

    Database:
    - assumes a postgres database is installed
    '''

    def __init__(self, db='tradeBot', db_table='history', freq=60, user='', password='', host='localhost'):
        assert freq >= 1, "Freq must be >= 1."
        self.db = db
        self.db_table = db_table
        self.freq = freq
        self.timer = threading.Timer(self.freq, self.start_logging)
        self.user = user
        self.password = password
        self.host = host
        self.conn = psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s'" %(self.db, self.user, self.host, self.password))
        self.conn.autocommit = True
        self.cur = self.conn.cursor()

    def start_logging(self):
        '''
        threading timer to initiate logging bitcoin
        prices to the database
        '''
        self.log_price()
        self.timer = threading.Timer(self.freq, self.start_logging)
        self.timer.start()

    def stop_logging(self):
        '''
        stop the threading timer that logs prices
        '''
        self.timer.cancel()

    def truncate_history(self):
        '''
        clear out the history table
        '''
        sql = "TRUNCATE %s RESTART identity CASCADE;" %self.db_table
        self.cur.execute(sql)

    def status(self):
        print 'Price logging is currently ' + ('on.' if self.timer.is_alive() else 'off.')
        return

    def log_price(self):
        '''
        log bitcoin price to database
        '''
        price = self.get_price()
        if price:
            columns = ','.join(price.keys())
            values = ','.join(price.values())

            # insert into db
            sql = "INSERT INTO %s (%s) VALUES (%s);" %(self.db_table, columns, values)
            self.cur.execute(sql)

    def get_price(self):
        '''
        ping bitstamp for the current bitcoin price

        Yields:
        -------
        dict with format
        {
            "high": "2600.00",             # Last 24 hours price high.
            "last": "2540.53",             # Last BTC price.
            "timestamp": "1501167080",     # Unix timestamp date and time.
            "bid": "2542.30",              # Highest buy order.
            "vwap": "2513.48",             # Last 24 hours volume weighted average price.
            "volume": "12586.57241041",    # Last 24 hours volume.
            "low": "2400.00",              # Last 24 hours price low.
            "ask": "2547.45",              # Lowest sell order.
            "open": 2524.99                # First price of the day.
        }
        '''
        try:
            price = bitstamp.client.Public().ticker()
            price['timestamp'] = str(time.time()) # get a more accurate timestamp
        except:
            print 'error occurred'
            price = False
        return price

    def get_historical_prices(self, columns=None):
        '''
        query database for historical price data

        Args:
            columns (list): list of columns requested, must
            include only those that are provided as keys
            from get_price()

        Yield:
            Pandas DataFrame of historical price data;
            if the dataframe contains a column 'timestamp'
            the index of the return dataframe will be the
            date formatted timestamp column and the
            timestamp column will be removed
        '''

        available_columns = self.get_price().keys()

        if not columns:
            columns = available_columns
        else:
            assert isinstance(columns, list), "Must provide columns as a list"
            assert set(columns) <= set(available_columns), "Provided columns must include only: %s" %(','.join(available_columns))

        sql = "SELECT %s from %s" %(','.join(columns), self.db_table)
        self.cur.execute(sql)
        rows = self.cur.fetchall()
        df = pd.DataFrame(rows, columns=columns)

        if 'timestamp' in columns:
            df.index = pd.to_datetime(df.timestamp,unit='s')
            df = df[[l for l in df.columns if l != 'timestamp']]

        return df


    def plot_historical_prices(self, columns=None, size=(16,6)):
        '''
        '''

        df = self.get_historical_prices()
        available_plot_columns = [l for l in self.get_price().keys() if l not in ['timestamp','volume']]

        if not columns: columns = available_plot_columns

        ax = df[columns].plot(figsize=size)
        ax.set_ylabel('Price (USD)')

        return ax


'''
CREATE TABLE public.history (
    id SERIAL NOT NULL,
    "last" float8 NOT NULL,
    high float8 NOT NULL,
    low float8 NOT NULL,
    vwap float8 NOT NULL,
    volume float8 NOT NULL,
    bid float8 NOT NULL,
    ask float8 NOT NULL,
    "timestamp" float8 NOT NULL,
    "open" float8 NOT NULL,
    CONSTRAINT history_pkey PRIMARY KEY (id)
);
CREATE INDEX last_ix ON public.history ("last");
CREATE INDEX high_ix ON public.history (high);
CREATE INDEX low_ix ON public.history (low);
CREATE INDEX vwap_ix ON public.history (vwap);
CREATE INDEX volume_ix ON public.history (volume);
CREATE INDEX bid_ix ON public.history (bid);
CREATE INDEX ask_ix ON public.history (ask);
CREATE INDEX timestamp_ix ON public.history ("timestamp");
CREATE INDEX open_ix ON public.history ("open");
TRUNCATE public.history RESTART identity CASCADE;

'''
