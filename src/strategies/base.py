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

    min_open_interest: int = 100
    min_volume: int = 0

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
    tolerance: float = 0.15,
    min_open_interest: int = 100,
    min_volume: int = 0
) -> OptionLeg | None:
    """
    Busca a opção cujo delta está mais próximo do alvo dentro de uma tolerância,
    filtrando estritamente por liquidez mínima (Open Interest e Volume) conforme §1.1.
    """
    candidates = []
    for leg in legs:
        if leg.option_type != opt_type:
            continue
        if not leg.delta.is_available or leg.delta.value is None:
            continue
        if abs(leg.delta.value - target_delta) > tolerance:
            continue
        # Filtro de liquidez (§1.1): descarta strikes com OI ou volume abaixo do piso se medido
        if (
            leg.open_interest is not None
            and leg.open_interest.is_available
            and leg.open_interest.value is not None
            and leg.open_interest.value < min_open_interest
        ):
            continue
        if (
            leg.volume is not None
            and leg.volume.is_available
            and leg.volume.value is not None
            and leg.volume.value < min_volume
        ):
            continue
        candidates.append(leg)

    if not candidates:
        return None

    return min(candidates, key=lambda leg: abs((leg.delta.value or 0.0) - target_delta))


def find_atm_option(
    legs: Sequence[OptionLeg],
    opt_type: str,
    spot_price: float,
    min_open_interest: int = 100,
    min_volume: int = 0,
) -> OptionLeg | None:
    """Retorna a perna mais próxima do dinheiro (strike mais próximo do spot).

    Aplica filtro de liquidez (§1.1): descarta strikes com OI < min_open_interest ou volume < min_volume
    se os dados estiverem disponíveis.
    """
    candidates = []
    for leg in legs:
        if leg.option_type != opt_type:
            continue
        if (
            leg.open_interest is not None
            and leg.open_interest.is_available
            and leg.open_interest.value is not None
            and leg.open_interest.value < min_open_interest
        ):
            continue
        if (
            leg.volume is not None
            and leg.volume.is_available
            and leg.volume.value is not None
            and leg.volume.value < min_volume
        ):
            continue
        candidates.append(leg)

    if not candidates:
        return None
    return min(candidates, key=lambda l: abs(l.strike - spot_price))


def check_dividend_assignment_risk(
    ctx: MarketContext,
    short_call_leg: OptionLeg
) -> tuple[bool, str]:
    """
    Verifica se há risco de atribuição antecipada por dividendo na perna curta de Call (§1.2 e §2.2).
    Regra determinística:
      - Atribuição é provável se a data ex-dividendo for anterior ou igual ao vencimento
        E o dividendo esperado for maior ou igual ao valor extrínseco da Call vendida.
    Retorna (has_risk: bool, warning_message: str).
    """
    if not ctx.dividend_ex_date or not ctx.dividend_ex_date.is_available or not ctx.dividend_ex_date.value:
        return False, ""

    ex_date = ctx.dividend_ex_date.value
    if ex_date > short_call_leg.expiration:
        return False, ""

    # Determina o provento esperado por ação
    div_amount = 0.0
    if ctx.dividend_rate_per_share and ctx.dividend_rate_per_share.is_available and ctx.dividend_rate_per_share.value:
        div_amount = ctx.dividend_rate_per_share.value
    elif ctx.dividend_yield and ctx.dividend_yield.is_available and ctx.dividend_yield.value and ctx.spot_price.value:
        div_amount = round((ctx.spot_price.value * (ctx.dividend_yield.value / 100.0)) / 4.0, 2)

    if div_amount <= 0.0:
        return False, ""

    # Extrínseco = Call_Mid - max(0, Spot - Strike)
    spot = ctx.spot_price.value or 0.0
    intrinsic = max(0.0, spot - short_call_leg.strike)
    call_bid = short_call_leg.bid.value or 0.0
    call_ask = short_call_leg.ask.value or 0.0
    call_mid = (call_bid + call_ask) / 2.0 if (call_bid > 0 and call_ask > 0) else (call_bid or call_ask)
    extrinsic = max(0.0, round(call_mid - intrinsic, 2))

    if div_amount >= extrinsic:
        msg = (
            f"⚠️ RISCO DE ATRIBUIÇÃO POR DIVIDENDO: Data ex ({ex_date}) ocorre antes ou no vencimento "
            f"({short_call_leg.expiration}). Dividendo projetado (${div_amount:.2f}) >= valor extrínseco "
            f"da Call vendida strike {short_call_leg.strike:.1f} (${extrinsic:.2f}). Risco iminente de exercício antecipado."
        )
        return True, msg

    return False, ""


def check_put_call_parity_sanity(
    chain: Sequence[OptionLeg],
    spot_price: float,
    max_divergence_pct: float = 0.20
) -> list[str]:
    """
    Sanity check de paridade Put-Call para detecção de dados corrompidos ou ticks anômalos (§1.4).
    Compara |(C_mid - P_mid) - (S - K)| para opções ATM.
    """
    warnings: list[str] = []
    calls = {l.strike: l for l in chain if l.option_type == "CALL" and l.bid.is_available and l.ask.is_available}
    puts = {l.strike: l for l in chain if l.option_type == "PUT" and l.bid.is_available and l.ask.is_available}
    common_strikes = set(calls.keys()) & set(puts.keys())

    for k in common_strikes:
        if abs(k - spot_price) > spot_price * 0.05:
            continue
        c = calls[k]
        p = puts[k]
        c_bid = c.bid.value or 0.0
        c_ask = c.ask.value or 0.0
        p_bid = p.bid.value or 0.0
        p_ask = p.ask.value or 0.0
        c_mid = (c_bid + c_ask) / 2.0
        p_mid = (p_bid + p_ask) / 2.0
        parity_diff = abs((c_mid - p_mid) - (spot_price - k))
        if spot_price > 0 and (parity_diff / spot_price) > max_divergence_pct:
            warnings.append(
                f"Alerta de paridade Put-Call no strike {k}: desvio de ${parity_diff:.2f} "
                f"({parity_diff / spot_price * 100:.1f}% do spot) pode indicar tick anômalo."
            )
    return warnings
