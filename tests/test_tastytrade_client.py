"""
Testes Unitários do Cliente Tastytrade e Validação de Fixtures Auditadas.
Garante a Seção 3.1, 3.2, 3.3 e 3.4 da Especificação Técnica.
"""

from src.tastytrade_client import TastytradeClient
from src.pricing import OptionLeg
from src.provenance import DataValue


def test_atm_weighted_iv_formula() -> None:
    """Verifica a fórmula documentada de média de IV ponderada por proximidade do spot (Seção 3.2)."""
    ts = "2026-09-21T10:00:00Z"
    ep = "/chains/TEST"

    # Spot = 100. Strike 100 (dist 0 -> peso 1.0, IV 30%), Strike 105 (dist 5 -> peso 1/6 = 0.1667, IV 36%)
    leg1 = OptionLeg(
        symbol="T100", strike=100.0, option_type="CALL", action="BUY", ratio=1,
        bid=DataValue.medido(3.0, "api", ep, ts), ask=DataValue.medido(3.2, "api", ep, ts),
        expiration="2026-10-16", dte=30, delta=DataValue.medido(0.5, "api", ep, ts),
        iv=DataValue.medido(30.0, "api", ep, ts)
    )
    leg2 = OptionLeg(
        symbol="T105", strike=105.0, option_type="CALL", action="BUY", ratio=1,
        bid=DataValue.medido(1.0, "api", ep, ts), ask=DataValue.medido(1.2, "api", ep, ts),
        expiration="2026-10-16", dte=30, delta=DataValue.medido(0.25, "api", ep, ts),
        iv=DataValue.medido(36.0, "api", ep, ts)
    )

    result = TastytradeClient.calculate_atm_weighted_iv([leg1, leg2], spot_price=100.0, endpoint=ep, timestamp=ts)

    assert result.is_available is True
    assert result.provenance == "DERIVADO"
    # peso1 = 1.0, peso2 = 1/6 = 0.1667 -> soma_pesos = 1.1667
    # soma_iv = 1.0 * 30 + 0.1667 * 36 = 30 + 6 = 36
    # média = 36 / 1.1667 = ~30.857
    assert 30.0 < result.value < 32.0


def test_fixtures_load_spy() -> None:
    client = TastytradeClient()
    ctx = client.fetch_market_context_from_fixture("SPY")
    assert ctx.symbol == "SPY"
    assert ctx.spot_price.is_available is True
    assert ctx.iv_rank.value == 25.0
    assert ctx.trend.direction.value == "ALTA"
    assert ctx.event_in_horizon.provenance == "INDISPONIVEL"  # Demonstrando conformidade Seção 3.4
    assert len(ctx.chains_by_expiration) >= 2
    # Curva a termo de IV invertida em SPY (Curto 38.0 > Longo 30.0)
    assert ctx.term_structure_atm_iv["2026-10-16"].value > ctx.term_structure_atm_iv["2026-11-20"].value


def test_fixtures_load_aapl() -> None:
    client = TastytradeClient()
    ctx = client.fetch_market_context_from_fixture("AAPL")
    assert ctx.symbol == "AAPL"
    assert ctx.iv_rank.value == 62.0
    assert ctx.trend.direction.value == "NEUTRO"
    assert ctx.event_in_horizon.value is False


def test_fixtures_load_qqq() -> None:
    client = TastytradeClient()
    ctx = client.fetch_market_context_from_fixture("QQQ")
    assert ctx.symbol == "QQQ"
    assert ctx.iv_rank.value == 35.0
    assert ctx.trend.direction.value == "BAIXA"
    assert ctx.event_in_horizon.value is False
