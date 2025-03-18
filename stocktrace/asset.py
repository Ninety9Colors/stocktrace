import datetime as dt
from typing import Optional
import pandas as pd

from stocktrace.file import CSV
from stocktrace.logger import Logger as logger
from stocktrace.history import AssetHistory
from stocktrace.utils import InitClass, requires_init

ASSET_HISTORY_PATH = 'data/'

class Asset:
	def __init__(self, ticker_symbol: str, interval: str='1d', auto_save = False) -> None:
		logger.debug(f'Asset.__init__ Creating Asset with ticker symbol {ticker_symbol}, interval {interval}')
		self.__ticker_symbol = ticker_symbol
		self.__interval = interval
		file_path = ASSET_HISTORY_PATH + self.ticker_symbol + interval + '.csv'
		
		self.__history = AssetHistory(self.ticker_symbol, file_path, self.interval, auto_save=auto_save)
	
	def add_listener(self, func) -> None:
		self.history.add_listener(func)
	
	def update_data(self) -> None:
		self.history.update_data()
	
	def save_data(self) -> None:
		self.history.save_data()
	
	def latest_cents(self, col: str = 'Close') -> Optional[int]:
		return self.__history.latest_cents(col)

	def get_cents(self, time: dt.datetime, col: str = 'Close') -> Optional[int]:
		return self.__history.get_cents(time, col)
	
	def latest_date(self) -> dt.datetime:
		return self.__history.latest_date()
	
	def prev_date(self, time: dt.datetime) -> dt.datetime:
		return self.__history.prev_date(time)

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

	@property
	def csv(self) -> CSV:
		return self.history.csv

	def __repr__(self) -> str:
		return f'Asset({self.ticker_symbol}, {self.interval})'

class AssetManager(InitClass):
	@classmethod
	def init(cls) -> None:
		cls._initialized = True
		cls.__assets = {}
		logger.info(f'--- Asset Manager Initialized ---')
	
	@classmethod
	@requires_init
	def get(cls, ticker_symbol: str, interval: str='1d') -> Asset:
		if ticker_symbol not in cls.__assets:
			cls.__assets[ticker_symbol] = Asset(ticker_symbol, interval)
		return cls.__assets[ticker_symbol]

	@classmethod
	@requires_init
	def get_assets(cls) -> dict:
		return cls.__assets