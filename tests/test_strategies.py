"""
Testes Unitários do Motor de Estratégias (Seção 4 e Seção 8).
Garante para CADA UMA das 8 estratégias:
- Pelo menos 1 caso que PASSOU (APROVADO ou CONDICIONAL)
- Pelo menos 1 caso que FALHOU (REJEITADO)
Provando que todos os filtros discriminam rigorosamente as oportunidades.
"""



from src.indicators import TrendAnalysis
from src.models import MarketContext
from src.pricing import OptionLeg
from src.provenance import DataValue
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


def _make_dummy_leg(
    symbol: str,
    strike: float,
    opt_type: str,
    delta: float,
    bid: float = 2.0,
    ask: float = 2.2,
    expiration: str = "2026-10-16",
    dte: int = 40,
    iv: float = 30.0,
    open_interest: int | None = None
) -> OptionLeg:
    endpoint = f"/chains/{symbol}/{strike}"
    ts = "2026-09-21T10:00:00Z"
    oi_dv = DataValue.medido(open_interest, "api:oi", endpoint, ts) if open_interest is not None else None
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
        iv=DataValue.medido(iv, "api:greeks", endpoint, ts),
        open_interest=oi_dv
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

    dv_event: DataValue[bool | None]
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
    leg_buy = _make_dummy_leg("SPY", 535.0, "CALL", 0.50, dte=40)
    leg_sell = _make_dummy_leg("SPY", 545.0, "CALL", 0.25, dte=40)
    chains = {"2026-10-16": [leg_buy, leg_sell]}
    ctx = _build_context(direction="ALTA", iv_rank=28.0, chains_by_exp=chains)
    res = strat.evaluate(ctx)
    assert res.status == "APROVADO"
    assert res.is_opportunity is True
    assert len(res.suggested_legs) == 2


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


def test_bull_call_spread_fail_missing_legs() -> None:
    strat = BullCallSpreadStrategy()
    ctx = _build_context(direction="ALTA", iv_rank=28.0, chains_by_exp={})
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("Ausência de pernas" in r for r in res.rejection_reasons)


# -------------------------------------------------------------
# 2. BEAR PUT SPREAD
# -------------------------------------------------------------
def test_bear_put_spread_pass() -> None:
    strat = BearPutSpreadStrategy()
    leg_buy = _make_dummy_leg("SPY", 545.0, "PUT", -0.50, dte=40)
    leg_sell = _make_dummy_leg("SPY", 535.0, "PUT", -0.25, dte=40)
    chains = {"2026-10-16": [leg_buy, leg_sell]}
    ctx = _build_context(direction="BAIXA", iv_rank=32.0, chains_by_exp=chains)
    res = strat.evaluate(ctx)
    assert res.status == "APROVADO"
    assert len(res.suggested_legs) == 2


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


def test_bear_put_spread_fail_missing_legs() -> None:
    strat = BearPutSpreadStrategy()
    ctx = _build_context(direction="BAIXA", iv_rank=32.0, chains_by_exp={})
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("Ausência de pernas" in r for r in res.rejection_reasons)


# -------------------------------------------------------------
# 3. LONG STRANGLE
# -------------------------------------------------------------
def test_long_strangle_pass_approved() -> None:
    strat = LongStrangleStrategy()
    leg_c = _make_dummy_leg("SPY", 555.0, "CALL", 0.25, dte=40)
    leg_p = _make_dummy_leg("SPY", 525.0, "PUT", -0.25, dte=40)
    chains = {"2026-10-16": [leg_c, leg_p]}
    ctx = _build_context(iv_rank=22.0, event_in_horizon=True, chains_by_exp=chains)
    res = strat.evaluate(ctx)
    assert res.status == "APROVADO"
    assert len(res.suggested_legs) == 2


def test_long_strangle_pass_conditional_when_event_indisponivel() -> None:
    strat = LongStrangleStrategy()
    leg_c = _make_dummy_leg("SPY", 555.0, "CALL", 0.25, dte=40)
    leg_p = _make_dummy_leg("SPY", 525.0, "PUT", -0.25, dte=40)
    chains = {"2026-10-16": [leg_c, leg_p]}
    ctx = _build_context(iv_rank=22.0, event_in_horizon=None, chains_by_exp=chains)
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


def test_long_strangle_fail_missing_legs() -> None:
    strat = LongStrangleStrategy()
    ctx = _build_context(iv_rank=22.0, event_in_horizon=True, chains_by_exp={})
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("Ausência de pernas" in r for r in res.rejection_reasons)


