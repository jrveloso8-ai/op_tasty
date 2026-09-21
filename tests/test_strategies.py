"""
Testes Unitários do Motor de Estratégias (Seção 4 e Seção 8).
Garante para CADA UMA das 8 estratégias:
- Pelo menos 1 caso que PASSOU (APROVADO ou CONDICIONAL)
- Pelo menos 1 caso que FALHOU (REJEITADO)
Provando que todos os filtros discriminam rigorosamente as oportunidades.
"""

import pytest
from src.provenance import DataValue
from src.indicators import TrendAnalysis
from src.pricing import OptionLeg
from src.models import MarketContext
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


def _make_dummy_leg(
    symbol: str,
    strike: float,
    opt_type: str,
    delta: float,
    bid: float = 2.0,
    ask: float = 2.2,
    expiration: str = "2026-10-16",
    dte: int = 40,
    iv: float = 30.0
) -> OptionLeg:
    endpoint = f"/chains/{symbol}/{strike}"
    ts = "2026-09-21T10:00:00Z"
    return OptionLeg(
        symbol=symbol,
        strike=strike,
        option_type=opt_type,  # type: ignore[arg-type]
        action="BUY",
        ratio=1,
        bid=DataValue.medido(bid, "api:quote", endpoint, ts),
        ask=DataValue.medido(ask, "api:quote", endpoint, ts),
        expiration=expiration,
        dte=dte,
        delta=DataValue.medido(delta, "api:greeks", endpoint, ts),
        iv=DataValue.medido(iv, "api:greeks", endpoint, ts)
    )


def _build_context(
    symbol: str = "SPY",
    price: float = 540.0,
    iv_rank: float = 35.0,
    direction: str = "ALTA",
    event_in_horizon: bool | None = None,
    chains_by_exp: dict[str, list[OptionLeg]] | None = None,
    term_ivs: dict[str, float] | None = None
) -> MarketContext:
    endpoint = f"/metrics/{symbol}"
    ts = "2026-09-21T10:00:00Z"

    dv_price = DataValue.medido(price, "api:spot", endpoint, ts)
    dv_ivr = DataValue.medido(iv_rank, "api:ivr", endpoint, ts)
    dv_ivp = DataValue.medido(iv_rank * 1.05, "api:ivp", endpoint, ts)

    dv_dir = (
        DataValue.medido(direction, "calc:trend", endpoint, ts)
        if direction in ("ALTA", "BAIXA", "NEUTRO")
        else DataValue.indisponivel("calc:trend", endpoint, ts)
    )

    trend = TrendAnalysis(
        direction=dv_dir,  # type: ignore[arg-type]
        current_price=dv_price,
        mm20=DataValue.medido(price - 5, "calc:mm20", endpoint, ts),
        mm50=DataValue.medido(price - 15, "calc:mm50", endpoint, ts),
        mm200=DataValue.medido(price - 40, "calc:mm200", endpoint, ts),
        rsi14=DataValue.medido(55.0, "calc:rsi", endpoint, ts),
        notes="mocked"
    )

    if event_in_horizon is None:
        dv_event = DataValue.indisponivel("api:event", endpoint, ts)
    else:
        dv_event = DataValue.medido(event_in_horizon, "api:event", endpoint, ts)

    chains = chains_by_exp or {}
    term_map: dict[str, DataValue[float]] = {}
    if term_ivs:
        for exp, val in term_ivs.items():
            term_map[exp] = DataValue.medido(val, "calc:atm_iv", f"/chains/{exp}", ts)

    return MarketContext(
        symbol=symbol,
        spot_price=dv_price,
        iv_rank=dv_ivr,
        iv_percentile=dv_ivp,
        trend=trend,
        event_in_horizon=dv_event,
        chains_by_expiration=chains,
        term_structure_atm_iv=term_map,
        timestamp=ts
    )


# -------------------------------------------------------------
# 1. BULL CALL SPREAD
# -------------------------------------------------------------
def test_bull_call_spread_pass() -> None:
    strat = BullCallSpreadStrategy()
    ctx = _build_context(direction="ALTA", iv_rank=28.0)
    res = strat.evaluate(ctx)
    assert res.status == "APROVADO"
    assert res.is_opportunity is True


def test_bull_call_spread_fail_direction() -> None:
    strat = BullCallSpreadStrategy()
    ctx = _build_context(direction="BAIXA", iv_rank=28.0)
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("esperado ALTA" in r for r in res.rejection_reasons)


def test_bull_call_spread_fail_iv_rank() -> None:
    strat = BullCallSpreadStrategy()
    ctx = _build_context(direction="ALTA", iv_rank=52.0)
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any(">= 40.0" in r for r in res.rejection_reasons)


