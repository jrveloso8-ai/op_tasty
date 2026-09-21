"""
Testes Unitários do Módulo de Proveniência e Regra de Contágio.
Garante a cerca estrutural, proibição de ESTIMADO e contágio obrigatório.
"""

import pytest
from src.provenance import DataValue, apply_contagion


def test_create_medido_success() -> None:
    dv = DataValue.medido(
        value=540.25,
        source="tastytrade:quote",
        endpoint="/market-metrics?symbols=SPY",
        timestamp="2026-09-21T10:00:00Z"
    )
    assert dv.provenance == "MEDIDO"
    assert dv.value == 540.25
    assert dv.source == "tastytrade:quote"
    assert dv.endpoint == "/market-metrics?symbols=SPY"
    assert dv.timestamp == "2026-09-21T10:00:00Z"
    assert dv.is_available is True


def test_create_derivado_success() -> None:
    dv = DataValue.derivado(
        value=535.10,
        source="calc:mm20",
        endpoint="/market-metrics?symbols=SPY",
        timestamp="2026-09-21T10:00:00Z"
    )
    assert dv.provenance == "DERIVADO"
    assert dv.value == 535.10
    assert dv.is_available is True


def test_create_indisponivel_success() -> None:
    dv = DataValue.indisponivel(
        source="tastytrade:earnings",
        endpoint="/instruments/equities/SPY/events",
        timestamp="2026-09-21T10:00:00Z"
    )
    assert dv.provenance == "INDISPONIVEL"
    assert dv.value is None
    assert dv.is_available is False


def test_prohibition_of_estimado() -> None:
    """Verifica que a cerca estrutural rejeita fatalmente qualquer dado ESTIMADO."""
    with pytest.raises(ValueError, match="ESTIMADO"):
        DataValue(
            value=25.0,
            provenance="ESTIMADO",  # type: ignore[arg-type]
            source="manual:proxy",
            endpoint="/dummy",
            timestamp="2026-09-21T10:00:00Z"
        )


def test_invalid_provenance_type() -> None:
    with pytest.raises(ValueError, match="Proveniência inválida"):
        DataValue(
            value=10.0,
            provenance="APROXIMADO",  # type: ignore[arg-type]
            source="test",
            endpoint="/test",
            timestamp="2026-09-21T10:00:00Z"
        )


def test_indisponivel_cannot_have_value() -> None:
    with pytest.raises(ValueError, match="não pode conter valor"):
        DataValue(
            value=10.0,
            provenance="INDISPONIVEL",
            source="test",
            endpoint="/test",
            timestamp="2026-09-21T10:00:00Z"
        )


def test_medido_or_derivado_cannot_have_none_value() -> None:
    with pytest.raises(ValueError, match="não pode ter valor None"):
        DataValue(
            value=None,
            provenance="MEDIDO",
            source="test",
            endpoint="/test",
            timestamp="2026-09-21T10:00:00Z"
        )


def test_missing_audit_fields() -> None:
    with pytest.raises(ValueError, match="source"):
        DataValue(value=1.0, provenance="MEDIDO", source="", endpoint="/test", timestamp="2026-09-21T10:00:00Z")
    with pytest.raises(ValueError, match="endpoint"):
        DataValue(value=1.0, provenance="MEDIDO", source="src", endpoint="", timestamp="2026-09-21T10:00:00Z")
    with pytest.raises(ValueError, match="timestamp"):
        DataValue(value=1.0, provenance="MEDIDO", source="src", endpoint="/test", timestamp="")


def test_contagion_rule_when_input_is_indisponivel() -> None:
    """Regra de contágio: derivado de insumo INDISPONIVEL vira INDISPONIVEL."""
    input1 = DataValue.medido(100.0, "api:price", "/price", "2026-09-21T10:00:00Z")
    input2 = DataValue.indisponivel("api:iv", "/market-metrics", "2026-09-21T10:05:00Z")

    calc_executed = False

    def dummy_sum(a: float, b: float) -> float:
        nonlocal calc_executed
        calc_executed = True
        return a + b

    result = apply_contagion(dummy_sum, input1, input2, source="calc:dummy_sum")

    assert calc_executed is False, "O cálculo nunca deve ser executado quando há contágio de indisponibilidade"
    assert result.provenance == "INDISPONIVEL"
    assert result.value is None
    assert "CONTAGIO_INDISPONIVEL" in result.source
    assert result.timestamp == "2026-09-21T10:05:00Z"
    assert "/price" in result.endpoint
    assert "/market-metrics" in result.endpoint


def test_contagion_rule_when_all_inputs_available() -> None:
    input1 = DataValue.medido(10.0, "api:ask", "/chains", "2026-09-21T10:00:00Z")
    input2 = DataValue.medido(4.0, "api:bid", "/chains", "2026-09-21T10:02:00Z")

    result = apply_contagion(lambda a, b: a - b, input1, input2, source="calc:net_debit")

    assert result.provenance == "DERIVADO"
    assert result.value == 6.0
    assert result.source == "calc:net_debit"
    assert result.timestamp == "2026-09-21T10:02:00Z"


def test_serialization_roundtrip() -> None:
    dv = DataValue.medido(45.5, "api:iv", "/metrics", "2026-09-21T10:00:00Z")
    data_dict = dv.to_dict()
    restored = DataValue.from_dict(data_dict)
    assert restored == dv
