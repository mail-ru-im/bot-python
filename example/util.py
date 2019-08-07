import logging
import os
import random
import sys
from enum import Enum
from functools import wraps
from logging.handlers import TimedRotatingFileHandler


class DynamicTimedRotatingFileHandler(TimedRotatingFileHandler):
    # noinspection PyPep8Naming
    def __init__(self, filename, when='h', interval=1, backupCount=0, encoding=None, delay=False, utc=False):
        dir_name = os.path.dirname(filename)
        file_name = os.path.basename(filename)
        script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        filename = os.path.join(dir_name, script_name + file_name)

        if dir_name:
            try:
                os.makedirs(dir_name)
            except OSError:
                if not os.path.isdir(dir_name):
                    raise

        super(DynamicTimedRotatingFileHandler, self).__init__(
            filename=filename, when=when, interval=interval, backupCount=backupCount, encoding=encoding, delay=delay,
            utc=utc
        )


class LineBreakFormatter(logging.Formatter):
    def format(self, record):
        return super(LineBreakFormatter, self).format(record) + "\n"


def random_choice(sequence):
    """ Same as :meth:`random.choice`, but also supports :class:`set` type to be passed as sequence. """
    return random.choice(tuple(sequence) if isinstance(sequence, set) else sequence)


def log_call(func):
    logger = logging.getLogger(func.__module__)

    @wraps(func)
    def _log(self, *args, **kwargs):
        logger.debug("Entering function: '{}'.".format(func.__qualname__))
        result = func(self, *args, **kwargs)
        logger.debug("Result is: '{}'.".format(result))
        logger.debug("Exiting function: '{}'.".format(func.__qualname__))
        return result

    return _log


class AutoNumberEnum(Enum):
    def __new__(cls):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj


def mean(data):
    return float(sum(data)) / max(len(data), 1)
