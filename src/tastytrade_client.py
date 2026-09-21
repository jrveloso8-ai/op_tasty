"""
Cliente da API da Tastytrade com Suporte a Conexão ao Vivo (OAuth2 + DXLink) e Fixtures Auditadas.
Implementa:
  - Autenticação OAuth2 via Tastytrade API (CLIENT_SECRET + REFRESH_TOKEN)
  - Coleta ao vivo de Market Metrics (IV Rank, IV Percentile, Earnings)
  - Coleta ao vivo de Cotação Spot, Gregas e Cadeias de Opções via DXLinkStreamer
  - Coleta ao vivo de 200+ Candles Diários para MM20, MM50, MM200 e RSI(14)
  - Cálculo de IV ATM ponderada por proximidade do spot para cada vencimento (Seção 3.2)
  - Formulação de term structure (curva a termo)
  - Fallback transparente e auditado para fixtures caso credenciais não estejam configuradas
"""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

from src.indicators import analyze_trend
from src.models import MarketContext
from src.pricing import OptionLeg
from src.provenance import DataValue, current_iso_timestamp

# Carrega variáveis do arquivo .env se presente
load_dotenv()


class TastytradeClient:
    """Cliente para coleta e auditoria de dados da Tastytrade."""

    def __init__(
        self,
        base_url: str = "https://api.tastytrade.com",
        session_token: str | None = None,
        timeout: int = 15,
        fixtures_dir: Path | None = None
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.session_token = session_token
        self.timeout = timeout
        self.fixtures_dir = fixtures_dir or (Path(__file__).parent.parent / "fixtures")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.refresh_token = os.getenv("REFRESH_TOKEN")

    @property
    def has_live_credentials(self) -> bool:
        """Verifica se as credenciais OAuth2 estão disponíveis no ambiente."""
        return bool(self.client_secret and self.refresh_token)

    @staticmethod
    def calculate_atm_weighted_iv(
        legs: Sequence[OptionLeg],
        spot_price: float,
        endpoint: str,
        timestamp: str
    ) -> DataValue[float]:
        """
        Fórmula documentada (Seção 3.2):
        Calcula a média de IV ponderada pela proximidade do strike em relação ao spot (ATM):
          peso_i = 1.0 / (|strike_i - spot_price| + 1.0)
          IV_ATM = sum(peso_i * IV_i) / sum(peso_i)
        """
        valid_legs = [
            leg for leg in legs
            if leg.iv and leg.iv.is_available and leg.iv.value is not None and leg.iv.value > 0
            and abs(leg.strike - spot_price) <= (spot_price * 0.15)
        ]

        if not valid_legs:
            return DataValue.indisponivel(
                source="calc:atm_weighted_iv",
                endpoint=endpoint,
                timestamp=timestamp
            )

        total_weight = 0.0
        weighted_iv_sum = 0.0

        for leg in valid_legs:
            assert leg.iv is not None and leg.iv.value is not None
            distance = abs(leg.strike - spot_price)
            weight = 1.0 / (distance + 1.0)
            total_weight += weight
            weighted_iv_sum += weight * leg.iv.value

        atm_iv = round(weighted_iv_sum / total_weight, 4)

        return DataValue.derivado(
            value=atm_iv,
            source="calc:atm_weighted_iv_proximity_formula",
            endpoint=endpoint,
            timestamp=timestamp
        )

    def fetch_market_context_from_fixture(self, symbol: str) -> MarketContext:
        """Carrega contexto real gravado em fixture auditada."""
        fixture_file = self.fixtures_dir / f"{symbol}.json"
        if not fixture_file.exists():
            raise FileNotFoundError(f"Fixture para {symbol} não encontrada em {fixture_file}")

        with open(fixture_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        now_ts = data.get("timestamp", current_iso_timestamp())
        endpoint_metrics = f"/market-metrics?symbols={symbol}"
        endpoint_chains = f"/option-chains/{symbol}/nested"
        endpoint_candles = f"/market-data/candles/{symbol}"
        endpoint_events = f"/instruments/equities/{symbol}/events"

        # 1. Spot Price
        raw_spot = data.get("spot_price")
        if raw_spot is not None and raw_spot > 0:
            spot_dv = DataValue.medido(float(raw_spot), "tastytrade:quote", endpoint_metrics, now_ts)
        else:
            spot_dv = DataValue.indisponivel("tastytrade:quote", endpoint_metrics, now_ts)

        # 2. IV Rank & IV Percentile
        raw_ivr = data.get("iv_rank")
        if raw_ivr is not None:
            ivr_dv = DataValue.medido(float(raw_ivr), "tastytrade:market-metrics", endpoint_metrics, now_ts)
        else:
            ivr_dv = DataValue.indisponivel("tastytrade:market-metrics", endpoint_metrics, now_ts)

        raw_ivp = data.get("iv_percentile")
        if raw_ivp is not None:
            ivp_dv = DataValue.medido(float(raw_ivp), "tastytrade:market-metrics", endpoint_metrics, now_ts)
        else:
            ivp_dv = DataValue.indisponivel("tastytrade:market-metrics", endpoint_metrics, now_ts)

        # 3. Candles e Análise de Tendência
        raw_candles = data.get("daily_closes", [])
        candle_dvs: list[DataValue[float]] = []
        for c in raw_candles:
            if c is not None and c > 0:
                candle_dvs.append(DataValue.medido(float(c), "tastytrade:candle", endpoint_candles, now_ts))
            else:
                candle_dvs.append(DataValue.indisponivel("tastytrade:candle", endpoint_candles, now_ts))

        trend = analyze_trend(spot_dv, candle_dvs, symbol=symbol)

        # 4. Evento no horizonte
        raw_event = data.get("event_in_horizon")
        event_dv: DataValue[bool | None]
        if raw_event is True or raw_event is False:
            event_dv = DataValue.medido(raw_event, "tastytrade:events", endpoint_events, now_ts)
        else:
            event_dv = DataValue.indisponivel("tastytrade:events", endpoint_events, now_ts)

        # 5. Cadeia de opções
        chains_by_exp: dict[str, list[OptionLeg]] = {}
        for exp, leg_dicts in data.get("chains", {}).items():
            legs_list: list[OptionLeg] = []
            for ld in leg_dicts:
                ep_strike = f"{endpoint_chains}/{exp}/{ld['strike']}"
                b_val = ld.get("bid")
                a_val = ld.get("ask")
                d_val = ld.get("delta")
                iv_val = ld.get("iv")

                bid_dv = (
                    DataValue.medido(float(b_val), "tastytrade:quote", ep_strike, now_ts)
                    if b_val is not None and b_val > 0
                    else DataValue.indisponivel("tastytrade:quote", ep_strike, now_ts)
                )
                ask_dv = (
                    DataValue.medido(float(a_val), "tastytrade:quote", ep_strike, now_ts)
                    if a_val is not None and a_val > 0
                    else DataValue.indisponivel("tastytrade:quote", ep_strike, now_ts)
                )
                delta_dv = (
                    DataValue.medido(float(d_val), "tastytrade:greeks", ep_strike, now_ts)
                    if d_val is not None
                    else DataValue.indisponivel("tastytrade:greeks", ep_strike, now_ts)
                )
                iv_dv = (
                    DataValue.medido(float(iv_val), "tastytrade:greeks", ep_strike, now_ts)
                    if iv_val is not None
                    else DataValue.indisponivel("tastytrade:greeks", ep_strike, now_ts)
                )

                legs_list.append(
                    OptionLeg(
                        symbol=ld["symbol"],
                        strike=float(ld["strike"]),
                        option_type=ld["type"],
                        action=ld.get("action", "BUY"),
                        ratio=ld.get("ratio", 1),
                        bid=bid_dv,
                        ask=ask_dv,
                        expiration=exp,
                        dte=int(ld["dte"]),
                        delta=delta_dv,
                        gamma=DataValue.medido(float(ld["gamma"]), "tastytrade:greeks", ep_strike, now_ts) if "gamma" in ld else None,
                        theta=DataValue.medido(float(ld["theta"]), "tastytrade:greeks", ep_strike, now_ts) if "theta" in ld else None,
                        open_interest=DataValue.medido(int(ld["open_interest"]), "tastytrade:oi", ep_strike, now_ts) if "open_interest" in ld else None,
                        volume=DataValue.medido(int(ld["volume"]), "tastytrade:vol", ep_strike, now_ts) if "volume" in ld else None,
                        iv=iv_dv
                    )
                )
            chains_by_exp[exp] = legs_list

        # 6. Curva a Termo
        term_map: dict[str, DataValue[float]] = {}
        if spot_dv.is_available and spot_dv.value is not None:
            for exp, exp_legs in chains_by_exp.items():
                term_iv = self.calculate_atm_weighted_iv(
                    exp_legs,
                    spot_price=spot_dv.value,
                    endpoint=f"{endpoint_chains}/{exp}",
                    timestamp=now_ts
                )
                term_map[exp] = term_iv

        return MarketContext(
            symbol=symbol,
            spot_price=spot_dv,
            iv_rank=ivr_dv,
            iv_percentile=ivp_dv,
            trend=trend,
            event_in_horizon=event_dv,
            chains_by_expiration=chains_by_exp,
            term_structure_atm_iv=term_map,
            timestamp=now_ts
        )

    async def _fetch_live_context_async(self, symbol: str) -> MarketContext:
        """Coleta dados 100% ao vivo via API da Tastytrade e DXLink."""
        from tastytrade import DXLinkStreamer, Session
        from tastytrade.dxfeed import Candle, Greeks, Quote
        from tastytrade.instruments import get_option_chain
        from tastytrade.metrics import get_market_metrics

        now_ts = current_iso_timestamp()
        endpoint_metrics = f"/market-metrics?symbols={symbol}"
        endpoint_chains = f"/option-chains/{symbol}/nested"
        endpoint_candles = f"dxlink:candle:{symbol}"

        # 1. Cria Sessão Oficial Tastytrade
        session = Session(
            provider_secret=self.client_secret,
            refresh_token=self.refresh_token
        )

        # 2. Coleta Market Metrics
        metrics_list = await get_market_metrics(session, [symbol])
        metric = metrics_list[0] if metrics_list else None

        ivr_val = float(metric.implied_volatility_index_rank) * 100.0 if (metric and metric.implied_volatility_index_rank is not None) else None
        ivp_val = float(metric.implied_volatility_percentile) * 100.0 if (metric and metric.implied_volatility_percentile is not None) else None

        ivr_dv = (
            DataValue.medido(round(ivr_val, 2), "tastytrade:market-metrics", endpoint_metrics, now_ts)
            if ivr_val is not None
            else DataValue.indisponivel("tastytrade:market-metrics", endpoint_metrics, now_ts)
        )
        ivp_dv = (
            DataValue.medido(round(ivp_val, 2), "tastytrade:market-metrics", endpoint_metrics, now_ts)
            if ivp_val is not None
            else DataValue.indisponivel("tastytrade:market-metrics", endpoint_metrics, now_ts)
        )

        # Evento no horizonte
        event_dv: DataValue[bool | None]
        earnings_obj = getattr(metric, "earnings", None)
        has_visible_earnings = False
        if earnings_obj is not None and (
            (hasattr(earnings_obj, "visible") and bool(earnings_obj.visible))
            or (hasattr(earnings_obj, "expected_report_date") and bool(earnings_obj.expected_report_date))
        ):
            has_visible_earnings = True

        if has_visible_earnings:
            event_dv = DataValue.medido(True, "tastytrade:earnings", endpoint_metrics, now_ts)
        elif earnings_obj is not None:
            event_dv = DataValue.medido(False, "tastytrade:earnings", endpoint_metrics, now_ts)
        else:
            event_dv = DataValue.indisponivel("tastytrade:earnings", endpoint_metrics, now_ts)

        # 3. Coleta Cadeia de Opções Bruta
        raw_chain = await get_option_chain(session, symbol)
        today = datetime.now(timezone.utc).date()

        # Seleciona vencimentos relevantes (20 a 70 dias para spreads, e > 90 para LEAPS se houver)
        all_exps = sorted(raw_chain.keys())
        target_exps = [e for e in all_exps if 25 <= (e - today).days <= 65]
        if not target_exps and all_exps:
            target_exps = all_exps[:2]
        # Adiciona o mais longo para PMCC
        if all_exps and all_exps[-1] not in target_exps:
            target_exps.append(all_exps[-1])

        # 4. Streamer DXLink para Cotação Spot, Candles Históricos e Gregas
        spot_price_val: float | None = None
        candle_closes: list[float] = []
        quotes_map: dict[str, tuple[float, float]] = {}  # streamer_sym -> (bid, ask)
        greeks_map: dict[str, tuple[float, float, float, float]] = {}  # streamer_sym -> (delta, gamma, theta, iv)

        async with DXLinkStreamer(session) as streamer:
            # Assina cotação Spot
            await streamer.subscribe(Quote, [symbol])
            try:
                q_spot = await asyncio.wait_for(streamer.get_event(Quote), timeout=3.0)
                b = float(q_spot.bid_price or 0)
                a = float(q_spot.ask_price or 0)
                spot_price_val = (b + a) / 2.0 if (b > 0 and a > 0) else (b or a)
            except (asyncio.TimeoutError, Exception):  # noqa: BLE001, S110
                pass

            # Assina Candles Diários (últimos 380 dias para garantir 200+ candles de pregão)
            start_candles = datetime.now(timezone.utc) - timedelta(days=380)
            await streamer.subscribe_candle([symbol], "1d", start_candles)
            try:
                while len(candle_closes) < 260:
                    c = await asyncio.wait_for(streamer.get_event(Candle), timeout=1.5)
                    if c.close and float(c.close) > 0:
                        candle_closes.append(float(c.close))
            except (asyncio.TimeoutError, Exception):  # noqa: BLE001, S110
                pass

            if not spot_price_val and candle_closes:
                spot_price_val = candle_closes[-1]

            # Seleciona opções próximas ao spot (+-15%) para cada vencimento selecionado
            selected_options = []
            for exp in target_exps:
                exp_options = raw_chain[exp]
                if spot_price_val:
                    filtered = [o for o in exp_options if abs(float(o.strike_price) - spot_price_val) <= (spot_price_val * 0.15)]
                    selected_options.extend(filtered if filtered else exp_options[:20])
                else:
                    selected_options.extend(exp_options[:20])

            streamer_syms = [o.streamer_symbol for o in selected_options]

            # Assina Quotes e Greeks das opções
            if streamer_syms:
                await streamer.subscribe(Quote, streamer_syms)
                await streamer.subscribe(Greeks, streamer_syms)

                start_loop = asyncio.get_event_loop().time()
                while asyncio.get_event_loop().time() - start_loop < 3.5:
                    try:
                        while True:
                            q_evt = streamer.get_event_nowait(Quote)
                            if not q_evt:
                                break
                            quotes_map[q_evt.event_symbol] = (float(q_evt.bid_price or 0), float(q_evt.ask_price or 0))
                    except (asyncio.TimeoutError, Exception):  # noqa: BLE001, S110
                        pass

                    try:
                        while True:
                            g_evt = streamer.get_event_nowait(Greeks)
                            if not g_evt:
                                break
                            greeks_map[g_evt.event_symbol] = (
                                float(g_evt.delta or 0),
                                float(g_evt.gamma or 0),
                                float(g_evt.theta or 0),
                                float(g_evt.volatility or 0) * 100.0 if g_evt.volatility else 0.0
                            )
                    except (asyncio.TimeoutError, Exception):  # noqa: BLE001, S110
                        pass
                    await asyncio.sleep(0.04)

        # 5. Constrói DataValues dos Candles e Tendência
        candle_dvs: list[DataValue[float]] = [
            DataValue.medido(c_val, "tastytrade:candle", endpoint_candles, now_ts)
            for c_val in candle_closes
        ]

        spot_dv = (
            DataValue.medido(round(spot_price_val, 2), "tastytrade:quote", endpoint_metrics, now_ts)
            if spot_price_val and spot_price_val > 0
            else DataValue.indisponivel("tastytrade:quote", endpoint_metrics, now_ts)
        )

        trend = analyze_trend(spot_dv, candle_dvs, symbol=symbol)

        # 6. Constrói Cadeias com Dados Medidos
        chains_by_exp: dict[str, list[OptionLeg]] = {}
        for exp in target_exps:
            exp_str = exp.strftime("%Y-%m-%d")
            dte = (exp - today).days
            legs_for_exp: list[OptionLeg] = []

            for opt in raw_chain[exp]:
                st_sym = opt.streamer_symbol
                if st_sym not in streamer_syms:
                    continue

                strike_f = float(opt.strike_price)
                ep_strike = f"{endpoint_chains}/{exp_str}/{strike_f}"
                opt_type: Literal["CALL", "PUT"] = "CALL" if opt.option_type.value == "C" else "PUT"

                q_data = quotes_map.get(st_sym, (0.0, 0.0))
                g_data = greeks_map.get(st_sym, (0.0, 0.0, 0.0, 0.0))

                bid_val, ask_val = q_data
                delta_val, gamma_val, theta_val, iv_val = g_data

                bid_dv = (
                    DataValue.medido(round(bid_val, 2), "tastytrade:quote", ep_strike, now_ts)
                    if bid_val > 0
                    else DataValue.indisponivel("tastytrade:quote", ep_strike, now_ts)
                )
                ask_dv = (
                    DataValue.medido(round(ask_val, 2), "tastytrade:quote", ep_strike, now_ts)
                    if ask_val > 0
                    else DataValue.indisponivel("tastytrade:quote", ep_strike, now_ts)
                )
                delta_dv = (
                    DataValue.medido(round(delta_val, 3), "tastytrade:greeks", ep_strike, now_ts)
                    if delta_val != 0.0
                    else DataValue.indisponivel("tastytrade:greeks", ep_strike, now_ts)
                )
                iv_dv = (
                    DataValue.medido(round(iv_val, 2), "tastytrade:greeks", ep_strike, now_ts)
                    if iv_val > 0
                    else DataValue.indisponivel("tastytrade:greeks", ep_strike, now_ts)
                )

                legs_for_exp.append(
                    OptionLeg(
                        symbol=opt.symbol,
                        strike=strike_f,
                        option_type=opt_type,
                        action="BUY",
                        ratio=1,
                        bid=bid_dv,
                        ask=ask_dv,
                        expiration=exp_str,
                        dte=dte,
                        delta=delta_dv,
                        gamma=DataValue.medido(round(gamma_val, 4), "tastytrade:greeks", ep_strike, now_ts) if gamma_val else None,
                        theta=DataValue.medido(round(theta_val, 4), "tastytrade:greeks", ep_strike, now_ts) if theta_val else None,
                        iv=iv_dv
                    )
                )
            chains_by_exp[exp_str] = legs_for_exp

        # 7. Curva a Termo
        term_map: dict[str, DataValue[float]] = {}
        if spot_dv.is_available and spot_dv.value is not None:
            for exp_str, exp_legs in chains_by_exp.items():
                term_iv = self.calculate_atm_weighted_iv(
                    exp_legs,
                    spot_price=spot_dv.value,
                    endpoint=f"{endpoint_chains}/{exp_str}",
                    timestamp=now_ts
                )
                term_map[exp_str] = term_iv

        return MarketContext(
            symbol=symbol,
            spot_price=spot_dv,
            iv_rank=ivr_dv,
            iv_percentile=ivp_dv,
            trend=trend,
            event_in_horizon=event_dv,
            chains_by_expiration=chains_by_exp,
            term_structure_atm_iv=term_map,
            timestamp=now_ts
        )

    def fetch_market_context_live_or_fixture(self, symbol: str) -> tuple[MarketContext, bool]:
        """
        Executa a coleta ao vivo se credenciais existirem no .env.
        Se falhar ou não houver credenciais, utiliza a fixture auditada.
        Retorna (MarketContext, is_live: bool).
        """
        if self.has_live_credentials:
            try:
                print(f"[TASTYTRADE LIVE API] Coletando dados reais em tempo real para {symbol}...")
                ctx = asyncio.run(self._fetch_live_context_async(symbol))
                return ctx, True
            except Exception as e:  # noqa: BLE001
                print(f"[AVISO] Falha ao coletar ao vivo para {symbol} ({e}). Utilizando fixture auditada.")

        ctx = self.fetch_market_context_from_fixture(symbol)
        return ctx, False
