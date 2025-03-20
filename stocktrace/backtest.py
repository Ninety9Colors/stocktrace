import datetime as dt
import pandas as pd
from typing import Optional

from stocktrace.algorithm import Algorithm
from stocktrace.logger import Logger as logger
from stocktrace.trade_system import Broker

class Backtest:
    def __init__(self, algorithm: Algorithm, broker: Broker, start_date: dt.datetime, end_date: Optional[dt.datetime]) -> None:
        logger.debug(f'Backtest.__init__ Creating Backtest with algorithm {algorithm.name}, start date {start_date}, end date {end_date}')
        self.__algorithm = algorithm
        self.__broker = broker
        self.__start_date = start_date
        self.__end_date = end_date
        self.__completed = False
    
    def run(self) -> None:
        logger.info(f'Backtest.run() Running backtest {self}')
        self.__algorithm.init()
        time = max(self.__start_date, self.__algorithm.get_latest_start())
        
    
    @property
    def completed(self) -> bool:
        return self.__completed

    def __repr__(self) -> str:
        return f'Backtest({self.__algorithm}, {self.__start_date}, {self.__end_date})'