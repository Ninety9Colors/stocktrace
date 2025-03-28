import datetime as dt
from dateutil.relativedelta import relativedelta
import pandas as pd
from pyqtgraph.Qt.QtGui import QColor

import stocktrace.logger as logger

DATA_PATH = 'data/'

DEFAULT_FONT = 'Helvetica'

# TODO: Get timezone from settings
TIMEDELTA = dt.timedelta(hours=-5)
TIMEZONE = dt.timezone(TIMEDELTA)

# TODO: Get color from settings
DARK_STR = '(50,50,50)'
NORMAL_STR = '(80,80,80)'

BULLISH_STR = '(0, 255, 0)'
BEARISH_STR = '(255, 0, 0)'

DARK = QColor(50,50,50)
NORMAL = QColor(80,80,80)

BULLISH = QColor(0, 255, 0)
BEARISH = QColor(255, 0, 0)

def requires_explicit_init(func):
    def wrapper(cls, *args, **kwargs):
        if not cls._initialized:
            logger.Logger.critical(f'{cls} not explicitly initialized, raising RuntimeError')
            raise RuntimeError(f'{cls} is not initialized')
        return func(cls, *args, **kwargs)
    return wrapper

def requires_init(func):
    def wrapper(cls, *args, **kwargs):
        if not cls._initialized:
            cls.init()
        return func(cls, *args, **kwargs)
    return wrapper

def interval_to_timedelta(interval):
    if interval == "1d":
        return relativedelta(days=1)
    elif interval == "1mo":
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

def delta_to_seconds(delta) -> int:
    if isinstance(delta, pd.Timedelta):
        return delta.total_seconds()
    elif isinstance(delta, relativedelta):
        days = delta.years * 365 + delta.months * 30 + delta.days
        seconds = days * 86400 + delta.hours * 3600 + delta.minutes * 60 + delta.seconds
        return seconds
    else:
        raise ValueError(f'Delta must be pd.Timedelta or relativedelta, got {type(delta)}')