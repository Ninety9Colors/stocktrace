from abc import ABC, abstractmethod
import datetime as dt
from typing import Optional
import numpy as np
import pandas as pd

from stocktrace.asset import Asset, AssetManager
from stocktrace.utils import requires_explicit_init
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
    
    def init(self, ticker_symbol: str) -> None:
        self._initialized = True
        logger.info(f'Indicator.init() Initializing indicator {self.__name} for {ticker_symbol}')
        self.__ticker_symbol = ticker_symbol
        asset = AssetManager.get(self.__ticker_symbol)
        self.__data = pd.Series(np.nan, index=asset.data.index, name=self.__name)

        for time in asset.data.index:
            try:
                self.__data[time] = self.compute(asset, time)
            except:
                logger.info(f'Indicator.init() Could not compute {self.__name} at {time}, likely due to warmup lag')
        
        self.__data.dropna(inplace=True)
    
    @property
    @requires_explicit_init
    def data(self) -> pd.Series:
        return self.__data

    @property
    def name(self) -> str:
        return self.__name

class SMA_TWENTY(Indicator):
    def compute(self, asset: Asset, time: dt.datetime) -> float:
        time = asset.prev_or_equal_date(time)
        end = asset.data.index.get_loc(time) # inclusive
        start = end-19 # inclusive
        if start < 0:
            return np.nan
        return asset.data.iloc[start:end+1]['Close'].mean()
    
class SMA_TEN(Indicator):
    def compute(self, asset: Asset, time: dt.datetime) -> float:
        time = asset.prev_or_equal_date(time)
        end = asset.data.index.get_loc(time) # inclusive
        start = end-9 # inclusive
        if start < 0:
            return np.nan
        return asset.data.iloc[start:end+1]['Close'].mean()
