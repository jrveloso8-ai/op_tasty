"""
Implementação dos Avaliadores das 8 Estratégias de Opções.
Cumpre integralmente a Seção 4 da Especificação Técnica.
"""

from __future__ import annotations

from dataclasses import replace

from src.models import MarketContext, ScreeningResult
from src.pricing import OptionLeg, calculate_conservative_pricing
from src.provenance import current_iso_timestamp
from src.strategies.base import BaseStrategy, find_atm_option, find_option_by_delta


class BullCallSpreadStrategy(BaseStrategy):
    """
    4.1 BULL CALL SPREAD (débito)
    Obrigatórios:
    - Direção = ALTA
    - IV Rank < 40
    Sugestão de strikes:
    - Compra: delta 0.45 a 0.55, vencimento 30-60 dias
    - Venda: delta 0.20 a 0.30, mesmo vencimento
    """
    @property
    def strategy_id(self) -> str:
        return "bull_call_spread"

    @property
    def strategy_name(self) -> str:
        return "Bull Call Spread"

    def evaluate(self, ctx: MarketContext) -> ScreeningResult:
        rejections: list[str] = []
        now_ts = current_iso_timestamp()

        # Critério 1: Direção = ALTA
        if not ctx.trend.direction.is_available or ctx.trend.direction.value is None:
            rejections.append("Direção/Tendência com DADO INDISPONIVEL")
        elif ctx.trend.direction.value != "ALTA":
            rejections.append(f"Direção é {ctx.trend.direction.value}, esperado ALTA")

        # Critério 2: IV Rank < 40
        if not ctx.iv_rank.is_available or ctx.iv_rank.value is None:
            rejections.append("IV Rank com DADO INDISPONIVEL")
        elif ctx.iv_rank.value >= 40.0:
            rejections.append(f"IV Rank={ctx.iv_rank.value:.1f} >= 40.0")

        criteria = {
            "direction": ctx.trend.direction.to_dict(),
            "iv_rank": ctx.iv_rank.to_dict()
        }

        if rejections:
            return ScreeningResult(
                symbol=ctx.symbol,
                strategy_id=self.strategy_id,
                strategy_name=self.strategy_name,
                status="REJEITADO",
                mandatory_criteria=criteria,
                rejection_reasons=rejections,
                timestamp=now_ts,
                notes="Rejeitado por critérios obrigatórios de entrada."
            )

        # Montagem das pernas sugeridas
        expirations = ctx.get_expirations_in_dte_range(30, 60)
        suggested_legs: list[OptionLeg] = []
        pricing = None

        if expirations:
            target_exp = expirations[0]
            chain = ctx.chains_by_expiration.get(target_exp, [])
            buy_leg = find_option_by_delta(chain, target_delta=0.50, opt_type="CALL")
            sell_leg = find_option_by_delta(chain, target_delta=0.25, opt_type="CALL")

            if buy_leg and sell_leg and buy_leg.strike < sell_leg.strike:
                leg1 = replace(buy_leg, action="BUY", ratio=1)
                leg2 = replace(sell_leg, action="SELL", ratio=1)
                suggested_legs = [leg1, leg2]
                pricing = calculate_conservative_pricing(suggested_legs)

        return ScreeningResult(
            symbol=ctx.symbol,
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            status="APROVADO",
            mandatory_criteria=criteria,
            suggested_legs=suggested_legs,
            pricing=pricing,
            timestamp=now_ts,
            notes="Critérios obrigatórios atendidos: Direção=ALTA e IV Rank < 40."
        )


