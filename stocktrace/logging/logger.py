import datetime as dt

from stocktrace.utils import InitClass, requires_init, TIMEZONE

DEFAULT_LOG_PATH = 'stocktrace/data/logs/'
DEFAULT_LOG_FILE_NAME = 'debug'

class LOG_LEVEL:
	INFO = 0
	DEBUG = 1
	WARNING = 2
	CRITICAL = 3

class Log:
	def __init__(self, file_name: str, file_path: str, log_level: int=LOG_LEVEL.INFO):
		self.__file_name = file_name
		self.__file_path = file_path
		self.__log_level = log_level

	def write_log(self, text: str, message_level: int, end='\n') -> None:
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
				raise NameError(f'Log level {log_level} not found')
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

class Logger(InitClass):
	@classmethod
	def init(cls):
		cls._initialized = True;
		cls._logs = []
		cls._logs.append(Log(DEFAULT_LOG_FILE_NAME, DEFAULT_LOG_PATH))

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
	def append_log(cls, log: Log):
		cls._logs.append(log)

	@classmethod
	def _propagate_log(cls, message: str, log_level: int):
		for log in cls._logs:
			log.write_log(message, log_level)