# -------------------------------------------------------------
# 4. IRON CONDOR
# -------------------------------------------------------------
def test_iron_condor_pass_approved() -> None:
    strat = IronCondorStrategy(wing_width=5.0)
    sc = _make_dummy_leg("SPY", 555.0, "CALL", 0.16, dte=40)
    lc = _make_dummy_leg("SPY", 560.0, "CALL", 0.10, dte=40)
    sp = _make_dummy_leg("SPY", 525.0, "PUT", -0.16, dte=40)
    lp = _make_dummy_leg("SPY", 520.0, "PUT", -0.10, dte=40)
    chains = {"2026-10-16": [sc, lc, sp, lp]}
    ctx = _build_context(direction="NEUTRO", iv_rank=65.0, event_in_horizon=False, chains_by_exp=chains)
    res = strat.evaluate(ctx)
    assert res.status == "APROVADO"
    assert len(res.suggested_legs) == 4


def test_iron_condor_pass_conditional_when_event_indisponivel() -> None:
    strat = IronCondorStrategy(wing_width=5.0)
    sc = _make_dummy_leg("SPY", 555.0, "CALL", 0.16, dte=40)
    lc = _make_dummy_leg("SPY", 560.0, "CALL", 0.10, dte=40)
    sp = _make_dummy_leg("SPY", 525.0, "PUT", -0.16, dte=40)
    lp = _make_dummy_leg("SPY", 520.0, "PUT", -0.10, dte=40)
    chains = {"2026-10-16": [sc, lc, sp, lp]}
    ctx = _build_context(direction="NEUTRO", iv_rank=65.0, event_in_horizon=None, chains_by_exp=chains)
    res = strat.evaluate(ctx)
    assert res.status == "CONDICIONAL"
    assert len(res.suggested_legs) == 4


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


def test_iron_condor_fail_missing_legs() -> None:
    strat = IronCondorStrategy()
    ctx = _build_context(direction="NEUTRO", iv_rank=65.0, event_in_horizon=False, chains_by_exp={})
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("Ausência de pernas" in r for r in res.rejection_reasons)


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
    # Perna longa só tem delta 0.40, sem opção [0.70-0.85]
    chains = {
        "2026-10-16": [_make_dummy_leg("SPY", 550.0, "CALL", 0.25, dte=25)],
        "2027-01-15": [_make_dummy_leg("SPY", 540.0, "CALL", 0.40, dte=116)]
    }
    ctx = _build_context(direction="ALTA", chains_by_exp=chains)
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("Ausência de perna longa" in r for r in res.rejection_reasons)


def test_diagonal_spread_fail_missing_short_leg_amc_scenario() -> None:
    """
    Cenário real identificado no AMC:
    Tem CALL longa delta 0.78 no vencimento de 120 dias,
    mas no vencimento curto (dte 30) NÃO há strike com delta 0.20-0.30 (ex: apenas 0.77 e 0.50).
    A estratégia DEVE ser REJEITADA com motivo explícito, NUNCA aprovada sem pernas sugeridas.
    """
    strat = DiagonalSpreadStrategy()
    chains = {
        "2026-10-16": [
            _make_dummy_leg("AMC", 2.5, "CALL", 0.77, dte=30),
            _make_dummy_leg("AMC", 3.0, "CALL", 0.50, dte=30)
        ],
        "2027-01-15": [_make_dummy_leg("AMC", 2.0, "CALL", 0.78, dte=120)]
    }
    ctx = _build_context(symbol="AMC", price=2.91, direction="ALTA", chains_by_exp=chains)
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("Ausência de perna curta com delta entre 0.20 e 0.30" in r for r in res.rejection_reasons)
    assert len(res.suggested_legs) == 0


# -------------------------------------------------------------
# 7. PUT RATIO SPREAD (1x2)
# -------------------------------------------------------------
def test_put_ratio_spread_pass_alta() -> None:
    strat = PutRatioSpreadStrategy()
    leg_buy = _make_dummy_leg("SPY", 545.0, "PUT", -0.45, dte=40)
    leg_sell = _make_dummy_leg("SPY", 535.0, "PUT", -0.20, dte=40)
    chains = {"2026-10-16": [leg_buy, leg_sell]}
    ctx = _build_context(direction="ALTA", iv_rank=58.0, chains_by_exp=chains)
    res = strat.evaluate(ctx)
    assert res.status == "APROVADO"
    assert len(res.suggested_legs) == 2


