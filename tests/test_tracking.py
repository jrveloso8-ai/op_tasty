"""
Testes Unitários do Módulo de Rastreamento de Posições (src/tracking.py).
Valida:
- Precificação conservadora de liquidação (venda no Bid, recompra no Ask)
- Disparo dos sinais MANTER, STOPAR e REALIZAR_GAIN
- Regra de contágio quando falta Bid ou Ask em qualquer perna
- Encerramento de posições com registro de P&L realizado
- Cálculo do ranking consolidado de estratégias
"""

from pathlib import Path

import pytest

from src.models import MarketContext, TrendAnalysis
from src.pricing import OptionLeg
from src.provenance import DataValue
from src.tracking import (
    STATUS_CLOSED,
    STATUS_OPEN,
    ExecutedLeg,
    TrackedPosition,
    calculate_strategy_ranking,
    close_position,
    evaluate_position_liquidation,
    evaluate_tracked_positions_against_market,
    load_tracked_positions_from_json,
    normalize_position_status,
)


def _make_dummy_leg(
    symbol: str,
    strike: float,
    opt_type: str,
    bid: float,
    ask: float,
    dte: int = 35,
    expiration: str = "2026-10-23"
) -> OptionLeg:
    endpoint = f"/chains/{symbol}/{strike}"
    ts = "2026-09-22T12:00:00Z"
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
        delta=DataValue.medido(0.50, "api:greeks", endpoint, ts),
        iv=DataValue.medido(30.0, "api:greeks", endpoint, ts)
    )


def test_liquidation_debit_spread_and_gain_signal() -> None:
    # Bull Call Spread executado a débito por $2.00
    ts = "2026-09-22T10:00:00Z"
    pos = TrackedPosition(
        symbol="SPY",
        strategy_id="bull_call_spread",
        strategy_name="Bull Call Spread",
        legs=[
            ExecutedLeg(
                symbol="SPY",
                strike=540.0,
                option_type="CALL",
                action="BUY",
                ratio=1,
                expiration="2026-10-23",
                dte_at_entry=45,
                entry_price=DataValue.medido(3.50, "user:exec", "/pos", ts)
            ),
            ExecutedLeg(
                symbol="SPY",
                strike=550.0,
                option_type="CALL",
                action="SELL",
                ratio=1,
                expiration="2026-10-23",
                dte_at_entry=45,
                entry_price=DataValue.medido(1.50, "user:exec", "/pos", ts)
            )
        ],
        entry_pricing_type="DEBIT",
        entry_unit_price=DataValue.medido(2.00, "user:exec", "/pos", ts),
        target_gain_percent=50.0,
        stop_loss_percent=50.0
    )

    # Cotações atuais:
    # Perna comprada (540C) vendida no Bid atual: $4.50
    # Perna vendida (550C) recomprada no Ask atual: $1.30
    # Liquidação líquida = 4.50 - 1.30 = $3.20
    # P&L = 3.20 - 2.00 = +$1.20 (+60.0%) -> Dispara REALIZAR_GAIN
    q1 = _make_dummy_leg("SPY", 540.0, "CALL", bid=4.50, ask=4.60, dte=30)
    q2 = _make_dummy_leg("SPY", 550.0, "CALL", bid=1.20, ask=1.30, dte=30)

    eval_res = evaluate_position_liquidation(pos, [q1, q2])

    assert eval_res.liquidate_price.value == 3.20
    assert eval_res.pnl_unit.value == 1.20
    assert eval_res.pnl_percent.value == 60.0
    assert eval_res.signal == "REALIZAR_GAIN"
    assert "Meta de lucro atingida" in eval_res.signal_reason


