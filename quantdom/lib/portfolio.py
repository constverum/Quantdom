"""Portfolio."""

import itertools
from contextlib import contextmanager
from enum import Enum, auto

import numpy as np

from .base import Quotes
from .performance import BriefPerformance, Performance, Stats
from .utils import fromtimestamp, timeit

__all__ = ('Portfolio', 'Position', 'Order')


class BasePortfolio:
    def __init__(self, balance=100_000, leverage=5):
        self._initial_balance = balance
        self.balance = balance
        self.equity = None
        # TODO:
        # self.cash
        # self.currency
        self.leverage = leverage
        self.positions = []

        self.balance_curve = None
        self.equity_curve = None
        self.long_curve = None
        self.short_curve = None
        self.mae_curve = None
        self.mfe_curve = None

        self.stats = None
        self.performance = None
        self.brief_performance = None

    def clear(self):
        self.positions.clear()
        self.balance = self._initial_balance

    @property
    def initial_balance(self):
        return self._initial_balance

    @initial_balance.setter
    def initial_balance(self, value):
        self._initial_balance = value

    def add_position(self, position):
        position.ticket = len(self.positions) + 1
        self.positions.append(position)

    def position_count(self, tp=None):
        if tp == Order.BUY:
            return len([p for p in self.positions if p.type == Order.BUY])
        elif tp == Order.SELL:
            return len([p for p in self.positions if p.type == Order.SELL])
        return len(self.positions)

    def _close_open_positions(self):
        for p in self.positions:
            if p.status == Position.OPEN:
                p.close(
                    price=Quotes[-1].open, volume=p.volume, time=Quotes[-1].time
                )

    def _get_market_position(self):
        p = self.positions[0]  # real postions
        p = Position(
            symbol=p.symbol,
            ptype=Order.BUY,
            volume=p.volume,
            price=Quotes[0].open,
            open_time=Quotes[0].time,
            close_price=Quotes[-1].close,
            close_time=Quotes[-1].time,
            id_bar_close=len(Quotes) - 1,
            status=Position.CLOSED,
        )
        p.profit = p.calc_profit(close_price=Quotes[-1].close)
        p.profit_perc = p.profit / self._initial_balance * 100
        return p

    def _calc_equity_curve(self):
        """Equity curve."""
        self.equity_curve = np.zeros_like(Quotes.time)
        for i, p in enumerate(self.positions):
            balance = np.sum(self.stats['All'][:i].abs)
            for ibar in range(p.id_bar_open, p.id_bar_close):
                profit = p.calc_profit(close_price=Quotes[ibar].close)
                self.equity_curve[ibar] = balance + profit
        # taking into account the real balance after the last trade
        self.equity_curve[-1] = self.balance_curve[-1]

    def _calc_buy_and_hold_curve(self):
        """Buy and Hold."""
        p = self._get_market_position()
        self.buy_and_hold_curve = np.array(
            [p.calc_profit(close_price=price) for price in Quotes.close]
        )

    def _calc_long_short_curves(self):
        """Only Long/Short positions curve."""
        self.long_curve = np.zeros_like(Quotes.time)
        self.short_curve = np.zeros_like(Quotes.time)

        for i, p in enumerate(self.positions):
            if p.type == Order.BUY:
                name = 'Long'
                curve = self.long_curve
            else:
                name = 'Short'
                curve = self.short_curve
            balance = np.sum(self.stats[name][:i].abs)
            # Calculate equity for this position
            for ibar in range(p.id_bar_open, p.id_bar_close):
                profit = p.calc_profit(close_price=Quotes[ibar].close)
                curve[ibar] = balance + profit

        for name, curve in [
            ('Long', self.long_curve),
            ('Short', self.short_curve),
        ]:
            curve[:] = fill_zeros_with_last(curve)
            # taking into account the real balance after the last trade
            curve[-1] = np.sum(self.stats[name].abs)

    def _calc_curves(self):
        self.mae_curve = np.cumsum(self.stats['All'].mae)
        self.mfe_curve = np.cumsum(self.stats['All'].mfe)
        self.balance_curve = np.cumsum(self.stats['All'].abs)
        self._calc_equity_curve()
        self._calc_buy_and_hold_curve()
        self._calc_long_short_curves()

    @contextmanager
    def optimization_mode(self):
        """Backup and restore current balance and positions."""
        # mode='general',
        self.backup_balance = self.balance
        self.backup_positions = self.positions.copy()
        self.balance = self._initial_balance
        self.positions.clear()
        yield
        self.balance = self.backup_balance
        self.positions = self.backup_positions.copy()
        self.backup_positions.clear()

    @timeit
    def run_optimization(self, strategy, params):
        keys = list(params.keys())
        vals = list(params.values())
        variants = list(itertools.product(*vals))
        self.brief_performance = BriefPerformance(shape=(len(variants),))
        with self.optimization_mode():
            for i, vals in enumerate(variants):
                kwargs = {keys[n]: val for n, val in enumerate(vals)}
                strategy.start(**kwargs)
                self._close_open_positions()
                self.brief_performance.add(
                    self._initial_balance, self.positions, i, kwargs
                )
                self.clear()

    @timeit
    def summarize(self):
        self._close_open_positions()
        positions = {
            'All': self.positions,
            'Long': [p for p in self.positions if p.type == Order.BUY],
            'Short': [p for p in self.positions if p.type == Order.SELL],
            'Market': [self._get_market_position()],
        }
        self.stats = Stats(positions)
        self.performance = Performance(
            self._initial_balance, self.stats, positions
        )
        self._calc_curves()