def test_put_ratio_spread_pass_neutro() -> None:
    strat = PutRatioSpreadStrategy()
    leg_buy = _make_dummy_leg("SPY", 545.0, "PUT", -0.45, dte=40)
    leg_sell = _make_dummy_leg("SPY", 535.0, "PUT", -0.20, dte=40)
    chains = {"2026-10-16": [leg_buy, leg_sell]}
    ctx = _build_context(direction="NEUTRO", iv_rank=62.0, chains_by_exp=chains)
    res = strat.evaluate(ctx)
    assert res.status == "APROVADO"
    assert len(res.suggested_legs) == 2


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


def test_put_ratio_spread_fail_missing_legs() -> None:
    strat = PutRatioSpreadStrategy()
    ctx = _build_context(direction="ALTA", iv_rank=58.0, chains_by_exp={})
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("Ausência de pernas" in r for r in res.rejection_reasons)


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


# -------------------------------------------------------------
# 9. GESTÃO DE RISCO PARA ATIVOS DE ALTO VALOR (> $100)
# -------------------------------------------------------------
def test_put_ratio_spread_rejected_on_high_price_when_rule_enabled() -> None:
    strat = PutRatioSpreadStrategy(prohibit_naked_on_high_price=True, high_price_threshold=100.0)
    leg_buy = _make_dummy_leg("SPY", 545.0, "PUT", -0.45, dte=40)
    leg_sell = _make_dummy_leg("SPY", 535.0, "PUT", -0.20, dte=40)
    chains = {"2026-10-16": [leg_buy, leg_sell]}
    # Spot = 540.0 > 100.0 -> deve rejeitar por ponta nua a descoberto
    ctx = _build_context(symbol="SPY", price=540.0, direction="ALTA", iv_rank=58.0, chains_by_exp=chains)
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("Proibido risco não-definido/ponta a descoberto" in r for r in res.rejection_reasons)


def test_put_ratio_spread_approved_on_low_price_when_rule_enabled() -> None:
    strat = PutRatioSpreadStrategy(prohibit_naked_on_high_price=True, high_price_threshold=100.0)
    leg_buy = _make_dummy_leg("BAC", 45.0, "PUT", -0.45, dte=40)
    leg_sell = _make_dummy_leg("BAC", 40.0, "PUT", -0.20, dte=40)
    chains = {"2026-10-16": [leg_buy, leg_sell]}
    # Spot = 44.0 <= 100.0 -> aprovado
    ctx = _build_context(symbol="BAC", price=44.0, direction="ALTA", iv_rank=58.0, chains_by_exp=chains)
    res = strat.evaluate(ctx)
    assert res.status == "APROVADO"
    assert len(res.suggested_legs) == 2


def test_iron_condor_wing_width_capped_on_high_price() -> None:
    # Se configurado wing_width=10.0, para spot > 100 deve capar em max_wing_width_high_price=5.0
    strat = IronCondorStrategy(
        wing_width=10.0,
        high_price_threshold=100.0,
        max_wing_width_high_price=5.0
    )
    # Pernas vendidas em delta 0.18
    sc = _make_dummy_leg("SPY", 560.0, "CALL", 0.18, dte=35)
    sp = _make_dummy_leg("SPY", 520.0, "PUT", -0.18, dte=35)
    # Pernas compradas: a 5 pontos (565 / 515) e a 10 pontos (570 / 510)
    lc_5 = _make_dummy_leg("SPY", 565.0, "CALL", 0.10, dte=35)
    lc_10 = _make_dummy_leg("SPY", 570.0, "CALL", 0.05, dte=35)
    lp_5 = _make_dummy_leg("SPY", 515.0, "PUT", -0.10, dte=35)
    lp_10 = _make_dummy_leg("SPY", 510.0, "PUT", -0.05, dte=35)
    chains = {"2026-10-16": [sc, sp, lc_5, lc_10, lp_5, lp_10]}
    ctx = _build_context(symbol="SPY", price=540.0, direction="NEUTRO", iv_rank=60.0, event_in_horizon=False, chains_by_exp=chains)
    res = strat.evaluate(ctx)
    assert res.status == "APROVADO"
    # A asa comprada de call deve ser 565.0 (largura 5), não 570.0 (largura 10)
    bought_call = next(l for l in res.suggested_legs if l.action == "BUY" and l.option_type == "CALL")
    assert bought_call.strike == 565.0
    assert "Asa limitada a $5.00" in res.notes


