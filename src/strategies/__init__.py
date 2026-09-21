"""
Pacote de Estratégias do Screener Tastytrade.
"""

from src.strategies.base import BaseStrategy
from src.strategies.implementations import (
    BearPutSpreadStrategy,
    BullCallSpreadStrategy,
    CalendarSpreadStrategy,
    CallBackspreadStrategy,
    DiagonalSpreadStrategy,
    IronCondorStrategy,
    LongStrangleStrategy,
    PutRatioSpreadStrategy,
)
from src.strategies.screener_engine import ScreenerEngine, get_all_strategies

__all__ = [
    "BaseStrategy",
    "BearPutSpreadStrategy",
    "BullCallSpreadStrategy",
    "CalendarSpreadStrategy",
    "CallBackspreadStrategy",
    "DiagonalSpreadStrategy",
    "IronCondorStrategy",
    "LongStrangleStrategy",
    "PutRatioSpreadStrategy",
    "ScreenerEngine",
    "get_all_strategies"
]
