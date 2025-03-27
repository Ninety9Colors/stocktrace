import datetime as dt
from math import ceil
import pandas as pd

from os.path import isfile
from typing import Optional

from stocktrace.logger import Logger as logger
from stocktrace.utils import TIMEZONE

class CSV:
    def __init__(self, file_path: str) -> None:
        logger.debug(f'CSV.__init__ Creating CSV with file path {file_path}')
        self.__file_path = file_path
        self._data = pd.DataFrame()
        self.__file_length = 0
        self.data
    
    def save(self) -> None:
        if self._data.empty:
            return
        logger.debug(f'CSV.save() saving data of {self.file_path}...')
        if self.__file_length == 0:
            self._data.to_csv(self.__file_path)
            self.__file_length = len(self._data.index)
        elif self.__file_length < len(self.data.index):
            append_data = self._data.iloc[self.__file_length:]
            append_data.to_csv(self.__file_path, mode='a', header=False)
            self.__file_length = len(self.data.index)
    
    def append(self, data: pd.DataFrame) -> None:
        logger.info(f'CSV.append() appending data to {self.file_path}')
        if self._data.empty:
            self._data = data
        else:
            self._data = pd.concat([self._data, data])
    
    def read_csv(self) -> None:
        self._data = pd.read_csv(self.__file_path, index_col=0)
    
    @property
    def data(self) -> pd.DataFrame:
        if self._data.empty and isfile(self.__file_path):
            self.read_csv()
            self.__file_length = len(self._data.index)
        return self._data

    @property
    def file_path(self) -> str:
        return self.__file_path

class TIME_CSV(CSV):
    def __init__(self, file_path: str) -> None:
        super().__init__(file_path)
    
    def read_csv(self) -> None:
        self._data = pd.read_csv(self.file_path, parse_dates=[0], index_col=0)

    def get_cents(self, time: dt.datetime, col: str = 'Close') -> Optional[int]:
        # logger.info(f'CSV.get_cents() getting {col} at {time} from {self.file_path} ...')
        time = self.prev_or_equal_date(time)
        try:
            result = ceil(self.data.loc[time][col]*100)
            # logger.info(f'... {result}')
            return result
        except KeyError:
            logger.warning(f'CSV.get_cents() could not find date {time} in {self.file_path}')
            return None
    
    def prev_date(self, time: dt.datetime) -> dt.datetime:
        if self.data.empty:
            logger.warning(f'CSV.prev_date() no data in {self.file_path}')
            return dt.datetime.min.replace(tzinfo=TIMEZONE)
        try:
            return self._data.index[self._data.index < time][-1]
        except IndexError:
            logger.warning(f'CSV.prev_date() could not find previous date to {time} in {self.file_path}')
            return dt.datetime.min.replace(tzinfo=TIMEZONE)
    
    def prev_or_equal_date(self, time: dt.datetime) -> dt.datetime:
        if self.data.empty:
            logger.warning(f'CSV.prev_or_equal_date() no data in {self.file_path}')
            return dt.datetime.min.replace(tzinfo=TIMEZONE)
        try:
            return self._data.index[self._data.index <= time][-1]
        except IndexError:
            logger.warning(f'CSV.prev_or_equal_date() could not find previous or equal date to {time} in {self.file_path}')
            return dt.datetime.min.replace(tzinfo=TIMEZONE)
        
    def latest_date(self) -> dt.datetime:
        if self.data.empty:
            logger.warning(f'CSV.latest_date() no data in {self.file_path}')
            return dt.datetime.min.replace(tzinfo=TIMEZONE)
        return pd.to_datetime(self.data.index.max()).replace(tzinfo=TIMEZONE)
    
    def latest_cents(self, col: str = 'Close') -> Optional[int]:
        if self.data.empty:
            logger.warning(f'CSV.latest_cents() no data in {self.file_path}')
            return None
        return ceil(self.data[col][-1]*100)