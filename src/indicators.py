"""
Módulo de Indicadores Técnicos e Filtro de Direção — Screener Tastytrade.
Calcula MM20, MM50, MM200 e RSI(14) sobre fechamentos reais (OHLC).
Implementa a classificação estrita:
  ALTA   = preço > MM20 > MM50 > MM200 (descartado se RSI > 70 -> NEUTRO)
  BAIXA  = preço < MM20 < MM50 < MM200 (descartado se RSI < 30 -> NEUTRO)
  NEUTRO = desalinhamento de médias ou RSI em zona extrema
Se menos de 200 candles disponíveis ou se houver dado incompleto: DADO INDISPONIVEL.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from src.provenance import DataValue, current_iso_timestamp

DirectionType = Literal["ALTA", "BAIXA", "NEUTRO"]


@dataclass(frozen=True)
class TrendAnalysis:
    """Resultado auditável da análise de tendência e indicadores."""
    direction: DataValue[DirectionType]
    current_price: DataValue[float]
    mm20: DataValue[float]
    mm50: DataValue[float]
    mm200: DataValue[float]
    rsi14: DataValue[float]
    notes: str


def calculate_sma(closes: Sequence[float], period: int) -> float:
    """Calcula a média móvel simples dos últimos N períodos."""
    if len(closes) < period:
        raise ValueError(f"Histórico insuficiente para SMA({period}): {len(closes)} candles fornecidos.")
    window = closes[-period:]
    return sum(window) / period


def calculate_rsi(closes: Sequence[float], period: int = 14) -> float:
    """
    Calcula o RSI (Relative Strength Index) de Wilder de 14 períodos.
    Fórmula canônica:
      gains / losses iniciais = média simples de 14 dias
      suavização de Wilder: avg_gain = (prev_gain * 13 + current_gain) / 14
      RS = avg_gain / avg_loss
      RSI = 100 - (100 / (1 + RS))
    """
    if len(closes) < period + 1:
        raise ValueError(f"Histórico insuficiente para RSI({period}): {len(closes)} candles fornecidos.")

    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

    # Médias iniciais dos primeiros 14 períodos
    gains = [d if d > 0 else 0.0 for d in deltas[:period]]
    losses = [-d if d < 0 else 0.0 for d in deltas[:period]]

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    # Suavização de Wilder para o restante do histórico
    for delta in deltas[period:]:
        current_gain = delta if delta > 0 else 0.0
        current_loss = -delta if delta < 0 else 0.0
        avg_gain = (avg_gain * (period - 1) + current_gain) / period
        avg_loss = (avg_loss * (period - 1) + current_loss) / period

    if avg_loss == 0.0:
        return 100.0 if avg_gain > 0.0 else 50.0

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return round(rsi, 4)


def analyze_trend(
    current_price: DataValue[float],
    daily_closes: Sequence[DataValue[float]],
    symbol: str = "ASSET"
) -> TrendAnalysis:
    """
    Avalia a direção do ativo com a regra inegociável de proveniência.
    Exige no mínimo 200 candles diários válidos e sem dados parciais.
    Se histórico < 200 ou qualquer candle for INDISPONIVEL, classifica como INDISPONIVEL.
    """
    endpoint_base = f"/market-data/candles/{symbol}"
    now_ts = current_iso_timestamp()

    # 1. Validação de contágio e disponibilidade do preço spot
    if not current_price.is_available or current_price.value is None:
        return TrendAnalysis(
            direction=DataValue.indisponivel("calc:trend", endpoint_base, now_ts),
            current_price=current_price,
            mm20=DataValue.indisponivel("calc:mm20", endpoint_base, now_ts),
            mm50=DataValue.indisponivel("calc:mm50", endpoint_base, now_ts),
            mm200=DataValue.indisponivel("calc:mm200", endpoint_base, now_ts),
            rsi14=DataValue.indisponivel("calc:rsi14", endpoint_base, now_ts),
            notes="Preço atual indisponível"
        )

    # 2. Verificação de volume e consistência de candles (mínimo 200 períodos)
    if len(daily_closes) < 200:
        return TrendAnalysis(
            direction=DataValue.indisponivel("calc:trend", endpoint_base, now_ts),
            current_price=current_price,
            mm20=DataValue.indisponivel("calc:mm20", endpoint_base, now_ts),
            mm50=DataValue.indisponivel("calc:mm50", endpoint_base, now_ts),
            mm200=DataValue.indisponivel("calc:mm200", endpoint_base, now_ts),
            rsi14=DataValue.indisponivel("calc:rsi14", endpoint_base, now_ts),
            notes=f"Histórico insuficiente para MM200 ({len(daily_closes)}/200 candles retornados)"
        )

    # 3. Verificação de contágio na série temporal de candles
    infected_candles = [c for c in daily_closes if not c.is_available or c.value is None]
    if infected_candles:
        return TrendAnalysis(
            direction=DataValue.indisponivel("calc:trend[CONTAGIO_CANDLES]", endpoint_base, now_ts),
            current_price=current_price,
            mm20=DataValue.indisponivel("calc:mm20", endpoint_base, now_ts),
            mm50=DataValue.indisponivel("calc:mm50", endpoint_base, now_ts),
            mm200=DataValue.indisponivel("calc:mm200", endpoint_base, now_ts),
            rsi14=DataValue.indisponivel("calc:rsi14", endpoint_base, now_ts),
            notes=f"Contágio: {len(infected_candles)} candles continham dados incompletos/nulos"
        )

    # 4. Extração dos valores numéricos brutos
    raw_closes: list[float] = [c.value for c in daily_closes if c.value is not None]
    latest_candle_ts = max((c.timestamp for c in daily_closes), default=now_ts)

    # 5. Cálculo auditável dos indicadores
    sma20_val = round(calculate_sma(raw_closes, 20), 4)
    sma50_val = round(calculate_sma(raw_closes, 50), 4)
    sma200_val = round(calculate_sma(raw_closes, 200), 4)
    rsi14_val = calculate_rsi(raw_closes, 14)

    dv_mm20 = DataValue.derivado(sma20_val, "calc:sma20", endpoint_base, latest_candle_ts)
    dv_mm50 = DataValue.derivado(sma50_val, "calc:sma50", endpoint_base, latest_candle_ts)
    dv_mm200 = DataValue.derivado(sma200_val, "calc:sma200", endpoint_base, latest_candle_ts)
    dv_rsi14 = DataValue.derivado(rsi14_val, "calc:rsi14", endpoint_base, latest_candle_ts)

    price = current_price.value

    # 6. Avaliação da regra de direção com filtro de confirmação RSI
    direction: DirectionType = "NEUTRO"
    notes = "Médias desalinhadas"

    is_bullish_alignment = price > sma20_val > sma50_val > sma200_val
    is_bearish_alignment = price < sma20_val < sma50_val < sma200_val

    if is_bullish_alignment:
        if rsi14_val > 70.0:
            direction = "NEUTRO"
            notes = f"Alinhamento de alta detectado (P>{sma20_val}>{sma50_val}>{sma200_val}), mas descartado por sobrecompra RSI={rsi14_val} > 70"
        else:
            direction = "ALTA"
            notes = f"Tendência de ALTA confirmada (P>{sma20_val}>{sma50_val}>{sma200_val}) e RSI={rsi14_val} na faixa neutra"
    elif is_bearish_alignment:
        if rsi14_val < 30.0:
            direction = "NEUTRO"
            notes = f"Alinhamento de baixa detectado (P<{sma20_val}<{sma50_val}<{sma200_val}), mas descartado por sobrevenda RSI={rsi14_val} < 30"
        else:
            direction = "BAIXA"
            notes = f"Tendência de BAIXA confirmada (P<{sma20_val}<{sma50_val}<{sma200_val}) e RSI={rsi14_val} na faixa neutra"
    else:
        direction = "NEUTRO"
        notes = f"Configuração neutra/desalinhada: Preço={price}, MM20={sma20_val}, MM50={sma50_val}, MM200={sma200_val}"

    dv_direction = DataValue.derivado(direction, "calc:trend_decision", endpoint_base, latest_candle_ts)

    return TrendAnalysis(
        direction=dv_direction,
        current_price=current_price,
        mm20=dv_mm20,
        mm50=dv_mm50,
        mm200=dv_mm200,
        rsi14=dv_rsi14,
        notes=notes
    )
