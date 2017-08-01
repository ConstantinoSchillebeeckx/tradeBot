# tradeBot

## Guiding principles

- there is enough volatility in the daily market that if we time things properly, we could take advantage of that volatility
- after a sustained drop in price, BUY - this volatility is temporary so we buy at a cheap rate
- after leveling off, SELL - we are waiting for another drop to buy


To start logging, run the following:
```bash
nohup python start_logging.py &
```

Generate table with

'''sql

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
