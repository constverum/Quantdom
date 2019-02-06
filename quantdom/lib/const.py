"""Constants."""

from enum import Enum, auto

__all__ = ('ChartType', 'TimeFrame')


class ChartType(Enum):
    BAR = auto()
    CANDLESTICK = auto()
    LINE = auto()


class TimeFrame(Enum):
    M1 = auto()
    M5 = auto()
    M15 = auto()
    M30 = auto()
    H1 = auto()
    H4 = auto()
    D1 = auto()
    W1 = auto()
    MN = auto()


ANNUAL_PERIOD = 252  # number of trading days in a year

# # TODO: 6.5 - US trading hours (trading session); fix it for fx
# ANNUALIZATION_FACTORS = {
#     TimeFrame.M1: int(252 * 6.5 * 60),
#     TimeFrame.M5: int(252 * 6.5 * 12),
#     TimeFrame.M15: int(252 * 6.5 * 4),
#     TimeFrame.M30: int(252 * 6.5 * 2),
#     TimeFrame.H1: int(252 * 6.5),
#     TimeFrame.D1: 252,
# }
