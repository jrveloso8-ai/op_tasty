"""
Script auxiliar para geração das fixtures auditadas de mercado (SPY, AAPL, QQQ).
Garante que os 220 candles diários e as cadeias completas de opções contenham dados consistentes.
"""

import json
from pathlib import Path

fixtures_dir = Path(__file__).parent.parent / "fixtures"
fixtures_dir.mkdir(parents=True, exist_ok=True)

# 1. SPY: Bullish, Low IV Rank (25.0), Inverted Term Structure (Short IV > Long IV), Event INDISPONIVEL
spy_closes = []
price = 480.0
for i in range(220):
    delta = 0.5 if i % 2 == 0 else -0.2
    price += delta
    spy_closes.append(round(price, 2))

spy_spot = round(price + 1.0, 2)  # ~514

spy_chains = {
    "2026-10-16": [
        {"symbol": "SPY   261016C00480000", "strike": 480.0, "type": "CALL", "bid": 36.20, "ask": 36.60, "delta": 0.88, "gamma": 0.008, "theta": -0.04, "open_interest": 15400, "volume": 3200, "iv": 39.0, "dte": 35},
        {"symbol": "SPY   261016C00500000", "strike": 500.0, "type": "CALL", "bid": 18.50, "ask": 18.80, "delta": 0.72, "gamma": 0.012, "theta": -0.06, "open_interest": 22100, "volume": 5400, "iv": 38.5, "dte": 35},
        {"symbol": "SPY   261016C00515000", "strike": 515.0, "type": "CALL", "bid": 7.40, "ask": 7.60, "delta": 0.50, "gamma": 0.018, "theta": -0.09, "open_interest": 35400, "volume": 12800, "iv": 38.0, "dte": 35},
        {"symbol": "SPY   261016C00525000", "strike": 525.0, "type": "CALL", "bid": 2.80, "ask": 2.95, "delta": 0.25, "gamma": 0.014, "theta": -0.07, "open_interest": 41200, "volume": 14200, "iv": 37.5, "dte": 35},
        {"symbol": "SPY   261016P00500000", "strike": 500.0, "type": "PUT", "bid": 3.10, "ask": 3.25, "delta": -0.25, "gamma": 0.013, "theta": -0.07, "open_interest": 38000, "volume": 11500, "iv": 38.2, "dte": 35},
        {"symbol": "SPY   261016P00515000", "strike": 515.0, "type": "PUT", "bid": 7.20, "ask": 7.45, "delta": -0.50, "gamma": 0.018, "theta": -0.09, "open_interest": 29000, "volume": 9800, "iv": 38.0, "dte": 35}
    ],
    "2026-11-20": [
        {"symbol": "SPY   261120C00515000", "strike": 515.0, "type": "CALL", "bid": 11.20, "ask": 11.50, "delta": 0.52, "gamma": 0.014, "theta": -0.07, "open_interest": 18200, "volume": 4100, "iv": 30.0, "dte": 70},
        {"symbol": "SPY   261120C00530000", "strike": 530.0, "type": "CALL", "bid": 4.50, "ask": 4.70, "delta": 0.28, "gamma": 0.011, "theta": -0.05, "open_interest": 24000, "volume": 5600, "iv": 29.5, "dte": 70}
    ],
    "2027-01-15": [
        {"symbol": "SPY   270115C00450000", "strike": 450.0, "type": "CALL", "bid": 78.00, "ask": 79.50, "delta": 0.76, "gamma": 0.005, "theta": -0.03, "open_interest": 12000, "volume": 1800, "iv": 28.0, "dte": 126}
    ]
}

spy_data = {
    "symbol": "SPY",
    "spot_price": spy_spot,
    "iv_rank": 25.0,
    "iv_percentile": 27.5,
    "daily_closes": spy_closes,
    "event_in_horizon": None,  # INDISPONIVEL na API para teste de CONDICIONAL
    "chains": spy_chains,
    "timestamp": "2026-09-21T10:30:00Z"
}

with open(fixtures_dir / "SPY.json", "w", encoding="utf-8") as f:
    json.dump(spy_data, f, indent=2)

# 2. AAPL: Neutral, High IV Rank (62.0), Normal Term Structure, Event = False (Ideal Iron Condor & Put Ratio)
aapl_closes = []
price = 220.0
for i in range(220):
    delta = 0.8 if (i % 4 in (0, 1)) else -0.78
    price += delta
    aapl_closes.append(round(price, 2))

aapl_spot = round(price, 2)  # ~221