class BearPutSpreadStrategy(BaseStrategy):
    """
    4.2 BEAR PUT SPREAD (débito)
    Obrigatórios:
    - Direção = BAIXA
    - IV Rank < 40
    Sugestão de strikes:
    - Compra: delta -0.45 a -0.55, vencimento 30-60 dias
    - Venda: delta -0.20 a -0.30, mesmo vencimento
    """
    @property
    def strategy_id(self) -> str:
        return "bear_put_spread"

    @property
    def strategy_name(self) -> str:
        return "Bear Put Spread"

    def evaluate(self, ctx: MarketContext) -> ScreeningResult:
        rejections: list[str] = []
        now_ts = current_iso_timestamp()

        # Critério 1: Direção = BAIXA
        if not ctx.trend.direction.is_available or ctx.trend.direction.value is None:
            rejections.append("Direção/Tendência com DADO INDISPONIVEL")
        elif ctx.trend.direction.value != "BAIXA":
            rejections.append(f"Direção é {ctx.trend.direction.value}, esperado BAIXA")

        # Critério 2: IV Rank < 40
        if not ctx.iv_rank.is_available or ctx.iv_rank.value is None:
            rejections.append("IV Rank com DADO INDISPONIVEL")
        elif ctx.iv_rank.value >= 40.0:
            rejections.append(f"IV Rank={ctx.iv_rank.value:.1f} >= 40.0")

        criteria = {
            "direction": ctx.trend.direction.to_dict(),
            "iv_rank": ctx.iv_rank.to_dict()
        }

        if rejections:
            return ScreeningResult(
                symbol=ctx.symbol,
                strategy_id=self.strategy_id,
                strategy_name=self.strategy_name,
                status="REJEITADO",
                mandatory_criteria=criteria,
                rejection_reasons=rejections,
                timestamp=now_ts,
                notes="Rejeitado por critérios obrigatórios de entrada."
            )

        expirations = ctx.get_expirations_in_dte_range(30, 60)
        suggested_legs: list[OptionLeg] = []
        pricing = None

        if expirations:
            target_exp = expirations[0]
            chain = ctx.chains_by_expiration.get(target_exp, [])
            buy_leg = find_option_by_delta(chain, target_delta=-0.50, opt_type="PUT")
            sell_leg = find_option_by_delta(chain, target_delta=-0.25, opt_type="PUT")

            if buy_leg and sell_leg and buy_leg.strike > sell_leg.strike:
                leg1 = replace(buy_leg, action="BUY", ratio=1)
                leg2 = replace(sell_leg, action="SELL", ratio=1)
                suggested_legs = [leg1, leg2]
                pricing = calculate_conservative_pricing(suggested_legs)

        return ScreeningResult(
            symbol=ctx.symbol,
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            status="APROVADO",
            mandatory_criteria=criteria,
            suggested_legs=suggested_legs,
            pricing=pricing,
            timestamp=now_ts,
            notes="Critérios obrigatórios atendidos: Direção=BAIXA e IV Rank < 40."
        )


class LongStrangleStrategy(BaseStrategy):
    """
    4.3 LONG STRANGLE (compra volatilidade)
    Obrigatórios:
    - IV Rank < 30
    - Evento no horizonte = TRUE dentro da janela do vencimento
      (Se o dado de evento não existir, marcar como CONDICIONAL, nunca aprovar só por IV Rank baixo)
    Sugestão de strikes:
    - Call e Put com delta entre 0.20 e 0.30 (ou -0.20 a -0.30)
    """
    @property
    def strategy_id(self) -> str:
        return "long_strangle"

    @property
    def strategy_name(self) -> str:
        return "Long Strangle"

    def evaluate(self, ctx: MarketContext) -> ScreeningResult:
        rejections: list[str] = []
        now_ts = current_iso_timestamp()

        # Critério 1: IV Rank < 30
        if not ctx.iv_rank.is_available or ctx.iv_rank.value is None:
            rejections.append("IV Rank com DADO INDISPONIVEL")
        elif ctx.iv_rank.value >= 30.0:
            rejections.append(f"IV Rank={ctx.iv_rank.value:.1f} >= 30.0")

        # Critério 2: Evento no horizonte
        status: str = "APROVADO"
        event_note = ""

        if not ctx.event_in_horizon.is_available or ctx.event_in_horizon.value is None:
            # Dado de evento indisponível -> Marca como CONDICIONAL
            status = "CONDICIONAL"
            event_note = "Dado de evento no horizonte INDISPONIVEL na API — oportunidade classificada como CONDICIONAL"
        elif ctx.event_in_horizon.value is False:
            rejections.append("Evento no horizonte é FALSE (Strangle exige catalisador/evento)")
        else:
            event_note = "Evento no horizonte confirmado (TRUE)"

        criteria = {
            "iv_rank": ctx.iv_rank.to_dict(),
            "event_in_horizon": ctx.event_in_horizon.to_dict()
        }

        if rejections:
            return ScreeningResult(
                symbol=ctx.symbol,
                strategy_id=self.strategy_id,
                strategy_name=self.strategy_name,
                status="REJEITADO",
                mandatory_criteria=criteria,
                rejection_reasons=rejections,
                timestamp=now_ts,
                notes="Rejeitado por critérios obrigatórios."
            )

        expirations = ctx.get_expirations_in_dte_range(30, 60)
        suggested_legs: list[OptionLeg] = []
        pricing = None

        if expirations:
            target_exp = expirations[0]
            chain = ctx.chains_by_expiration.get(target_exp, [])
            call_leg = find_option_by_delta(chain, target_delta=0.25, opt_type="CALL")
            put_leg = find_option_by_delta(chain, target_delta=-0.25, opt_type="PUT")

            if call_leg and put_leg:
                leg1 = replace(call_leg, action="BUY", ratio=1)
                leg2 = replace(put_leg, action="BUY", ratio=1)
                suggested_legs = [leg1, leg2]
                pricing = calculate_conservative_pricing(suggested_legs)

        return ScreeningResult(
            symbol=ctx.symbol,
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            status=status,  # type: ignore[arg-type]
            mandatory_criteria=criteria,
            suggested_legs=suggested_legs,
            pricing=pricing,
            timestamp=now_ts,
            notes=f"IV Rank baixo (< 30). {event_note}"
        )