def test_liquidation_credit_spread_and_stop_signal() -> None:
    # Iron Condor / Credit Spread executado a crédito de $1.00
    ts = "2026-09-22T10:00:00Z"
    pos = TrackedPosition(
        symbol="QQQ",
        strategy_id="iron_condor",
        strategy_name="Iron Condor",
        legs=[
            ExecutedLeg("QQQ", 480.0, "CALL", "SELL", 1, "2026-10-23", 45, DataValue.medido(1.20, "user:exec", "/pos", ts)),
            ExecutedLeg("QQQ", 485.0, "CALL", "BUY", 1, "2026-10-23", 45, DataValue.medido(0.20, "user:exec", "/pos", ts))
        ],
        entry_pricing_type="CREDIT",
        entry_unit_price=DataValue.medido(1.00, "user:exec", "/pos", ts),
        target_gain_percent=50.0,
        stop_loss_percent=200.0  # Stop clássico da Tastytrade de 2x o crédito
    )

    # Cotações atuais desfavoráveis:
    # Comprada (485C) vende no Bid: $1.00
    # Vendida (480C) recompra no Ask: $4.20
    # Liquidação líquida = 1.00 - 4.20 = -$3.20 (precisa pagar 3.20 para fechar)
    # P&L = 1.00 - 3.20 = -$2.20 (-220.0%) -> Dispara STOPAR (> 200%)
    q1 = _make_dummy_leg("QQQ", 480.0, "CALL", bid=4.00, ask=4.20, dte=25)
    q2 = _make_dummy_leg("QQQ", 485.0, "CALL", bid=1.00, ask=1.10, dte=25)

    eval_res = evaluate_position_liquidation(pos, [q1, q2])

    assert eval_res.liquidate_price.value == -3.20
    assert eval_res.pnl_unit.value == -2.20
    assert eval_res.pnl_percent.value == -220.0
    assert eval_res.signal == "STOPAR"
    assert "Limite de perda atingido" in eval_res.signal_reason


def test_liquidation_manter_and_time_warning() -> None:
    # Posição a crédito com DTE <= 21 dias e P&L neutro
    ts = "2026-09-22T10:00:00Z"
    pos = TrackedPosition(
        symbol="AAPL",
        strategy_id="iron_condor",
        strategy_name="Iron Condor",
        legs=[
            ExecutedLeg("AAPL", 230.0, "CALL", "SELL", 1, "2026-10-23", 45, DataValue.medido(1.00, "user:exec", "/pos", ts)),
            ExecutedLeg("AAPL", 235.0, "CALL", "BUY", 1, "2026-10-23", 45, DataValue.medido(0.20, "user:exec", "/pos", ts))
        ],
        entry_pricing_type="CREDIT",
        entry_unit_price=DataValue.medido(0.80, "user:exec", "/pos", ts),
        target_gain_percent=50.0,
        stop_loss_percent=200.0
    )

    # Cotações atuais dão P&L de +15%:
    # Vendida recompra no Ask: $0.80
    # Comprada vende no Bid: $0.12
    # Liquidação líquida = 0.12 - 0.80 = -$0.68
    # P&L = 0.80 - 0.68 = +$0.12 (+15.0%)
    q1 = _make_dummy_leg("AAPL", 230.0, "CALL", bid=0.75, ask=0.80, dte=19)
    q2 = _make_dummy_leg("AAPL", 235.0, "CALL", bid=0.12, ask=0.15, dte=19)

    eval_res = evaluate_position_liquidation(pos, [q1, q2])

    assert eval_res.signal == "MANTER"
    assert "Alerta DTE=19d" in eval_res.time_warning


def test_contagion_when_leg_quote_is_missing() -> None:
    # Se qualquer perna tiver Bid ou Ask indisponível, contágio estrito
    ts = "2026-09-22T10:00:00Z"
    pos = TrackedPosition(
        symbol="NVDA",
        strategy_id="bull_call_spread",
        strategy_name="Bull Call Spread",
        legs=[
            ExecutedLeg("NVDA", 120.0, "CALL", "BUY", 1, "2026-10-23", 45, DataValue.medido(5.00, "user:exec", "/pos", ts)),
            ExecutedLeg("NVDA", 125.0, "CALL", "SELL", 1, "2026-10-23", 45, DataValue.medido(2.00, "user:exec", "/pos", ts))
        ],
        entry_pricing_type="DEBIT",
        entry_unit_price=DataValue.medido(3.00, "user:exec", "/pos", ts)
    )

    q1 = _make_dummy_leg("NVDA", 120.0, "CALL", bid=6.00, ask=6.10, dte=30)
    # Perna 2 com ASK INDISPONIVEL (necessário para recompra)
    q2_broken = OptionLeg(
        symbol="NVDA",
        strike=125.0,
        option_type="CALL",
        action="SELL",
        ratio=1,
        bid=DataValue.medido(2.50, "api:quote", "/nvda", ts),
        ask=DataValue.indisponivel("api:quote", "/nvda", ts),
        expiration="2026-10-23",
        dte=30,
        delta=DataValue.medido(0.30, "api:greeks", "/nvda", ts),
        iv=DataValue.medido(35.0, "api:greeks", "/nvda", ts)
    )

    eval_res = evaluate_position_liquidation(pos, [q1, q2_broken])

    assert eval_res.signal == "INDISPONIVEL"
    assert not eval_res.liquidate_price.is_available
    assert not eval_res.pnl_unit.is_available


