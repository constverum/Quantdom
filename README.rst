Quantdom
========

.. image:: https://img.shields.io/pypi/v/quantdom.svg?style=flat-square
    :target: https://pypi.python.org/pypi/quantdom/
.. image:: https://img.shields.io/travis/constverum/Quantdom.svg?style=flat-square
    :target: https://travis-ci.org/constverum/Quantdom
.. image:: https://img.shields.io/pypi/wheel/quantdom.svg?style=flat-square
    :target: https://pypi.python.org/pypi/quantdom/
.. image:: https://img.shields.io/pypi/pyversions/quantdom.svg?style=flat-square
    :target: https://pypi.python.org/pypi/quantdom/
.. image:: https://img.shields.io/pypi/l/quantdom.svg?style=flat-square
    :target: https://pypi.python.org/pypi/quantdom/

Quantdom is a simple but powerful backtesting framework written in python, that strives to let you focus on modeling financial strategies, portfolio management, and analyzing backtests. It has been created as a useful and flexible tool to save the systematic trading community from re-inventing the wheel and let them evaluate their trading ideas easier with minimal effort. It's designed for people who are already comfortable with *Python* and who want to create, test and explore their own trading strategies.

.. image:: http://f.cl.ly/items/1z1t1T0A0P161f053i45/quantdom_v0.1a1.gif

Quantdom is in an early alpha state at the moment. So please be patient with possible errors and report them.


Features
--------

* Free, open-source and cross-platform backtesting framework
* Multiple data feeds: csv files and online sources such as Google Finance, Yahoo Finance, Quandl and more
* Investment Analysis (performance and risk analysis of financial portfolio)
* Charting and reporting that help visualize backtest results


Requirements
------------

* Python **3.6** or higher
* `PyQt5 <https://pypi.python.org/pypi/PyQt5>`_
* `PyQtGraph <http://www.pyqtgraph.org/>`_
* `NumPy <http://www.numpy.org/>`_
* See `pyproject.toml <https://github.com/constverum/Quantdom/blob/master/pyproject.toml#L43-L50>`_ for full details.


Installation
------------

Using the binaries
##################

You can download binary packages for your system (see the `Github Releases <https://github.com/constverum/Quantdom/releases>`_ page for available downloads):

* For `Windows  <https://github.com/constverum/Quantdom/releases/download/v0.1/quantdom_0.1.exe>`_
* For `MacOS  <https://github.com/constverum/Quantdom/releases/download/v0.1/quantdom_0.1.dmg>`_
* For `Linux  <https://github.com/constverum/Quantdom/releases/download/v0.1/quantdom_0.1.zip>`_

Running from source code
########################

You can install last *stable release* from pypi:

.. code-block:: bash

    $ pip install quantdom

And latest *development version* can be installed directly from GitHub:

.. code-block:: bash

    $ pip install -U git+https://github.com/constverum/Quantdom.git

After that, to run the application just execute one command:

.. code-block:: bash

    $ quantdom


Usage
-----

1. Run Quantdom.
2. Choose a market instrument (symbol) for backtesting on the ``Data`` tab.
3. Specify a file with your strategies on the ``Quotes`` tab, and select one of them.
4. Run a backtest. Once this is done, you can analyze the results and optimize parameters of the strategy.


Strategy Examples
-----------------

Three-bar strategy
##################

A simple trading strategy based on the assumption that after three consecutive bullish bars (bar closing occurred higher than its opening) bulls predominate in the market and therefore the price will continue to grow; after 3 consecutive bearish bars (the bar closes lower than its opening), the price will continue to down, since bears predominate in the market.

.. code-block:: python

    from quantdom import AbstractStrategy, Order, Portfolio

    class ThreeBarStrategy(AbstractStrategy):

        def init(self, high_bars=3, low_bars=3):
            Portfolio.initial_balance = 100000  # default value
            self.seq_low_bars = 0
            self.seq_high_bars = 0
            self.signal = None
            self.last_position = None
            self.volume = 100  # shares
            self.high_bars = high_bars
            self.low_bars = low_bars

        def handle(self, quote):
            if self.signal:
                props = {
                    'symbol': self.symbol,  # current selected symbol
                    'otype': self.signal,
                    'price': quote.open,
                    'volume': self.volume,
                    'time': quote.time,
                }
                if not self.last_position:
                    self.last_position = Order.open(**props)
                elif self.last_position.type != self.signal:
                    Order.close(self.last_position, price=quote.open, time=quote.time)
                    self.last_position = Order.open(**props)
                self.signal = False
                self.seq_high_bars = self.seq_low_bars = 0

            if quote.close > quote.open:
                self.seq_high_bars += 1
                self.seq_low_bars = 0
            else:
                self.seq_high_bars = 0
                self.seq_low_bars += 1

            if self.seq_high_bars == self.high_bars:
                self.signal = Order.BUY
            elif self.seq_low_bars == self.low_bars:
                self.signal = Order.SELL


Documentation
-------------

In progress ;)


TODO
----

* Add integration with `TA-Lib <http://ta-lib.org/>`_
* Add the ability to use TensorFlow/CatBoost/Scikit-Learn and other ML tools to create incredible algorithms and strategies. Just as one of the first tasks is Elliott Wave Theory(Principle) - to recognize of current wave and on the basis of this predict price movement at confidence intervals
* Add the ability to make a sentiment analysis from different sources (news, tweets, etc)
* Add ability to create custom screens, ranking functions, reports


Contributing
------------

* Fork it: https://github.com/constverum/Quantdom/fork
* Create your feature branch: git checkout -b my-new-feature
* Commit your changes: git commit -am 'Add some feature'
* Push to the branch: git push origin my-new-feature
* Submit a pull request!


Disclaimer
----------

This software should not be used as a financial advisor, it is for educational use only.
Absolutely no warranty is implied with this product. By using this software you release the author(s) from any liability regarding the use of this software. You can lose money because this program probably has some errors in it, so use it at your own risk. And please don't take risks with money you can't afford to lose.


Feedback
--------

I'm very interested in your experience with Quantdom.
Please feel free to send me any feedback, ideas, enhancement requests or anything else.


License
-------

Licensed under the Apache License, Version 2.0
