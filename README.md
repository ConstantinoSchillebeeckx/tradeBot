# tradeBot

## Guiding principles

I want to take a very simple approach to buying/selling bitcoin to try and take advantage of the volatility in the current market. The underlying assumptions are the following:
- large-ish drops in value are common and seem to occur almost at a daily level
- these drops tend to be followed by a relatively quick recovery of the market

Approach:
- watch market value and wait for those drops (TODO define maginute of drop)
- once the drop occurs, wait for the market to level (TODO define leveling of market) and BUY
- wait for market to recover and sell once it plateaus (TODO define plateaus of market) and SELL


I've setup a cronjob (running at a frequency of ~30s) to log prices.
```
# log prices every 30s
# crontab only has minute granularity; so we sleep for ~30s between calls
* * * * * /bin/bash -l -c "python /home/data_repo/ipython/Constantino/tradeBot/log_price.py; sleep 30 ; python /home/data_repo/ipython/Constantino/tradeBot/log_price.py"
```


To start logging, run the following:
```bash
nohup python start_logging.py &
```

Generate table with

```sql
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
```