def test_close_position_and_ranking() -> None:
    ts = "2026-09-22T10:00:00Z"
    pos1 = TrackedPosition(
        symbol="MSFT",
        strategy_id="bull_call_spread",
        strategy_name="Bull Call Spread",
        legs=[
            ExecutedLeg("MSFT", 400.0, "CALL", "BUY", 1, "2026-10-23", 45, DataValue.medido(10.0, "user:exec", "/pos", ts)),
            ExecutedLeg("MSFT", 410.0, "CALL", "SELL", 1, "2026-10-23", 45, DataValue.medido(4.0, "user:exec", "/pos", ts))
        ],
        entry_pricing_type="DEBIT",
        entry_unit_price=DataValue.medido(6.00, "user:exec", "/pos", ts),
        quantity_lots=2
    )

    pos2 = TrackedPosition(
        symbol="TSLA",
        strategy_id="calendar_spread",
        strategy_name="Calendar Spread",
        legs=[
            ExecutedLeg("TSLA", 250.0, "CALL", "SELL", 1, "2026-10-16", 25, DataValue.medido(3.0, "user:exec", "/pos", ts)),
            ExecutedLeg("TSLA", 250.0, "CALL", "BUY", 1, "2026-11-20", 60, DataValue.medido(5.0, "user:exec", "/pos", ts))
        ],
        entry_pricing_type="DEBIT",
        entry_unit_price=DataValue.medido(2.00, "user:exec", "/pos", ts),
        quantity_lots=1
    )

    # Fecha pos1 com lucro: saiu a $9.00 -> Realizado = (9.00 - 6.00) * 100 * 2 lotes = $600.00
    pos1_closed = close_position(pos1, exit_unit_price=9.00, notes="Take profit atingido")
    assert pos1_closed.status == STATUS_CLOSED
    assert pos1_closed.realized_pnl is not None
    assert pos1_closed.realized_pnl.value == 600.00

    # Fecha pos2 com prejuízo: saiu a $1.20 -> Realizado = (1.20 - 2.00) * 100 * 1 lote = -$80.00
    pos2_closed = close_position(pos2, exit_unit_price=1.20, notes="Stop loss atingido")
    assert pos2_closed.realized_pnl is not None
    assert pos2_closed.realized_pnl.value == -80.00

    ranking = calculate_strategy_ranking([pos1_closed, pos2_closed])
    assert len(ranking) == 2
    assert ranking[0]["strategy_name"] == "Bull Call Spread"
    assert ranking[0]["total_pnl"] == 600.00
    assert ranking[0]["win_rate"] == 100.0
    assert ranking[1]["strategy_name"] == "Calendar Spread"
    assert ranking[1]["total_pnl"] == -80.00
    assert ranking[1]["win_rate"] == 0.0


def test_load_tracked_positions_from_json_sanitized_and_provenance() -> None:
    pos_file = Path(__file__).parent.parent / "op_tasty_posicoes.json"
    positions = load_tracked_positions_from_json(pos_file)
    assert len(positions) == 7

    for pos in positions:
        # Garante ausência total de número de conta ou de ordens reais
        assert "5WX93066" not in pos.notes
        assert "Conta Duda" not in pos.notes
        assert "LMT #" not in pos.notes
        assert pos.entry_unit_price.is_available
        assert pos.entry_unit_price.value is not None

        # Garante que pernas possuem timestamp de snapshot e DataValue
        for leg in pos.legs:
            assert leg.quote_timestamp != ""
            assert leg.quote_provenance == "SNAPSHOT_MANUAL"
            assert leg.current_bid is not None
            assert leg.current_ask is not None
            assert leg.current_mid is not None
            assert leg.current_bid.is_available
            assert leg.current_ask.is_available


