"""Ui."""

import logging
import logging.config
import os.path
from datetime import datetime

from PyQt5 import QtCore, QtGui

from .lib import (
    EquityChart,
    OptimizatimizedResultsTable,
    OptimizationTable,
    Portfolio,
    QuotesChart,
    ResultsTable,
    Settings,
    Symbol,
    TradesTable,
    get_quotes,
    get_symbols,
    strategies_from_file,
)

__all__ = ('MainWidget',)


logger = logging.getLogger(__name__)

DEFAULT_TICKER = 'AAPL'
SYMBOL_COLUMNS = ['Symbol', 'Security Name']


class SymbolsLoaderThread(QtCore.QThread):

    symbols_loaded = QtCore.pyqtSignal(object)

    def run(self):
        symbols = get_symbols()
        self.symbols_loaded.emit(symbols[SYMBOL_COLUMNS].values)


class DataTabWidget(QtGui.QWidget):

    data_updated = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.select_source = QtGui.QTabWidget(self)
        self.select_source.setGeometry(210, 50, 340, 200)

        self.init_shares_tab_ui()
        self.init_external_tab_ui()

        self.symbols_loader = SymbolsLoaderThread()
        self.symbols_loader.started.connect(self.on_symbols_loading)
        self.symbols_loader.symbols_loaded.connect(
            self.on_symbols_loaded, QtCore.Qt.QueuedConnection
        )
        self.symbols_loader.start()

        self.date_from = self.shares_date_from.date().toPyDate()
        self.date_to = self.shares_date_to.date().toPyDate()

    def init_external_tab_ui(self):
        """External data."""
        self.external_tab = QtGui.QWidget()
        self.external_tab.setEnabled(False)
        self.external_layout = QtGui.QVBoxLayout(self.external_tab)

        self.import_data_name = QtGui.QLabel('Import External Data')
        self.import_data_label = QtGui.QLabel('...')
        self.import_data_btn = QtGui.QPushButton('Import')
        self.import_data_btn.clicked.connect(self.open_file)

        self.external_layout.addWidget(
            self.import_data_name, 0, QtCore.Qt.AlignCenter
        )
        self.external_layout.addWidget(
            self.import_data_label, 0, QtCore.Qt.AlignCenter
        )
        self.external_layout.addWidget(
            self.import_data_btn, 0, QtCore.Qt.AlignCenter
        )

        self.select_source.addTab(self.external_tab, 'Custom data')

    def init_shares_tab_ui(self):
        """Shares."""
        self.shares_tab = QtGui.QWidget()
        self.shares_layout = QtGui.QFormLayout(self.shares_tab)
        today = datetime.today()

        self.shares_date_from = QtGui.QDateEdit()
        self.shares_date_from.setMinimumDate(QtCore.QDate(1900, 1, 1))
        self.shares_date_from.setMaximumDate(QtCore.QDate(2030, 12, 31))
        self.shares_date_from.setDate(QtCore.QDate(today.year, 1, 1))
        self.shares_date_from.setDisplayFormat('dd.MM.yyyy')

        self.shares_date_to = QtGui.QDateEdit()
        self.shares_date_to.setMinimumDate(QtCore.QDate(1900, 1, 1))
        self.shares_date_to.setMaximumDate(QtCore.QDate(2030, 12, 31))
        self.shares_date_to.setDate(
            QtCore.QDate(today.year, today.month, today.day)
        )
        self.shares_date_to.setDisplayFormat('dd.MM.yyyy')

        self.shares_symbol_list = QtGui.QComboBox()
        self.shares_symbol_list.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.shares_symbol_list.setMaxVisibleItems(20)
        self.shares_symbol_list.setEditable(True)

        self.shares_show_btn = QtGui.QPushButton('Load')
        self.shares_show_btn.clicked.connect(self.update_data)

        self.shares_layout.addRow('From', self.shares_date_from)
        self.shares_layout.addRow('To', self.shares_date_to)
        self.shares_layout.addRow('Symbol', self.shares_symbol_list)
        self.shares_layout.addRow(None, self.shares_show_btn)

        self.select_source.addTab(self.shares_tab, 'Shares/Futures/ETFs')

    def on_symbols_loading(self):
        self.shares_symbol_list.addItem('Loading...')
        self.shares_symbol_list.setEnabled(False)

    def on_symbols_loaded(self, symbols):
        self.shares_symbol_list.clear()
        self.shares_symbol_list.setEnabled(True)
        # self.symbols = ['%s/%s' % (ticker, name) for ticker, name in symbols]
        # self.shares_symbol_list.addItems(self.symbols)
        model = QtGui.QStandardItemModel()
        model.setHorizontalHeaderLabels(SYMBOL_COLUMNS)
        for irow, (ticker, name) in enumerate(symbols):
            model.setItem(irow, 0, QtGui.QStandardItem(ticker))
            model.setItem(irow, 1, QtGui.QStandardItem(name))

        table_view = QtGui.QTableView()
        table_view.setModel(model)
        table_view.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        table_view.verticalHeader().setVisible(False)
        table_view.setAutoScroll(False)
        table_view.setShowGrid(False)
        table_view.resizeRowsToContents()
        table_view.setColumnWidth(0, 60)
        table_view.setColumnWidth(1, 240)
        table_view.setMinimumWidth(300)

        completer = QtGui.QCompleter(model)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        completer.setModel(model)

        self.symbols = symbols
        self.shares_symbol_list.setModel(model)
        self.shares_symbol_list.setView(table_view)
        self.shares_symbol_list.setCompleter(completer)

        # set default symbol
        self.shares_symbol_list.setCurrentIndex(
            self.shares_symbol_list.findText(DEFAULT_TICKER)
        )

    def open_file(self):
        filename = QtGui.QFileDialog.getOpenFileName(
            parent=None,
            caption='Open a source of data',
            directory=QtCore.QDir.currentPath(),
            filter='All (*);;Text (*.txt)',
        )

        self.import_data_label.setText('Loading %s' % filename)

        with open(filename, 'r', encoding='utf-8') as f:
            self.data = f.readlines()

    def update_data(self, ticker=None):
        ticker = ticker or self.shares_symbol_list.currentText()
        self.symbol = Symbol(ticker=ticker, mode=Symbol.SHARES)
        self.date_from = self.shares_date_from.date().toPyDate()
        self.date_to = self.shares_date_to.date().toPyDate()

        get_quotes(
            symbol=self.symbol.ticker,
            date_from=self.date_from,
            date_to=self.date_to,
        )

        self.data_updated.emit(self.symbol)


