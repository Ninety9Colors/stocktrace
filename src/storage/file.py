import datetime as dt
import os
import modin.pandas as pd

from typing import Optional

# TODO: Get timezone from settings
TIMEZONE = dt.UTC

class FileQuery:
    """ Contains information relating to a single file request: path, request time, end time
    """
    def __init__(self, file_path: str):
        self.__file_path = file_path

        self.__begin_time = dt.datetime.now(TIMEZONE)
        self.__end_time = None
    
    @property
    def file_path(self) -> str:
        return self.__file_path
    
    @property
    def begin_time(self) -> dt.datetime:
        return self.__begin_time
    
    @property
    def end_time(self) -> Optional[dt.datetime]:
        return self.__end_time
    
    @end_time.setter
    def end_time(self, end_time: dt.datetime):
        self.__end_time = end_time
    
    @property
    def is_complete(self) -> bool:
        return self.__end_time != None

def requires_init(func):
    def wrapper(cls, *args, **kwargs):
        assert cls._initialized == True
        return func(cls, *args, **kwargs)
    return wrapper

class FileManager:
    _initialized: bool = False
    @classmethod
    def init(cls):
        #TODO: Verify File Structure
        cls._initialized = True
    
    @classmethod
    @requires_init
    def append_file(cls, query: FileQuery, message: pd.DataFrame, header=False, index=False):
        file_exists: bool = header and not os.path.isfile(query.file_path)
        message.to_csv(query.file_path, mode='a', header=file_exists, sep='\t', index=index, quoting=3, escapechar='\\')
        query.end_time = dt.datetime.now(TIMEZONE)