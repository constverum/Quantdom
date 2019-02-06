"""Abstract strategy."""

import inspect
import logging
from abc import ABC, abstractmethod

from .base import Quotes
from .utils import timeit

__all__ = ('AbstractStrategy',)


logger = logging.getLogger(__name__)


class AbstractStrategy(ABC):
    def __init__(self, name=None, period=None, symbols=None):
        self.name = name or self.__class__.__name__
        self.period = period
        # it comes a list of symbols. temporary we support only the first one
        self.symbols = symbols
        self.symbol = symbols[0]
        # deposit ?

    @classmethod
    def get_name(cls):
        return cls.__name__

    @timeit
    def run(self):
        logger.debug('Starting backtest of strategy: %s', self.name)
        self.start()
        logger.debug('Backtest is done.')
        args = inspect.getfullargspec(self.init).args[1:]
        defaults = inspect.getfullargspec(self.init).defaults
        self.kwargs = dict(zip(args, defaults))

    def start(self, *args, **kwargs):
        self.init(*args, **kwargs)
        for quote in Quotes:
            self.handle(quote)

    @abstractmethod
    def init(self):
        """Called once at start.

        Initialize the backtest parameters.
        * kwargs - are parameters that you want to optimize.
        """

    @abstractmethod
    def handle(self, quote):
        """Called for each iteration (on every bar received)."""
