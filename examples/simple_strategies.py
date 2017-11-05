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
