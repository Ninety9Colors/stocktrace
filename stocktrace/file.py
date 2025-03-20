import datetime as dt
from math import ceil
import pandas as pd

from os.path import isfile
from typing import Optional

from stocktrace.logger import Logger as logger
from stocktrace.utils import TIMEZONE

class CSV:
    def __init__(self, file_path: str, lazy_load = True) -> None:
        logger.debug(f'CSV.__init__ Creating CSV with file path {file_path} and lazy_load {lazy_load}')
        self.__file_path = file_path
        self.__data = pd.DataFrame()
        self.__append_indice = -1
        if not lazy_load:
            self.data
    
    def save(self) -> None:
        if self.__data.empty:
            return
        logger.debug(f'CSV.save() saving data of {self.file_path}...')
        if self.__append_indice != -1:
            append_data = self.__data.iloc[self.__append_indice:]
            append_data.to_csv(self.__file_path, mode='a', header=False)
        else:
            self.__data.to_csv(self.__file_path)
    
    def append(self, data: pd.DataFrame) -> None:
        logger.info(f'CSV.append() appending data to {self.file_path}')
        if self.__data.empty:
            self.__data = data
        else:
            if self.__append_indice == -1:
                self.__append_indice = len(self.__data.index)
            self.__data = pd.concat([self.__data, data])

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
            return self.__data.index[self.__data.index < time][-1]
        except IndexError:
            logger.warning(f'CSV.prev_date() could not find previous date to {time} in {self.file_path}')
            return dt.datetime.min.replace(tzinfo=TIMEZONE)
    
    def prev_or_equal_date(self, time: dt.datetime) -> dt.datetime:
        if self.data.empty:
            logger.warning(f'CSV.prev_or_equal_date() no data in {self.file_path}')
            return dt.datetime.min.replace(tzinfo=TIMEZONE)
        try:
            return self.__data.index[self.__data.index <= time][-1]
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
    
    @property
    def data(self) -> pd.DataFrame:
        if self.__data.empty and isfile(self.__file_path):
            self.__data = pd.read_csv(self.__file_path, parse_dates=[0], index_col=0)
        return self.__data

    @property
    def file_path(self) -> str:
        return self.__file_path