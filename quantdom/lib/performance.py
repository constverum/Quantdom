"""Performance."""

import codecs
import json
from collections import OrderedDict, defaultdict

import numpy as np

from .base import Quotes
from .const import ANNUAL_PERIOD
from .utils import fromtimestamp, get_resource_path

__all__ = (
    'BriefPerformance',
    'Performance',
    'Stats',
    'REPORT_COLUMNS',
    'REPORT_ROWS',
)


REPORT_COLUMNS = ('All', 'Long', 'Short', 'Market')
with codecs.open(
    get_resource_path('report_rows.json'), mode='r', encoding='utf-8'
) as f:
    REPORT_ROWS = OrderedDict(json.load(f))


class Stats(np.recarray):
    def __new__(cls, positions, shape=None, dtype=None, order='C'):
        shape = shape or (len(positions['All']),)
        dtype = np.dtype(
            [
                ('type', object),
                ('symbol', object),
                ('volume', float),
                ('open_time', float),
                ('close_time', float),
                ('open_price', float),
                ('close_price', float),
                ('total_profit', float),
                ('entry_name', object),
                ('exit_name', object),
                ('status', object),
                ('comment', object),
                ('abs', float),
                ('perc', float),
                ('bars', float),
                ('on_bar', float),
                ('mae', float),
                ('mfe', float),
            ]
        )
        dt = [(col, dtype) for col in REPORT_COLUMNS]
        return np.ndarray.__new__(cls, shape, (np.record, dt), order=order)

    def __init__(self, positions, **kwargs):
        for col, _positions in positions.items():
            for i, p in enumerate(_positions):
                self._add_position(p, col, i)

    def _add_position(self, p, col, i):
        self[col][i].type = p.type
        self[col][i].symbol = p.symbol
        self[col][i].volume = p.volume
        self[col][i].open_time = p.open_time
        self[col][i].close_time = p.close_time
        self[col][i].open_price = p.open_price
        self[col][i].close_price = p.close_price
        self[col][i].total_profit = p.total_profit
        self[col][i].entry_name = p.entry_name
        self[col][i].exit_name = p.exit_name
        self[col][i].status = p.status
        self[col][i].comment = p.comment
        self[col][i].abs = p.profit
        self[col][i].perc = p.profit_perc

        quotes_on_trade = Quotes[p.id_bar_open : p.id_bar_close]

        if not quotes_on_trade.size:
            # if position was opened and closed on the last bar
            quotes_on_trade = Quotes[p.id_bar_open : p.id_bar_close + 1]

        kwargs = {
            'low': quotes_on_trade.low.min(),
            'high': quotes_on_trade.high.max(),
        }
        self[col][i].mae = p.calc_mae(**kwargs)
        self[col][i].mfe = p.calc_mfe(**kwargs)

        bars = p.id_bar_close - p.id_bar_open
        self[col][i].bars = bars
        self[col][i].on_bar = p.profit_perc / bars


class BriefPerformance(np.recarray):
    def __new__(cls, shape=None, dtype=None, order='C'):
        dt = np.dtype(
            [
                ('kwargs', object),
                ('net_profit_abs', float),
                ('net_profit_perc', float),
                ('year_profit', float),
                ('win_average_profit_perc', float),
                ('loss_average_profit_perc', float),
                ('max_drawdown_abs', float),
                ('total_trades', int),
                ('win_trades_abs', int),
                ('win_trades_perc', float),
                ('profit_factor', float),
                ('recovery_factor', float),
                ('payoff_ratio', float),
            ]
        )
        shape = shape or (1,)
        return np.ndarray.__new__(cls, shape, (np.record, dt), order=order)

    def _days_count(self, positions):
        if hasattr(self, 'days'):
            return self.days
        self.days = (
            (
                fromtimestamp(positions[-1].close_time)
                - fromtimestamp(positions[0].open_time)
            ).days
            if positions
            else 1
        )
        return self.days

    def add(self, initial_balance, positions, i, kwargs):
        position_count = len(positions)
        profit = np.recarray(
            (position_count,), dtype=[('abs', float), ('perc', float)]
        )
        for n, position in enumerate(positions):
            profit[n].abs = position.profit
            profit[n].perc = position.profit_perc
        s = self[i]
        s.kwargs = kwargs
        s.net_profit_abs = np.sum(profit.abs)
        s.net_profit_perc = np.sum(profit.perc)
        days = self._days_count(positions)
        gain_factor = (s.net_profit_abs + initial_balance) / initial_balance
        s.year_profit = (gain_factor ** (365 / days) - 1) * 100
        s.win_average_profit_perc = np.mean(profit.perc[profit.perc > 0])
        s.loss_average_profit_perc = np.mean(profit.perc[profit.perc < 0])
        s.max_drawdown_abs = profit.abs.min()
        s.total_trades = position_count
        wins = profit.abs[profit.abs > 0]
        loss = profit.abs[profit.abs < 0]
        s.win_trades_abs = len(wins)
        s.win_trades_perc = round(s.win_trades_abs / s.total_trades * 100, 2)
        s.profit_factor = abs(np.sum(wins) / np.sum(loss))
        s.recovery_factor = abs(s.net_profit_abs / s.max_drawdown_abs)
        s.payoff_ratio = abs(np.mean(wins) / np.mean(loss))


