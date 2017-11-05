"""Parser."""

import logging
import os.path
import pickle

from pandas_datareader._utils import RemoteDataError
from pandas_datareader.data import (
    get_data_google,
    get_data_quandl,
    get_data_yahoo,
)
from pandas_datareader.nasdaq_trader import get_nasdaq_symbols

from .base import Quotes
from .utils import get_data_path, timeit


__all__ = (
    'YahooQuotesLoader',
    'GoogleQuotesLoader',
    'QuandleQuotesLoader',
    'get_symbols',
    'get_quotes',
)


logger = logging.getLogger(__name__)


class QuotesLoader:

    source = None
    timeframe = '1D'
    name_format = '%(symbol)s_%(tf)s_%(date_from)s_%(date_to)s.%(ext)s'

    @classmethod
    def _get_file_path(cls, symbol, tf, date_from, date_to):
        fname = cls.name_format % {
            'symbol': symbol,
            'tf': tf,
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat(),
            'ext': 'qdom',
        }
        return os.path.join(get_data_path('stock_data'), fname)

    @classmethod
    def _save_to_disk(cls, fpath, data):
        logger.debug('Saving quotes to a file: %s', fpath)
        with open(fpath, 'wb') as f:
            pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)

    @classmethod
    def _load_from_disk(cls, fpath):
        logger.debug('Loading quotes from a file: %s', fpath)
        with open(fpath, 'rb') as f:
            return pickle.load(f)

    @classmethod
    @timeit
    def get_quotes(cls, symbol, date_from, date_to):
        fpath = cls._get_file_path(
            symbol, cls.timeframe, date_from, date_to)
        if os.path.exists(fpath):
            Quotes.new(cls._load_from_disk(fpath))
        else:
            quotes = cls._get(symbol, date_from, date_to)
            Quotes.new(quotes, source=cls.source)
            cls._save_to_disk(fpath, Quotes)


class YahooQuotesLoader(QuotesLoader):

    source = 'yahoo'

    @classmethod
    def _get(cls, symbol, date_from, date_to):
        return get_data_yahoo(symbol, date_from, date_to)


class GoogleQuotesLoader(QuotesLoader):

    source = 'google'

    @classmethod
    def _get(cls, symbol, date_from, date_to):
        # FIXME: temporary fix
        from pandas_datareader.google.daily import GoogleDailyReader
        GoogleDailyReader.url = 'http://finance.google.com/finance/historical'
        return get_data_google(symbol, date_from, date_to)


class QuandleQuotesLoader(QuotesLoader):

    source = 'quandle'

    @classmethod
    def _get(cls, symbol, date_from, date_to):
        quotes = get_data_quandl(symbol, date_from, date_to)
        quotes.sort_index(inplace=True)
        return quotes


def get_symbols():
    fpath = os.path.join(get_data_path('stock_data'), 'symbols.qdom')
    if os.path.exists(fpath):
        with open(fpath, 'rb') as f:
            symbols = pickle.load(f)
    else:
        symbols = get_nasdaq_symbols()
        symbols.reset_index(inplace=True)
        with open(fpath, 'wb') as f:
            pickle.dump(symbols, f, pickle.HIGHEST_PROTOCOL)
    return symbols


def get_quotes(*args, **kwargs):
    quotes = []
    loaders = [YahooQuotesLoader, GoogleQuotesLoader, QuandleQuotesLoader]
    while loaders:
        loader = loaders.pop(0)
        try:
            quotes = loader.get_quotes(*args, **kwargs)
            break
        except RemoteDataError:
            pass
    return quotes