Portfolio = BasePortfolio()


class PositionStatus(Enum):
    OPEN = auto()
    CLOSED = auto()
    CANCELED = auto()


class Position:

    OPEN = PositionStatus.OPEN
    CLOSED = PositionStatus.CLOSED
    CANCELED = PositionStatus.CANCELED

    __slots__ = (
        'type',
        'symbol',
        'ticket',
        'open_price',
        'close_price',
        'open_time',
        'close_time',
        'volume',
        'sl',
        'tp',
        'status',
        'profit',
        'profit_perc',
        'commis',
        'id_bar_open',
        'id_bar_close',
        'entry_name',
        'exit_name',
        'total_profit',
        'comment',
    )

    def __init__(
        self,
        symbol,
        ptype,
        price,
        volume,
        open_time,
        sl=None,
        tp=None,
        status=OPEN,
        entry_name='',
        exit_name='',
        comment='',
        **kwargs,
    ):
        self.type = ptype
        self.symbol = symbol
        self.ticket = None
        self.open_price = price
        self.close_price = None
        self.open_time = open_time
        self.close_time = None
        self.volume = volume
        self.sl = sl
        self.tp = tp
        self.status = status
        self.profit = None
        self.profit_perc = None
        self.commis = None
        self.id_bar_open = np.where(Quotes.time == self.open_time)[0][0]
        self.id_bar_close = None
        self.entry_name = entry_name
        self.exit_name = exit_name
        self.total_profit = 0
        self.comment = comment
        # self.bars_on_trade = None
        # self.is_profitable = False

        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        _type = 'LONG' if self.type == Order.BUY else 'SHORT'
        time = fromtimestamp(self.open_time).strftime('%d.%m.%y %H:%M')
        return '%s/%s/[%s - %.4f]' % (
            self.status.name,
            _type,
            time,
            self.open_price,
        )

    def close(self, price, time, volume=None):
        # TODO: allow closing only part of the volume
        self.close_price = price
        self.close_time = time
        self.id_bar_close = np.where(Quotes.time == self.close_time)[0][0]
        self.profit = self.calc_profit(volume=volume or self.volume)
        self.profit_perc = self.profit / Portfolio.balance * 100

        Portfolio.balance += self.profit

        self.total_profit = Portfolio.balance - Portfolio.initial_balance
        self.status = self.CLOSED

    def calc_profit(self, volume=None, close_price=None):
        # TODO: rewrite it
        close_price = close_price or self.close_price
        volume = volume or self.volume
        factor = 1 if self.type == Order.BUY else -1
        price_delta = (close_price - self.open_price) * factor
        if self.symbol.mode in [self.symbol.FOREX, self.symbol.CFD]:
            # Margin:  Lots*Contract_Size/Leverage
            if (
                self.symbol.mode == self.symbol.FOREX
                and self.symbol.ticker[:3] == 'USD'
            ):
                # Example: 'USD/JPY'
                #          Прибыль       Размер   Объем     Текущий
                #          в пунктах     пункта   позиции   курс
                #          1          *  0.0001 * 100000  / 1.00770
                # USD/CHF: 1*0.0001*100000/1.00770  =  $9.92
                #               0.01
                # USD/JPY: 1*0.01*100000/121.35     =  $8.24
                # (1.00770-1.00595)/0.0001 = 17.5 пунктов
                # (1.00770-1.00595)/0.0001*0.0001*100000*1/1.00770*1
                _points = price_delta / self.symbol.tick_size
                _profit = (
                    _points
                    * self.symbol.tick_size
                    * self.symbol.contract_size
                    / close_price
                    * volume
                )
            elif (
                self.symbol.mode == self.symbol.FOREX
                and self.symbol.ticker[-3:] == 'USD'
            ):
                # Example: 'EUR/USD'
                # Profit:      (close_price-open_price)*Contract_Size*Lots
                # EUR/USD BUY: (1.05875-1.05850)*100000*1 = +$25 (без комиссии)
                _profit = price_delta * self.symbol.contract_size * volume
            else:
                # Cross rates. Example: 'GBP/CHF'
                # Цена пункта =
                # объем поз.*размер п.*тек.курс баз.вал. к USD/тек. кросс-курс
                # GBP/CHF: 100000*0.0001*1.48140/1.48985 = $9.94
                # TODO: temporary patch (same as the previous choice) -
                # in the future connect to some quotes provider and get rates
                _profit = price_delta * self.symbol.contract_size * volume
        elif self.symbol.mode == self.symbol.FUTURES:
            # Margin: Lots *InitialMargin*Percentage/100
            # Profit:          (close_price-open_price)*TickPrice/TickSize*Lots
            # CL BUY:       (46.35-46.30)*10/0.01*1 = $50 (без учета комиссии!)
            # EuroFX(6E) BUY:(1.05875-1.05850)*12.50/0.0001*1 =$31.25 (без ком)
            # RTS (RIH5) BUY:(84510-84500)*12.26506/10*1 = @12.26506 (без ком)
            # E-miniSP500 BUY:(2065.95-2065.25)*12.50/0.25 = $35 (без ком)
            # http://americanclearing.ru/specifications.php
            # http://www.moex.com/ru/contract.aspx?code=RTS-3.18
            # http://www.cmegroup.com/trading/equity-index/us-index/e-mini-sandp500_contract_specifications.html
            _profit = (
                price_delta
                * self.symbol.tick_value
                / self.symbol.tick_size
                * volume
            )
        else:
            # shares
            _profit = price_delta * volume

        return _profit

    def calc_mae(self, low, high):
        """Return [MAE] Maximum Adverse Excursion."""
        if self.type == Order.BUY:
            return self.calc_profit(close_price=low)
        return self.calc_profit(close_price=high)

    def calc_mfe(self, low, high):
        """Return [MFE] Maximum Favorable Excursion."""
        if self.type == Order.BUY:
            return self.calc_profit(close_price=high)
        return self.calc_profit(close_price=low)