def test_long_strangle_high_price_capital_warning() -> None:
    strat = LongStrangleStrategy(high_price_threshold=100.0)
    c = _make_dummy_leg("NVDA", 130.0, "CALL", 0.25, dte=40)
    p = _make_dummy_leg("NVDA", 110.0, "PUT", -0.25, dte=40)
    chains = {"2026-10-16": [c, p]}
    ctx = _build_context(symbol="NVDA", price=120.0, iv_rank=15.0, event_in_horizon=True, chains_by_exp=chains)
    res = strat.evaluate(ctx)
    assert res.status == "APROVADO"
    assert "Gestão de Risco: Ativo com spot elevado" in res.notes


def test_long_strangle_low_iv_rank_threshold_alert() -> None:
    # IV Rank = 5.0% < threshold 20.0% -> alerta de piso histórico / vácuo de catalisador
    strat = LongStrangleStrategy(low_iv_rank_threshold=20.0)
    c = _make_dummy_leg("NVDA", 130.0, "CALL", 0.25, dte=40)
    p = _make_dummy_leg("NVDA", 110.0, "PUT", -0.25, dte=40)
    chains = {"2026-10-16": [c, p]}
    ctx = _build_context(symbol="NVDA", price=50.0, iv_rank=5.0, event_in_horizon=True, chains_by_exp=chains)
    res = strat.evaluate(ctx)
    assert res.status == "APROVADO"
    assert "IV Rank no piso histórico (5.0% < 20.0%)" in res.notes
    assert "Possível vácuo de catalisador" in res.notes


def test_liquidity_filter_rejects_low_open_interest() -> None:
    # Opção com OI = 20 (< piso mínimo de 100) deve ser filtrada conforme §1.1
    ts = "2026-09-22T10:00:00Z"
    leg_illiquid = OptionLeg(
        symbol="XYZ",
        strike=100.0,
        option_type="CALL",
        action="BUY",
        ratio=1,
        bid=DataValue.medido(2.0, "api:quote", "/quote", ts),
        ask=DataValue.medido(2.2, "api:quote", "/quote", ts),
        expiration="2026-10-16",
        dte=35,
        delta=DataValue.medido(0.50, "api:greeks", "/greeks", ts),
        open_interest=DataValue.medido(20, "api:oi", "/oi", ts)  # OI < 100
    )
    from src.strategies.base import find_option_by_delta
    res = find_option_by_delta([leg_illiquid], target_delta=0.50, opt_type="CALL", min_open_interest=100)
    assert res is None


def test_dividend_assignment_risk_downgrades_bull_call_to_conditional() -> None:
    # Ex-dividend ocorre em 2026-10-10 (antes do vencimento 2026-10-16) com provento $1.50 > extrínseco da Call 550 vendida ($0.80)
    strat = BullCallSpreadStrategy()
    leg_buy = _make_dummy_leg("SPY", 540.0, "CALL", 0.50, bid=5.0, ask=5.2)
    leg_sell = _make_dummy_leg("SPY", 550.0, "CALL", 0.25, bid=0.75, ask=0.85)  # Mid $0.80, Strike 550 OTM (extrínseco $0.80)
    chains = {"2026-10-16": [leg_buy, leg_sell]}
    ts = "2026-09-22T10:00:00Z"

    ctx = _build_context(
        symbol="SPY",
        price=540.0,
        direction="ALTA",
        iv_rank=25.0,
        chains_by_exp=chains
    )
    # Anexa dividendo que excede o extrínseco
    ctx.dividend_ex_date = DataValue.medido("2026-10-10", "api:div", "/div", ts)
    ctx.dividend_rate_per_share = DataValue.medido(1.50, "api:div", "/div", ts)

    res = strat.evaluate(ctx)
    assert res.status == "CONDICIONAL"
    assert "RISCO DE ATRIBUIÇÃO POR DIVIDENDO" in res.notes
    assert res.mandatory_criteria.get("dividend_assignment_risk", {}).get("risk") is True


def test_put_ratio_spread_declares_undefined_risk_on_approval() -> None:
    strat = PutRatioSpreadStrategy()
    buy_put = _make_dummy_leg("XYZ", 90.0, "PUT", -0.45, bid=3.0, ask=3.2)
    sell_put = _make_dummy_leg("XYZ", 80.0, "PUT", -0.20, bid=1.8, ask=2.0)
    chains = {"2026-10-16": [buy_put, sell_put]}
    ctx = _build_context(symbol="XYZ", price=85.0, direction="NEUTRO", iv_rank=65.0, chains_by_exp=chains)

    res = strat.evaluate(ctx)
    assert res.status == "APROVADO"
    assert "RISCO NÃO DEFINIDO" in res.notes
    assert res.mandatory_criteria.get("undefined_risk_warning", {}).get("declared") is True


