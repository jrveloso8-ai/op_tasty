"""
Módulo de Proveniência de Dados — Screener Tastytrade
Implementa a taxonomia formal de proveniência (MEDIDO, DERIVADO, INDISPONIVEL)
e a regra inegociável de contágio de indisponibilidade.
PROIBIÇÃO ESTRITA: O tipo ESTIMADO não existe e é rejeitado em tempo de execução.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Generic, Literal, TypeVar

T = TypeVar("T")

ProvenanceType = Literal["MEDIDO", "DERIVADO", "INDISPONIVEL"]


def current_iso_timestamp() -> str:
    """Retorna timestamp UTC corrente no padrão ISO-8601."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class DataValue(Generic[T]):
    """
    Invólucro estrutural para todo dado numérico ou categórico do sistema.
    Garante rastreabilidade ao endpoint e timestamp, e proíbe fabricação.
    """
    value: T | None
    provenance: ProvenanceType
    source: str
    endpoint: str
    timestamp: str

    def __post_init__(self) -> None:
        # 1. Proibição estrita de ESTIMADO
        if str(self.provenance).upper() == "ESTIMADO":
            raise ValueError(
                "VIOLAÇÃO DO CONTRATO: 'ESTIMADO' é expressamente proibido neste sistema. "
                "Nunca utilize estimativas, proxies ou fallbacks."
            )

        # 2. Validação da taxonomia permitida
        if self.provenance not in ("MEDIDO", "DERIVADO", "INDISPONIVEL"):
            raise ValueError(
                f"Proveniência inválida: '{self.provenance}'. "
                "Valores aceitos: MEDIDO, DERIVADO, INDISPONIVEL."
            )

        # 3. Consistência de INDISPONIVEL
        if self.provenance == "INDISPONIVEL" and self.value is not None:
            raise ValueError(
                f"Dado com proveniência INDISPONIVEL não pode conter valor ({self.value}). "
                "O valor deve ser obrigatoriamente None."
            )

        # 4. Consistência de MEDIDO e DERIVADO
        if self.provenance in ("MEDIDO", "DERIVADO") and self.value is None:
            raise ValueError(
                f"Dado com proveniência {self.provenance} não pode ter valor None. "
                "Se o dado não foi obtido ou calculado, classifique como INDISPONIVEL."
            )

        # 5. Rastreabilidade obrigatória
        if not self.source or not self.source.strip():
            raise ValueError("O campo 'source' é obrigatório para auditoria de proveniência.")
        if not self.endpoint or not self.endpoint.strip():
            raise ValueError("O campo 'endpoint' é obrigatório para auditoria de proveniência.")
        if not self.timestamp or not self.timestamp.strip():
            raise ValueError("O campo 'timestamp' é obrigatório para auditoria de proveniência.")

    @classmethod
    def medido(
        cls,
        value: T,
        source: str,
        endpoint: str,
        timestamp: str | None = None
    ) -> DataValue[T]:
        """Cria um registro MEDIDO direto da API."""
        return cls(
            value=value,
            provenance="MEDIDO",
            source=source,
            endpoint=endpoint,
            timestamp=timestamp or current_iso_timestamp()
        )

    @classmethod
    def derivado(
        cls,
        value: T,
        source: str,
        endpoint: str,
        timestamp: str | None = None
    ) -> DataValue[T]:
        """Cria um registro DERIVADO calculado a partir de insumos 100% MEDIDOS."""
        return cls(
            value=value,
            provenance="DERIVADO",
            source=source,
            endpoint=endpoint,
            timestamp=timestamp or current_iso_timestamp()
        )

    @classmethod
    def indisponivel(
        cls,
        source: str,
        endpoint: str,
        timestamp: str | None = None
    ) -> DataValue[T]:
        """Cria um registro INDISPONIVEL quando a fonte falha ou omite o dado."""
        return cls(
            value=None,
            provenance="INDISPONIVEL",
            source=source,
            endpoint=endpoint,
            timestamp=timestamp or current_iso_timestamp()
        )

    @property
    def is_available(self) -> bool:
        """Indica se o dado está disponível com valor auditado."""
        return self.provenance != "INDISPONIVEL" and self.value is not None

    def to_dict(self) -> dict[str, Any]:
        """Serialização para JSON/dicionário."""
        return {
            "value": self.value,
            "provenance": self.provenance,
            "source": self.source,
            "endpoint": self.endpoint,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DataValue[Any]:
        """Deserialização a partir de dicionário."""
        return cls(
            value=data.get("value"),
            provenance=data["provenance"],
            source=data["source"],
            endpoint=data["endpoint"],
            timestamp=data["timestamp"]
        )


def apply_contagion(
    calc_fn: Callable[..., T],
    *inputs: DataValue[Any],
    source: str,
    custom_endpoint: str | None = None
) -> DataValue[T]:
    """
    Executa um cálculo aplicando rigorosamente a REGRA DE CONTÁGIO:
    Se QUALQUER insumo for INDISPONIVEL ou tiver valor None, o resultado
    torna-se automaticamente INDISPONIVEL.
    Nunca calcula dados parciais.
    """
    # 1. Verifica se há contágio de indisponibilidade
    infected = [inp for inp in inputs if inp.provenance == "INDISPONIVEL" or inp.value is None]

    # Consolida endpoints e timestamps
    all_endpoints = " | ".join(sorted({inp.endpoint for inp in inputs}))
    endpoint = custom_endpoint or all_endpoints or "local:calc"
    latest_timestamp = max((inp.timestamp for inp in inputs), default=current_iso_timestamp())

    if infected:
        return DataValue.indisponivel(
            source=f"{source}[CONTAGIO_INDISPONIVEL]",
            endpoint=endpoint,
            timestamp=latest_timestamp
        )

    # 2. Todos os insumos estão disponíveis -> executa cálculo auditado
    raw_values = [inp.value for inp in inputs]
    result_value = calc_fn(*raw_values)

    return DataValue.derivado(
        value=result_value,
        source=source,
        endpoint=endpoint,
        timestamp=latest_timestamp
    )