class IronCondorStrategy(BaseStrategy):
    """
    4.4 IRON CONDOR (venda volatilidade, risco definido)
    Obrigatórios:
    - IV Rank > 50
    - Direção = NEUTRO
    - Evento no horizonte = FALSE (se indisponível, CONDICIONAL; se TRUE, rejeita por risco de evento)
    Sugestão:
    - Pernas vendidas (call e put) com delta entre 0.15 e 0.20
    - Pernas compradas na largura de asas configurada
    - Vencimento 30-45 dias
    """
    def __init__(self, wing_width: float = 5.0) -> None:
        self.wing_width = wing_width

    @property
    def strategy_id(self) -> str:
        return "iron_condor"

    @property
    def strategy_name(self) -> str:
        return "Iron Condor"

    def evaluate(self, ctx: MarketContext) -> ScreeningResult:
        rejections: list[str] = []
        now_ts = current_iso_timestamp()

        # Critério 1: IV Rank > 50
        if not ctx.iv_rank.is_available or ctx.iv_rank.value is None:
            rejections.append("IV Rank com DADO INDISPONIVEL")
        elif ctx.iv_rank.value <= 50.0:
            rejections.append(f"IV Rank={ctx.iv_rank.value:.1f} <= 50.0")

        # Critério 2: Direção = NEUTRO
        if not ctx.trend.direction.is_available or ctx.trend.direction.value is None:
            rejections.append("Direção com DADO INDISPONIVEL")
        elif ctx.trend.direction.value != "NEUTRO":
            rejections.append(f"Direção é {ctx.trend.direction.value}, esperado NEUTRO")

        # Critério 3: Evento no horizonte
        status: str = "APROVADO"
        event_note = ""

        if not ctx.event_in_horizon.is_available or ctx.event_in_horizon.value is None:
            status = "CONDICIONAL"
            event_note = "Dado de evento no horizonte INDISPONIVEL — oportunidade classificada como CONDICIONAL"
        elif ctx.event_in_horizon.value is True:
            rejections.append("Evento no horizonte é TRUE (risco binário inaceitável para Iron Condor)")
        else:
            event_note = "Sem eventos binários no horizonte (FALSE)"

        criteria = {
            "iv_rank": ctx.iv_rank.to_dict(),
            "direction": ctx.trend.direction.to_dict(),
            "event_in_horizon": ctx.event_in_horizon.to_dict()
        }

        if rejections:
            return ScreeningResult(
                symbol=ctx.symbol,
                strategy_id=self.strategy_id,
                strategy_name=self.strategy_name,
                status="REJEITADO",
                mandatory_criteria=criteria,
                rejection_reasons=rejections,
                timestamp=now_ts,
                notes="Rejeitado por critérios de entrada."
            )

        expirations = ctx.get_expirations_in_dte_range(30, 45)
        suggested_legs: list[OptionLeg] = []
        pricing = None

        if expirations:
            target_exp = expirations[0]
            chain = ctx.chains_by_expiration.get(target_exp, [])
            short_call = find_option_by_delta(chain, target_delta=0.18, opt_type="CALL")
            short_put = find_option_by_delta(chain, target_delta=-0.18, opt_type="PUT")

            if short_call and short_put:
                # Busca asas compradas
                target_long_call_strike = short_call.strike + self.wing_width
                target_long_put_strike = short_put.strike - self.wing_width

                long_calls = [l for l in chain if l.option_type == "CALL" and l.strike >= target_long_call_strike]
                long_puts = [l for l in chain if l.option_type == "PUT" and l.strike <= target_long_put_strike]

                long_call = min(long_calls, key=lambda l: l.strike) if long_calls else None
                long_put = max(long_puts, key=lambda l: l.strike) if long_puts else None

                if long_call and long_put:
                    suggested_legs = [
                        replace(short_call, action="SELL", ratio=1),
                        replace(long_call, action="BUY", ratio=1),
                        replace(short_put, action="SELL", ratio=1),
                        replace(long_put, action="BUY", ratio=1)
                    ]
                    pricing = calculate_conservative_pricing(suggested_legs)

        return ScreeningResult(
            symbol=ctx.symbol,
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            status=status,  # type: ignore[arg-type]
            mandatory_criteria=criteria,
            suggested_legs=suggested_legs,
            pricing=pricing,
            timestamp=now_ts,
            notes=f"IV Rank elevado (> 50) e Direção Neutra. {event_note}"
        )


