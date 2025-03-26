from abc import ABC, abstractmethod
import datetime as dt
from typing import Optional
import numpy as np
import pandas as pd

from stocktrace.asset import Asset, AssetManager
from stocktrace.utils import requires_explicit_init, requires_init
from stocktrace.logger import Logger as logger

class Indicator(ABC):
    def __init__(self, name: Optional[str]=None) -> None:
        self._initialized = False
        self.__name = name
        self.__ticker_symbol = 'Uninitialized'
        self.__data = pd.Series()
    
    @abstractmethod
    def compute(self, asset: Asset, time: dt.datetime) -> float:
        '''User defined function to compute indicator value given a certain time, from Asset OHLCV data'''
        pass

    def update_data(self, new_ticker: Optional[str]=None) -> None:
        assert self._initialized
        logger.info(f'Indicator.update_data() Updating indicator {self.name}, new ticker? = {new_ticker}')
        if new_ticker:
            self.__ticker_symbol = new_ticker
        self._initialized = False
        self.init(self.__ticker_symbol)
        self._initialized = True
    
    def init(self, ticker_symbol: str) -> None:
        self._initialized = True
        logger.info(f'Indicator.init() Initializing indicator {self.__name} for {ticker_symbol}...')
        self.__ticker_symbol = ticker_symbol
        asset = AssetManager.get(self.__ticker_symbol)
        self.__data = pd.Series(np.nan, index=asset.data.index, name=self.__name)

        for time in asset.data.index:
            try:
                self.__data[time] = self.compute(asset, time)
            except:
                logger.info(f'Indicator.init() Could not compute {self.__name} at {time}, likely due to warmup lag')
        
        self.__data.dropna(inplace=True)
        logger.info(f'Initialized!:\n{self.__data}')
    
    @property
    @requires_explicit_init
    def data(self) -> pd.Series:
        return self.__data

    @property
    def name(self) -> str:
        return self.__name
    
class IndicatorManager():
    _initialized = False

    @classmethod
    def init(cls) -> None:
        logger.info('IndicatorManager.init() Initializing Indicator Manager')
        from stocktrace.custom.custom_indicator import import_indicators
        cls._initialized = True
        cls.__indicators = {}
        import_indicators()
    
    @classmethod
    @requires_init
    def add_indicator(cls, name: str, indicator) -> bool:
        if name not in cls.__indicators.keys():
            logger.info(f'IndicatorManager.add_indicator() Importing indicator {name}')
            cls.__indicators[name] = indicator
            return True
        logger.warning(f'IndicatorManager.add_indicator() Indicator {name} already exists! Ignoring...')
        return False

    @classmethod
    @requires_init
    def get_indicator(cls, name: str):
        if name not in cls.__indicators.keys():
            logger.warning(f'IndicatorManager.get_indicator() Indicator {name} does not exist! Ignoring...')
            return None
        return cls.__indicators[name]
    
    @classmethod
    @requires_init
    def get_indicators(cls) -> dict[str, Indicator]:
        return cls.__indicators
