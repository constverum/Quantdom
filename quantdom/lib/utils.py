"""Utils."""

import importlib.util
import inspect
import logging
import os
import os.path
import sys
import time
from datetime import datetime
from functools import wraps

from PyQt5 import QtCore

__all__ = (
    'BASE_DIR',
    'Settings',
    'timeit',
    'fromtimestamp',
    'get_data_path',
    'get_resource_path',
    'strategies_from_file',
)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_path(path=''):
    data_path = QtCore.QStandardPaths.writableLocation(
        QtCore.QStandardPaths.AppDataLocation
    )
    data_path = os.path.join(data_path, path)
    os.makedirs(data_path, mode=0o755, exist_ok=True)
    return data_path


def get_resource_path(relative_path):
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    base_path = getattr(sys, '_MEIPASS', BASE_DIR)
    return os.path.join(base_path, relative_path)


config_path = os.path.join(get_data_path(), 'Quantdom', 'config.ini')
Settings = QtCore.QSettings(config_path, QtCore.QSettings.IniFormat)


def timeit(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        t = time.time()
        res = fn(*args, **kwargs)
        logger = logging.getLogger('runtime')
        logger.debug(
            '%s.%s: %.4f sec'
            % (fn.__module__, fn.__qualname__, time.time() - t)
        )
        return res

    return wrapper


def fromtimestamp(timestamp):
    if timestamp == 0:
        # on Win zero timestamp cause error
        return datetime(1970, 1, 1)
    return datetime.fromtimestamp(timestamp)


def strategies_from_file(filepath):
    from .strategy import AbstractStrategy

    spec = importlib.util.spec_from_file_location('Strategy', filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    is_strategy = lambda _class: (  # noqa:E731
        inspect.isclass(_class)
        and issubclass(_class, AbstractStrategy)
        and _class.__name__ != 'AbstractStrategy'
    )
    return [_class for _, _class in inspect.getmembers(module, is_strategy)]
