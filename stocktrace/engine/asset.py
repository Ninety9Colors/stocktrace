import pandas as pd

from stocktrace.logging.logger import Logger as logger
from stocktrace.engine.history import AssetHistory

ASSET_HISTORY_PATH = 'data/'

class Asset:
	def __init__(self, ticker_symbol: str, interval: str='1d') -> None:
		logger.debug(f'Asset.__init__ Creating Asset with ticker symbol {ticker_symbol}, interval {interval}')
		self.__ticker_symbol = ticker_symbol
		file_path = ASSET_HISTORY_PATH + self.ticker_symbol + interval + '.csv'
		
		self.__history = AssetHistory(self.ticker_symbol, file_path, interval)

	@property
	def history(self) -> AssetHistory:
		return self.__history

	@property
	def file_path(self) -> str:
		return self.__file_path

	@property
	def ticker_symbol(self) -> str:
		return self.__ticker_symbol

	@property
	def data(self) -> pd.DataFrame:
		return self.history.data