class Performance:
    """Performance Metrics."""

    rows = REPORT_ROWS
    columns = REPORT_COLUMNS

    def __init__(self, initial_balance, stats, positions):
        self._data = {}
        for col in self.columns:
            column = type('Column', (object,), dict.fromkeys(self.rows, 0))
            column.initial_balance = initial_balance
            self._data[col] = column
            self.calculate(column, stats[col], positions[col])

    def __getitem__(self, col):
        return self._data[col]

    def _calc_trade_series(self, col, positions):
        win_in_series, loss_in_series = 0, 0
        for i, p in enumerate(positions):
            if p.profit >= 0:
                win_in_series += 1
                loss_in_series = 0
                if win_in_series > col.win_in_series:
                    col.win_in_series = win_in_series
            else:
                win_in_series = 0
                loss_in_series += 1
                if loss_in_series > col.loss_in_series:
                    col.loss_in_series = loss_in_series

    def calculate(self, col, stats, positions):
        self._calc_trade_series(col, positions)

        col.total_trades = len(positions)

        profit_abs = stats[np.flatnonzero(stats.abs)].abs
        profit_perc = stats[np.flatnonzero(stats.perc)].perc
        bars = stats[np.flatnonzero(stats.bars)].bars
        on_bar = stats[np.flatnonzero(stats.on_bar)].on_bar

        gt_zero_abs = stats[stats.abs > 0].abs
        gt_zero_perc = stats[stats.perc > 0].perc
        win_bars = stats[stats.perc > 0].bars

        lt_zero_abs = stats[stats.abs < 0].abs
        lt_zero_perc = stats[stats.perc < 0].perc
        los_bars = stats[stats.perc < 0].bars

        col.average_profit_abs = np.mean(profit_abs) if profit_abs.size else 0
        col.average_profit_perc = (
            np.mean(profit_perc) if profit_perc.size else 0
        )
        col.bars_on_trade = np.mean(bars) if bars.size else 0
        col.bar_profit = np.mean(on_bar) if on_bar.size else 0

        col.win_average_profit_abs = (
            np.mean(gt_zero_abs) if gt_zero_abs.size else 0
        )
        col.win_average_profit_perc = (
            np.mean(gt_zero_perc) if gt_zero_perc.size else 0
        )
        col.win_bars_on_trade = np.mean(win_bars) if win_bars.size else 0

        col.loss_average_profit_abs = (
            np.mean(lt_zero_abs) if lt_zero_abs.size else 0
        )
        col.loss_average_profit_perc = (
            np.mean(lt_zero_perc) if lt_zero_perc.size else 0
        )
        col.loss_bars_on_trade = np.mean(los_bars) if los_bars.size else 0

        col.win_trades_abs = len(gt_zero_abs)
        col.win_trades_perc = (
            round(col.win_trades_abs / col.total_trades * 100, 2)
            if col.total_trades
            else 0
        )

        col.loss_trades_abs = len(lt_zero_abs)
        col.loss_trades_perc = (
            round(col.loss_trades_abs / col.total_trades * 100, 2)
            if col.total_trades
            else 0
        )

        col.total_profit = np.sum(gt_zero_abs)
        col.total_loss = np.sum(lt_zero_abs)
        col.net_profit_abs = np.sum(stats.abs)
        col.net_profit_perc = np.sum(stats.perc)
        col.total_mae = np.sum(stats.mae)
        col.total_mfe = np.sum(stats.mfe)

        # https://financial-calculators.com/roi-calculator

        days = (
            (
                fromtimestamp(positions[-1].close_time)
                - fromtimestamp(positions[0].open_time)
            ).days
            if positions
            else 1
        )
        gain_factor = (
            col.net_profit_abs + col.initial_balance
        ) / col.initial_balance
        col.year_profit = (gain_factor ** (365 / days) - 1) * 100
        col.month_profit = (gain_factor ** (365 / days / 12) - 1) * 100

        col.max_profit_abs = stats.abs.max()
        col.max_profit_perc = stats.perc.max()
        col.max_profit_abs_day = fromtimestamp(
            stats.close_time[stats.abs == col.max_profit_abs][0]
        )
        col.max_profit_perc_day = fromtimestamp(
            stats.close_time[stats.perc == col.max_profit_perc][0]
        )

        col.max_drawdown_abs = stats.abs.min()
        col.max_drawdown_perc = stats.perc.min()
        col.max_drawdown_abs_day = fromtimestamp(
            stats.close_time[stats.abs == col.max_drawdown_abs][0]
        )
        col.max_drawdown_perc_day = fromtimestamp(
            stats.close_time[stats.perc == col.max_drawdown_perc][0]
        )

        col.profit_factor = (
            abs(col.total_profit / col.total_loss) if col.total_loss else 0
        )
        col.recovery_factor = (
            abs(col.net_profit_abs / col.max_drawdown_abs)
            if col.max_drawdown_abs
            else 0
        )
        col.payoff_ratio = (
            abs(col.win_average_profit_abs / col.loss_average_profit_abs)
            if col.loss_average_profit_abs
            else 0
        )
        col.sharpe_ratio = annualized_sharpe_ratio(stats)
        col.sortino_ratio = annualized_sortino_ratio(stats)

        # TODO:
        col.alpha_ratio = np.nan
        col.beta_ratio = np.nan