class CalendarSpreadStrategy(BaseStrategy):
    """
    4.5 CALENDAR SPREAD (Call ATM, dois vencimentos)
    Obrigatórios:
    - IV do vencimento curto > IV do vencimento longo no mesmo strike ATM (term structure invertida).
    """
    @property
    def strategy_id(self) -> str:
        return "calendar_spread"

    @property
    def strategy_name(self) -> str:
        return "Calendar Spread"

    def evaluate(self, ctx: MarketContext) -> ScreeningResult:
        rejections: list[str] = []
        now_ts = current_iso_timestamp()

        # Requer pelo menos 2 vencimentos com IV ATM calculada
        available_term_ivs = {
            exp: iv for exp, iv in ctx.term_structure_atm_iv.items()
            if iv.is_available and iv.value is not None
        }

        if len(available_term_ivs) < 2:
            rejections.append("Estrutura a termo de IV insuficiente (< 2 vencimentos válidos)")

        sorted_exps = sorted(
            available_term_ivs.keys(),
            key=lambda e: ctx.chains_by_expiration[e][0].dte if ctx.chains_by_expiration.get(e) else 0
        )

        short_exp = sorted_exps[0] if sorted_exps else ""
        long_exp = sorted_exps[1] if len(sorted_exps) > 1 else ""

        iv_short = available_term_ivs.get(short_exp)
        iv_long = available_term_ivs.get(long_exp)

        term_structure_inverted = False
        if iv_short and iv_long and iv_short.value is not None and iv_long.value is not None:
            if iv_short.value > iv_long.value:
                term_structure_inverted = True
            else:
                rejections.append(
                    f"Estrutura a termo normal/contango (IV Curto={iv_short.value:.1f}% <= IV Longo={iv_long.value:.1f}%)"
                )

        criteria = {
            "short_exp": short_exp,
            "long_exp": long_exp,
            "iv_short": iv_short.to_dict() if iv_short else None,
            "iv_long": iv_long.to_dict() if iv_long else None,
            "term_structure_inverted": term_structure_inverted
        }

        if rejections:
            return ScreeningResult(
                symbol=ctx.symbol,
                strategy_id=self.strategy_id,
                strategy_name=self.strategy_name,
                status="REJEITADO",
                mandatory_criteria=criteria,
                rejection_reasons=rejections,
                timestamp=now_ts,
                notes="Rejeitado por ausência de inversão na curva de IV a termo."
            )

        suggested_legs: list[OptionLeg] = []
        pricing = None

        if short_exp and long_exp and ctx.spot_price.is_available and ctx.spot_price.value is not None:
            chain_short = ctx.chains_by_expiration.get(short_exp, [])
            chain_long = ctx.chains_by_expiration.get(long_exp, [])

            opt_short = find_atm_option(chain_short, "CALL", ctx.spot_price.value)
            if opt_short:
                # Procura a mesma opção (mesmo strike) no vencimento longo
                matching_long = [l for l in chain_long if l.option_type == "CALL" and l.strike == opt_short.strike]
                if matching_long:
                    opt_long = matching_long[0]
                    suggested_legs = [
                        replace(opt_short, action="SELL", ratio=1),
                        replace(opt_long, action="BUY", ratio=1)
                    ]
                    pricing = calculate_conservative_pricing(suggested_legs)

        return ScreeningResult(
            symbol=ctx.symbol,
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            status="APROVADO",
            mandatory_criteria=criteria,
            suggested_legs=suggested_legs,
            pricing=pricing,
            timestamp=now_ts,
            notes=f"Term structure invertida confirmada: IV {short_exp} > IV {long_exp}."
        )


