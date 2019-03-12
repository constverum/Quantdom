"""Base classes."""

from enum import Enum, auto

import numpy as np
import pandas as pd

from .const import ChartType, TimeFrame

__all__ = ('Indicator', 'Symbol', 'Quotes')


class BaseQuotes(np.recarray):
    def __new__(cls, shape=None, dtype=None, order='C'):
        dt = np.dtype(
            [
                ('id', int),
                ('time', float),
                ('open', float),
                ('high', float),
                ('low', float),
                ('close', float),
                ('volume', int),
            ]
        )
        shape = shape or (1,)
        return np.ndarray.__new__(cls, shape, (np.record, dt), order=order)

    def _nan_to_closest_num(self):
        """Return interpolated values instead of NaN."""
        for col in ['open', 'high', 'low', 'close']:
            mask = np.isnan(self[col])
            if not mask.size:
                continue
            self[col][mask] = np.interp(
                np.flatnonzero(mask), np.flatnonzero(~mask), self[col][~mask]
            )

    def _set_time_frame(self, default_tf):
        tf = {
            1: TimeFrame.M1,
            5: TimeFrame.M5,
            15: TimeFrame.M15,
            30: TimeFrame.M30,
            60: TimeFrame.H1,
            240: TimeFrame.H4,
            1440: TimeFrame.D1,
        }
        minutes = int(np.diff(self.time[-10:]).min() / 60)
        self.timeframe = tf.get(minutes) or tf[default_tf]

    def new(self, data, source=None, default_tf=None):
        shape = (len(data),)
        self.resize(shape, refcheck=False)

        if isinstance(data, pd.DataFrame):
            data.reset_index(inplace=True)
            data.insert(0, 'id', data.index)
            data.Date = self.convert_dates(data.Date)
            data = data.rename(
                columns={
                    'Date': 'time',
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume',
                }
            )
            for name in self.dtype.names:
                self[name] = data[name]
        elif isinstance(data, (np.recarray, BaseQuotes)):
            self[:] = data[:]

        self._nan_to_closest_num()
        self._set_time_frame(default_tf)
        return self

    def convert_dates(self, dates):
        return np.array([d.timestamp() for d in dates])


class SymbolType(Enum):
    FOREX = auto()
    CFD = auto()
    FUTURES = auto()
    SHARES = auto()


class Symbol:

    FOREX = SymbolType.FOREX
    CFD = SymbolType.CFD
    FUTURES = SymbolType.FUTURES
    SHARES = SymbolType.SHARES

    def __init__(self, ticker, mode, tick_size=0, tick_value=None):
        self.ticker = ticker
        self.mode = mode
        if self.mode in [self.FOREX, self.CFD]:
            # number of units of the commodity, currency
            # or financial asset in one lot
            self.contract_size = 100_000  # (100000 == 1 Lot)
        elif self.mode == self.FUTURES:
            # cost of a single price change point ($10) /
            # one minimum price movement
            self.tick_value = tick_value
        # minimum price change step (0.0001)
        self.tick_size = tick_size
        if isinstance(tick_size, float):
            self.digits = len(str(tick_size).split('.')[1])
        else:
            self.digits = 0

    def __repr__(self):
        return 'Symbol (%s | %s)' % (self.ticker, self.mode)


class Indicator:
    def __init__(
        self, label=None, window=None, data=None, tp=None, base=None, **kwargs
    ):
        self.label = label
        self.window = window
        self.data = data or [0]
        self.type = tp or ChartType.LINE
        self.base = base or {'linewidth': 0.5, 'color': 'black'}
        self.lineStyle = {'linestyle': '-', 'linewidth': 0.5, 'color': 'blue'}
        self.lineStyle.update(kwargs)


Quotes = BaseQuotes()