def test_evaluate_tracked_positions_flags_snapshot_provenance() -> None:
    pos_file = Path(__file__).parent.parent / "op_tasty_posicoes.json"
    positions = load_tracked_positions_from_json(pos_file)

    # Avaliando sem cadeias ao vivo (contexts vazio) -> cai obrigatoriamente no fallback de snapshot
    evaluated = evaluate_tracked_positions_against_market(positions, {})
    assert len(evaluated) == 7

    for item in evaluated:
        eval_dict = item["evaluation"]
        assert eval_dict["is_live_quote"] is False
        assert eval_dict["quote_source"] == "snapshot:manual"
        assert "⚠️ COTAÇÃO DE SNAPSHOT MANUAL" in eval_dict["signal_reason"]


def test_bull_call_spread_ko_maintains_when_spot_is_itm_and_dte_is_active() -> None:
    # Caso Real KO: Bull Call Spread 88/89 C, 31 DTE, entrada a $0.53
    ts = "2026-09-22T12:00:00Z"
    pos = TrackedPosition(
        symbol="KO",
        strategy_id="bull_call_spread",
        strategy_name="Bull Call Spread",
        legs=[
            ExecutedLeg(
                symbol="KO",
                strike=88.0,
                option_type="CALL",
                action="BUY",
                ratio=1,
                expiration="2026-10-23",
                dte_at_entry=31,
                entry_price=DataValue.medido(1.10, "user:exec", "/pos", ts)
            ),
            ExecutedLeg(
                symbol="KO",
                strike=89.0,
                option_type="CALL",
                action="SELL",
                ratio=1,
                expiration="2026-10-23",
                dte_at_entry=31,
                entry_price=DataValue.medido(0.57, "user:exec", "/pos", ts)
            )
        ],
        entry_pricing_type="DEBIT",
        entry_unit_price=DataValue.medido(0.53, "user:exec", "/pos", ts),
        target_gain_percent=50.0,
        stop_loss_percent=50.0
    )

    # Cotações de mercado (com spread bid/ask de formador de mercado):
    # Long 88C: Bid $1.05, Ask $1.15 -> Mid $1.10
    # Short 89C: Bid $0.60, Ask $0.68 -> Mid $0.64
    # Mid Net = 1.10 - 0.64 = 0.46 -> P&L Mid = (0.46 - 0.53) = -$0.07 (-13.2%)
    # Conservative Bid/Ask Net = 1.05 - 0.68 = 0.37 -> P&L = -$0.16 (-30.2%)
    # Spot Price = $88.58 (ITM acima de 88.00)
    q1 = _make_dummy_leg("KO", 88.0, "CALL", bid=1.05, ask=1.15, dte=31)
    q2 = _make_dummy_leg("KO", 89.0, "CALL", bid=0.60, ask=0.68, dte=31)
    spot_dv = DataValue.medido(88.58, "api:quote", "/spot/KO", ts)

    eval_res = evaluate_position_liquidation(pos, [q1, q2], spot_price=spot_dv)

    # Não deve estopar prematuramente: spot ITM e 31 DTE é saudável
    assert eval_res.signal == "MANTER"
    assert eval_res.pnl_mid_percent is not None
    assert eval_res.pnl_mid_percent.value == -13.2
    assert "Maturação saudável aos 31d DTE" in eval_res.signal_reason
    assert "Spot $88.58 ITM acima do strike comprado $88.00" in eval_res.signal_reason


def test_bull_call_spread_stops_only_when_dte_terminal_and_otm() -> None:
    # Bull Call Spread com 10 DTE (<= 14d) e spot colapsado abaixo do strike
    ts = "2026-09-22T12:00:00Z"
    pos = TrackedPosition(
        symbol="XYZ",
        strategy_id="bull_call_spread",
        strategy_name="Bull Call Spread",
        legs=[
            ExecutedLeg("XYZ", 100.0, "CALL", "BUY", 1, "2026-10-02", 10, DataValue.medido(2.50, "user:exec", "/pos", ts)),
            ExecutedLeg("XYZ", 105.0, "CALL", "SELL", 1, "2026-10-02", 10, DataValue.medido(0.50, "user:exec", "/pos", ts))
        ],
        entry_pricing_type="DEBIT",
        entry_unit_price=DataValue.medido(2.00, "user:exec", "/pos", ts),
        target_gain_percent=50.0,
        stop_loss_percent=50.0
    )

    # Cotações colapsadas:
    # 100C: Bid $0.30, Ask $0.40 -> Mid $0.35
    # 105C: Bid $0.05, Ask $0.15 -> Mid $0.10
    # Net Mid = 0.35 - 0.10 = 0.25 -> P&L Mid = -1.75 / 2.00 = -87.5% <= -50%
    q1 = _make_dummy_leg("XYZ", 100.0, "CALL", bid=0.30, ask=0.40, dte=10)
    q2 = _make_dummy_leg("XYZ", 105.0, "CALL", bid=0.05, ask=0.15, dte=10)
    spot_dv = DataValue.medido(90.00, "api:quote", "/spot/XYZ", ts)  # Bem OTM

    eval_res = evaluate_position_liquidation(pos, [q1, q2], spot_price=spot_dv)

    assert eval_res.signal == "STOPAR"
    assert "Encerramento defensivo: DTE avançado" in eval_res.signal_reason


