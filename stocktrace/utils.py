import datetime as dt
from dateutil.relativedelta import relativedelta
import pandas as pd

import stocktrace.logging.logger as logger

# TODO: Get timezone from settings
TIMEZONE = dt.timezone(dt.timedelta(hours=-6))

class InitClass:
    _initialized: bool = False

def requires_explicit_init(func):
    def wrapper(cls, *args, **kwargs):
        if not cls._initialized:
            logger.Logger.critical(f'{cls.__name__} not explicitly initialized, raising RuntimeError')
            raise RuntimeError(f'{cls.__name__} is not initialized')
        return func(cls, *args, **kwargs)
    return wrapper

def requires_init(func):
    def wrapper(cls, *args, **kwargs):
        if not cls._initialized:
            cls.init()
        return func(cls, *args, **kwargs)
    return wrapper

def interval_to_timedelta(interval):
    if interval == "1mo":
        return relativedelta(months=1)
    elif interval == "3mo":
        return relativedelta(months=3)
    elif interval == "6mo":
        return relativedelta(months=6)
    elif interval == "1y":
        return relativedelta(years=1)
    elif interval == "2y":
        return relativedelta(years=2)
    elif interval == "5y":
        return relativedelta(years=5)
    elif interval == "10y":
        return relativedelta(years=10)
    elif interval == "1wk":
        return pd.Timedelta(days=7)
    else:
        return pd.Timedelta(interval)