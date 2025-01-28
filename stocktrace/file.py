import datetime as dt

from os.path import isfile
from typing import Optional

from stocktrace.logger import Logger as logger
from stocktrace.utils import InitClass, requires_explicit_init, TIMEZONE

class FileQuery:
    """ Contains information relating to a single file request: path, request time, end time
    """
    def __init__(self, file_path: str) -> None:
        logger.info(f'FileQuery.__init__ initializing FileQuery: {file_path=}')
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
    def end_time(self, end_time: dt.datetime) -> None:
        self.__end_time = end_time
    
    @property
    def is_complete(self) -> bool:
        return self.__end_time != None

class FileManager(InitClass):
    @classmethod
    def init(cls) -> None:
        #TODO: Verify File Structure
        logger.info('FileManager.init initializing FileManager')
        cls._initialized = True
    
    @classmethod
    @requires_explicit_init
    def append_file(cls, query: FileQuery, message: str, end: str='\n') -> None:
        logger.debug(f'FileManager.append_file Appending to file {query.file_path} with message: \"{message}\"')
        with open(query.file_path, 'a') as file:
            file.write(message)
            file.write(end)
        query.end_time = dt.datetime.now(TIMEZONE)