def test_specialized_strategy_exit_rules() -> None:
    ts = "2026-09-22T12:00:00Z"

    # 1. Calendar Spread: stop defensivo quando perna curta atinge DTE <= 3d
    cal_pos = TrackedPosition(
        symbol="SPY",
        strategy_id="calendar_spread",
        strategy_name="Calendar Spread",
        legs=[
            ExecutedLeg("SPY", 550.0, "CALL", "SELL", 1, "2026-09-24", 2, DataValue.medido(1.00, "user:exec", "/pos", ts)),
            ExecutedLeg("SPY", 550.0, "CALL", "BUY", 1, "2026-10-23", 31, DataValue.medido(4.00, "user:exec", "/pos", ts))
        ],
        entry_pricing_type="DEBIT",
        entry_unit_price=DataValue.medido(3.00, "user:exec", "/pos", ts),
        target_gain_percent=30.0,
        stop_loss_percent=50.0
    )
    q1_cal = _make_dummy_leg("SPY", 550.0, "CALL", bid=0.90, ask=1.00, dte=2)
    q2_cal = _make_dummy_leg("SPY", 550.0, "CALL", bid=3.90, ask=4.10, dte=31)
    eval_cal = evaluate_position_liquidation(cal_pos, [q1_cal, q2_cal])
    assert eval_cal.signal == "STOPAR"
    assert "Perna curta expirando em 2d" in eval_cal.signal_reason

    # 2. Long Strangle: stop temporal por esgotamento de DTE <= 14d sem evento
    strangle_pos = TrackedPosition(
        symbol="TSLA",
        strategy_id="long_strangle",
        strategy_name="Long Strangle",
        legs=[
            ExecutedLeg("TSLA", 220.0, "PUT", "BUY", 1, "2026-10-02", 10, DataValue.medido(2.00, "user:exec", "/pos", ts)),
            ExecutedLeg("TSLA", 260.0, "CALL", "BUY", 1, "2026-10-02", 10, DataValue.medido(2.00, "user:exec", "/pos", ts))
        ],
        entry_pricing_type="DEBIT",
        entry_unit_price=DataValue.medido(4.00, "user:exec", "/pos", ts),
        target_gain_percent=50.0,
        stop_loss_percent=50.0
    )
    q1_str = _make_dummy_leg("TSLA", 220.0, "PUT", bid=1.40, ask=1.60, dte=10)
    q2_str = _make_dummy_leg("TSLA", 260.0, "CALL", bid=1.40, ask=1.60, dte=10)
    eval_str = evaluate_position_liquidation(strangle_pos, [q1_str, q2_str], event_pending=False)
    assert eval_str.signal == "STOPAR"
    assert "Stop temporal por esgotamento de DTE" in eval_str.signal_reason

    # 3. Long Strangle com evento pendente: NÃO stopa aos 10 DTE (§2.2)
    eval_str_event = evaluate_position_liquidation(strangle_pos, [q1_str, q2_str], event_pending=True)
    assert eval_str_event.signal == "MANTER"
    assert "Aguardando realização do catalisador/evento no horizonte" in eval_str_event.signal_reason

    # 4. Iron Condor de asa estreita ($5): calibra meta para 30% (§2.3)
    ic_pos = TrackedPosition(
        symbol="SPY",
        strategy_id="iron_condor",
        strategy_name="Iron Condor",
        legs=[
            ExecutedLeg("SPY", 530.0, "PUT", "SELL", 1, "2026-10-23", 31, DataValue.medido(2.00, "user:exec", "/pos", ts)),
            ExecutedLeg("SPY", 525.0, "PUT", "BUY", 1, "2026-10-23", 31, DataValue.medido(1.20, "user:exec", "/pos", ts)),
            ExecutedLeg("SPY", 570.0, "CALL", "SELL", 1, "2026-10-23", 31, DataValue.medido(2.00, "user:exec", "/pos", ts)),
            ExecutedLeg("SPY", 575.0, "CALL", "BUY", 1, "2026-10-23", 31, DataValue.medido(1.20, "user:exec", "/pos", ts))
        ],
        entry_pricing_type="CREDIT",
        entry_unit_price=DataValue.medido(1.60, "user:exec", "/pos", ts),
        target_gain_percent=50.0,
        stop_loss_percent=100.0
    )
    # Cotação com lucro de ~31% (crédito remanescente = 1.10 -> lucro = 0.50 / 1.60 = 31.2%)
    q_ic1 = _make_dummy_leg("SPY", 530.0, "PUT", bid=1.35, ask=1.45, dte=28)
    q_ic2 = _make_dummy_leg("SPY", 525.0, "PUT", bid=0.80, ask=0.90, dte=28)
    q_ic3 = _make_dummy_leg("SPY", 570.0, "CALL", bid=1.35, ask=1.45, dte=28)
    q_ic4 = _make_dummy_leg("SPY", 575.0, "CALL", bid=0.80, ask=0.90, dte=28)
    eval_ic = evaluate_position_liquidation(ic_pos, [q_ic1, q_ic2, q_ic3, q_ic4])
    assert eval_ic.signal == "REALIZAR_GAIN"
    assert "largura de asa estreita $5.0 = 30%" in eval_ic.signal_reason

    # 5. QQQ Calendar Spread: respeita meta de 50% e emite MANTER para posição atual a -1.0% Mark
    qqq_pos = TrackedPosition(
        symbol="QQQ",
        strategy_id="calendar_spread",
        strategy_name="Calendar Spread",
        legs=[
            ExecutedLeg("QQQ", 740.0, "CALL", "SELL", 1, "2026-10-16", 24, DataValue.medido(18.00, "user:exec", "/pos", ts)),
            ExecutedLeg("QQQ", 740.0, "CALL", "BUY", 1, "2026-10-23", 31, DataValue.medido(20.41, "user:exec", "/pos", ts))
        ],
        entry_pricing_type="DEBIT",
        entry_unit_price=DataValue.medido(2.41, "user:exec", "/pos", ts),
        target_gain_percent=50.0,
        stop_loss_percent=50.0
    )
    q_qqq_short = _make_dummy_leg("QQQ", 740.0, "CALL", bid=18.96, ask=19.06, dte=24, expiration="2026-10-16")
    q_qqq_long = _make_dummy_leg("QQQ", 740.0, "CALL", bid=21.34, ask=21.45, dte=31, expiration="2026-10-23")
    eval_qqq = evaluate_position_liquidation(qqq_pos, [q_qqq_short, q_qqq_long])
    assert eval_qqq.signal == "MANTER"
    assert eval_qqq.pnl_mid_percent is not None
    assert -5.0 <= (eval_qqq.pnl_mid_percent.value or 0.0) <= 5.0


