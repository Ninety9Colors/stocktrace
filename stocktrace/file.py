import datetime as dt
import pandas as pd

from os.path import isfile
from typing import Optional

from stocktrace.logger import Logger as logger
from stocktrace.utils import InitClass, requires_explicit_init, TIMEZONE

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
        
    def latest_date(self) -> dt.datetime:
        if self.data.empty:
            return dt.datetime.min.replace(tzinfo=TIMEZONE)
        return pd.to_datetime(self.data.index.max()).replace(tzinfo=TIMEZONE)
    
    @property
    def data(self) -> pd.DataFrame:
        if self.__data.empty and isfile(self.__file_path):
            self.__data = pd.read_csv(self.__file_path, parse_dates=[0], index_col=0)
        return self.__data

    @property
    def file_path(self) -> str:
        return self.__file_path