import pandas as pd

from stocktrace.logging.logger import Logger as logger
from stocktrace.engine.history import AssetHistory

ASSET_HISTORY_PATH = 'data/'

class Asset:
	def __init__(self, ticker_symbol: str, interval: str='1d') -> None:
		logger.debug(f'Asset.__init__ Creating Asset with ticker symbol {ticker_symbol}, interval {interval}')
		self.__ticker_symbol = ticker_symbol
		self.__interval = interval
		file_path = ASSET_HISTORY_PATH + self.ticker_symbol + interval + '.csv'
		
		self.__history = AssetHistory(self.ticker_symbol, file_path, self.interval)
	
	def add_listener(self, func) -> None:
		self.history.add_listener(func)
	
	def update_data(self) -> None:
		self.history.update_data()

	@property
	def history(self) -> AssetHistory:
		return self.__history

	@property
	def file_path(self) -> str:
		return self.history.file_path

	@property
	def ticker_symbol(self) -> str:
		return self.__ticker_symbol

	@property
	def interval(self) -> str:
		return self.__interval

	@property
	def data(self) -> pd.DataFrame:
		return self.history.data

	def __repr__(self) -> str:
		return f'Asset({self.ticker_symbol}, {self.interval})'