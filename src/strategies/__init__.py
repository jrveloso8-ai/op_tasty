"""
Pacote de Estratégias do Screener Tastytrade.
"""

from src.strategies.base import BaseStrategy
from src.strategies.screener_engine import ScreenerEngine, get_all_strategies
from src.strategies.implementations import (
    BullCallSpreadStrategy,
    BearPutSpreadStrategy,
    LongStrangleStrategy,
    IronCondorStrategy,
    CalendarSpreadStrategy,
    DiagonalSpreadStrategy,
    PutRatioSpreadStrategy,
    CallBackspreadStrategy
)

__all__ = [
    "BaseStrategy",
    "ScreenerEngine",
    "get_all_strategies",
    "BullCallSpreadStrategy",
    "BearPutSpreadStrategy",
    "LongStrangleStrategy",
    "IronCondorStrategy",
    "CalendarSpreadStrategy",
    "DiagonalSpreadStrategy",
    "PutRatioSpreadStrategy",
    "CallBackspreadStrategy"
]