# -------------------------------------------------------------
# 2. BEAR PUT SPREAD
# -------------------------------------------------------------
def test_bear_put_spread_pass() -> None:
    strat = BearPutSpreadStrategy()
    ctx = _build_context(direction="BAIXA", iv_rank=32.0)
    res = strat.evaluate(ctx)
    assert res.status == "APROVADO"


def test_bear_put_spread_fail_direction() -> None:
    strat = BearPutSpreadStrategy()
    ctx = _build_context(direction="ALTA", iv_rank=32.0)
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("esperado BAIXA" in r for r in res.rejection_reasons)


def test_bear_put_spread_fail_iv_rank() -> None:
    strat = BearPutSpreadStrategy()
    ctx = _build_context(direction="BAIXA", iv_rank=45.0)
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any(">= 40.0" in r for r in res.rejection_reasons)


# -------------------------------------------------------------
# 3. LONG STRANGLE
# -------------------------------------------------------------
def test_long_strangle_pass_approved() -> None:
    strat = LongStrangleStrategy()
    ctx = _build_context(iv_rank=22.0, event_in_horizon=True)
    res = strat.evaluate(ctx)
    assert res.status == "APROVADO"


def test_long_strangle_pass_conditional_when_event_indisponivel() -> None:
    strat = LongStrangleStrategy()
    ctx = _build_context(iv_rank=22.0, event_in_horizon=None)  # evento INDISPONIVEL
    res = strat.evaluate(ctx)
    assert res.status == "CONDICIONAL"
    assert res.is_opportunity is True
    assert "CONDICIONAL" in res.notes


def test_long_strangle_fail_high_iv() -> None:
    strat = LongStrangleStrategy()
    ctx = _build_context(iv_rank=45.0, event_in_horizon=True)
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any(">= 30.0" in r for r in res.rejection_reasons)


def test_long_strangle_fail_no_event() -> None:
    strat = LongStrangleStrategy()
    ctx = _build_context(iv_rank=22.0, event_in_horizon=False)
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("FALSE" in r for r in res.rejection_reasons)


# -------------------------------------------------------------
# 4. IRON CONDOR
# -------------------------------------------------------------
def test_iron_condor_pass_approved() -> None:
    strat = IronCondorStrategy(wing_width=5.0)
    ctx = _build_context(direction="NEUTRO", iv_rank=65.0, event_in_horizon=False)
    res = strat.evaluate(ctx)
    assert res.status == "APROVADO"


def test_iron_condor_pass_conditional_when_event_indisponivel() -> None:
    strat = IronCondorStrategy()
    ctx = _build_context(direction="NEUTRO", iv_rank=65.0, event_in_horizon=None)
    res = strat.evaluate(ctx)
    assert res.status == "CONDICIONAL"


def test_iron_condor_fail_low_iv() -> None:
    strat = IronCondorStrategy()
    ctx = _build_context(direction="NEUTRO", iv_rank=42.0, event_in_horizon=False)
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("<= 50.0" in r for r in res.rejection_reasons)


def test_iron_condor_fail_directional() -> None:
    strat = IronCondorStrategy()
    ctx = _build_context(direction="ALTA", iv_rank=65.0, event_in_horizon=False)
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("esperado NEUTRO" in r for r in res.rejection_reasons)


def test_iron_condor_fail_event_present() -> None:
    strat = IronCondorStrategy()
    ctx = _build_context(direction="NEUTRO", iv_rank=65.0, event_in_horizon=True)
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("TRUE" in r for r in res.rejection_reasons)


# -------------------------------------------------------------
# 5. CALENDAR SPREAD
# -------------------------------------------------------------
def test_calendar_spread_pass_inverted_term_structure() -> None:
    strat = CalendarSpreadStrategy()
    chains = {
        "2026-10-16": [_make_dummy_leg("SPY", 540.0, "CALL", 0.50, dte=25)],
        "2026-11-20": [_make_dummy_leg("SPY", 540.0, "CALL", 0.50, dte=60)]
    }
    # Vencimento curto (42%) > Vencimento longo (32%) = Invertida
    term_ivs = {"2026-10-16": 42.0, "2026-11-20": 32.0}
    ctx = _build_context(chains_by_exp=chains, term_ivs=term_ivs)
    res = strat.evaluate(ctx)
    assert res.status == "APROVADO"
    assert res.mandatory_criteria["term_structure_inverted"] is True


def test_calendar_spread_fail_contango() -> None:
    strat = CalendarSpreadStrategy()
    chains = {
        "2026-10-16": [_make_dummy_leg("SPY", 540.0, "CALL", 0.50, dte=25)],
        "2026-11-20": [_make_dummy_leg("SPY", 540.0, "CALL", 0.50, dte=60)]
    }
    # Curto (28%) <= Longo (35%) = Normal (rejeita)
    term_ivs = {"2026-10-16": 28.0, "2026-11-20": 35.0}
    ctx = _build_context(chains_by_exp=chains, term_ivs=term_ivs)
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("contango" in r.lower() for r in res.rejection_reasons)


