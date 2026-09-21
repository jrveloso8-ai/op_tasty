"""
Módulo de Precificação Conservadora de Estruturas de Opções — Screener Tastytrade.
Implementa a regra estrita da Seção 5.1:
  - Perna COMPRADA -> usa ASK (preço de compra realista, nunca mid)
  - Perna VENDIDA   -> usa BID (preço de venda realista, nunca mid)
  - Resultado < 0   -> "CUSTO MÁXIMO A PAGAR" (valor absoluto)
  - Resultado > 0   -> "VALOR MÍNIMO A RECEBER"
  - Se bid ou ask de qualquer perna for nulo/ausente/zerado:
    DADO INDISPONIVEL integral (nunca usa mid como fallback).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Literal, Optional, Sequence
from src.provenance import DataValue, current_iso_timestamp

LegAction = Literal["BUY", "SELL"]
OptionType = Literal["CALL", "PUT"]
PricingType = Literal["DEBIT", "CREDIT", "INDISPONIVEL"]
PricingLabel = Literal["CUSTO MÁXIMO A PAGAR", "VALOR MÍNIMO A RECEBER", "DADO INDISPONIVEL"]


@dataclass(frozen=True)
class OptionLeg:
    """Representação de uma perna individual de estrutura de opções com proveniência."""
    symbol: str
    strike: float
    option_type: OptionType
    action: LegAction
    ratio: int  # 1 para normal, 2 para venda dobrada em ratio spreads, etc.
    bid: DataValue[float]
    ask: DataValue[float]
    expiration: str
    dte: int
    delta: DataValue[float]
    gamma: Optional[DataValue[float]] = None
    theta: Optional[DataValue[float]] = None
    open_interest: Optional[DataValue[int]] = None
    volume: Optional[DataValue[int]] = None
    iv: Optional[DataValue[float]] = None


@dataclass(frozen=True)
class StructurePricing:
    """Resultado auditável da precificação conservadora da estrutura."""
    net_cash_flow: DataValue[float]
    display_value: DataValue[float]  # Custo em valor absoluto se débito, ou crédito se crédito
    label: PricingLabel
    pricing_type: PricingType
    details: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "net_cash_flow": self.net_cash_flow.to_dict(),
            "display_value": self.display_value.to_dict(),
            "label": self.label,
            "pricing_type": self.pricing_type,
            "details": self.details
        }


def calculate_conservative_pricing(legs: Sequence[OptionLeg]) -> StructurePricing:
    """
    Calcula o custo máximo a pagar ou valor mínimo a receber da estrutura de forma conservadora.
    Aplica a regra inegociável de contágio: se qualquer perna tiver bid/ask ausente ou <= 0,
    marca a precificação inteira como INDISPONIVEL.
    """
    now_ts = current_iso_timestamp()

    if not legs:
        return StructurePricing(
            net_cash_flow=DataValue.indisponivel("calc:pricing", "none", now_ts),
            display_value=DataValue.indisponivel("calc:pricing", "none", now_ts),
            label="DADO INDISPONIVEL",
            pricing_type="INDISPONIVEL",
            details=[]
        )

    endpoints = " | ".join(sorted({leg.bid.endpoint for leg in legs} | {leg.ask.endpoint for leg in legs}))
    latest_ts = max([leg.bid.timestamp for leg in legs] + [leg.ask.timestamp for leg in legs], default=now_ts)

    # 1. Auditoria rigorosa de cada perna: ausência de preço ou cotação <= 0
    details: list[dict[str, Any]] = []
    has_unavailable_leg = False

    for leg in legs:
        leg_desc = f"{leg.action} {leg.ratio}x {leg.symbol} ${leg.strike} {leg.option_type} exp {leg.expiration}"

        if leg.action == "BUY":
            # Compra utiliza ASK conservador
            if not leg.ask.is_available or leg.ask.value is None or leg.ask.value <= 0.0:
                has_unavailable_leg = True
                details.append({
                    "leg": leg_desc,
                    "action": leg.action,
                    "used_metric": "ASK",
                    "price": None,
                    "status": "INDISPONIVEL (Ask ausente ou <= 0)"
                })
            else:
                price = leg.ask.value
                details.append({
                    "leg": leg_desc,
                    "action": leg.action,
                    "used_metric": "ASK",
                    "price": price,
                    "cash_flow": -round(price * leg.ratio, 4),
                    "status": "MEDIDO"
                })
        else:
            # Venda utiliza BID conservador
            if not leg.bid.is_available or leg.bid.value is None or leg.bid.value <= 0.0:
                has_unavailable_leg = True
                details.append({
                    "leg": leg_desc,
                    "action": leg.action,
                    "used_metric": "BID",
                    "price": None,
                    "status": "INDISPONIVEL (Bid ausente ou <= 0)"
                })
            else:
                price = leg.bid.value
                details.append({
                    "leg": leg_desc,
                    "action": leg.action,
                    "used_metric": "BID",
                    "price": price,
                    "cash_flow": round(price * leg.ratio, 4),
                    "status": "MEDIDO"
                })

    # 2. Se houver qualquer falha em perna, contágio total
    if has_unavailable_leg:
        return StructurePricing(
            net_cash_flow=DataValue.indisponivel("calc:net_cash_flow[CONTAGIO_PERNA]", endpoints, latest_ts),
            display_value=DataValue.indisponivel("calc:display_pricing[CONTAGIO_PERNA]", endpoints, latest_ts),
            label="DADO INDISPONIVEL",
            pricing_type="INDISPONIVEL",
            details=details
        )

    # 3. Cálculo do fluxo de caixa líquido
    net_flow = sum(item["cash_flow"] for item in details)
    net_flow = round(net_flow, 4)

    dv_net_flow = DataValue.derivado(
        value=net_flow,
        source="calc:net_cash_flow(ask_buys, bid_sells)",
        endpoint=endpoints,
        timestamp=latest_ts
    )

    # 4. Determinação do rótulo e tipo baseado no SINAL REAL, não na teoria
    if net_flow < 0:
        # Débito líquido: o usuário paga a saída de caixa
        abs_cost = abs(net_flow)
        dv_display = DataValue.derivado(
            value=abs_cost,
            source="calc:cost_max_to_pay",
            endpoint=endpoints,
            timestamp=latest_ts
        )
        return StructurePricing(
            net_cash_flow=dv_net_flow,
            display_value=dv_display,
            label="CUSTO MÁXIMO A PAGAR",
            pricing_type="DEBIT",
            details=details
        )
    else:
        # Crédito líquido: o usuário recebe na montagem
        dv_display = DataValue.derivado(
            value=net_flow,
            source="calc:min_value_to_receive",
            endpoint=endpoints,
            timestamp=latest_ts
        )
        return StructurePricing(
            net_cash_flow=dv_net_flow,
            display_value=dv_display,
            label="VALOR MÍNIMO A RECEBER",
            pricing_type="CREDIT",
            details=details
        )
