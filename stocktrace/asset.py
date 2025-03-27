import datetime as dt
from typing import Optional
import pandas as pd

from stocktrace.file import CSV, TIME_CSV
from stocktrace.logger import Logger as logger
from stocktrace.history import AssetHistory
from stocktrace.utils import requires_init, DATA_PATH

class Asset:
	def __init__(self, ticker_symbol: str, interval: str='1d', auto_save = False) -> None:
		logger.debug(f'Asset.__init__ Creating Asset with ticker symbol {ticker_symbol}, interval {interval}')
		self.__ticker_symbol = ticker_symbol
		self.__interval = interval
		file_path = DATA_PATH + self.ticker_symbol + interval + '.csv'
		
		self.__history = AssetHistory(self.ticker_symbol, file_path, self.interval, auto_save=auto_save)
	
	def add_listener(self, func) -> None:
		self.history.add_listener(func)
	
	def remove_listener(self, func) -> None:
		self.history.remove_listener(func)
	
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

	def prev_or_equal_date(self, time: dt.datetime) -> dt.datetime:
		return self.__history.prev_or_equal_date(time)

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
	def csv(self) -> TIME_CSV:
		return self.history.csv
	
	@property
	def ticker_found(self) -> bool:
		return self.__history.ticker_found

	def __repr__(self) -> str:
		return f'Asset({self.ticker_symbol}, {self.interval})'

class AssetManager():
	_initialized = False
	@classmethod
	def init(cls, auto_save: bool=True) -> None:
		cls._initialized = True

		cls.__auto_save = auto_save
		cls.__assets = {}
		cls.__ticker_csv = CSV(f'{DATA_PATH}loaded_tickers.csv')
		if not cls.__ticker_csv.data.empty:
			logger.info('Initializing existing loaded tickers...')
			for name in cls.__ticker_csv.data['Tickers'].to_numpy():
				logger.info(f'{name}')
				asset = cls.get(name)
				if asset is None:
					logger.warning(f'Asset with ticker {name} not found...')
					continue
				cls.__assets[name] = cls.get(name)
		else:
			cls.__ticker_csv.data['Tickers'] = pd.Series(dtype=str)

		logger.info(f'--- Asset Manager Initialized ---')
	
	@classmethod
	@requires_init
	def save_data(cls) -> None:
		cls.__ticker_csv.save()
	
	@classmethod
	@requires_init
	def get(cls, ticker_symbol: str, interval: str='1d') -> Asset:
		if ticker_symbol not in cls.__assets:
			asset = Asset(ticker_symbol, interval)
			if asset.ticker_found:
				cls.__assets[ticker_symbol] = asset
				if ticker_symbol not in cls.__ticker_csv.data['Tickers'].values:
					new_df = pd.DataFrame(columns=['Tickers'])
					new_df.loc[0] = ticker_symbol
					cls.__ticker_csv.append(new_df)
				if cls.__auto_save:
					cls.__ticker_csv.save()
				return asset
			return None
		return cls.__assets[ticker_symbol]

	@classmethod
	@requires_init
	def get_assets(cls) -> dict:
		return cls.__assets