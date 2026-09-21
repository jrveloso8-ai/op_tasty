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
from src.provenance import current_iso_timestamp
from src.strategies.screener_engine import ScreenerEngine
from src.tastytrade_client import TastytradeClient


def load_config(config_path: Path) -> dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_screener(
    config_path: Path | None = None,
    output_dir: Path | None = None
) -> tuple[list[ScreeningResult], list[MarketContext], bool]:
    root = Path(__file__).parent.parent
    cfg_file = config_path or (root / "config.yaml")
    out_dir = output_dir or root

    config = load_config(cfg_file)
    universe: list[str] = config.get("universe", ["SPY", "AAPL", "QQQ"])
    wing_width: float = config.get("strategy_params", {}).get("iron_condor", {}).get("wing_width", 5.0)

    client = TastytradeClient()
    engine = ScreenerEngine()
    # Atualiza largura de asa no Iron Condor
    for s in engine.strategies:
        if hasattr(s, "wing_width"):
            s.wing_width = wing_width

    contexts: list[MarketContext] = []
    is_live = False

    for symbol in universe:
        try:
            ctx, live_flag = client.fetch_market_context_live_or_fixture(symbol)
            contexts.append(ctx)
            if live_flag:
                is_live = True
        except FileNotFoundError:
            # Ativo sem fixture ainda disponível no ambiente de teste
            continue

    all_results = engine.screen_universe(contexts)
    opportunities = engine.filter_opportunities(all_results)

    # Exportação JSON
    json_payload = {
        "generated_at": current_iso_timestamp(),
        "is_live_data": is_live,
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
                "term_structure_atm_iv": {exp: iv.to_dict() for exp, iv in ctx.term_structure_atm_iv.items()},
                "chains": {
                    exp: [
                        {
                            "symbol": leg.symbol,
                            "strike": leg.strike,
                            "type": leg.option_type,
                            "bid": leg.bid.to_dict(),
                            "ask": leg.ask.to_dict(),
                            "mid": round((leg.bid.value + leg.ask.value) / 2.0, 2) if leg.bid.value and leg.ask.value else None,
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
                f"{l.action} {l.ratio}x {l.strike}{l.option_type[0]} ({l.expiration})"
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

    return all_results, contexts, is_live


if __name__ == "__main__":
    results, contexts, is_live = run_screener()
    opps = [r for r in results if r.is_opportunity]
    print(f"Varredura concluída: {len(results)} avaliações, {len(opps)} oportunidades identificadas.")
    for o in opps:
        val_str = f"${o.pricing.display_value.value:.2f}" if o.pricing and o.pricing.display_value.value else "N/D"
        lbl = o.pricing.label if o.pricing else ""
        print(f"  [{o.status}] {o.symbol} - {o.strategy_name}: {lbl} {val_str}")