class StrategyBoxWidget(QtGui.QGroupBox):

    run_backtest = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle('Strategy')
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.layout = QtGui.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.list = QtGui.QComboBox()

        self.add_btn = QtGui.QPushButton('+')
        self.add_btn.clicked.connect(self.add_strategies)

        self.start_btn = QtGui.QPushButton('Start Backtest')
        self.start_btn.clicked.connect(self.load_strategy)

        self.layout.addWidget(self.list, stretch=2)
        self.layout.addWidget(self.add_btn, stretch=0)
        self.layout.addWidget(self.start_btn, stretch=0)

        self.load_strategies_from_settings()

    def reload_strategies(self):
        """Reload user's file to get actual version of the strategies."""
        self.strategies = strategies_from_file(self.strategies_path)

    def reload_list(self):
        self.list.clear()
        self.list.addItems([s.get_name() for s in self.strategies])

    def load_strategies_from_settings(self):
        filename = Settings.value('strategies/path', None)
        if not filename or not os.path.exists(filename):
            return
        self.strategies_path = filename
        self.reload_strategies()
        self.reload_list()

    def save_strategies_to_settings(self):
        Settings.setValue('strategies/path', self.strategies_path)

    def add_strategies(self):
        filename, _filter = QtGui.QFileDialog.getOpenFileName(
            self,
            caption='Open Strategy.',
            directory=QtCore.QDir.currentPath(),
            filter='Python modules (*.py)',
        )
        if not filename:
            return
        self.strategies_path = filename
        self.save_strategies_to_settings()
        self.reload_strategies()
        self.reload_list()

    def load_strategy(self):
        self.reload_strategies()
        self.run_backtest.emit(self.strategies[self.list.currentIndex()])


class QuotesTabWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.toolbar_layout = QtGui.QHBoxLayout()
        self.toolbar_layout.setContentsMargins(10, 10, 15, 0)
        self.chart_layout = QtGui.QHBoxLayout()

        self.init_timeframes_ui()
        self.init_strategy_ui()

        self.layout.addLayout(self.toolbar_layout)
        self.layout.addLayout(self.chart_layout)

    def init_timeframes_ui(self):
        self.tf_layout = QtGui.QHBoxLayout()
        self.tf_layout.setSpacing(0)
        self.tf_layout.setContentsMargins(0, 12, 0, 0)
        time_frames = ('1M', '5M', '15M', '30M', '1H', '1D', '1W', 'MN')
        btn_prefix = 'TF'
        for tf in time_frames:
            btn_name = ''.join([btn_prefix, tf])
            btn = QtGui.QPushButton(tf)
            # TODO:
            btn.setEnabled(False)
            setattr(self, btn_name, btn)
            self.tf_layout.addWidget(btn)
        self.toolbar_layout.addLayout(self.tf_layout)

    def init_strategy_ui(self):
        self.strategy_box = StrategyBoxWidget(self)
        self.toolbar_layout.addWidget(self.strategy_box)

    def update_chart(self, symbol):
        if not self.chart_layout.isEmpty():
            self.chart_layout.removeWidget(self.chart)
        self.chart = QuotesChart()
        self.chart.plot(symbol)
        self.chart_layout.addWidget(self.chart)

    def add_signals(self):
        self.chart.add_signals()


class EquityTabWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QtGui.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def update_chart(self):
        if not self.layout.isEmpty():
            self.layout.removeWidget(self.chart)
        self.chart = EquityChart()
        self.chart.plot()
        self.layout.addWidget(self.chart)


class ResultsTabWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QtGui.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def update_table(self):
        if not self.layout.isEmpty():
            self.layout.removeWidget(self.table)
        self.table = ResultsTable()
        self.table.plot()
        self.layout.addWidget(self.table)


class TradesTabWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QtGui.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def update_table(self):
        if not self.layout.isEmpty():
            self.layout.removeWidget(self.table)
        self.table = TradesTable()
        self.table.plot()
        self.layout.addWidget(self.table)


class OptimizationTabWidget(QtGui.QWidget):

    optimization_done = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.table_layout = QtGui.QHBoxLayout()
        self.top_layout = QtGui.QHBoxLayout()
        self.top_layout.setContentsMargins(0, 10, 0, 0)

        self.start_optimization_btn = QtGui.QPushButton('Start')
        self.start_optimization_btn.clicked.connect(self.start_optimization)
        self.top_layout.addWidget(
            self.start_optimization_btn, alignment=QtCore.Qt.AlignRight
        )

        self.layout.addLayout(self.top_layout)
        self.layout.addLayout(self.table_layout)

    def update_table(self, strategy):
        if not self.table_layout.isEmpty():
            # close() to avoid an UI issue with duplication of the table
            self.table.close()
            self.table_layout.removeWidget(self.table)
        self.table = OptimizationTable()
        self.table.plot(strategy)
        self.table_layout.addWidget(self.table)

    def start_optimization(self, *args, **kwargs):
        logger.debug('Start optimization')
        self.table.optimize()
        self.optimization_done.emit()
        logger.debug('Optimization is done')


class OptimizatimizedResultsTabWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QtGui.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.table = OptimizatimizedResultsTable()
        self.table.plot()

        self.layout.addWidget(self.table)


class MainWidget(QtGui.QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDocumentMode(True)

        self.data_tab = DataTabWidget(self)
        self.data_tab.data_updated.connect(self._update_quotes_chart)
        self.addTab(self.data_tab, 'Data')

    def _add_quotes_tab(self):
        if self.count() >= 2:  # quotes tab is already exists
            return
        self.quotes_tab = QuotesTabWidget(self)
        self.quotes_tab.strategy_box.run_backtest.connect(self._run_backtest)
        self.addTab(self.quotes_tab, 'Quotes')

    def _add_result_tabs(self):
        if self.count() >= 3:  # tabs are already exist
            return
        self.equity_tab = EquityTabWidget(self)
        self.results_tab = ResultsTabWidget(self)
        self.trades_tab = TradesTabWidget(self)
        self.optimization_tab = OptimizationTabWidget(self)
        self.optimization_tab.optimization_done.connect(
            self._add_optimized_results
        )  # noqa
        self.addTab(self.equity_tab, 'Equity')
        self.addTab(self.results_tab, 'Results')
        self.addTab(self.trades_tab, 'Trades')
        self.addTab(self.optimization_tab, 'Optimization')

    def _update_quotes_chart(self, symbol):
        self._add_quotes_tab()
        self.symbol = symbol
        self.quotes_tab.update_chart(self.symbol)
        self.setCurrentIndex(1)

    def _run_backtest(self, strategy):
        logger.debug('Run backtest')
        Portfolio.clear()

        stg = strategy(symbols=[self.symbol])
        stg.run()

        Portfolio.summarize()
        self.quotes_tab.add_signals()
        self._add_result_tabs()
        self.equity_tab.update_chart()
        self.results_tab.update_table()
        self.trades_tab.update_table()
        self.optimization_tab.update_table(strategy=stg)
        logger.debug(
            'Count positions in the portfolio: %d', Portfolio.position_count()
        )

    def _add_optimized_results(self):
        self.addTab(OptimizatimizedResultsTabWidget(self), 'Optimized Results')
        self.setCurrentIndex(self.count() - 1)

    def plot_test_data(self):
        logger.debug('Plot test data')
        self.data_tab.update_data(ticker=DEFAULT_TICKER)
        self.quotes_tab.strategy_box.load_strategy()
