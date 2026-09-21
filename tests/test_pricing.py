"""
Testes Unitários de Precificação Conservadora de Estruturas de Opções.
Garante a regra estrita da Seção 5.1 (Ask para compra, Bid para venda,
rótulos conforme sinal real, e contágio por bid/ask ausente ou zero).
"""

import pytest
from src.provenance import DataValue
from src.pricing import (
    OptionLeg,
    calculate_conservative_pricing
)


def _make_leg(
    symbol: str,
    strike: float,
    opt_type: str,
    action: str,
    ratio: int,
    bid: float | None,
    ask: float | None,
    delta: float = 0.5
) -> OptionLeg:
    """Helper para criar uma perna de teste com proveniência auditada."""
    endpoint = f"/market-data/chains/TEST/{strike}"
    ts = "2026-09-21T10:00:00Z"

    dv_bid = (
        DataValue.medido(bid, "api:quote", endpoint, ts)
        if bid is not None and bid > 0
        else DataValue.indisponivel("api:quote", endpoint, ts)
    )
    dv_ask = (
        DataValue.medido(ask, "api:quote", endpoint, ts)
        if ask is not None and ask > 0
        else DataValue.indisponivel("api:quote", endpoint, ts)
    )
    dv_delta = DataValue.medido(delta, "api:greeks", endpoint, ts)

    return OptionLeg(
        symbol=symbol,
        strike=strike,
        option_type=opt_type,  # type: ignore[arg-type]
        action=action,  # type: ignore[arg-type]
        ratio=ratio,
        bid=dv_bid,
        ask=dv_ask,
        expiration="2026-10-16",
        dte=45,
        delta=dv_delta
    )


def test_debit_spread_pricing_custo_maximo() -> None:
    """Compra no Ask (5.20) e Venda no Bid (2.10) gera débito líquido de 3.10."""
    leg_buy = _make_leg("SPY_C540", 540.0, "CALL", "BUY", 1, bid=5.00, ask=5.20, delta=0.50)
    leg_sell = _make_leg("SPY_C550", 550.0, "CALL", "SELL", 1, bid=2.10, ask=2.25, delta=0.25)

    pricing = calculate_conservative_pricing([leg_buy, leg_sell])

    assert pricing.pricing_type == "DEBIT"
    assert pricing.label == "CUSTO MÁXIMO A PAGAR"
    assert pricing.net_cash_flow.value == -3.10
    assert pricing.display_value.value == 3.10
    assert pricing.display_value.provenance == "DERIVADO"
    assert len(pricing.details) == 2


def test_credit_spread_pricing_valor_minimo() -> None:
    """Estrutura com saldo positivo gera 'VALOR MÍNIMO A RECEBER'."""
    leg_sell = _make_leg("SPY_P520", 520.0, "PUT", "SELL", 1, bid=3.00, ask=3.20, delta=-0.25)
    leg_buy = _make_leg("SPY_P510", 510.0, "PUT", "BUY", 1, bid=1.10, ask=1.20, delta=-0.15)

    pricing = calculate_conservative_pricing([leg_sell, leg_buy])

    # Recebe 3.00 (Bid da venda) - Paga 1.20 (Ask da compra) = +1.80
    assert pricing.pricing_type == "CREDIT"
    assert pricing.label == "VALOR MÍNIMO A RECEBER"
    assert pricing.net_cash_flow.value == 1.80
    assert pricing.display_value.value == 1.80
    assert pricing.display_value.provenance == "DERIVADO"


def test_ratio_spread_1x2_pricing() -> None:
    """1 comprada (Ask 4.00) e 2 vendidas (Bid 2.50) -> net = -4.00 + 5.00 = +1.00 crédito."""
    leg_buy = _make_leg("AAPL_P220", 220.0, "PUT", "BUY", 1, bid=3.80, ask=4.00, delta=-0.45)
    leg_sell = _make_leg("AAPL_P210", 210.0, "PUT", "SELL", 2, bid=2.50, ask=2.65, delta=-0.20)

    pricing = calculate_conservative_pricing([leg_buy, leg_sell])

    assert pricing.pricing_type == "CREDIT"
    assert pricing.label == "VALOR MÍNIMO A RECEBER"
    assert pricing.display_value.value == 1.00


def test_missing_ask_on_bought_leg_causes_contagion() -> None:
    """Se o Ask da perna comprada for INDISPONIVEL, toda a precificação é INDISPONIVEL."""
    leg_buy = _make_leg("SPY_C540", 540.0, "CALL", "BUY", 1, bid=5.00, ask=None)  # Ask ausente
    leg_sell = _make_leg("SPY_C550", 550.0, "CALL", "SELL", 1, bid=2.10, ask=2.25)

    pricing = calculate_conservative_pricing([leg_buy, leg_sell])

    assert pricing.pricing_type == "INDISPONIVEL"
    assert pricing.label == "DADO INDISPONIVEL"
    assert pricing.display_value.provenance == "INDISPONIVEL"
    assert pricing.display_value.value is None


def test_missing_bid_on_sold_leg_causes_contagion() -> None:
    """Se o Bid da perna vendida for INDISPONIVEL, toda a precificação é INDISPONIVEL."""
    leg_buy = _make_leg("SPY_C540", 540.0, "CALL", "BUY", 1, bid=5.00, ask=5.20)
    leg_sell = _make_leg("SPY_C550", 550.0, "CALL", "SELL", 1, bid=None, ask=2.25)  # Bid ausente

    pricing = calculate_conservative_pricing([leg_buy, leg_sell])

    assert pricing.pricing_type == "INDISPONIVEL"
    assert pricing.label == "DADO INDISPONIVEL"
    assert pricing.display_value.provenance == "INDISPONIVEL"
    assert pricing.display_value.value is None


def test_zero_bid_or_ask_never_falls_back_to_mid() -> None:
    """Bid ou Ask zero na API deve ser tratado como INDISPONIVEL, nunca usar mid."""
    endpoint = "/market-data/chains/TEST/540"
    ts = "2026-09-21T10:00:00Z"
    # Cria leg explicitamente com bid = 0.0 medido da API
    leg_buy = OptionLeg(
        symbol="TEST_ZERO",
        strike=540.0,
        option_type="CALL",
        action="BUY",
        ratio=1,
        bid=DataValue.medido(0.0, "api:quote", endpoint, ts),
        ask=DataValue.medido(0.0, "api:quote", endpoint, ts),  # Ask zerado
        expiration="2026-10-16",
        dte=45,
        delta=DataValue.medido(0.5, "api:greeks", endpoint, ts)
    )
    leg_sell = _make_leg("SPY_C550", 550.0, "CALL", "SELL", 1, bid=1.0, ask=1.2)

    pricing = calculate_conservative_pricing([leg_buy, leg_sell])
    assert pricing.pricing_type == "INDISPONIVEL"
    assert pricing.label == "DADO INDISPONIVEL"


def test_empty_legs_returns_indisponivel() -> None:
    pricing = calculate_conservative_pricing([])
    assert pricing.pricing_type == "INDISPONIVEL"
    assert pricing.label == "DADO INDISPONIVEL"
