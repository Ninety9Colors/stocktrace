from abc import ABC, abstractmethod
import datetime as dt
from typing import Optional

from stocktrace.asset import AssetManager
from stocktrace.indicator import IndicatorManager, Indicator
from stocktrace.logger import Logger as logger
from stocktrace.trade_system import Broker, Order
from stocktrace.utils import TIMEZONE, requires_init

class Algorithm(ABC):
    def __init__(self, name: Optional[str] = None) -> None:
        logger.debug(f'Algorithm.__init__ Creating Algorithm with name {name}')
        self.__name = name
        self.__indicators: list[Indicator] = []
        self.__latest_start = dt.datetime.min.replace(tzinfo=TIMEZONE)
    
    def indicator(self, indicator, ticker_symbol: str, *args, **kwargs) -> Indicator:
        logger.info(f'Algorithm.indicator() adding Indicator {indicator.name} for {ticker_symbol} to Algorithm {self}')
        ind = indicator(*args, **kwargs)
        ind.init(ticker_symbol)
        self.__indicators.append(ind)
        return ind
    
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
    
    @name.setter
    def name(self, new_name) -> None:
        self.__name = new_name
    
    def __repr__(self) -> str:
        return f'Algorithm({self.name})'
    
class AlgorithmManager():
    _initialized = False

    @classmethod
    def init(cls) -> None:
        logger.info('AlgorithmManager.init() Initializing Algorithm Manager')
        from stocktrace.custom.custom_algorithm import import_algorithms
        cls._initialized = True
        cls.__algorithms = {}
        import_algorithms()
    
    @classmethod
    @requires_init
    def add_algorithm(cls, name: str, algorithm) -> bool:
        if name not in cls.__algorithms.keys():
            logger.info(f'AlgorithmManager.add_algorithm() Importing algorithm {name}')
            cls.__algorithms[name] = algorithm
            return True
        logger.warning(f'AlgorithmManager.add_algorithm() Algorithm {name} already exists! Ignoring...')
        return False

    @classmethod
    @requires_init
    def get_algorithm(cls, name: str):
        if name not in cls.__algorithms.keys():
            logger.warning(f'AlgorithmManager.get_algorithm() Algorithm {name} does not exist! Ignoring...')
            return None
        return cls.__algorithms[name]
