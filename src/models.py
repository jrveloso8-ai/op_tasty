"""
Modelos de Dados do Screener Tastytrade.
Representa ativos, contexto de mercado e resultados de screening por oportunidade.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal, Optional
from src.provenance import DataValue
from src.indicators import TrendAnalysis
from src.pricing import OptionLeg, StructurePricing

OpportunityStatus = Literal["APROVADO", "CONDICIONAL", "REJEITADO"]


@dataclass
class MarketContext:
    """Contexto completo de mercado coletado para um ativo."""
    symbol: str
    spot_price: DataValue[float]
    iv_rank: DataValue[float]
    iv_percentile: DataValue[float]
    trend: TrendAnalysis
    event_in_horizon: DataValue[Optional[bool]]
    chains_by_expiration: dict[str, list[OptionLeg]] = field(default_factory=dict)
    term_structure_atm_iv: dict[str, DataValue[float]] = field(default_factory=dict)
    timestamp: str = ""

    def get_expirations_in_dte_range(self, min_dte: int, max_dte: int) -> list[str]:
        """Filtra vencimentos disponíveis dentro da janela de DTE especificada."""
        matching: list[str] = []
        for exp, legs in self.chains_by_expiration.items():
            if legs and min_dte <= legs[0].dte <= max_dte:
                matching.append(exp)
        return sorted(matching, key=lambda e: self.chains_by_expiration[e][0].dte if self.chains_by_expiration[e] else 0)


@dataclass
class ScreeningResult:
    """Resultado da avaliação de uma estratégia sobre um ativo."""
    symbol: str
    strategy_id: str
    strategy_name: str
    status: OpportunityStatus
    mandatory_criteria: dict[str, Any]
    rejection_reasons: list[str] = field(default_factory=list)
    pricing: Optional[StructurePricing] = None
    suggested_legs: list[OptionLeg] = field(default_factory=list)
    timestamp: str = ""
    notes: str = ""

    @property
    def is_opportunity(self) -> bool:
        """Retorna True se aprovado ou condicional (entra na lista de oportunidades)."""
        return self.status in ("APROVADO", "CONDICIONAL")

    def to_dict(self) -> dict[str, Any]:
        """Serialização tabular auditável."""
        return {
            "symbol": self.symbol,
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "status": self.status,
            "mandatory_criteria": self.mandatory_criteria,
            "rejection_reasons": self.rejection_reasons,
            "pricing": self.pricing.to_dict() if self.pricing else None,
            "suggested_legs": [
                {
                    "symbol": leg.symbol,
                    "strike": leg.strike,
                    "type": leg.option_type,
                    "action": leg.action,
                    "ratio": leg.ratio,
                    "expiration": leg.expiration,
                    "dte": leg.dte,
                    "delta": leg.delta.to_dict(),
                    "bid": leg.bid.to_dict(),
                    "ask": leg.ask.to_dict()
                }
                for leg in self.suggested_legs
            ],
            "timestamp": self.timestamp,
            "notes": self.notes
        }
