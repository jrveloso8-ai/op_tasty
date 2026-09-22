"""
Módulo de Rastreamento de Posições Executadas (Trade Tracking & Management).
Responsável por:
1. Estruturação de dados de posições abertas e encerradas com proveniência estrita.
2. Cálculo conservador de liquidação (vender no Bid, recomprar no Ask).
3. Emissão determinística de sinais de gestão: MANTER, STOPAR, REALIZAR GAIN ou INDISPONIVEL.
4. Histórico de trades e métricas consolidadas para ranking de estratégias.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.pricing import OptionLeg
from src.provenance import DataValue, current_iso_timestamp

if TYPE_CHECKING:
    from src.models import MarketContext


@dataclass(frozen=True)
class ExecutedLeg:
    """Representação de uma perna executada na posição com proveniência estrita."""
    symbol: str
    strike: float
    option_type: str  # "CALL" | "PUT"
    action: str       # "BUY" | "SELL"
    ratio: int
    expiration: str
    dte_at_entry: int
    entry_price: DataValue[float]  # Preço da perna na execução
    current_bid: DataValue[float] | None = None
    current_ask: DataValue[float] | None = None
    current_mid: DataValue[float] | None = None
    quote_timestamp: str = ""
    quote_provenance: str = "MEDIDO"

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "strike": self.strike,
            "option_type": self.option_type,
            "action": self.action,
            "ratio": self.ratio,
            "expiration": self.expiration,
            "dte_at_entry": self.dte_at_entry,
            "entry_price": self.entry_price.to_dict(),
            "current_bid": self.current_bid.to_dict() if self.current_bid else None,
            "current_ask": self.current_ask.to_dict() if self.current_ask else None,
            "current_mid": self.current_mid.to_dict() if self.current_mid else None,
            "quote_timestamp": self.quote_timestamp,
            "quote_provenance": self.quote_provenance
        }


@dataclass(frozen=True)
class LiquidationEvaluation:
    """Resultado da avaliação de encerramento da posição em tempo real."""
    liquidate_price: DataValue[float]
    pnl_unit: DataValue[float]
    pnl_percent: DataValue[float]
    signal: str  # "MANTER" | "STOPAR" | "REALIZAR_GAIN" | "ALVO_PROXIMO" | "INDISPONIVEL"
    signal_reason: str
    dte_remaining: int
    time_warning: str = ""
    is_live_quote: bool = True
    quote_source: str = "live:chain"
    quote_timestamp: str = ""
    mid_price: DataValue[float] | None = None
    pnl_mid_unit: DataValue[float] | None = None
    pnl_mid_percent: DataValue[float] | None = None

    def to_dict(self) -> dict:
        return {
            "liquidate_price": self.liquidate_price.to_dict(),
            "pnl_unit": self.pnl_unit.to_dict(),
            "pnl_percent": self.pnl_percent.to_dict(),
            "mid_price": self.mid_price.to_dict() if self.mid_price else self.liquidate_price.to_dict(),
            "pnl_mid_unit": self.pnl_mid_unit.to_dict() if self.pnl_mid_unit else self.pnl_unit.to_dict(),
            "pnl_mid_percent": self.pnl_mid_percent.to_dict() if self.pnl_mid_percent else self.pnl_percent.to_dict(),
            "signal": self.signal,
            "signal_reason": self.signal_reason,
            "dte_remaining": self.dte_remaining,
            "time_warning": self.time_warning,
            "is_live_quote": self.is_live_quote,
            "quote_source": self.quote_source,
            "quote_timestamp": self.quote_timestamp
        }


STATUS_OPEN = "OPEN"
STATUS_CLOSED = "CLOSED"

_VALID_STATUS_MAP: dict[str, str] = {
    "OPEN": STATUS_OPEN,
    "ABERTA": STATUS_OPEN,
    "CLOSED": STATUS_CLOSED,
    "ENCERRADA": STATUS_CLOSED,
}


def normalize_position_status(raw_status: str) -> str:
    """
    Normaliza o status da posição para a convenção canônica ('OPEN' ou 'CLOSED').
    Aceita 'OPEN', 'ABERTA', 'CLOSED', 'ENCERRADA' (case-insensitive).
    Lança ValueError explícito se o status for inválido (sem fallback silencioso).
    """
    if not isinstance(raw_status, str):
        raise TypeError(f"Status de posição inválido (esperado str): {type(raw_status).__name__}")
    cleaned = raw_status.strip().upper()
    if cleaned not in _VALID_STATUS_MAP:
        raise ValueError(
            f"Status de posição inválido: '{raw_status}'. "
            f"Esperado 'OPEN'/'ABERTA' ou 'CLOSED'/'ENCERRADA'."
        )
    return _VALID_STATUS_MAP[cleaned]


@dataclass
class TrackedPosition:
    """Posição em acompanhamento (ativa ou encerrada)."""
    symbol: str
    strategy_id: str
    strategy_name: str
    legs: list[ExecutedLeg]
    entry_pricing_type: str  # "DEBIT" | "CREDIT"
    entry_unit_price: DataValue[float]  # Débito pago (>0) ou Crédito recebido (>0)
    quantity_lots: int = 1               # 1 lote = 100 cotas por perna
    target_gain_percent: float = 50.0   # Meta padrão de Take Profit (+50%)
    stop_loss_percent: float = 50.0     # Limite de Stop Loss
    position_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    entry_timestamp: str = field(default_factory=current_iso_timestamp)
    status: str = STATUS_OPEN            # "OPEN" | "CLOSED"
    exit_timestamp: str | None = None
    exit_unit_price: DataValue[float] | None = None
    realized_pnl: DataValue[float] | None = None
    notes: str = ""

    def to_dict(self) -> dict:
        entry_price_val = self.entry_unit_price.value if self.entry_unit_price.value is not None else 0.0
        exit_price_val = (
            self.exit_unit_price.value
            if (self.exit_unit_price and self.exit_unit_price.value is not None)
            else None
        )
        realized_val = (
            self.realized_pnl.value
            if (self.realized_pnl and self.realized_pnl.value is not None)
            else None
        )

        return {
            "id": self.position_id,
            "position_id": self.position_id,
            "symbol": self.symbol,
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "strategy_type": self.entry_pricing_type,
            "entry_date": self.entry_timestamp,
            "entry_price": entry_price_val,
            "quantity": self.quantity_lots,
            "legs": [leg.to_dict() for leg in self.legs],
            "entry_pricing_type": self.entry_pricing_type,
            "entry_unit_price": self.entry_unit_price.to_dict(),
            "quantity_lots": self.quantity_lots,
            "target_gain_percent": self.target_gain_percent,
            "stop_loss_percent": self.stop_loss_percent,
            "entry_timestamp": self.entry_timestamp,
            "status": self.status,
            "exit_timestamp": self.exit_timestamp,
            "exit_date": self.exit_timestamp,
            "exit_price": exit_price_val,
            "exit_unit_price": self.exit_unit_price.to_dict() if self.exit_unit_price else None,
            "realized_pnl": realized_val,
            "realized_pnl_dv": self.realized_pnl.to_dict() if self.realized_pnl else None,
            "notes": self.notes
        }


def evaluate_position_liquidation(
    position: TrackedPosition,
    current_quotes_by_leg: list[OptionLeg],
    spot_price: DataValue[float] | None = None,
    event_pending: bool = False
) -> LiquidationEvaluation:
    """
    Avalia a posição com rigor matemático de analista sênior de derivativos e proveniência estrita.
    
    1. Preço de Saída Conservadora (Bid/Ask Pior Caso): Métrica de atrito de liquidez e slippage a mercado.
    2. Preço Mark Corretora (Mid-price): Balizador econômico e decisório para metas de ganho e limites de perda.
    3. Gestão por Família de Estratégia, Moneyness e DTE:
       - Travas de Débito (Bull Call / Bear Put): Não stopa prematuramente em DTE > 14 se o ativo estiver
         na faixa ou favorável ao strike comprado (evita o clássico erro de stopar no bid por ruído de spread).
       - Estruturas de Crédito (Iron Condor / Ratios): Monitoramento estrito de gama com alerta aos 21 DTE.
       - Compra de Volatilidade (Long Strangle): Stop temporal aos 14 DTE para evitar o precipício de teta.
       - Calendars e Diagonais: Alvo em 25-35% e controle de vencimento da perna curta.
    """
    ts = current_iso_timestamp()
    endpoint = f"/positions/{position.position_id}/evaluate"

    # Encontra o menor DTE entre as pernas
    min_dte = min((leg.dte for leg in current_quotes_by_leg), default=0) if current_quotes_by_leg else 0

    if len(current_quotes_by_leg) != len(position.legs):
        dv_indisp: DataValue[float] = DataValue.indisponivel(
            source="calc:liquidation",
            endpoint=endpoint,
            timestamp=ts
        )
        return LiquidationEvaluation(
            liquidate_price=dv_indisp,
            pnl_unit=dv_indisp,
            pnl_percent=dv_indisp,
            signal="INDISPONIVEL",
            signal_reason="Incompatibilidade de pernas entre posição e cotações atuais fornecidas.",
            dte_remaining=min_dte,
            time_warning="",
            mid_price=dv_indisp,
            pnl_mid_unit=dv_indisp,
            pnl_mid_percent=dv_indisp
        )

    # Aplica a regra de contágio sobre todas as cotações de fechamento
    collected_dvs: list[DataValue] = [position.entry_unit_price]
    matched_pos_indices: list[int | None] = []
    used_indices: set[int] = set()

    for q_leg in current_quotes_by_leg:
        # Tenta match exato incluindo vencimento (crucial para Calendar/Diagonal com strikes idênticos)
        m_idx = next(
            (
                idx for idx, pl in enumerate(position.legs)
                if idx not in used_indices
                and abs(pl.strike - q_leg.strike) < 0.001
                and pl.option_type == q_leg.option_type
                and pl.expiration == q_leg.expiration
            ),
            None
        )
        if m_idx is None:
            # Fallback para strike e tipo
            m_idx = next(
                (
                    idx for idx, pl in enumerate(position.legs)
                    if idx not in used_indices
                    and abs(pl.strike - q_leg.strike) < 0.001
                    and pl.option_type == q_leg.option_type
                ),
                None
            )

        matched_pos_indices.append(m_idx)
        if m_idx is not None:
            used_indices.add(m_idx)
            matching_pos_leg = position.legs[m_idx]
            if matching_pos_leg.action == "BUY":
                collected_dvs.append(q_leg.bid)
            else:
                collected_dvs.append(q_leg.ask)
        else:
            collected_dvs.append(DataValue.indisponivel("calc:liquidation", endpoint, ts))

    if any(not dv.is_available for dv in collected_dvs) or len(used_indices) != len(position.legs):
        dv_contagio: DataValue[float] = DataValue.indisponivel(
            source="calc:liquidation[CONTAGIO_INDISPONIVEL]",
            endpoint=endpoint,
            timestamp=ts
        )
        return LiquidationEvaluation(
            liquidate_price=dv_contagio,
            pnl_unit=dv_contagio,
            pnl_percent=dv_contagio,
            signal="INDISPONIVEL",
            signal_reason="Cotação de uma ou mais pernas indisponível ou pernas não correspondidas (contágio de proveniência ativado).",
            dte_remaining=min_dte,
            time_warning="",
            mid_price=dv_contagio,
            pnl_mid_unit=dv_contagio,
            pnl_mid_percent=dv_contagio
        )

    # 1. Cálculo da liquidação conservadora (Venda no Bid, Recompra no Ask)
    # 2. Cálculo do Mark / Mid (Preço Justo da Corretora)
    net_liquidation = 0.0
    mid_liquidation = 0.0
    for q_leg, m_idx in zip(current_quotes_by_leg, matched_pos_indices, strict=False):
        assert m_idx is not None
        matching_pos_leg = position.legs[m_idx]
        assert q_leg.bid.value is not None
        assert q_leg.ask.value is not None
        leg_mid = round((q_leg.bid.value + q_leg.ask.value) / 2.0, 4)

        if matching_pos_leg.action == "BUY":
            net_liquidation += (q_leg.bid.value * matching_pos_leg.ratio)
            mid_liquidation += (leg_mid * matching_pos_leg.ratio)
        else:
            net_liquidation -= (q_leg.ask.value * matching_pos_leg.ratio)
            mid_liquidation -= (leg_mid * matching_pos_leg.ratio)

    net_liquidation = round(net_liquidation, 2)
    mid_liquidation = round(mid_liquidation, 2)

    dv_liquidate = DataValue.derivado(
        value=net_liquidation,
        source="calc:net_liquidation",
        endpoint=endpoint,
        timestamp=ts
    )
    dv_mid = DataValue.derivado(
        value=mid_liquidation,
        source="calc:mid_liquidation",
        endpoint=endpoint,
        timestamp=ts
    )

    assert position.entry_unit_price.value is not None
    entry_price = position.entry_unit_price.value

    if position.entry_pricing_type == "DEBIT":
        pnl_val = round(net_liquidation - entry_price, 2)
        pnl_pct = round((pnl_val / entry_price) * 100.0, 1) if entry_price > 0 else 0.0
        pnl_mid_val = round(mid_liquidation - entry_price, 2)
        pnl_mid_pct = round((pnl_mid_val / entry_price) * 100.0, 1) if entry_price > 0 else 0.0
    else:
        # Crédito inicial positivo; saídas representam custo de recompra
        pnl_val = round(entry_price + net_liquidation, 2)
        pnl_pct = round((pnl_val / entry_price) * 100.0, 1) if entry_price > 0 else 0.0
        pnl_mid_val = round(entry_price + mid_liquidation, 2)
        pnl_mid_pct = round((pnl_mid_val / entry_price) * 100.0, 1) if entry_price > 0 else 0.0

    dv_pnl = DataValue.derivado(value=pnl_val, source="calc:pnl_conservative", endpoint=endpoint, timestamp=ts)
    dv_pnl_pct = DataValue.derivado(value=pnl_pct, source="calc:pnl_conservative_percent", endpoint=endpoint, timestamp=ts)
    dv_pnl_mid = DataValue.derivado(value=pnl_mid_val, source="calc:pnl_mid", endpoint=endpoint, timestamp=ts)
    dv_pnl_mid_pct = DataValue.derivado(value=pnl_mid_pct, source="calc:pnl_mid_percent", endpoint=endpoint, timestamp=ts)

    # Avaliação Especializada por Família de Estratégia
    signal = "MANTER"
    signal_reason = ""
    time_warning = ""

    # 1. TRAVAS VERTICAIS DE DÉBITO (Bull Call Spread, Bear Put Spread)
    if position.strategy_id in ("bull_call_spread", "bear_put_spread"):
        long_leg = next((l for l in position.legs if l.action == "BUY"), None)

        spot_val = spot_price.value if (spot_price and spot_price.is_available) else None
        is_favorable_spot = False
        spot_desc = ""

        if spot_val is not None and long_leg is not None:
            if position.strategy_id == "bull_call_spread":
                is_favorable_spot = (spot_val >= long_leg.strike * 0.99)
                if spot_val >= long_leg.strike:
                    spot_desc = f"Spot ${spot_val:.2f} ITM acima do strike comprado ${long_leg.strike:.2f}."
                else:
                    spot_desc = f"Spot ${spot_val:.2f} próximo ao strike comprado ${long_leg.strike:.2f}."
            else: # bear_put_spread
                is_favorable_spot = (spot_val <= long_leg.strike * 1.01)
                if spot_val <= long_leg.strike:
                    spot_desc = f"Spot ${spot_val:.2f} ITM abaixo do strike comprado ${long_leg.strike:.2f}."
                else:
                    spot_desc = f"Spot ${spot_val:.2f} próximo ao strike comprado ${long_leg.strike:.2f}."

        if pnl_mid_pct >= position.target_gain_percent:
            signal = "REALIZAR_GAIN"
            signal_reason = f"Meta de lucro atingida no Mark (+{pnl_mid_pct:.1f}% >= +{position.target_gain_percent:.1f}%)."
        elif pnl_mid_pct >= position.target_gain_percent * 0.85:
            signal = "ALVO_PROXIMO"
            signal_reason = f"Próximo ao alvo de lucro (+{pnl_mid_pct:.1f}% de +{position.target_gain_percent:.1f}%). {spot_desc}"
        elif min_dte > 14:
            signal = "MANTER"
            if is_favorable_spot:
                signal_reason = f"Maturação saudável aos {min_dte}d DTE ({pnl_mid_pct:+.1f}% Mark). {spot_desc} Aguardar decaimento do valor extrínseco da perna vendida."
            else:
                signal_reason = f"Em maturação aos {min_dte}d DTE ({pnl_mid_pct:+.1f}% Mark). Tese técnica em andamento; risco limitado ao débito pago."
        else:
            time_warning = f"Alerta DTE={min_dte}d (<=14d): Aceleração do decaimento teta contra a posição."
            if pnl_mid_pct <= -position.stop_loss_percent and not is_favorable_spot:
                signal = "STOPAR"
                signal_reason = f"Encerramento defensivo: DTE avançado ({min_dte}d <= 14d) com ativo fora do dinheiro ({pnl_mid_pct:.1f}% <= -{position.stop_loss_percent:.1f}%)."
            else:
                signal = "MANTER"
                signal_reason = f"Reta final ({min_dte}d DTE) com P&L Mark em {pnl_mid_pct:+.1f}%. {spot_desc}"

    # 2. ESTRATÉGIAS A CRÉDITO (Iron Condor, Put Ratio, Spreads de Crédito)
    elif position.entry_pricing_type == "CREDIT" or position.strategy_id in ("iron_condor", "put_ratio_spread"):
        if min_dte <= 21:
            time_warning = f"Alerta DTE={min_dte}d (<=21d): Risco gama terminal. Considere encerrar ou rolar no Mark."

        credit_target = position.target_gain_percent
        target_note = ""
        if position.strategy_id == "iron_condor":
            call_strikes = sorted([l.strike for l in position.legs if l.option_type == "CALL"])
            put_strikes = sorted([l.strike for l in position.legs if l.option_type == "PUT"])
            call_wing = (call_strikes[1] - call_strikes[0]) if len(call_strikes) >= 2 else 0.0
            put_wing = (put_strikes[1] - put_strikes[0]) if len(put_strikes) >= 2 else 0.0
            wing_w = max(call_wing, put_wing)
            if 0.0 < wing_w <= 5.0:
                credit_target = min(position.target_gain_percent, 30.0)
                target_note = f" (Alvo calibrado pela largura de asa estreita ${wing_w:.1f} = {credit_target:.0f}%)"

        if pnl_mid_pct >= credit_target:
            signal = "REALIZAR_GAIN"
            signal_reason = f"Meta de crédito atingida (+{pnl_mid_pct:.1f}% >= +{credit_target:.1f}%){target_note}."
        elif pnl_mid_pct <= -position.stop_loss_percent:
            signal = "STOPAR"
            signal_reason = f"Limite de perda atingido ({pnl_mid_pct:.1f}% <= -{position.stop_loss_percent:.1f}%)."
        elif min_dte <= 21:
            signal = "MANTER"
            signal_reason = f"Operação a crédito em zona de defesa temporal ({min_dte}d DTE). {time_warning}"
        else:
            signal = "MANTER"
            signal_reason = f"Operação a crédito maturando com teta positivo ({pnl_mid_pct:+.1f}% Mark)."

    # 3. COMPRA DE VOLATILIDADE (Long Strangle, Call Backspread)
    elif position.strategy_id in ("long_strangle", "call_backspread"):
        if pnl_mid_pct >= position.target_gain_percent:
            signal = "REALIZAR_GAIN"
            signal_reason = f"Meta de expansão de volatilidade atingida (+{pnl_mid_pct:.1f}% >= +{position.target_gain_percent:.1f}%)."
        elif min_dte <= 14:
            if event_pending:
                time_warning = f"Alerta DTE={min_dte}d (<=14d): Evento catalisador pendente no horizonte. Manter estrutura até a realização do evento antes de aplicar stop temporal."
                signal = "MANTER"
                signal_reason = f"Aguardando realização do catalisador/evento no horizonte antes do stop temporal ({pnl_mid_pct:+.1f}% Mark, {min_dte}d DTE)."
            else:
                time_warning = f"Alerta DTE={min_dte}d (<=14d): Precipício de decaimento teta em opções compradas."
                signal = "STOPAR"
                signal_reason = f"Stop temporal por esgotamento de DTE ({min_dte}d <= 14d) para evitar precipício de decaimento teta."
        elif pnl_mid_pct <= -position.stop_loss_percent:
            signal = "STOPAR"
            signal_reason = f"Limite de perda atingido ({pnl_mid_pct:.1f}% <= -{position.stop_loss_percent:.1f}%)."
        else:
            signal = "MANTER"
            signal_reason = f"Aguardando expansão de volatilidade ({pnl_mid_pct:+.1f}% Mark, {min_dte}d DTE)."

    # 4. ESTRUTURAS TEMPORAIS E HÍBRIDAS (Calendar Spread, Diagonal Spread)
    elif position.strategy_id in ("calendar_spread", "diagonal_spread"):
        cal_target = position.target_gain_percent
        if pnl_mid_pct >= cal_target:
            signal = "REALIZAR_GAIN"
            signal_reason = f"Meta de calendar/diagonal atingida (+{pnl_mid_pct:.1f}% >= +{cal_target:.1f}%)."
        elif min_dte <= 3:
            signal = "STOPAR"
            signal_reason = f"Perna curta expirando em {min_dte}d. Encerrar para evitar risco de atribuição."
        elif pnl_mid_pct <= -position.stop_loss_percent:
            signal = "STOPAR"
            signal_reason = f"Limite de perda atingido ({pnl_mid_pct:.1f}% <= -{position.stop_loss_percent:.1f}%)."
        else:
            signal = "MANTER"
            signal_reason = f"Spread temporal maturando via decaimento da perna curta ({pnl_mid_pct:+.1f}% Mark, {min_dte}d DTE)."

    # 5. DEFAULT / OUTROS
    else:
        if pnl_mid_pct >= position.target_gain_percent:
            signal = "REALIZAR_GAIN"
            signal_reason = f"Meta de ganho atingida (+{pnl_mid_pct:.1f}% >= +{position.target_gain_percent:.1f}%)."
        elif pnl_mid_pct <= -position.stop_loss_percent:
            signal = "STOPAR"
            signal_reason = f"Limite de perda atingido ({pnl_mid_pct:.1f}% <= -{position.stop_loss_percent:.1f}%)."
        else:
            signal = "MANTER"
            signal_reason = f"Operação dentro da faixa de maturação ({pnl_mid_pct:+.1f}% Mark)."

    # Detecção de proveniência das cotações recebidas (Live Chain vs Snapshot Manual)
    is_live = all(
        (q.bid.source != "snapshot:manual" and q.ask.source != "snapshot:manual")
        for q in current_quotes_by_leg
    )
    quote_src = "live:chain" if is_live else "snapshot:manual"
    quote_ts = current_quotes_by_leg[0].bid.timestamp if current_quotes_by_leg else ts

    if not is_live:
        signal_reason = f"{signal_reason} [⚠️ COTAÇÃO DE SNAPSHOT MANUAL — Requer cotação fresca da corretora para confirmação]".strip()

    return LiquidationEvaluation(
        liquidate_price=dv_liquidate,
        pnl_unit=dv_pnl,
        pnl_percent=dv_pnl_pct,
        signal=signal,
        signal_reason=signal_reason,
        dte_remaining=min_dte,
        time_warning=time_warning,
        is_live_quote=is_live,
        quote_source=quote_src,
        quote_timestamp=quote_ts,
        mid_price=dv_mid,
        pnl_mid_unit=dv_pnl_mid,
        pnl_mid_percent=dv_pnl_mid_pct
    )


def close_position(
    position: TrackedPosition,
    exit_unit_price: float,
    notes: str = ""
) -> TrackedPosition:
    """Encerra uma posição com registro formal de proveniência e cálculo de P&L realizado."""
    ts = current_iso_timestamp()
    endpoint = f"/positions/{position.position_id}/close"

    dv_exit = DataValue.medido(
        value=round(exit_unit_price, 2),
        source="user:order_execution",
        endpoint=endpoint,
        timestamp=ts
    )

    assert position.entry_unit_price.value is not None
    entry_p = position.entry_unit_price.value

    if position.entry_pricing_type == "DEBIT":
        realized = round((exit_unit_price - entry_p) * 100 * position.quantity_lots, 2)
    else:
        # Crédito inicial x custo de recompra
        realized = round((entry_p - exit_unit_price) * 100 * position.quantity_lots, 2)

    dv_realized = DataValue.derivado(
        value=realized,
        source="calc:realized_pnl",
        endpoint=endpoint,
        timestamp=ts
    )

    position.status = STATUS_CLOSED
    position.exit_timestamp = ts
    position.exit_unit_price = dv_exit
    position.realized_pnl = dv_realized
    if notes:
        position.notes = notes

    return position


def calculate_strategy_ranking(positions: list[TrackedPosition]) -> list[dict]:
    """Calcula o ranking consolidado de estratégias por P&L total e taxa de acerto."""
    closed = [
        p for p in positions
        if normalize_position_status(p.status) == STATUS_CLOSED
        and p.realized_pnl and p.realized_pnl.value is not None
    ]
    by_strat: dict[str, list[TrackedPosition]] = {}

    for p in closed:
        by_strat.setdefault(p.strategy_name, []).append(p)

    ranking: list[dict[str, Any]] = []
    for strat_name, trades in by_strat.items():
        total_pnl = sum(t.realized_pnl.value for t in trades if t.realized_pnl and t.realized_pnl.value is not None)  # type: ignore[union-attr]
        wins = [t for t in trades if t.realized_pnl and t.realized_pnl.value is not None and t.realized_pnl.value > 0]
        losses = [t for t in trades if t.realized_pnl and t.realized_pnl.value is not None and t.realized_pnl.value < 0]
        total_trades = len(trades)
        win_rate = round((len(wins) / total_trades) * 100.0, 1) if total_trades > 0 else 0.0

        ranking.append({
            "strategy_name": strat_name,
            "total_trades": total_trades,
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": win_rate,
            "total_pnl": round(total_pnl, 2)
        })

    ranking.sort(key=lambda r: float(str(r["total_pnl"])), reverse=True)
    return ranking


def load_tracked_positions_from_json(file_path: Path) -> list[TrackedPosition]:
    """Carrega posições salvas do arquivo JSON com validação estrita de proveniência."""
    if not file_path.exists():
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    positions: list[TrackedPosition] = []
    for item in data:
        entry_ts = item.get("entry_date", current_iso_timestamp())
        pos_id = item.get("id") or item.get("position_id") or str(uuid.uuid4())[:8]
        norm_status = normalize_position_status(item.get("status", STATUS_OPEN))
        exit_ts = item.get("exit_date") or item.get("exit_timestamp")

        legs: list[ExecutedLeg] = []
        for l_data in item.get("legs", []):
            leg_ts = l_data.get("quote_timestamp", entry_ts)
            leg_prov = l_data.get("quote_provenance", "SNAPSHOT_MANUAL")
            source_label = "snapshot:manual" if leg_prov == "SNAPSHOT_MANUAL" else "live:chain"

            bid_val = l_data.get("current_bid")
            ask_val = l_data.get("current_ask")
            mid_val = l_data.get("current_mid")

            c_bid = (
                DataValue.medido(float(bid_val), source_label, f"/positions/{pos_id}/leg", leg_ts)
                if bid_val is not None
                else DataValue.indisponivel(source_label, f"/positions/{pos_id}/leg", leg_ts)
            )
            c_ask = (
                DataValue.medido(float(ask_val), source_label, f"/positions/{pos_id}/leg", leg_ts)
                if ask_val is not None
                else DataValue.indisponivel(source_label, f"/positions/{pos_id}/leg", leg_ts)
            )
            c_mid = (
                DataValue.derivado(float(mid_val), "calc:mid", f"/positions/{pos_id}/leg", leg_ts)
                if mid_val is not None
                else DataValue.indisponivel("calc:mid", f"/positions/{pos_id}/leg", leg_ts)
            )

            legs.append(
                ExecutedLeg(
                    symbol=l_data["symbol"],
                    strike=float(l_data["strike"]),
                    option_type=l_data["option_type"],
                    action=l_data["action"],
                    ratio=int(l_data.get("ratio", 1)),
                    expiration=l_data["expiration"],
                    dte_at_entry=int(l_data.get("dte", 30)),
                    entry_price=DataValue.medido(
                        float(item["entry_price"]), "user:execution_order", f"/positions/{pos_id}", entry_ts
                    ),
                    current_bid=c_bid,
                    current_ask=c_ask,
                    current_mid=c_mid,
                    quote_timestamp=leg_ts,
                    quote_provenance=leg_prov
                )
            )

        # Desserialização de exit_unit_price se presente
        exit_price_raw = item.get("exit_price")
        if exit_price_raw is None and item.get("exit_unit_price") is not None:
            eup = item["exit_unit_price"]
            exit_price_raw = eup.get("value") if isinstance(eup, dict) else eup

        exit_dv: DataValue[float] | None = None
        if exit_price_raw is not None:
            exit_dv = DataValue.medido(
                float(exit_price_raw),
                "user:execution_order",
                f"/positions/{pos_id}/exit",
                exit_ts or entry_ts
            )

        # Desserialização de realized_pnl se presente
        realized_raw = item.get("realized_pnl")
        if isinstance(realized_raw, dict):
            realized_raw = realized_raw.get("value")

        realized_dv: DataValue[float] | None = None
        if realized_raw is not None:
            realized_dv = DataValue.derivado(
                float(realized_raw),
                "calc:realized_pnl",
                f"/positions/{pos_id}/realized",
                exit_ts or entry_ts
            )
        elif norm_status == STATUS_CLOSED and exit_dv is not None and exit_dv.value is not None:
            entry_p = float(item["entry_price"])
            qty = int(item.get("quantity", item.get("quantity_lots", 1)))
            strat_type = item.get("strategy_type") or item.get("entry_pricing_type", "DEBIT")
            if strat_type == "DEBIT":
                calc_realized = round((exit_dv.value - entry_p) * 100 * qty, 2)
            else:
                calc_realized = round((entry_p - exit_dv.value) * 100 * qty, 2)
            realized_dv = DataValue.derivado(
                calc_realized,
                "calc:realized_pnl",
                f"/positions/{pos_id}/realized",
                exit_ts or entry_ts
            )

        pos = TrackedPosition(
            symbol=item["symbol"],
            strategy_id=item["strategy_id"],
            strategy_name=item["strategy_name"],
            legs=legs,
            entry_pricing_type=item.get("strategy_type") or item.get("entry_pricing_type", "DEBIT"),
            entry_unit_price=DataValue.medido(
                float(item["entry_price"]), "user:execution_order", f"/positions/{pos_id}", entry_ts
            ),
            quantity_lots=int(item.get("quantity", item.get("quantity_lots", 1))),
            target_gain_percent=float(item.get("target_gain_percent", 50.0)),
            stop_loss_percent=float(item.get("stop_loss_percent", 50.0)),
            position_id=pos_id,
            entry_timestamp=entry_ts,
            status=norm_status,
            exit_timestamp=exit_ts,
            exit_unit_price=exit_dv,
            realized_pnl=realized_dv,
            notes=item.get("notes", "")
        )
        positions.append(pos)
    return positions


def evaluate_tracked_positions_against_market(
    positions: list[TrackedPosition],
    contexts_by_symbol: dict[str, MarketContext]
) -> list[dict[str, Any]]:
    """
    Avalia cada posição rastreada buscando cotação ao vivo nas cadeias de opções do MarketContext.
    Se a posição estiver ENCERRADA/CLOSED, não realiza avaliação ao vivo nem cotação de mercado,
    preservando o estado estático com sinal "ENCERRADA".
    Se a cotação ao vivo não existir (ex: strike fora da faixa ou ticker sem cadeia ao vivo),
    faz fallback estrito para a cotação do snapshot com identificação transparente de proveniência.
    """
    results: list[dict[str, Any]] = []

    for pos in positions:
        norm_status = normalize_position_status(pos.status)
        if norm_status == STATUS_CLOSED:
            pos_dict = pos.to_dict()
            pos_dict["evaluation"] = {
                "liquidate_price": pos.exit_unit_price.to_dict() if pos.exit_unit_price else None,
                "pnl_unit": None,
                "pnl_percent": None,
                "mid_price": pos.exit_unit_price.to_dict() if pos.exit_unit_price else None,
                "pnl_mid_unit": None,
                "pnl_mid_percent": None,
                "signal": "ENCERRADA",
                "signal_reason": "Posição encerrada. Cotação a mercado e sinais de gestão desativados.",
                "dte_remaining": 0,
                "time_warning": "",
                "is_live_quote": False,
                "quote_source": "closed:static",
                "quote_timestamp": pos.exit_timestamp or "",
            }
            results.append(pos_dict)
            continue

        ctx = contexts_by_symbol.get(pos.symbol)
        quote_legs: list[OptionLeg] = []
        updated_legs: list[ExecutedLeg] = []

        for leg in pos.legs:
            found_live_leg: OptionLeg | None = None
            if ctx and leg.expiration in ctx.chains_by_expiration:
                chain = ctx.chains_by_expiration[leg.expiration]
                found_live_leg = next(
                    (
                        item for item in chain
                        if abs(item.strike - leg.strike) < 0.001 and item.option_type == leg.option_type
                    ),
                    None
                )

            if found_live_leg is not None and found_live_leg.bid.is_available and found_live_leg.ask.is_available:
                # Cotação fresca da cadeia ao vivo
                quote_legs.append(found_live_leg)
                q_ts = found_live_leg.bid.timestamp or current_iso_timestamp()
                mid_val = (
                    round((found_live_leg.bid.value + found_live_leg.ask.value) / 2.0, 4)
                    if (found_live_leg.bid.value is not None and found_live_leg.ask.value is not None)
                    else None
                )
                mid_dv = (
                    DataValue.derivado(mid_val, "calc:mid", f"/positions/{pos.position_id}/leg", q_ts)
                    if mid_val is not None
                    else leg.current_mid
                )
                updated_leg = replace(
                    leg,
                    current_bid=found_live_leg.bid,
                    current_ask=found_live_leg.ask,
                    current_mid=mid_dv,
                    quote_timestamp=q_ts,
                    quote_provenance="MEDIDO"
                )
                updated_legs.append(updated_leg)
            elif leg.current_bid and leg.current_bid.is_available and leg.current_ask and leg.current_ask.is_available:
                # Fallback para a cotação estática de snapshot manual
                assert leg.current_bid.value is not None
                assert leg.current_ask.value is not None
                fallback_leg = OptionLeg(
                    symbol=leg.symbol,
                    strike=leg.strike,
                    option_type=leg.option_type,  # type: ignore[arg-type]
                    action=leg.action,  # type: ignore[arg-type]
                    ratio=leg.ratio,
                    bid=leg.current_bid,
                    ask=leg.current_ask,
                    expiration=leg.expiration,
                    dte=leg.dte_at_entry,
                    delta=DataValue.indisponivel("snapshot:manual", f"/chains/{leg.symbol}", leg.quote_timestamp)
                )
                quote_legs.append(fallback_leg)
                updated_legs.append(leg)
            else:
                updated_legs.append(leg)

        has_event = bool(ctx.event_in_horizon.value) if (ctx and ctx.event_in_horizon and ctx.event_in_horizon.is_available) else False
        evaluation = evaluate_position_liquidation(
            pos,
            quote_legs,
            spot_price=ctx.spot_price if (ctx and ctx.spot_price) else None,
            event_pending=has_event
        )
        pos.legs = updated_legs
        pos_dict = pos.to_dict()
        if ctx and ctx.spot_price and ctx.spot_price.is_available:
            pos_dict["current_spot"] = ctx.spot_price.to_dict()
        pos_dict["evaluation"] = evaluation.to_dict()
        results.append(pos_dict)

    return results

