"""Parser."""

import logging
import os.path
import pickle

import pandas as pd
import pandas_datareader.data as web
from pandas_datareader._utils import RemoteDataError
from pandas_datareader.data import (
    get_data_google,
    get_data_quandl,
    get_data_yahoo,
    get_data_alphavantage,
)
from pandas_datareader.nasdaq_trader import get_nasdaq_symbols
from pandas_datareader.exceptions import ImmediateDeprecationError

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
    sort_index = False
    default_tf = None
    name_format = '%(symbol)s_%(tf)s_%(date_from)s_%(date_to)s.%(ext)s'

    @classmethod
    def _get(cls, symbol, date_from, date_to):
        quotes = web.DataReader(
            symbol, cls.source, start=date_from, end=date_to
        )
        if cls.sort_index:
            quotes.sort_index(inplace=True)
        return quotes

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
        quotes = None
        fpath = cls._get_file_path(symbol, cls.timeframe, date_from, date_to)
        if os.path.exists(fpath):
            quotes = Quotes.new(cls._load_from_disk(fpath))
        else:
            quotes_raw = cls._get(symbol, date_from, date_to)
            quotes = Quotes.new(
                quotes_raw, source=cls.source, default_tf=cls.default_tf
            )
            cls._save_to_disk(fpath, quotes)
        return quotes


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


class AlphaVantageQuotesLoader(QuotesLoader):

    source = 'alphavantage'
    api_key = 'demo'

    @classmethod
    def _get(cls, symbol, date_from, date_to):
        quotes = get_data_alphavantage(
            symbol, date_from, date_to, api_key=cls.api_key
        )
        return quotes


class StooqQuotesLoader(QuotesLoader):

    source = 'stooq'
    sort_index = True
    default_tf = 1440


class IEXQuotesLoader(QuotesLoader):

    source = 'iex'

    @classmethod
    def _get(cls, symbol, date_from, date_to):
        quotes = web.DataReader(
            symbol, cls.source, start=date_from, end=date_to
        )
        quotes['Date'] = pd.to_datetime(quotes.index)
        return quotes


class RobinhoodQuotesLoader(QuotesLoader):

    source = 'robinhood'


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
    # don't work:
    # GoogleQuotesLoader, QuandleQuotesLoader,
    # AlphaVantageQuotesLoader, RobinhoodQuotesLoader
    loaders = [YahooQuotesLoader, IEXQuotesLoader, StooqQuotesLoader]
    while loaders:
        loader = loaders.pop(0)
        try:
            quotes = loader.get_quotes(*args, **kwargs)
            break
        except (RemoteDataError, ImmediateDeprecationError) as e:
            logger.error('get_quotes => error: %r', e)
    return quotes
