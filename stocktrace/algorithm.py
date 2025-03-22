from abc import ABC, abstractmethod
import datetime as dt
from typing import Optional

from stocktrace.asset import AssetManager
from stocktrace.indicator import Indicator, SMA_TEN, SMA_TWENTY
from stocktrace.logger import Logger as logger
from stocktrace.trade_system import Broker, Order
from stocktrace.utils import TIMEZONE

class Algorithm(ABC):
    def __init__(self, name: Optional[str] = None) -> None:
        logger.debug(f'Algorithm.__init__ Creating Algorithm with name {name}')
        self.__name = name
        self.__indicators: list[Indicator] = []
        self.__latest_start = dt.datetime.min.replace(tzinfo=TIMEZONE)
    
    def indicator(self, indicator: Indicator, ticker_symbol: str) -> Indicator:
        logger.info(f'Algorithm.indicator() adding Indicator {indicator.name} for {ticker_symbol} to Algorithm {self}')
        indicator.init(ticker_symbol)
        self.__indicators.append(indicator)
        return indicator
    
    @abstractmethod
    def init(self) -> None:
        pass

    @abstractmethod
    def next(self, time: dt.datetime, broker: Broker) -> None:
        pass

    def get_latest_start(self) -> dt.datetime:
        latest_start = self.__latest_start
        for indicator in self.__indicators:
            latest_start = max(latest_start, indicator.data.index[0]).replace(tzinfo=TIMEZONE)
        return latest_start

    @property
    def name(self) -> str:
        return self.__name
    
    def __repr__(self) -> str:
        return f'Algorithm({self.name})'

class SMACrossOver(Algorithm):
    def init(self) -> None:
        self.sma1 = self.indicator(SMA_TEN(), 'GOOG')
        self.sma2 = self.indicator(SMA_TWENTY(), 'GOOG')
        self.__latest_start = self.sma2.data.index[1]
    
    def next(self, time: dt.datetime, broker: Broker) -> None:
        prev_time = AssetManager.get('^GSPC').prev_date(time)
        if prev_time < self.__latest_start:
            return
        if self.sma1.data[time] > self.sma2.data[time] and self.sma1.data[prev_time] <= self.sma2.data[prev_time]:
            close_order = Order(broker, 'GOOG', -broker.get_position('GOOG').shares, time_placed=time)
            buy_order = Order(broker, 'GOOG', broker.cash//AssetManager.get('GOOG').get_cents(time), time_placed=time)
            broker.place_order(close_order)
            broker.place_order(buy_order)
        elif self.sma1.data[time] < self.sma2.data[time] and self.sma1.data[prev_time] >= self.sma2.data[prev_time]:
            close_order = Order(broker, 'GOOG', -broker.get_position('GOOG').shares, time_placed=time)
            buy_order = Order(broker, 'GOOG', -broker.cash//AssetManager.get('GOOG').get_cents(time), time_placed=time)
            broker.place_order(close_order)
            broker.place_order(buy_order)
