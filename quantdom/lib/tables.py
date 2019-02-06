"""Tables."""

from datetime import datetime

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui

from .portfolio import Order, Portfolio, Position
from .utils import fromtimestamp

__all__ = (
    'OptimizatimizedResultsTable',
    'OptimizationTable',
    'ResultsTable',
    'TradesTable',
    'LogTable',
)


class ResultsTable(QtGui.QTableWidget):

    positive_color = pg.mkColor('#0000cc')
    negative_color = pg.mkColor('#cc0000')

    def __init__(self):
        super().__init__()
        self.setColumnCount(len(Portfolio.performance.columns))
        rows = sum(
            [
                2 if 'separated' in props else 1
                for props in Portfolio.performance.rows.values()
            ]
        )
        self.setRowCount(rows)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setHorizontalHeaderLabels(Portfolio.performance.columns)
        self.horizontalHeader().setSectionResizeMode(QtGui.QHeaderView.Stretch)

        # TODO: make cols editable (show/hide)

    def plot(self):
        rows = Portfolio.performance.rows.items()
        for icol, col in enumerate(Portfolio.performance.columns):
            irow = 0
            for prop_key, props in rows:
                if props.get('separated', False):
                    # add a blank row
                    self.setVerticalHeaderItem(irow, QtGui.QTableWidgetItem(''))
                    irow += 1
                units = props['units']
                header = props['header']
                colored = props['colored']
                self.setVerticalHeaderItem(irow, QtGui.QTableWidgetItem(header))
                val = getattr(Portfolio.performance[col], prop_key)
                if isinstance(val, float):
                    sval = '%.2f %s' % (val, units)
                elif isinstance(val, (int, str)):
                    sval = '%d %s' % (val, units)
                elif isinstance(val, datetime):
                    sval = '%s %s' % (val.strftime('%Y.%m.%d'), units)
                item = QtGui.QTableWidgetItem(sval)
                item.setTextAlignment(
                    QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight
                )
                item.setFlags(
                    QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
                )
                if colored:
                    color = (
                        self.positive_color if val > 0 else self.negative_color
                    )
                    item.setForeground(color)
                self.setItem(irow, icol, item)
                irow += 1


class TradesTable(QtGui.QTableWidget):

    cols = np.array(
        [
            ('Type', 'type'),
            ('Symbol', 'symbol'),
            ('Volume', 'volume'),
            ('Entry', 'entry'),
            ('Exit', 'exit'),
            ('Profit  $', 'abs'),
            ('Profit %', 'perc'),
            ('Bars', 'bars'),
            ('Profit on Bar', 'on_bar'),
            ('Total Profit', 'total_profit'),
            ('MAE', 'mae'),
            ('MFE', 'mfe'),
            ('Comment', 'comment'),
        ]
    )
    colored_cols = (
        'type',
        'abs',
        'perc',
        'total_profit',
        'mae',
        'mfe',
        'on_bar',
    )
    fg_positive_color = pg.mkColor('#0000cc')
    fg_negative_color = pg.mkColor('#cc0000')
    bg_positive_color = pg.mkColor('#e3ffe3')
    bg_negative_color = pg.mkColor('#ffe3e3')

    def __init__(self):
        super().__init__()
        self.setSortingEnabled(True)
        self.setColumnCount(len(self.cols))
        self.setHorizontalHeaderLabels(self.cols[:, 0])
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.verticalHeader().hide()

    def plot(self):
        # TODO if Only Long / Short mode is selected then choise it
        trades = Portfolio.stats['All']
        self.setRowCount(len(trades))

        for irow, trade in enumerate(trades):
            for icol, col in enumerate(self.cols[:, 1]):
                fg_color = None
                if col == 'type':
                    val, fg_color = (
                        ('▲ Buy', self.fg_positive_color)
                        if trade[col] == Order.BUY
                        else ('▼ Sell', self.fg_negative_color)
                    )
                elif col == 'status':
                    val = 'Open' if trade[col] == Position.OPEN else 'Closed'
                elif col == 'symbol':
                    val = trade[col].ticker
                elif col == 'bars':
                    val = int(trade[col])
                elif col == 'entry':
                    val = fromtimestamp(trade['open_time'])
                elif col == 'exit':
                    val = fromtimestamp(trade['close_time'])
                else:
                    val = trade[col]

                if isinstance(val, float):
                    s_val = '%.2f' % val
                elif isinstance(val, datetime):
                    time = val.strftime('%Y.%m.%d %H:%M')
                    price = (
                        trade['open_price']
                        if col == 'entry'
                        else trade['close_price']
                    )
                    # name = (trade['entry_name'] if col == 'entry' else
                    #         trade['exit_name'])
                    s_val = '%s at $%s' % (time, price)
                elif isinstance(val, (int, str, np.int_, np.str_)):
                    s_val = str(val)

                item = QtGui.QTableWidgetItem(s_val)
                align = QtCore.Qt.AlignVCenter
                align |= (
                    QtCore.Qt.AlignLeft
                    if col in ('type', 'entry', 'exit')
                    else QtCore.Qt.AlignRight
                )
                item.setTextAlignment(align)
                item.setFlags(
                    QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
                )
                bg_color = (
                    self.bg_positive_color
                    if trade['abs'] >= 0
                    else self.bg_negative_color
                )
                item.setBackground(bg_color)

                if col in self.colored_cols:
                    if fg_color is None:
                        fg_color = (
                            self.fg_positive_color
                            if val >= 0
                            else self.fg_negative_color
                        )
                    item.setForeground(fg_color)
                self.setItem(irow, icol, item)
        self.resizeColumnsToContents()


