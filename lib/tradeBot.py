import bitstamp.client
import threading, psycopg2
import datetime, threading, time
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from coinbase.wallet.client import Client
import urllib3
urllib3.disable_warnings()

from bokeh.layouts import gridplot
from bokeh.plotting import figure, show, output_file
from bokeh.io import push_notebook, show, output_notebook
from bokeh.palettes import Category10_10 as palette
output_notebook()

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
            with date as the index.
        '''

        available_columns = self.get_price().keys()

        if not columns:
            columns = available_columns
        else:
            assert isinstance(columns, list), "Must provide columns as a list"
            assert set(columns) <= set(available_columns), "Provided columns must include only: %s" %(','.join(available_columns))

        if 'timestamp' not in columns: columns.append('timestamp')

        sql = "SELECT %s from %s" %(','.join(columns), self.db_table)
        self.cur.execute(sql)
        rows = self.cur.fetchall()
        df = pd.DataFrame(rows, columns=columns)

        df.index = pd.to_datetime(df.timestamp,unit='s')
        df = df[[l for l in df.columns if l != 'timestamp']]

        return df

    def start_bokeh(self, size, title):
        '''
        Wrapper to initiate bokeh figure

        Args:
            size (tuple, default 1200,400) - sets plot_width/plot_height
            title (str, default: MSFT Candlestick) - title for plot

        Yields:
            bokeh figure
        '''

        tools = "pan,wheel_zoom,box_zoom,reset,save"

        return figure(plot_width=size[0], plot_height=size[1], tools=tools, 
                   x_axis_type='datetime', title=title, active_drag="pan", active_scroll="wheel_zoom")

    def candlestick(self, size=(1200,400), resample='1B', title="MSFT Candlestick"):
        '''
        Generate a bokeh candlestick plot of the 'last'
        price metric.

        Args:
            size (tuple, default 1200,400) - sets plot_width/plot_height
            resample (str, default: 1B) - pandas resample rule, see https://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases
            title (str, default: MSFT Candlestick) - title for plot

        Yield:
            void
        '''

        df = self.get_historical_prices(columns=['last']) # get data
        df = df.resample(resample).ohlc() # calculate ohlc
        df.columns = df.columns.levels[1]
        df.reset_index(inplace=True)

        # generate plot
        inc = df.close > df.open
        dec = df.open > df.close
        w = (df.ix[1,'timestamp']-df.ix[0,'timestamp']).total_seconds()*500 # half day in ms

        p = self.start_bokeh(size, title)
        p.segment(df.timestamp, df.high, df.timestamp, df.low, color="black")
        p.vbar(df.timestamp[inc], w, df.open[inc], df.close[inc], fill_color="#bfe2bc", line_color="black")
        p.vbar(df.timestamp[dec], w, df.open[dec], df.close[dec], fill_color="#F2583E", line_color="black")

        show(p, notebook_handle=True)





    def plot_historical_prices(self, columns=None, size=(1200,400), title=None, resample=None):
        '''
        Generate a bokeh line plot with the given columns

        Args:
            columns (list) - list of metrics to show in
              plot, must be a key from get_price()
            size (tuple, default 1200,400) - sets plot_width/plot_height
            resample (str, default: 1B) - pandas resample rule, see https://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases
              if provided, median() is used to aggregate group.

        Yield:
            void
        '''

        df = self.get_historical_prices() # query data
        available_plot_columns = [l for l in self.get_price().keys() if l not in ['timestamp','volume']]

        if not columns: columns = available_plot_columns

        dat = df[columns] # reduce data to requested columns

        # resample if needed
        if resample:
            dat = dat.resample(resample).median()

        # generate plot
        p = self.start_bokeh(size, title)
        p.xaxis.axis_label = 'Time'
        p.yaxis.axis_label = 'Price (USD)'

        for i, col in enumerate(dat.columns):
            p.line(dat.index.tolist(), dat[col].tolist(), legend=col, line_width=2, line_alpha=0.6, line_color=palette[i])

        p.legend.location = "top_left"

        show(p, notebook_handle=True)