def day_percentage_returns(stats):
    days = defaultdict(float)
    trade_count = np.count_nonzero(stats)

    if trade_count == 1:
        # market position, so returns should based on quotes
        # calculate percentage changes on a list of quotes
        changes = np.diff(Quotes.close) / Quotes[:-1].close * 100
        data = np.column_stack((Quotes[1:].time, changes))  # np.c_
    else:
        # slice `:trade_count` to exclude zero values in long/short columns
        data = stats[['close_time', 'perc']][:trade_count]

    # FIXME: [FutureWarning] https://github.com/numpy/numpy/issues/8383
    for close_time, perc in data:
        days[fromtimestamp(close_time).date()] += perc
    returns = np.array(list(days.values()))

    # if np.count_nonzero(stats) == 1:
    #     import pudb; pudb.set_trace()
    if len(returns) >= ANNUAL_PERIOD:
        return returns

    _returns = np.zeros(ANNUAL_PERIOD)
    _returns[: len(returns)] = returns
    return _returns


def annualized_sharpe_ratio(stats):
    # risk_free = 0
    returns = day_percentage_returns(stats)
    return np.sqrt(ANNUAL_PERIOD) * np.mean(returns) / np.std(returns)


def annualized_sortino_ratio(stats):
    # http://www.cmegroup.com/education/files/sortino-a-sharper-ratio.pdf
    required_return = 0
    returns = day_percentage_returns(stats)
    mask = [returns < required_return]
    tdd = np.zeros(len(returns))
    tdd[mask] = returns[mask]  # keep only negative values and zeros
    # "or 1" to prevent division by zero, if we don't have negative returns
    tdd = np.sqrt(np.mean(np.square(tdd))) or 1
    return np.sqrt(ANNUAL_PERIOD) * np.mean(returns) / tdd
