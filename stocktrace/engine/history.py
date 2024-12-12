from abc import ABC, abstractmethod
import datetime as dt
import os
import pandas as pd
import yfinance as yf

from stocktrace.logging.logger import Logger as logger

from stocktrace.utils import TIMEZONE, interval_to_timedelta

class History(ABC):
	def __init__(self, file_path: str, interval: str='1d') -> None:
		self.__file_path = file_path
		self.__interval = interval
		logger.info(f'Checking if data file {self.file_path} exists')
		if os.path.isfile(file_path):
			logger.info('File exists, parsing CSV')
			self._parse_csv()
			self.update_data()
		else:
			logger.info('File does not exist, calling init_data function')
			self._init_data()

	@abstractmethod
	def update_data() -> None:
		pass

	@abstractmethod
	def _init_data() -> None:
		pass
	
	@property
	def file_path(self) -> str:
		return self.__file_path

	@property
	def interval(self) -> str:
		return self.__interval

	@property
	def data(self) -> pd.DataFrame:
		return self.__data

	@data.setter
	def data(self, new_data: pd.DataFrame) -> None:
		self.__data = new_data

	def _parse_csv(self) -> None:
		self.__data = pd.read_csv(self.file_path, parse_dates=True)
		self.data.index = pd.to_datetime(self.data['Date'])
		self.data.drop(columns=self.data.columns[0], axis=1, inplace=True)
		logger.info(f'Parsed CSV:\n{self.data}')
	
	def __repr__(self) -> str:
		return self.data.__repr__()
	
class AssetHistory(History):
	def __init__(self, ticker_symbol: str, file_path: str, interval: str='1d') -> None:
		logger.debug(f'AssetHistory.__init__ Creating AssetHistory with ticker symbol {ticker_symbol}, file path {file_path}, interval {interval}')

		self.__ticker_symbol = ticker_symbol
		self.__ticker = yf.Ticker(self.ticker_symbol)
		super().__init__(file_path, interval)
	
	def update_data(self) -> None:
		logger.info(f'AssetHistory.update_data Retrieving recent data of {self.ticker_symbol}')
		last_updated = pd.to_datetime(self.data.index.max())
		current_date = dt.datetime.now(TIMEZONE)

		logger.info(f'Date of most recent data row: {last_updated}')
		start = last_updated+interval_to_timedelta(self.interval)
		if (start >= current_date):
			logger.info(f'Data is up to current date {current_date}, continuing...')
			return
		data_to_add = self._ticker.history(interval=self.interval, start=last_updated+interval_to_timedelta(self.interval), end=current_date)
		data_to_add.index = data_to_add.index.tz_convert(TIMEZONE)

		logger.info(f'Data retrieved, concatenating to existing {self.file_path}')
		logger.info(f'Data to concat:\n{data_to_add}')
		self.data = pd.concat([self.data, data_to_add])

		logger.info(f'Writing to file {self.file_path}')
		self.data.to_csv(self.file_path)
	
	def _init_data(self) -> None:
		logger.info(f'AssetHistory.init_data AssetHistory with ticker symbol {self.ticker_symbol} does not have data. Retrieving data from yfinance...')
		self.data = self._ticker.history(interval=self.interval, period='max')
		self.data.index = self.data.index.tz_convert(TIMEZONE)

		logger.info(f'Data retrieved, writing to csv...')
		self.data.to_csv(self.file_path)

	@property
	def ticker_symbol(self) -> str:
		return self.__ticker_symbol

	@property
	def _ticker(self) -> yf.Ticker:
		return self.__ticker