import datetime as dt

import stocktrace.logging.logger as logger

# TODO: Get timezone from settings
TIMEZONE = dt.timezone(dt.timedelta(hours=-6))

class InitClass:
    _initialized: bool = False

def requires_explicit_init(func):
    def wrapper(cls, *args, **kwargs):
        if not cls._initialized:
            logger.Logger.critical(f'{cls.__name__} not explicitly initialized, raising RuntimeError')
            raise RuntimeError(f'{cls.__name__} is not initialized')
        return func(cls, *args, **kwargs)
    return wrapper

def requires_init(func):
    def wrapper(cls, *args, **kwargs):
        if not cls._initialized:
            cls.init()
        return func(cls, *args, **kwargs)
    return wrapper