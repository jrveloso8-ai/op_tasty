"""
Executor Principal do Screener Tastytrade.
Varre o universo de ativos configurado em config.yaml,
executa o motor das 8 estratégias e gera screener_output.json e screener_output.csv.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml

from src.models import MarketContext, ScreeningResult
from src.provenance import DataValue, current_iso_timestamp
from src.strategies.base import check_put_call_parity_sanity
from src.strategies.implementations import (
    BearPutSpreadStrategy,
    BullCallSpreadStrategy,
    DiagonalSpreadStrategy,
    IronCondorStrategy,
    LongStrangleStrategy,
    PutRatioSpreadStrategy,
)
from src.strategies.screener_engine import ScreenerEngine
from src.tastytrade_client import TastytradeClient
from src.tracking import (
    evaluate_tracked_positions_against_market,
    load_tracked_positions_from_json,
)


def load_config(config_path: Path) -> dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_screener(
    config_path: Path | None = None,
    output_dir: Path | None = None
) -> tuple[list[ScreeningResult], list[MarketContext], bool]:
    cfg_file = config_path or Path(__file__).parent.parent / "config.yaml"
    out_dir = output_dir or Path(__file__).parent.parent

    cfg = load_config(cfg_file)
    universe: list[str] = cfg.get("universe", ["SPY", "AAPL", "QQQ"])
    strat_params: dict[str, Any] = cfg.get("strategy_params", {})
    risk_params: dict[str, Any] = cfg.get("risk_management", {})
    high_price_threshold = float(risk_params.get("high_price_threshold", 100.0))
    prohibit_naked = bool(risk_params.get("prohibit_naked_on_high_price", True))
    max_wing_width = float(risk_params.get("max_wing_width_high_price", 5.0))
    low_iv_rank_threshold = float(risk_params.get("low_iv_rank_threshold", 20.0))

    liquidity_cfg: dict[str, Any] = cfg.get("liquidity", {})
    min_open_interest = int(liquidity_cfg.get("min_open_interest", 100))
    min_volume = int(liquidity_cfg.get("min_volume", 0))

    client = TastytradeClient()
    engine = ScreenerEngine()

    # Propaga parâmetros do config.yaml para instâncias das estratégias (Achado 5 + Gestão de Risco)
    for s in engine.strategies:
        s.min_open_interest = min_open_interest
        s.min_volume = min_volume
        if isinstance(s, IronCondorStrategy):
            ic_cfg = strat_params.get("iron_condor", {})
            if "wing_width" in ic_cfg:
                s.wing_width = float(ic_cfg["wing_width"])
            if "dte_min" in ic_cfg:
                s.dte_min = int(ic_cfg["dte_min"])
            if "dte_max" in ic_cfg:
                s.dte_max = int(ic_cfg["dte_max"])
            if "short_delta" in ic_cfg:
                s.short_delta = float(ic_cfg["short_delta"])
            s.high_price_threshold = high_price_threshold
            s.max_wing_width_high_price = max_wing_width
        elif isinstance(s, (BullCallSpreadStrategy, BearPutSpreadStrategy)):
            spread_cfg = strat_params.get("spreads", {})
            if "dte_min" in spread_cfg:
                s.dte_min = int(spread_cfg["dte_min"])
            if "dte_max" in spread_cfg:
                s.dte_max = int(spread_cfg["dte_max"])
        elif isinstance(s, LongStrangleStrategy):
            s.high_price_threshold = high_price_threshold
            s.low_iv_rank_threshold = low_iv_rank_threshold
        elif isinstance(s, PutRatioSpreadStrategy):
            ratio_cfg = strat_params.get("ratio_spread", {})
            if "dte_min" in ratio_cfg:
                s.dte_min = int(ratio_cfg["dte_min"])
            if "dte_max" in ratio_cfg:
                s.dte_max = int(ratio_cfg["dte_max"])
            s.high_price_threshold = high_price_threshold
            s.prohibit_naked_on_high_price = prohibit_naked
        elif isinstance(s, DiagonalSpreadStrategy):
            diag_cfg = strat_params.get("diagonal", {})
            if "short_dte_min" in diag_cfg:
                s.short_dte_min = int(diag_cfg["short_dte_min"])
            if "short_dte_max" in diag_cfg:
                s.short_dte_max = int(diag_cfg["short_dte_max"])
            if "long_delta_min" in diag_cfg:
                s.long_delta_min = float(diag_cfg["long_delta_min"])
            if "long_delta_max" in diag_cfg:
                s.long_delta_max = float(diag_cfg["long_delta_max"])

    contexts: list[MarketContext] = []
    data_source_by_symbol: dict[str, str] = {}
    skipped_symbols: list[dict[str, str]] = []

    for symbol in universe:
        try:
            ctx, live_flag = client.fetch_market_context_live_or_fixture(symbol)
            contexts.append(ctx)
            data_source_by_symbol[symbol] = "LIVE" if live_flag else "FIXTURE"
        except FileNotFoundError as fnf_err:
            msg = f"Sem fixture local auditada ({fnf_err})"
            print(f"[AUDITORIA - ATIVO DESCARTADO] '{symbol}': {msg}")
            data_source_by_symbol[symbol] = "INDISPONIVEL"
            skipped_symbols.append({"symbol": symbol, "reason": "SEM_FIXTURE", "detail": msg})
        except Exception as exc:  # noqa: BLE001
            msg = f"Falha na coleta de mercado ({type(exc).__name__}: {exc})"
            print(f"[AUDITORIA - ATIVO DESCARTADO] '{symbol}': {msg}")
            data_source_by_symbol[symbol] = "INDISPONIVEL"
            skipped_symbols.append({"symbol": symbol, "reason": "ERRO_COLETA", "detail": msg})

    total_configured = len(universe)
    total_screened_assets = len(contexts)
    coverage_pct = round((total_screened_assets / total_configured * 100.0), 1) if total_configured > 0 else 0.0
    is_partial_universe = total_screened_assets < total_configured

    # is_live_data é true somente se TODOS os símbolos configurados foram varridos e todos ao vivo.
    all_live = (
        bool(contexts)
        and all(data_source_by_symbol.get(c.symbol) == "LIVE" for c in contexts)
        and not is_partial_universe
    )
    any_live = any(data_source_by_symbol.get(s) == "LIVE" for s in universe)
    all_fixture = bool(contexts) and all(data_source_by_symbol.get(c.symbol) == "FIXTURE" for c in contexts)

    # Classificação do Modo de Execução do Universo
    if all_live:
        execution_mode = "AO_VIVO_COMPLETO"
    elif any_live and not is_partial_universe:
        execution_mode = "MISTO_COMPLETO"
    elif any_live and is_partial_universe:
        execution_mode = "AO_VIVO_PARCIAL"
    elif all_fixture and not is_partial_universe:
        execution_mode = "FIXTURE_COMPLETO"
    else:
        execution_mode = "FIXTURE_PARCIAL"

    all_results = engine.screen_universe(contexts)
    opportunities = engine.filter_opportunities(all_results)

    # Sanity check de paridade Put-Call em opções ATM (§1.4)
    for ctx in contexts:
        if ctx.spot_price.is_available and ctx.spot_price.value is not None:
            spot_val = ctx.spot_price.value
            for exp, chain in ctx.chains_by_expiration.items():
                parity_warnings = check_put_call_parity_sanity(chain, spot_val, max_divergence_pct=0.20)
                if parity_warnings:
                    for opp in opportunities:
                        if opp.symbol == ctx.symbol:
                            opp.notes += f" [⚠️ Paridade Put-Call ({exp}): {'; '.join(parity_warnings)}]"
                            if opp.status == "APROVADO":
                                opp.status = "CONDICIONAL"

    now_ts = current_iso_timestamp()

    # Exportação JSON
    json_payload = {
        "generated_at": now_ts,
        "is_live_data": all_live,
        "any_live_data": any_live,
        "execution_mode": execution_mode,
        "is_partial_universe": is_partial_universe,
        "total_configured_assets": total_configured,
        "total_screened_assets": total_screened_assets,
        "coverage_pct": coverage_pct,
        "configured_universe": universe,
        "screened_universe": [ctx.symbol for ctx in contexts],
        "skipped_symbols": skipped_symbols,
        "data_source_by_symbol": data_source_by_symbol,
        "universe": [ctx.symbol for ctx in contexts],
        "total_screened": len(all_results),
        "total_opportunities": len(opportunities),
        "contexts": [
            {
                "symbol": ctx.symbol,
                "spot_price": ctx.spot_price.to_dict(),
                "iv_rank": ctx.iv_rank.to_dict(),
                "iv_percentile": ctx.iv_percentile.to_dict(),
                "direction": ctx.trend.direction.to_dict(),
                "mm20": ctx.trend.mm20.to_dict(),
                "mm50": ctx.trend.mm50.to_dict(),
                "mm200": ctx.trend.mm200.to_dict(),
                "rsi14": ctx.trend.rsi14.to_dict(),
                "event_in_horizon": ctx.event_in_horizon.to_dict(),
                "realized_volatility_20": ctx.realized_volatility_20.to_dict() if ctx.realized_volatility_20 else None,
                "volatility_risk_premium": ctx.volatility_risk_premium.to_dict() if ctx.volatility_risk_premium else None,
                "dividend_yield": ctx.dividend_yield.to_dict() if ctx.dividend_yield else None,
                "dividend_ex_date": ctx.dividend_ex_date.to_dict() if ctx.dividend_ex_date else None,
                "dividend_rate_per_share": ctx.dividend_rate_per_share.to_dict() if ctx.dividend_rate_per_share else None,
                "term_structure_atm_iv": {exp: iv.to_dict() for exp, iv in ctx.term_structure_atm_iv.items()},
                "chains": {
                    exp: [
                        {
                            "symbol": leg.symbol,
                            "strike": leg.strike,
                            "type": leg.option_type,
                            "bid": leg.bid.to_dict(),
                            "ask": leg.ask.to_dict(),
                            "mid": (
                                DataValue.derivado(
                                    round((leg.bid.value + leg.ask.value) / 2.0, 2),
                                    "calc:mid_price",
                                    f"{leg.bid.endpoint}/mid",
                                    ctx.timestamp
                                ).to_dict()
                                if (leg.bid.is_available and leg.ask.is_available and leg.bid.value is not None and leg.ask.value is not None)
                                else DataValue.indisponivel("calc:mid_price", f"{leg.bid.endpoint}/mid", ctx.timestamp).to_dict()
                            ),
                            "iv": leg.iv.to_dict() if leg.iv else None,
                            "delta": leg.delta.to_dict(),
                            "gamma": leg.gamma.to_dict() if leg.gamma else None,
                            "theta": leg.theta.to_dict() if leg.theta else None,
                            "open_interest": leg.open_interest.to_dict() if leg.open_interest else None,
                            "volume": leg.volume.to_dict() if leg.volume else None,
                            "dte": leg.dte
                        }
                        for leg in legs
                    ]
                    for exp, legs in ctx.chains_by_expiration.items()
                }
            }
            for ctx in contexts
        ],
        "results": [r.to_dict() for r in all_results],
        "opportunities": [r.to_dict() for r in opportunities]
    }

    # Avaliação de Posições Rastreadas via src.tracking (Proveniência estrita e contágio)
    pos_file = out_dir / "op_tasty_posicoes.json"
    if not pos_file.exists():
        pos_file = Path(__file__).parent.parent / "op_tasty_posicoes.json"

    contexts_by_sym = {ctx.symbol: ctx for ctx in contexts}
    tracked_positions = load_tracked_positions_from_json(pos_file)
    evaluated_tracked = evaluate_tracked_positions_against_market(tracked_positions, contexts_by_sym)
    json_payload["tracked_positions"] = evaluated_tracked

    with open(out_dir / "screener_output.json", "w", encoding="utf-8") as f:
        json.dump(json_payload, f, indent=2)

    # Exportação CSV Tabular das Oportunidades Aprovadas e Condicionais
    csv_file = out_dir / "screener_output.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "Ativo",
            "Estratégia",
            "Status",
            "Direção",
            "IV Rank",
            "Preço Spot",
            "Tipo Precificação",
            "Rótulo Valor",
            "Valor da Estrutura",
            "Pernas Sugeridas",
            "Timestamp Coleta",
            "Notas"
        ])
        for opp in opportunities:
            legs_desc = " + ".join([
                f"{'COMPRAR' if l.action == 'BUY' else 'VENDER'} {l.ratio}x {l.option_type} ${l.strike:.2f} (Venc: {l.expiration}, {l.dte}d)"
                for l in opp.suggested_legs
            ])
            pricing_label = opp.pricing.label if opp.pricing else "N/D"
            pricing_val = f"{opp.pricing.display_value.value:.2f}" if opp.pricing and opp.pricing.display_value.value is not None else "N/D"
            pricing_type = opp.pricing.pricing_type if opp.pricing else "N/D"

            writer.writerow([
                opp.symbol,
                opp.strategy_name,
                opp.status,
                opp.mandatory_criteria.get("direction", {}).get("value", "N/D"),
                opp.mandatory_criteria.get("iv_rank", {}).get("value", "N/D"),
                opp.pricing.net_cash_flow.endpoint if opp.pricing else "N/D",
                pricing_type,
                pricing_label,
                pricing_val,
                legs_desc,
                opp.timestamp,
                opp.notes
            ])

    return all_results, contexts, all_live


if __name__ == "__main__":
    results, contexts, is_live = run_screener()
    opps = [r for r in results if r.is_opportunity]
    print(f"Varredura concluída: {len(results)} avaliações, {len(opps)} oportunidades identificadas.")
    for o in opps:
        val_str = f"${o.pricing.display_value.value:.2f}" if o.pricing and o.pricing.display_value.value else "N/D"
        lbl = o.pricing.label if o.pricing else ""
        print(f"  [{o.status}] {o.symbol} - {o.strategy_name}: {lbl} {val_str}")
