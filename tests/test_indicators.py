"""
Testes Unitários dos Indicadores Técnicos e Filtro de Direção.
Garante a regra estrita da Seção 3.3 e a regra de contágio de candles.
"""

import pytest

from src.indicators import analyze_trend, calculate_rsi, calculate_sma
from src.provenance import DataValue


def _generate_candles(
    count: int,
    start_price: float = 100.0,
    slope: float = 0.5,
    oscillate: bool = False
) -> list[DataValue[float]]:
    """Gera sequência sintética auditada de candles para teste."""
    candles: list[DataValue[float]] = []
    price = start_price
    for i in range(count):
        if oscillate:
            delta = slope if i % 2 == 0 else -0.6 * slope
            price += delta
        else:
            price += slope
        candles.append(
            DataValue.medido(
                value=round(price, 2),
                source="api:candles",
                endpoint="/market-data/candles/TEST",
                timestamp=f"2026-01-01T{i % 24:02d}:00:00Z"
            )
        )
    return candles


def test_calculate_sma() -> None:
    closes = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert calculate_sma(closes, 3) == 40.0
    assert calculate_sma(closes, 5) == 30.0
    with pytest.raises(ValueError, match="Histórico insuficiente"):
        calculate_sma(closes, 10)


def test_calculate_rsi_neutral() -> None:
    # Alternating prices
    closes = [100.0 + (i % 2) * 2.0 for i in range(30)]
    rsi = calculate_rsi(closes, 14)
    assert 40.0 <= rsi <= 60.0


def test_trend_alta_confirmed() -> None:
    """Preço > MM20 > MM50 > MM200 com RSI neutro deve classificar como ALTA."""
    # Gera tendência de alta com oscilação natural (RSI ~60)
    candles = _generate_candles(250, start_price=100.0, slope=0.3, oscillate=True)
    latest_close = candles[-1].value
    assert latest_close is not None

    current_price = DataValue.medido(
        value=latest_close + 2.0,
        source="api:quote",
        endpoint="/market-metrics",
        timestamp="2026-09-21T10:00:00Z"
    )

    result = analyze_trend(current_price, candles, symbol="SPY")
    assert result.direction.provenance == "DERIVADO"
    assert result.direction.value == "ALTA"
    assert result.mm20.value is not None
    assert result.mm50.value is not None
    assert result.mm200.value is not None
    assert current_price.value is not None
    assert current_price.value > result.mm20.value > result.mm50.value > result.mm200.value


def test_trend_alta_discarded_by_overbought_rsi() -> None:
    """Alinhamento de alta com RSI > 70 deve ser descartado para NEUTRO."""
    # Cria uma disparada agressiva no final para levar RSI acima de 70
    candles = _generate_candles(200, start_price=100.0, slope=0.1)
    # Adiciona 20 dias de disparada vertical
    last_val = candles[-1].value or 120.0
    for i in range(25):
        last_val += 5.0
        candles.append(
            DataValue.medido(last_val, "api:candles", "/candles", f"2026-02-01T{i:02d}:00:00Z")
        )

    current_price = DataValue.medido(
        value=last_val + 2.0,
        source="api:quote",
        endpoint="/metrics",
        timestamp="2026-09-21T10:00:00Z"
    )

    result = analyze_trend(current_price, candles, symbol="AAPL")
    assert result.rsi14.value is not None and result.rsi14.value > 70.0
    assert result.direction.value == "NEUTRO"
    assert "sobrecompra" in result.notes.lower()


def test_trend_baixa_confirmed() -> None:
    """Preço < MM20 < MM50 < MM200 com RSI neutro deve classificar como BAIXA."""
    # Gera tendência de baixa com oscilação natural (RSI ~40)
    candles = _generate_candles(250, start_price=300.0, slope=-0.3, oscillate=True)
    latest_close = candles[-1].value
    assert latest_close is not None

    current_price = DataValue.medido(
        value=latest_close - 2.0,
        source="api:quote",
        endpoint="/metrics",
        timestamp="2026-09-21T10:00:00Z"
    )

    result = analyze_trend(current_price, candles, symbol="QQQ")
    assert result.direction.provenance == "DERIVADO"
    assert result.direction.value == "BAIXA"
    assert result.mm20.value is not None
    assert result.mm50.value is not None
    assert result.mm200.value is not None
    assert current_price.value is not None
    assert current_price.value < result.mm20.value < result.mm50.value < result.mm200.value


def test_trend_baixa_discarded_by_oversold_rsi() -> None:
    """Alinhamento de baixa com RSI < 30 deve ser descartado para NEUTRO."""
    candles = _generate_candles(200, start_price=300.0, slope=-0.1)
    last_val = candles[-1].value or 280.0
    for i in range(25):
        last_val -= 6.0
        candles.append(
            DataValue.medido(last_val, "api:candles", "/candles", f"2026-02-01T{i:02d}:00:00Z")
        )

    current_price = DataValue.medido(
        value=last_val - 2.0,
        source="api:quote",
        endpoint="/metrics",
        timestamp="2026-09-21T10:00:00Z"
    )

    result = analyze_trend(current_price, candles, symbol="IWM")
    assert result.rsi14.value is not None and result.rsi14.value < 30.0
    assert result.direction.value == "NEUTRO"
    assert "sobrevenda" in result.notes.lower()


def test_trend_misaligned_medias_is_neutro() -> None:
    """Médias desalinhadas classificam como NEUTRO."""
    # Preço lateral oscilante
    closes = [100.0 + (i % 5) * 2.0 for i in range(220)]
    candles = [
        DataValue.medido(c, "api:candles", "/candles", "2026-09-21T10:00:00Z")
        for c in closes
    ]
    current_price = DataValue.medido(102.0, "api:quote", "/metrics", "2026-09-21T10:00:00Z")

    result = analyze_trend(current_price, candles, symbol="MSFT")
    assert result.direction.value == "NEUTRO"


def test_insufficient_candles_yields_indisponivel() -> None:
    """Histórico menor que 200 períodos deve resultar em INDISPONIVEL."""
    candles = _generate_candles(150, start_price=100.0, slope=0.2)
    current_price = DataValue.medido(130.0, "api:quote", "/metrics", "2026-09-21T10:00:00Z")

    result = analyze_trend(current_price, candles, symbol="IPO_STOCK")
    assert result.direction.provenance == "INDISPONIVEL"
    assert result.direction.value is None
    assert result.mm200.provenance == "INDISPONIVEL"
    assert "insuficiente" in result.notes.lower()


def test_contagion_in_candle_history() -> None:
    """Se 1 candle da série histórica for INDISPONIVEL, a direção inteira vira INDISPONIVEL."""
    candles = _generate_candles(220, start_price=100.0, slope=0.2)
    # Contamina o candle 100
    candles[100] = DataValue.indisponivel("api:candles", "/candles", "2026-09-21T10:00:00Z")
    current_price = DataValue.medido(150.0, "api:quote", "/metrics", "2026-09-21T10:00:00Z")

    result = analyze_trend(current_price, candles, symbol="NVDA")
    assert result.direction.provenance == "INDISPONIVEL"
    assert result.direction.value is None
    assert "contágio" in result.notes.lower()
