from abc import ABC, abstractmethod
import datetime as dt
import os
import numpy as np
import pandas as pd
import yfinance as yf
from typing import Optional

from stocktrace.file import TIME_CSV
from stocktrace.logger import Logger as logger

from stocktrace.utils import TIMEZONE, interval_to_timedelta

class History(ABC):
	def __init__(self, file_path: str, interval: str='1d', listeners=[]) -> None:
		self.__file_path = file_path
		self.__interval = interval
		self.__listeners = listeners
		self.__csv = TIME_CSV(file_path)
		self.update_data()
	
	def save_data(self) -> None:
		self.__csv.save()

	@abstractmethod
	def update_data() -> None:
		pass

	def add_listener(self, func) -> None:
		logger.info(f'Adding listener {func} to {self}')
		self.listeners.append(func)
	
	def remove_listener(self, func) -> None:
		logger.info(f'Removing listener {func} from {self}')
		self.listeners.remove(func)
	
	def call_listeners(self) -> None:
		logger.info(f'Calling listeners in: {self}')
		for f in self.listeners:
			logger.info(f'Listener: {f}')
			f()
	
	@property
	def file_path(self) -> str:
		return self.__file_path

	@property
	def interval(self) -> str:
		return self.__interval
	
	@property
	def csv(self) -> TIME_CSV:
		return self.__csv

	@property
	def data(self) -> pd.DataFrame:
		return self.__csv.data

	@property
	def listeners(self) -> list:
		return self.__listeners
	
	def __repr__(self) -> str:
		return f'History({self.file_path}, {self.interval})'
	
class AssetHistory(History):
	def __init__(self, ticker_symbol: str, file_path: str, interval: str='1d', auto_save = False) -> None:
		logger.debug(f'AssetHistory.__init__ Creating AssetHistory with ticker symbol {ticker_symbol}, file path {file_path}, interval {interval}')

		self.__ticker_found = False
		self.__ticker_symbol = ticker_symbol
		self.__ticker = yf.Ticker(self.ticker_symbol)
		self.__auto_save = auto_save
		super().__init__(file_path, interval)
	
	def update_data(self) -> bool:
		result = True
		logger.info(f'AssetHistory.update_data Retrieving recent data of {self.ticker_symbol}')
		last_updated = self.latest_date()
		current_date = dt.datetime.now(TIMEZONE)

		logger.info(f'Date of most recent data row (min date if empty): {last_updated}')
		start = last_updated+interval_to_timedelta(self.interval)
		if (start >= current_date):
			logger.info(f'Data is up to current date {current_date}, continuing...')
			self.__ticker_found = True
			return
		if (last_updated == dt.datetime.min.replace(tzinfo=TIMEZONE)):
			logger.info(f'No cached data found, initializing data...')
			data_to_add = self._ticker.history(interval=self.interval, period='max')
		else:
			logger.info(f'Downloading new data...')
			data_to_add = self._ticker.history(interval=self.interval, start=start, end=current_date)
		logger.info(f'Cleaning data...')
		data_to_add = data_to_add[['Open','High','Low','Close']].replace(0,np.nan)
		null_count = data_to_add[['Open','High','Low','Close']].isna().sum().max()
		if null_count != 0:
			last_null_date = data_to_add[data_to_add[['Open','High','Low','Close']].isna().any(axis=1)].index[-1]
			logger.warning(f'Found null values while retrieving {self.ticker_symbol}, dropping rows up to {last_null_date}')
			data_to_add = data_to_add[data_to_add.index > last_null_date]

		if (data_to_add.empty):
			logger.info(f'Download failed, likely yfinance lag, ignoring.')
			result = False
		else:
			self.__ticker_found = True
			logger.info(f'Raw data retrieved:\n {data_to_add}')
			#data_to_add.drop(data_to_add.index[0],inplace=True)
			#logger.info(f'Raw data after dropping first index:\n {data_to_add}')
			data_to_add.index = data_to_add.index.tz_convert('America/New_York')
			data_to_add.index = data_to_add.index.normalize() + pd.Timedelta(hours=16)
			data_to_add.index = data_to_add.index.tz_convert(TIMEZONE)

			logger.info(f'Data retrieved, concatenating to existing CSV: {self.data}')
			logger.info(f'Data to concat:\n{data_to_add}')
			self.csv.append(data_to_add)
			if self.__auto_save:
				self.save_data()
		self.call_listeners()
		return result
	
	def latest_cents(self, col: str = 'Close') -> Optional[int]:
		return self.csv.latest_cents(col)
	
	def get_cents(self, time: dt.datetime, col: str = 'Close') -> Optional[int]:
		return self.csv.get_cents(time, col)
	
	def latest_date(self) -> dt.datetime:
		return self.csv.latest_date()
	
	def prev_date(self, time: dt.datetime) -> dt.datetime:
		return self.csv.prev_date(time)
	
	def prev_or_equal_date(self, time: dt.datetime) -> dt.datetime:
		return self.csv.prev_or_equal_date(time)

	@property
	def ticker_symbol(self) -> str:
		return self.__ticker_symbol
	
	@property
	def ticker_found(self) -> bool:
		return self.__ticker_found

	@property
	def _ticker(self) -> yf.Ticker:
		return self.__ticker