class OrderType(Enum):
    BUY = auto()
    SELL = auto()
    BUY_LIMIT = auto()
    SELL_LIMIT = auto()
    BUY_STOP = auto()
    SELL_STOP = auto()


class Order:

    BUY = OrderType.BUY
    SELL = OrderType.SELL
    BUY_LIMIT = OrderType.BUY_LIMIT
    SELL_LIMIT = OrderType.SELL_LIMIT
    BUY_STOP = OrderType.BUY_STOP
    SELL_STOP = OrderType.SELL_STOP

    @staticmethod
    def open(symbol, otype, price, volume, time, sl=None, tp=None):
        # TODO: add margin calculation
        # and if the margin is not enough - do not open the position
        position = Position(
            symbol=symbol,
            ptype=otype,
            price=price,
            volume=volume,
            open_time=time,
            sl=sl,
            tp=tp,
        )
        Portfolio.add_position(position)
        return position

    @staticmethod
    def close(position, price, time, volume=None):
        # FIXME: may be closed not the whole volume, but
        # the position status will be changed to CLOSED
        position.close(price=price, time=time, volume=volume)


def fill_zeros_with_last(arr):
    """Fill empty(zero) elements (between positions)."""
    index = np.arange(len(arr))
    index[arr == 0] = 0
    index = np.maximum.accumulate(index)
    return arr[index]