class OptimizationTable(QtGui.QTableWidget):

    cols = ('Variable', 'Value', 'Minimum', 'Maximum', 'Step', 'Optimize')

    def __init__(self):
        super().__init__()
        self.setColumnCount(len(self.cols))
        self.setHorizontalHeaderLabels(self.cols)
        self.horizontalHeader().setSectionResizeMode(QtGui.QHeaderView.Stretch)
        self.verticalHeader().hide()

    def plot(self, strategy):
        params = strategy.kwargs.copy()
        self.strategy = strategy
        self.setRowCount(len(params))

        for irow, item in enumerate(params.items()):
            key, value = item
            for icol, col in enumerate(self.cols):
                if col == 'Variable':
                    val = key
                elif col in ('Value', 'Minimum'):
                    val = value
                elif col == 'Maximum':
                    val = value * 2
                elif col == 'Step':
                    val = 1
                else:
                    continue

                item = QtGui.QTableWidgetItem(str(val))
                item.setTextAlignment(
                    QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight
                )
                # item.setFlags(
                #   QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.setItem(irow, icol, item)

    def _get_params(self):
        """Return params for optimization."""
        params = self.strategy.kwargs.copy()
        for irow in range(len(params)):
            var = self.item(irow, 0).text()
            _min = float(self.item(irow, 2).text())
            _max = float(self.item(irow, 3).text())
            _step = float(self.item(irow, 4).text())
            params[var] = np.arange(_min, _max, _step)
        return params

    def optimize(self, *args, **kwargs):
        params = self._get_params()
        Portfolio.run_optimization(self.strategy, params)


class OptimizatimizedResultsTable(QtGui.QTableWidget):

    sort_col = 3  # net_profit_perc
    main_cols = np.array(
        [
            ('net_profit_abs', 'Net Profit'),
            ('net_profit_perc', 'Net Profit %'),
            ('year_profit', 'Year Profit %'),  # Annual Profit ?
            ('win_average_profit_perc', 'Average Profit % (per trade)'),
            ('loss_average_profit_perc', 'Average Loss % (per trade)'),
            ('max_drawdown_abs', 'Maximum Drawdown'),
            ('total_trades', 'Number of Trades'),
            ('win_trades_abs', 'Winning Trades'),
            ('win_trades_perc', 'Winning Trades %'),
            ('profit_factor', 'Profit Factor'),
            ('recovery_factor', 'Recovery Factor'),
            ('payoff_ratio', 'Payoff Ratio'),
        ]
    )

    def __init__(self):
        super().__init__()
        self.setSortingEnabled(True)
        self.verticalHeader().hide()

    def plot(self):
        # TODO if Only Long / Short mode is selected then choise it
        performance = Portfolio.brief_performance
        kw_keys = performance[0].kwargs.keys()
        var_cols = np.array([(k, k) for k in performance[0].kwargs.keys()])
        self.cols = np.concatenate((var_cols, self.main_cols))
        self.setColumnCount(len(self.cols))
        self.setRowCount(len(performance))
        self.setHorizontalHeaderLabels(self.cols[:, 1])

        for irow, result in enumerate(performance):
            for i, col in enumerate(self.cols[:, 0]):
                val = result.kwargs[col] if col in kw_keys else result[col]
                if isinstance(val, float):
                    val = '%.2f' % val
                item = QtGui.QTableWidgetItem(str(val))
                item.setTextAlignment(
                    QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight
                )
                item.setFlags(
                    QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
                )
                self.setItem(irow, i, item)
        self.resizeColumnsToContents()
        self.sortByColumn(self.sort_col, QtCore.Qt.DescendingOrder)


class LogTable(QtGui.QTableWidget):
    def __init__(self):
        super().__init__()
        self.cols = np.array([('time', 'Time'), ('message', 'Message')])
        self.setColumnCount(len(self.cols))
        self.verticalHeader().hide()

    def plot(self):
        pass