def test_iron_condor_downgrades_to_conditional_when_vrp_is_negative() -> None:
    strat = IronCondorStrategy(wing_width=5.0)
    c_short = _make_dummy_leg("SPY", 560.0, "CALL", 0.18, bid=1.0, ask=1.1)
    c_long = _make_dummy_leg("SPY", 565.0, "CALL", 0.10, bid=0.4, ask=0.5)
    p_short = _make_dummy_leg("SPY", 530.0, "PUT", -0.18, bid=1.0, ask=1.1)
    p_long = _make_dummy_leg("SPY", 525.0, "PUT", -0.10, bid=0.4, ask=0.5)
    chains = {"2026-10-16": [c_short, c_long, p_short, p_long]}
    ts = "2026-09-22T10:00:00Z"

    ctx = _build_context(symbol="SPY", price=545.0, direction="NEUTRO", iv_rank=60.0, chains_by_exp=chains, event_in_horizon=False)
    # Anexa VRP negativo (ex: IV 22% < RV20 26% -> VRP = -4.0 pts)
    ctx.volatility_risk_premium = DataValue.derivado(-4.0, "calc:vrp", "/vrp", ts)

    res = strat.evaluate(ctx)
    assert res.status == "CONDICIONAL"
    assert "VRP NEGATIVO" in res.notes


def test_put_ratio_spread_downgrades_to_conditional_when_vrp_is_negative() -> None:
    strat = PutRatioSpreadStrategy()
    buy_put = _make_dummy_leg("XYZ", 90.0, "PUT", -0.45, bid=3.0, ask=3.2)
    sell_put = _make_dummy_leg("XYZ", 80.0, "PUT", -0.20, bid=1.8, ask=2.0)
    chains = {"2026-10-16": [buy_put, sell_put]}
    ts = "2026-09-22T10:00:00Z"
    ctx = _build_context(symbol="XYZ", price=85.0, direction="NEUTRO", iv_rank=65.0, chains_by_exp=chains)
    ctx.volatility_risk_premium = DataValue.derivado(-2.5, "calc:vrp", "/vrp", ts)

    res = strat.evaluate(ctx)
    assert res.status == "CONDICIONAL"
    assert "VRP NEGATIVO" in res.notes


def test_long_strangle_warns_when_vrp_is_excessively_high() -> None:
    strat = LongStrangleStrategy()
    call_leg = _make_dummy_leg("ABC", 110.0, "CALL", 0.25, bid=2.0, ask=2.2)
    put_leg = _make_dummy_leg("ABC", 90.0, "PUT", -0.25, bid=2.0, ask=2.2)
    chains = {"2026-10-16": [call_leg, put_leg]}
    ts = "2026-09-22T10:00:00Z"
    ctx = _build_context(symbol="ABC", price=100.0, iv_rank=18.0, event_in_horizon=True, chains_by_exp=chains)
    ctx.volatility_risk_premium = DataValue.derivado(18.5, "calc:vrp", "/vrp", ts)

    res = strat.evaluate(ctx)
    assert res.status == "CONDICIONAL"
    assert "VRP ELEVADO" in res.notes


def test_strategies_respect_custom_liquidity_thresholds() -> None:
    strat = BullCallSpreadStrategy()
    strat.min_open_interest = 5000  # Config customizada
    # leg_buy tem OI 1500 < 5000, leg_sell tem OI 6000
    leg_buy = _make_dummy_leg("SPY", 540.0, "CALL", 0.50, bid=5.0, ask=5.2, open_interest=1500)
    leg_sell = _make_dummy_leg("SPY", 550.0, "CALL", 0.25, bid=1.0, ask=1.2, open_interest=6000)
    chains = {"2026-10-16": [leg_buy, leg_sell]}

    ctx = _build_context(symbol="SPY", price=540.0, direction="ALTA", iv_rank=20.0, chains_by_exp=chains)
    res = strat.evaluate(ctx)
    assert res.status == "REJEITADO"
    assert any("Ausência de pernas elegíveis" in r for r in res.rejection_reasons)