def test_normalize_position_status_valid_and_invalid() -> None:
    assert normalize_position_status("OPEN") == STATUS_OPEN
    assert normalize_position_status("open") == STATUS_OPEN
    assert normalize_position_status("ABERTA") == STATUS_OPEN
    assert normalize_position_status("aberta") == STATUS_OPEN
    assert normalize_position_status("CLOSED") == STATUS_CLOSED
    assert normalize_position_status("closed") == STATUS_CLOSED
    assert normalize_position_status("ENCERRADA") == STATUS_CLOSED
    assert normalize_position_status("encerrada") == STATUS_CLOSED

    with pytest.raises(ValueError, match="Status de posição inválido"):
        normalize_position_status("PENDING")

    with pytest.raises(ValueError, match="Status de posição inválido"):
        normalize_position_status("LIQUIDADA")

    with pytest.raises(TypeError, match="Status de posição inválido"):
        normalize_position_status(123)  # type: ignore[arg-type]


def test_load_and_evaluate_closed_position_pipeline(tmp_path: Path) -> None:
    # Cria arquivo JSON simulando posição fechada pelo usuário ou UI
    sample_data = [
        {
            "id": "pos_closed_spy_01",
            "symbol": "SPY",
            "strategy_id": "bull_call_spread",
            "strategy_name": "Bull Call Spread",
            "strategy_type": "DEBIT",
            "entry_date": "2026-09-10T10:00:00Z",
            "entry_price": 2.00,
            "quantity": 1,
            "status": "CLOSED",
            "exit_date": "2026-09-20T15:00:00Z",
            "exit_price": 3.00,
            "realized_pnl": 100.0,
            "notes": "Fechamento antecipado no alvo",
            "legs": [
                {
                    "symbol": "SPY",
                    "strike": 540.0,
                    "option_type": "CALL",
                    "action": "BUY",
                    "expiration": "2026-10-23",
                    "dte": 30,
                    "current_bid": 4.0,
                    "current_ask": 4.1
                },
                {
                    "symbol": "SPY",
                    "strike": 550.0,
                    "option_type": "CALL",
                    "action": "SELL",
                    "expiration": "2026-10-23",
                    "dte": 30,
                    "current_bid": 1.0,
                    "current_ask": 1.1
                }
            ]
        },
        {
            "id": "pos_open_qqq_01",
            "symbol": "QQQ",
            "strategy_id": "long_strangle",
            "strategy_name": "Long Strangle",
            "strategy_type": "DEBIT",
            "entry_date": "2026-09-20T10:00:00Z",
            "entry_price": 1.50,
            "quantity": 1,
            "status": "OPEN",
            "legs": [
                {
                    "symbol": "QQQ",
                    "strike": 480.0,
                    "option_type": "CALL",
                    "action": "BUY",
                    "expiration": "2026-10-23",
                    "dte": 30,
                    "current_bid": 0.90,
                    "current_ask": 1.00
                }
            ]
        }
    ]

    import json
    f = tmp_path / "test_positions.json"
    f.write_text(json.dumps(sample_data), encoding="utf-8")

    positions = load_tracked_positions_from_json(f)
    assert len(positions) == 2

    # Verifica posição fechada
    p_closed = positions[0]
    assert p_closed.status == STATUS_CLOSED
    assert p_closed.exit_unit_price is not None
    assert p_closed.exit_unit_price.value == 3.00
    assert p_closed.realized_pnl is not None
    assert p_closed.realized_pnl.value == 100.0

    # Verifica posição aberta
    p_open = positions[1]
    assert p_open.status == STATUS_OPEN

    # Avalia contra o mercado (sem contextos)
    evaluated = evaluate_tracked_positions_against_market(positions, {})
    assert len(evaluated) == 2

    # Posição fechada não recalcula a mercado
    ev_closed = evaluated[0]["evaluation"]
    assert ev_closed["signal"] == "ENCERRADA"
    assert ev_closed["is_live_quote"] is False
    assert ev_closed["quote_source"] == "closed:static"

    # Posição aberta cai no snapshot manual
    ev_open = evaluated[1]["evaluation"]
    assert ev_open["signal"] != "ENCERRADA"
    assert ev_open["quote_source"] == "snapshot:manual"

    # Ranking calcula apenas posições fechadas
    ranking = calculate_strategy_ranking(positions)
    assert len(ranking) == 1
    assert ranking[0]["strategy_name"] == "Bull Call Spread"
    assert ranking[0]["total_trades"] == 1
    assert ranking[0]["total_pnl"] == 100.0


