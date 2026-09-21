"""
Motor de Varredura (Screener Engine) — Executa as 8 Estratégias sobre o Universo.
"""

from __future__ import annotations

from collections.abc import Sequence

from src.models import MarketContext, ScreeningResult
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


def get_all_strategies(iron_condor_wing_width: float = 5.0) -> list[BaseStrategy]:
    """Retorna instâncias das 8 estratégias especificadas na Seção 4."""
    return [
        BullCallSpreadStrategy(),
        BearPutSpreadStrategy(),
        LongStrangleStrategy(),
        IronCondorStrategy(wing_width=iron_condor_wing_width),
        CalendarSpreadStrategy(),
        DiagonalSpreadStrategy(),
        PutRatioSpreadStrategy(),
        CallBackspreadStrategy()
    ]


class ScreenerEngine:
    """Motor que executa a triagem determinística das estratégias."""

    def __init__(self, strategies: Sequence[BaseStrategy] | None = None) -> None:
        self.strategies = list(strategies) if strategies is not None else get_all_strategies()

    def screen_asset(self, ctx: MarketContext) -> list[ScreeningResult]:
        """Varre todas as estratégias para um único ativo."""
        results: list[ScreeningResult] = []
        for strategy in self.strategies:
            res = strategy.evaluate(ctx)
            results.append(res)
        return results

    def screen_universe(self, contexts: Sequence[MarketContext]) -> list[ScreeningResult]:
        """Varre todas as estratégias em todos os contextos de mercado."""
        all_results: list[ScreeningResult] = []
        for ctx in contexts:
            all_results.extend(self.screen_asset(ctx))
        return all_results

    def filter_opportunities(self, results: Sequence[ScreeningResult]) -> list[ScreeningResult]:
        """Filtra apenas resultados que atendem os critérios (APROVADO ou CONDICIONAL)."""
        return [r for r in results if r.is_opportunity]
