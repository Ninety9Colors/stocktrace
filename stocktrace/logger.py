import os

import datetime as dt

from stocktrace.utils import InitClass, requires_init, TIMEZONE

DEFAULT_LOG_PATH = 'logs/'
DEFAULT_LOG_FILE_NAME = 'debug'
DEFAULT_MAX_LOG_COUNT = 10

class LOG_LEVEL:
	INFO = 0
	DEBUG = 1
	WARNING = 2
	CRITICAL = 3

class TerminalLog:
	def __init__(self, log_level: int=LOG_LEVEL.INFO):
		self.__log_level = log_level

	def write_log(self, text: str, message_level: int=LOG_LEVEL.INFO, end='\n') -> None:
		if message_level < self.log_level:
			return

		now = dt.datetime.now(TIMEZONE)
		time_string = now.strftime('%m-%d %H:%M:%S %Z')
		level_string = self.level_string(message_level)
		message = time_string + ' ' + level_string + ' ' + text
		print(message, end=end)

	def level_string(self, message_level: int) -> str:
		match message_level:
			case LOG_LEVEL.INFO:
				return 'INFO'
			case LOG_LEVEL.DEBUG:
				return 'DEBUG'
			case LOG_LEVEL.WARNING:
				return 'WARNING'
			case LOG_LEVEL.CRITICAL:
				return 'CRITICAL'
			case _:
				raise NameError(f'Log level {self.log_level} not found')

	@property
	def log_level(self) -> int:
		return self.__log_level

class FileLog:
	def __init__(self, file_name: str, file_path: str, log_level: int=LOG_LEVEL.INFO):
		self.__file_name = file_name
		self.__file_path = file_path
		self.__log_level = log_level

	def write_log(self, text: str, message_level: int=LOG_LEVEL.INFO, end='\n') -> None:
		if message_level < self.log_level:
			return

		now = dt.datetime.now(TIMEZONE)
		time_string = now.strftime('%m-%d %H:%M:%S %Z')
		level_string = self.level_string(message_level)
		message = time_string + ' ' + level_string + ' ' + text
		with open(self.file_path+self.file_name+'_'+now.strftime('%Y-%m-%d')+'.log', 'a') as file:
			file.write(message)
			file.write(end)

	def level_string(self, message_level: int) -> str:
		match message_level:
			case LOG_LEVEL.INFO:
				return 'INFO'
			case LOG_LEVEL.DEBUG:
				return 'DEBUG'
			case LOG_LEVEL.WARNING:
				return 'WARNING'
			case LOG_LEVEL.CRITICAL:
				return 'CRITICAL'
			case _:
				raise NameError(f'Log level {self.log_level} not found')
				return ''

	@property
	def file_name(self) -> str:
		return self.__file_name

	@property
	def file_path(self) -> str:
		return self.__file_path

	@property
	def log_level(self) -> int:
		return self.__log_level

class CircularLog(FileLog):
	def __init__(self, file_name: str, file_path: str, log_level: int=LOG_LEVEL.INFO, max_log_count: int=5) -> None:
		super().__init__(file_name, file_path, log_level)
		self.__max_log_count = max_log_count

	def write_log(self, text: str, message_level: int=LOG_LEVEL.INFO, end='\n') -> None:
		super().write_log(text, message_level, end)
		self._verify_circular()

	def _verify_circular(self) -> None:
		# Create list of files in the log directory
		it = os.scandir(self.file_path)
		files = []
		for file in it:
			if self.file_name in file.name:
				files.append(file)

		# Sort by time, and remove old ones if there are too many
		files.sort(key=lambda file: -file.stat().st_birthtime)
		for i in range(len(files)-1, self.max_log_count-1, -1):
			os.remove(files[i].path)

	@property
	def max_log_count(self) -> int:
		return self.__max_log_count

class Logger(InitClass):
	@classmethod
	def init(cls):
		cls._initialized = True
		cls.__logs = []
		cls.__logs.append(CircularLog(DEFAULT_LOG_FILE_NAME, DEFAULT_LOG_PATH, max_log_count=DEFAULT_MAX_LOG_COUNT))
		cls.__logs.append(TerminalLog())
		cls.info('--- Logger Initialized ---')

	@classmethod
	@requires_init
	def info(cls, message):
		cls._propagate_log(message, LOG_LEVEL.INFO)

	@classmethod
	@requires_init
	def debug(cls, message):
		cls._propagate_log(message, LOG_LEVEL.DEBUG)

	@classmethod
	@requires_init
	def warning(cls, message):
		cls._propagate_log(message, LOG_LEVEL.WARNING)

	@classmethod
	@requires_init
	def critical(cls, message):
		cls._propagate_log(message, LOG_LEVEL.CRITICAL)

	@classmethod
	@requires_init
	def append_log(cls, log: FileLog):
		cls.__logs.append(log)

	@classmethod
	def _propagate_log(cls, message: str, log_level: int):
		for log in cls.__logs:
			log.write_log(message, log_level)