aapl_chains = {
    "2026-10-16": [
        {"symbol": "AAPL  261016C00220000", "strike": 220.0, "type": "CALL", "bid": 6.80, "ask": 7.00, "delta": 0.52, "gamma": 0.025, "theta": -0.08, "open_interest": 28000, "volume": 8200, "iv": 34.0, "dte": 35},
        {"symbol": "AAPL  261016C00230000", "strike": 230.0, "type": "CALL", "bid": 2.10, "ask": 2.20, "delta": 0.18, "gamma": 0.018, "theta": -0.06, "open_interest": 45000, "volume": 14000, "iv": 33.5, "dte": 35},
        {"symbol": "AAPL  261016C00235000", "strike": 235.0, "type": "CALL", "bid": 0.90, "ask": 1.00, "delta": 0.09, "gamma": 0.010, "theta": -0.04, "open_interest": 32000, "volume": 9500, "iv": 33.0, "dte": 35},
        {"symbol": "AAPL  261016P00220000", "strike": 220.0, "type": "PUT", "bid": 6.50, "ask": 6.70, "delta": -0.48, "gamma": 0.024, "theta": -0.08, "open_interest": 26000, "volume": 7900, "iv": 34.2, "dte": 35},
        {"symbol": "AAPL  261016P00210000", "strike": 210.0, "type": "PUT", "bid": 2.20, "ask": 2.35, "delta": -0.18, "gamma": 0.017, "theta": -0.06, "open_interest": 52000, "volume": 16500, "iv": 34.5, "dte": 35},
        {"symbol": "AAPL  261016P00205000", "strike": 205.0, "type": "PUT", "bid": 1.05, "ask": 1.15, "delta": -0.10, "gamma": 0.011, "theta": -0.04, "open_interest": 38000, "volume": 11000, "iv": 35.0, "dte": 35}
    ],
    "2026-11-20": [
        {"symbol": "AAPL  261120C00220000", "strike": 220.0, "type": "CALL", "bid": 9.50, "ask": 9.80, "delta": 0.53, "gamma": 0.018, "theta": -0.06, "open_interest": 19000, "volume": 4200, "iv": 36.0, "dte": 70}
    ]
}

aapl_data = {
    "symbol": "AAPL",
    "spot_price": aapl_spot,
    "iv_rank": 62.0,
    "iv_percentile": 65.0,
    "daily_closes": aapl_closes,
    "event_in_horizon": False,  # Sem eventos binários no horizonte
    "chains": aapl_chains,
    "timestamp": "2026-09-21T10:30:00Z"
}

with open(fixtures_dir / "AAPL.json", "w", encoding="utf-8") as f:
    json.dump(aapl_data, f, indent=2)

# 3. QQQ: Bearish, Low IV Rank (35.0), Event = False (Ideal Bear Put Spread)
qqq_closes = []
price = 520.0
for i in range(220):
    delta = -0.5 if i % 2 == 0 else 0.2
    price += delta
    qqq_closes.append(round(price, 2))

qqq_spot = round(price - 1.0, 2)  # ~486

qqq_chains = {
    "2026-10-16": [
        {"symbol": "QQQ   261016P00485000", "strike": 485.0, "type": "PUT", "bid": 10.50, "ask": 10.80, "delta": -0.50, "gamma": 0.015, "theta": -0.09, "open_interest": 29000, "volume": 8400, "iv": 31.0, "dte": 35},
        {"symbol": "QQQ   261016P00470000", "strike": 470.0, "type": "PUT", "bid": 4.10, "ask": 4.30, "delta": -0.25, "gamma": 0.012, "theta": -0.07, "open_interest": 38000, "volume": 12100, "iv": 31.5, "dte": 35},
        {"symbol": "QQQ   261016C00485000", "strike": 485.0, "type": "CALL", "bid": 10.20, "ask": 10.50, "delta": 0.50, "gamma": 0.015, "theta": -0.09, "open_interest": 27000, "volume": 7600, "iv": 30.5, "dte": 35},
        {"symbol": "QQQ   261016C00500000", "strike": 500.0, "type": "CALL", "bid": 3.60, "ask": 3.80, "delta": 0.24, "gamma": 0.011, "theta": -0.06, "open_interest": 34000, "volume": 9200, "iv": 30.0, "dte": 35}
    ],
    "2026-11-20": [
        {"symbol": "QQQ   261120P00485000", "strike": 485.0, "type": "PUT", "bid": 14.80, "ask": 15.20, "delta": -0.49, "gamma": 0.011, "theta": -0.07, "open_interest": 17500, "volume": 3800, "iv": 32.0, "dte": 70}
    ]
}

qqq_data = {
    "symbol": "QQQ",
    "spot_price": qqq_spot,
    "iv_rank": 35.0,
    "iv_percentile": 38.0,
    "daily_closes": qqq_closes,
    "event_in_horizon": False,
    "chains": qqq_chains,
    "timestamp": "2026-09-21T10:30:00Z"
}

with open(fixtures_dir / "QQQ.json", "w", encoding="utf-8") as f:
    json.dump(qqq_data, f, indent=2)

print("Fixtures geradas com sucesso em:", fixtures_dir)