# -------------------------------------------------------------
# 6. DIAGONAL SPREAD / PMCC
# -------------------------------------------------------------
def test_diagonal_spread_pass() -> None:
    strat = DiagonalSpreadStrategy()
    chains = {
        "2026-10-16": [_make_dummy_leg("SPY", 550.0, "CALL", 0.25, dte=25)],
        "2027-01-15": [_make_dummy_leg("SPY", 480.0, "CALL", 0.78, dte=116)]
    }
    ctx = _build_context(direction="ALTA", chains_by_exp=chains)
    res = strat.evaluate(ctx)
    assert res.status == "APROVADO"


def test_diagonal_spread_fail_direction() -> None:
    strat = DiagonalSpreadStrategy()
    chains = {
        "2026-10-16": [_make_dummy_leg("SPY", 550.0, "CALL", 0.25, dte=25)],
        "2027-01-15": [_make_dummy_leg("SPY", 480.0, "CALL", 0.78, dte=116)]
    }
    ctx = _build_context(direction="BAIXA", chains_by_exp=chains)
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("esperado ALTA" in r for r in res.rejection_reasons)


def test_diagonal_spread_fail_no_deep_itm_call() -> None:
    strat = DiagonalSpreadStrategy()
    # Perna longa só tem delta 0.40, sem opção 0.70-0.80
    chains = {
        "2026-10-16": [_make_dummy_leg("SPY", 550.0, "CALL", 0.25, dte=25)],
        "2027-01-15": [_make_dummy_leg("SPY", 540.0, "CALL", 0.40, dte=116)]
    }
    ctx = _build_context(direction="ALTA", chains_by_exp=chains)
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("delta 0.70-0.80" in r for r in res.rejection_reasons)


# -------------------------------------------------------------
# 7. PUT RATIO SPREAD (1x2)
# -------------------------------------------------------------
def test_put_ratio_spread_pass_alta() -> None:
    strat = PutRatioSpreadStrategy()
    ctx = _build_context(direction="ALTA", iv_rank=58.0)
    res = strat.evaluate(ctx)
    assert res.status == "APROVADO"


def test_put_ratio_spread_pass_neutro() -> None:
    strat = PutRatioSpreadStrategy()
    ctx = _build_context(direction="NEUTRO", iv_rank=62.0)
    res = strat.evaluate(ctx)
    assert res.status == "APROVADO"


def test_put_ratio_spread_fail_baixa() -> None:
    strat = PutRatioSpreadStrategy()
    ctx = _build_context(direction="BAIXA", iv_rank=58.0)
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("esperado ALTA ou NEUTRO" in r for r in res.rejection_reasons)


def test_put_ratio_spread_fail_low_iv() -> None:
    strat = PutRatioSpreadStrategy()
    ctx = _build_context(direction="ALTA", iv_rank=35.0)
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("<= 50.0" in r for r in res.rejection_reasons)


# -------------------------------------------------------------
# 8. CALL BACKSPREAD (1x2)
# -------------------------------------------------------------
def test_call_backspread_pass() -> None:
    strat = CallBackspreadStrategy()
    # Sold ATM IV (35%) >= Bought OTM IV (28%)
    leg_atm = _make_dummy_leg("SPY", 540.0, "CALL", 0.50, iv=35.0)
    leg_otm = _make_dummy_leg("SPY", 555.0, "CALL", 0.25, iv=28.0)
    chains = {"2026-10-16": [leg_atm, leg_otm]}
    ctx = _build_context(direction="ALTA", chains_by_exp=chains)
    res = strat.evaluate(ctx)
    assert res.status == "APROVADO"


def test_call_backspread_fail_direction() -> None:
    strat = CallBackspreadStrategy()
    ctx = _build_context(direction="NEUTRO")
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("esperado ALTA" in r for r in res.rejection_reasons)


def test_call_backspread_fail_skew() -> None:
    strat = CallBackspreadStrategy()
    # Sold ATM IV (22%) < Bought OTM IV (32%) -> Skew desfavorável
    leg_atm = _make_dummy_leg("SPY", 540.0, "CALL", 0.50, iv=22.0)
    leg_otm = _make_dummy_leg("SPY", 555.0, "CALL", 0.25, iv=32.0)
    chains = {"2026-10-16": [leg_atm, leg_otm]}
    ctx = _build_context(direction="ALTA", chains_by_exp=chains)
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("desfavorável" in r.lower() for r in res.rejection_reasons)