def test_to_dict_includes_flat_and_dv_fields() -> None:
    ts = "2026-09-22T10:00:00Z"
    pos = TrackedPosition(
        symbol="SPY",
        strategy_id="bull_call_spread",
        strategy_name="Bull Call Spread",
        legs=[],
        entry_pricing_type="DEBIT",
        entry_unit_price=DataValue.medido(2.00, "user:exec", "/pos", ts),
        quantity_lots=2,
        status=STATUS_CLOSED,
        exit_timestamp=ts,
        exit_unit_price=DataValue.medido(3.50, "user:exec", "/pos", ts),
        realized_pnl=DataValue.derivado(300.0, "calc:realized_pnl", "/pos", ts)
    )

    d = pos.to_dict()
    assert d["id"] == pos.position_id
    assert d["status"] == STATUS_CLOSED
    assert d["entry_price"] == 2.00
    assert d["exit_price"] == 3.50
    assert d["realized_pnl"] == 300.0
    assert d["realized_pnl_dv"]["value"] == 300.0
    assert d["realized_pnl_dv"]["provenance"] == "DERIVADO"


def test_evaluate_tracked_positions_updates_leg_quotes() -> None:
    ts = "2026-09-22T12:00:00Z"
    pos = TrackedPosition(
        symbol="SPY",
        strategy_id="bull_call_spread",
        strategy_name="Bull Call Spread",
        legs=[
            ExecutedLeg(
                symbol="SPY",
                strike=540.0,
                option_type="CALL",
                action="BUY",
                ratio=1,
                expiration="2026-10-23",
                dte_at_entry=35,
                entry_price=DataValue.medido(3.50, "user:exec", "/pos", ts),
                current_bid=DataValue.medido(3.50, "snapshot:manual", "/pos", ts),
                current_ask=DataValue.medido(3.60, "snapshot:manual", "/pos", ts),
                quote_provenance="SNAPSHOT_MANUAL"
            ),
            ExecutedLeg(
                symbol="SPY",
                strike=550.0,
                option_type="CALL",
                action="SELL",
                ratio=1,
                expiration="2026-10-23",
                dte_at_entry=35,
                entry_price=DataValue.medido(1.50, "user:exec", "/pos", ts),
                current_bid=DataValue.medido(1.50, "snapshot:manual", "/pos", ts),
                current_ask=DataValue.medido(1.60, "snapshot:manual", "/pos", ts),
                quote_provenance="SNAPSHOT_MANUAL"
            )
        ],
        entry_pricing_type="DEBIT",
        entry_unit_price=DataValue.medido(2.00, "user:exec", "/pos", ts),
    )

    # Cria contexto de mercado com cotação ao vivo fresca
    live_q1 = _make_dummy_leg("SPY", 540.0, "CALL", bid=4.80, ask=4.90, dte=30, expiration="2026-10-23")
    live_q2 = _make_dummy_leg("SPY", 550.0, "CALL", bid=1.10, ask=1.20, dte=30, expiration="2026-10-23")

    trend_obj = TrendAnalysis(
        direction=DataValue.medido("ALTA", "calc:trend", "/trend", ts),  # type: ignore[arg-type]
        current_price=DataValue.medido(545.0, "api:quote", "/spot", ts),
        mm20=DataValue.medido(540.0, "calc:mm20", "/trend", ts),
        mm50=DataValue.medido(530.0, "calc:mm50", "/trend", ts),
        mm200=DataValue.medido(500.0, "calc:mm200", "/trend", ts),
        rsi14=DataValue.medido(55.0, "calc:rsi", "/trend", ts),
        notes="mocked"
    )

    ctx = MarketContext(
        symbol="SPY",
        spot_price=DataValue.medido(545.0, "api:quote", "/spot", ts),
        iv_rank=DataValue.medido(30.0, "calc:ivr", "/ivr", ts),
        iv_percentile=DataValue.medido(30.0, "calc:ivp", "/ivp", ts),
        trend=trend_obj,
        event_in_horizon=DataValue.medido(False, "api:calendar", "/event", ts),
        chains_by_expiration={"2026-10-23": [live_q1, live_q2]},
        term_structure_atm_iv={},
        timestamp=ts
    )

    evaluated = evaluate_tracked_positions_against_market([pos], {"SPY": ctx})
    assert len(evaluated) == 1

    legs_res = evaluated[0]["legs"]
    assert len(legs_res) == 2
    # Perna 1 deve refletir a cotação ao vivo da cadeia (4.80 / 4.90), não o snapshot antigo (3.50 / 3.60)
    assert legs_res[0]["current_bid"]["value"] == 4.80
    assert legs_res[0]["current_ask"]["value"] == 4.90
    assert legs_res[0]["current_mid"]["value"] == 4.85
    assert legs_res[0]["quote_provenance"] == "MEDIDO"

    # Perna 2 deve refletir a cotação ao vivo da cadeia (1.10 / 1.20)
    assert legs_res[1]["current_bid"]["value"] == 1.10
    assert legs_res[1]["current_ask"]["value"] == 1.20
    assert legs_res[1]["current_mid"]["value"] == 1.15
    assert legs_res[1]["quote_provenance"] == "MEDIDO"





