from abc import ABC, abstractmethod
import datetime as dt

from stocktrace.indicator import Indicator
from stocktrace.logger import Logger as logger
from stocktrace.trade_system import Broker
from stocktrace.utils import TIMEZONE

class Algorithm(ABC):
    def __init__(self, name: str) -> None:
        logger.debug(f'Algorithm.__init__ Creating Algorithm with name {name}')
        self.__name = name
        self.__indicators: dict[str, Indicator] = {}
    
    def indicator(self, indicator: Indicator, ticker_symbol: str) -> Indicator:
        logger.info(f'Algorithm.indicator() adding Indicator {indicator.name} for {ticker_symbol} to Algorithm {self}')
        indicator.init(ticker_symbol)
        self.__indicators[indicator.name] = indicator
        return indicator
    
    @abstractmethod
    def init(self) -> None:
        pass

    @abstractmethod
    def next(self, time: dt.datetime, broker: Broker) -> None:
        pass

    def get_latest_start(self) -> dt.datetime:
        latest_start = dt.datetime.min.replace(tzinfo=TIMEZONE)
        for indicator in self.__indicators.values():
            latest_start = max(latest_start, indicator.data.index[0]).replace(tzinfo=TIMEZONE)
        return latest_start

    @property
    def name(self) -> str:
        return self.__name
    
    def __repr__(self) -> str:
        return f'Algorithm({self.name})'