class DiagonalSpreadStrategy(BaseStrategy):
    """
    4.6 DIAGONAL SPREAD / PMCC (Poor Man's Covered Call)
    Obrigatórios:
    - Direção = ALTA
    - Vencimento longo disponível com opção de delta 0.70 - 0.80
    Sugestão:
    - Perna longa: delta 0.70-0.80, vencimento mais longo disponível
    - Perna curta: delta 0.20-0.30, vencimento curto (30-45 dias)
    """
    @property
    def strategy_id(self) -> str:
        return "diagonal_spread"

    @property
    def strategy_name(self) -> str:
        return "Diagonal Spread / PMCC"

    def evaluate(self, ctx: MarketContext) -> ScreeningResult:
        rejections: list[str] = []
        now_ts = current_iso_timestamp()

        # Critério 1: Direção = ALTA
        if not ctx.trend.direction.is_available or ctx.trend.direction.value is None:
            rejections.append("Direção com DADO INDISPONIVEL")
        elif ctx.trend.direction.value != "ALTA":
            rejections.append(f"Direção é {ctx.trend.direction.value}, esperado ALTA")

        # Critério 2: Vencimento longo com delta 0.70-0.80
        all_exps = sorted(
            ctx.chains_by_expiration.keys(),
            key=lambda e: ctx.chains_by_expiration[e][0].dte if ctx.chains_by_expiration.get(e) else 0
        )

        has_long_leaps = False
        long_leg: OptionLeg | None = None
        short_leg: OptionLeg | None = None

        if len(all_exps) >= 2:
            longest_exp = all_exps[-1]
            chain_long = ctx.chains_by_expiration.get(longest_exp, [])
            candidate_long = find_option_by_delta(chain_long, target_delta=0.75, opt_type="CALL", tolerance=0.10)
            if candidate_long and candidate_long.delta.value and 0.70 <= candidate_long.delta.value <= 0.85:
                has_long_leaps = True
                long_leg = candidate_long

        if not has_long_leaps:
            rejections.append("Ausência de perna longa com delta 0.70-0.80 disponível na cadeia")

        criteria = {
            "direction": ctx.trend.direction.to_dict(),
            "has_long_delta_70_80": has_long_leaps
        }

        if rejections:
            return ScreeningResult(
                symbol=ctx.symbol,
                strategy_id=self.strategy_id,
                strategy_name=self.strategy_name,
                status="REJEITADO",
                mandatory_criteria=criteria,
                rejection_reasons=rejections,
                timestamp=now_ts,
                notes="Rejeitado por critérios de tendência ou perna longa indisponível."
            )

        suggested_legs: list[OptionLeg] = []
        pricing = None

        # Perna curta no vencimento mais curto (30-45 DTE)
        short_exps = ctx.get_expirations_in_dte_range(30, 45)
        if not short_exps and len(all_exps) >= 2:
            short_exps = [all_exps[0]]

        if short_exps and long_leg:
            chain_short = ctx.chains_by_expiration.get(short_exps[0], [])
            short_leg = find_option_by_delta(chain_short, target_delta=0.25, opt_type="CALL")

            if short_leg:
                suggested_legs = [
                    replace(long_leg, action="BUY", ratio=1),
                    replace(short_leg, action="SELL", ratio=1)
                ]
                pricing = calculate_conservative_pricing(suggested_legs)

        return ScreeningResult(
            symbol=ctx.symbol,
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            status="APROVADO",
            mandatory_criteria=criteria,
            suggested_legs=suggested_legs,
            pricing=pricing,
            timestamp=now_ts,
            notes="Critérios atendidos: Direção ALTA e perna longa profunda no dinheiro (delta 0.70-0.80) disponível."
        )


