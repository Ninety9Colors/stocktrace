import datetime as dt
import numpy as np

from stocktrace.logger import Logger as logger
from stocktrace.asset import Asset, AssetManager
from stocktrace.algorithm import Algorithm, AlgorithmManager
from stocktrace.indicator import IndicatorManager
from stocktrace.trade_system import Order, Broker

class SMACrossOver(Algorithm):
    def init(self) -> None:
        self.name = 'SMACrossOver'
        self.sma1 = self.indicator('SMA_TEN', 'GOOG')
        self.sma2 = self.indicator('SMA_TWENTY', 'GOOG')
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

class MultiSMACrossOver(Algorithm):
    def init(self) -> None:
        self.name = 'MultiSMACrossOver'
        self.sma1goog = self.indicator('SMA_TEN', 'GOOG')
        self.sma2goog = self.indicator('SMA_TWENTY', 'GOOG')
        self.sma1aapl = self.indicator('SMA_TEN', 'AAPL')
        self.sma2aapl = self.indicator('SMA_TWENTY', 'AAPL')
        self.__latest_start = max(self.sma2goog.data.index[1], self.sma2aapl.data.index[1])
    
    def next(self, time: dt.datetime, broker: Broker) -> None:
        prev_time = AssetManager.get('^GSPC').prev_date(time)
        if prev_time < self.__latest_start:
            return
        if self.sma1goog.data[time] > self.sma2goog.data[time] and self.sma1goog.data[prev_time] <= self.sma2goog.data[prev_time]:
            close_order = Order(broker, 'GOOG', -broker.get_position('GOOG').shares, time_placed=time)
            buy_order = Order(broker, 'GOOG', broker.cash//AssetManager.get('GOOG').get_cents(time), time_placed=time)
            broker.place_order(close_order)
            broker.place_order(buy_order)
        elif self.sma1goog.data[time] < self.sma2goog.data[time] and self.sma1goog.data[prev_time] >= self.sma2goog.data[prev_time]:
            close_order = Order(broker, 'GOOG', -broker.get_position('GOOG').shares, time_placed=time)
            buy_order = Order(broker, 'GOOG', -broker.cash//AssetManager.get('GOOG').get_cents(time), time_placed=time)
            broker.place_order(close_order)
            broker.place_order(buy_order)

        if self.sma1aapl.data[time] > self.sma2aapl.data[time] and self.sma1aapl.data[prev_time] <= self.sma2aapl.data[prev_time]:
            close_order = Order(broker, 'AAPL', -broker.get_position('AAPL').shares, time_placed=time)
            buy_order = Order(broker, 'AAPL', broker.cash//AssetManager.get('AAPL').get_cents(time), time_placed=time)
            broker.place_order(close_order)
            broker.place_order(buy_order)
        elif self.sma1aapl.data[time] < self.sma2aapl.data[time] and self.sma1aapl.data[prev_time] >= self.sma2aapl.data[prev_time]:
            close_order = Order(broker, 'AAPL', -broker.get_position('AAPL').shares, time_placed=time)
            buy_order = Order(broker, 'AAPL', -broker.cash//AssetManager.get('AAPL').get_cents(time), time_placed=time)
            broker.place_order(close_order)
            broker.place_order(buy_order)

def import_algorithms() -> None:
    logger.info('import_algorithms() Importing algorithms...')
    AlgorithmManager.add_algorithm('SMACrossOver', SMACrossOver)
    AlgorithmManager.add_algorithm('MultiSMACrossOver', MultiSMACrossOver)