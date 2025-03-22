import datetime as dt
import pandas as pd
from typing import Optional

from stocktrace.algorithm import Algorithm
from stocktrace.asset import AssetManager
from stocktrace.logger import Logger as logger
from stocktrace.trade_system import Broker
from stocktrace.utils import TIMEZONE

class Backtest:
    def __init__(self, 
                 algorithm: Algorithm, 
                 broker: Broker, 
                 start_date: Optional[dt.datetime]=dt.datetime.min.replace(tzinfo=TIMEZONE), 
                 end_date: Optional[dt.datetime]=None) -> None:
        logger.debug(f'Backtest.__init__ Creating Backtest with algorithm {algorithm.name}, start date {start_date}, end date {end_date}')
        self.__algorithm = algorithm
        self.__broker = broker
        self.__start_date = start_date
        self.__end_date = end_date
        self.__completed = False
        self.__equity = pd.Series(dtype=float)
    
    def run(self, trace=False) -> None:
        logger.info(f'Backtest.run() Running backtest {self}')
        self.__algorithm.init()
        snp = AssetManager.get('^GSPC')
        self.__start_date = snp.prev_or_equal_date(max(self.__start_date, self.__algorithm.get_latest_start()))
        time = self.__start_date
        self.__end_date = snp.prev_or_equal_date(self.__end_date if self.__end_date else dt.datetime.now(tz=TIMEZONE))
        last_percent = 0
        while (time <= self.__end_date):
            self.__broker.process_orders(time)
            self.__algorithm.next(time, self.__broker)
            self.__equity.loc[time] = self.__broker.equity(time)
            i = snp.data.index.get_loc(time)
            if trace:
                percent = (pd.Timestamp(time)-pd.Timestamp(self.__start_date))/(pd.Timestamp(self.__end_date)-pd.Timestamp(self.__start_date))*100
                if percent >= last_percent+10:
                    last_percent = percent
                    print(percent)
            time = snp.data.index[i+1] if i+1 < len(snp.data.index) else (self.__end_date+dt.timedelta(seconds=1))
        if trace:
            print('Complete!')
        self.__completed = True
    
    @property
    def start_date(self) -> dt.datetime:
        if not self.__completed:
            raise RuntimeError('Backtest has not been completed yet')
        return self.__start_date
    
    @property
    def end_date(self) -> dt.datetime:
        if not self.__completed:
            raise RuntimeError('Backtest has not been completed yet')
        return self.__end_date
    
    @property
    def algorithm(self) -> Algorithm:
        return self.__algorithm

    @property
    def broker(self) -> Broker:
        return self.__broker
    
    @property
    def completed(self) -> bool:
        return self.__completed
    
    @property
    def equity(self) -> pd.Series:
        if not self.__completed:
            raise RuntimeError('Backtest has not been completed yet')
        return self.__equity

    def __repr__(self) -> str:
        return f'Backtest({self.__algorithm}, {self.__start_date}, {self.__end_date})'