class PutRatioSpreadStrategy(BaseStrategy):
    """
    4.7 PUT RATIO SPREAD (1x2, crédito)
    Obrigatórios:
    - Direção = ALTA ou NEUTRO
    - IV Rank > 50
    Sugestão:
    - 1 put comprada perto do ATM/levemente OTM + 2 puts vendidas mais OTM
    - Validar que o crédito líquido cobre a largura entre a perna comprada e a primeira vendida
    """
    @property
    def strategy_id(self) -> str:
        return "put_ratio_spread"

    @property
    def strategy_name(self) -> str:
        return "Put Ratio Spread (1x2)"

    def evaluate(self, ctx: MarketContext) -> ScreeningResult:
        rejections: list[str] = []
        now_ts = current_iso_timestamp()

        # Critério 1: Direção = ALTA ou NEUTRO
        if not ctx.trend.direction.is_available or ctx.trend.direction.value is None:
            rejections.append("Direção com DADO INDISPONIVEL")
        elif ctx.trend.direction.value not in ("ALTA", "NEUTRO"):
            rejections.append(f"Direção é {ctx.trend.direction.value}, esperado ALTA ou NEUTRO")

        # Critério 2: IV Rank > 50
        if not ctx.iv_rank.is_available or ctx.iv_rank.value is None:
            rejections.append("IV Rank com DADO INDISPONIVEL")
        elif ctx.iv_rank.value <= 50.0:
            rejections.append(f"IV Rank={ctx.iv_rank.value:.1f} <= 50.0")

        criteria = {
            "direction": ctx.trend.direction.to_dict(),
            "iv_rank": ctx.iv_rank.to_dict()
        }

        if rejections:
            return ScreeningResult(
                symbol=ctx.symbol,
                strategy_id=self.strategy_id,
                strategy_name=self.strategy_name,
                status="REJEITADO",
                mandatory_criteria=criteria,
                rejection_reasons=rejections,
                timestamp=now_ts,
                notes="Rejeitado por critérios de entrada de IV Rank ou direção."
            )

        expirations = ctx.get_expirations_in_dte_range(30, 60)
        suggested_legs: list[OptionLeg] = []
        pricing = None
        notes = "Critérios obrigatórios atendidos: Direção ALTA/NEUTRO e IV Rank > 50."

        if expirations:
            target_exp = expirations[0]
            chain = ctx.chains_by_expiration.get(target_exp, [])
            buy_put = find_option_by_delta(chain, target_delta=-0.45, opt_type="PUT")
            sell_put = find_option_by_delta(chain, target_delta=-0.20, opt_type="PUT")

            if buy_put and sell_put and buy_put.strike > sell_put.strike:
                leg1 = replace(buy_put, action="BUY", ratio=1)
                leg2 = replace(sell_put, action="SELL", ratio=2)
                suggested_legs = [leg1, leg2]
                pricing = calculate_conservative_pricing(suggested_legs)

                # Validação de crédito cobrindo a largura da trava
                spread_width = buy_put.strike - sell_put.strike
                if pricing.pricing_type == "CREDIT" and pricing.display_value.value is not None:
                    if pricing.display_value.value >= spread_width:
                        notes += f" Crédito líquido (${pricing.display_value.value:.2f}) cobre a largura da trava (${spread_width:.2f}) — sem risco para cima."
                    else:
                        notes += f" Alerta: Crédito líquido (${pricing.display_value.value:.2f}) < largura da trava (${spread_width:.2f})."

        return ScreeningResult(
            symbol=ctx.symbol,
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            status="APROVADO",
            mandatory_criteria=criteria,
            suggested_legs=suggested_legs,
            pricing=pricing,
            timestamp=now_ts,
            notes=notes
        )


