import datetime as dt
import numpy as np

from stocktrace.logger import Logger as logger
from stocktrace.indicator import Indicator, IndicatorManager
from stocktrace.asset import Asset, AssetManager

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

def import_indicators() -> None:
    logger.info('import_indicators() Importing indicators...')
    IndicatorManager.add_indicator('SMA_TWENTY', SMA_TWENTY)
    IndicatorManager.add_indicator('SMA_TEN', SMA_TEN)