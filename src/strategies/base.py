"""
Definição Base e Utilitários de Estratégias de Opções.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from src.models import MarketContext, ScreeningResult
from src.pricing import OptionLeg


class BaseStrategy(ABC):
    """Classe base abstrata para triagem de estratégias."""

    @property
    @abstractmethod
    def strategy_id(self) -> str:
        pass

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        pass

    @abstractmethod
    def evaluate(self, ctx: MarketContext) -> ScreeningResult:
        """Avalia se o ativo cumpre todos os critérios obrigatórios da estratégia."""


def find_option_by_delta(
    legs: Sequence[OptionLeg],
    target_delta: float,
    opt_type: str,
    tolerance: float = 0.15
) -> OptionLeg | None:
    """Busca a opção cujo delta está mais próximo do alvo dentro de uma tolerância."""
    candidates = [
        leg for leg in legs
        if leg.option_type == opt_type
        and leg.delta.is_available
        and leg.delta.value is not None
        and abs(leg.delta.value - target_delta) <= tolerance
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda l: abs((l.delta.value or 0.0) - target_delta))


def find_atm_option(legs: Sequence[OptionLeg], opt_type: str, spot_price: float) -> OptionLeg | None:
    """Busca a opção mais próxima do preço spot (ATM)."""
    candidates = [leg for leg in legs if leg.option_type == opt_type]
    if not candidates:
        return None
    return min(candidates, key=lambda l: abs(l.strike - spot_price))