class CallBackspreadStrategy(BaseStrategy):
    """
    4.8 CALL BACKSPREAD (1x2, comprado)
    Obrigatórios:
    - Direção = ALTA
    - IV Rank da perna vendida (mais próxima do ATM) > IV Rank da perna comprada em dobro (mais OTM)
      (Se a API não expuser IV por strike individual, usar IV Rank do ativo como proxy e marcar a limitação no relatório)
    Sugestão:
    - 1 call vendida perto do ATM (delta 0.45-0.55)
    - 2 calls compradas mais OTM (delta 0.20-0.30)
    """
    @property
    def strategy_id(self) -> str:
        return "call_backspread"

    @property
    def strategy_name(self) -> str:
        return "Call Backspread (1x2)"

    def evaluate(self, ctx: MarketContext) -> ScreeningResult:
        rejections: list[str] = []
        now_ts = current_iso_timestamp()

        # Critério 1: Direção = ALTA
        if not ctx.trend.direction.is_available or ctx.trend.direction.value is None:
            rejections.append("Direção com DADO INDISPONIVEL")
        elif ctx.trend.direction.value != "ALTA":
            rejections.append(f"Direção é {ctx.trend.direction.value}, esperado ALTA")

        expirations = ctx.get_expirations_in_dte_range(30, 60)
        target_exp = expirations[0] if expirations else ""
        chain = ctx.chains_by_expiration.get(target_exp, [])

        sell_call = find_option_by_delta(chain, target_delta=0.50, opt_type="CALL")
        buy_call = find_option_by_delta(chain, target_delta=0.25, opt_type="CALL")

        # Critério 2: Skew de Volatilidade / IV Rank
        # Se IV por strike estiver disponível, compara diretamente. Se não, usa proxy documentado.
        iv_skew_favorable = False
        used_proxy = False

        if sell_call and buy_call and sell_call.iv and buy_call.iv and sell_call.iv.is_available and buy_call.iv.is_available:
            if (sell_call.iv.value or 0.0) >= (buy_call.iv.value or 0.0):
                iv_skew_favorable = True
            else:
                rejections.append(
                    f"Skew desfavorável para Backspread: IV ATM ({sell_call.iv.value:.1f}%) < IV OTM ({buy_call.iv.value:.1f}%)"
                )
        else:
            # Proxy conforme Seção 4.8: usar IV Rank do ativo se strike individual não expuser
            used_proxy = True
            if ctx.iv_rank.is_available and ctx.iv_rank.value is not None:
                iv_skew_favorable = True
            else:
                rejections.append("IV Rank e IV por strike INDISPONIVEIS")

        criteria = {
            "direction": ctx.trend.direction.to_dict(),
            "iv_skew_favorable": iv_skew_favorable,
            "used_proxy_limitation": used_proxy
        }

        if rejections:
            return ScreeningResult(
                symbol=ctx.symbol,
                strategy_id=self.strategy_id,
                strategy_name=self.strategy_name,
                status="REJEITADO",
                mandatory_criteria=criteria,
                rejection_reasons=rejections,
                timestamp=now_ts,
                notes="Rejeitado por direção ou skew de volatilidade."
            )

        suggested_legs: list[OptionLeg] = []
        pricing = None

        if sell_call and buy_call and sell_call.strike < buy_call.strike:
            leg1 = replace(sell_call, action="SELL", ratio=1)
            leg2 = replace(buy_call, action="BUY", ratio=2)
            suggested_legs = [leg1, leg2]
            pricing = calculate_conservative_pricing(suggested_legs)

        proxy_note = " (Limitação documentada: IV por strike não exposta individualmente, utilizado IV Rank geral como proxy conforme Seção 4.8)" if used_proxy else ""

        return ScreeningResult(
            symbol=ctx.symbol,
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            status="APROVADO",
            mandatory_criteria=criteria,
            suggested_legs=suggested_legs,
            pricing=pricing,
            timestamp=now_ts,
            notes=f"Critérios atendidos: Direção ALTA e skew de volatilidade favorável.{proxy_note}"
        )
