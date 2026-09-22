# Contrato de Proveniência de Dados — Screener Tastytrade

**Versão:** 1.0.0  
**Data:** 2026-09-21  
**Status:** Vigente e Inegociável  
**Escopo:** Screener de 8 Estratégias de Opções via API Tastytrade

---

## 1. Princípio Fundamental

Este sistema informa decisões de operações com **dinheiro real** no mercado de opções americano. Qualquer decisão baseada em números fabricados, extrapolados, desatualizados ou omitidos coloca capital em risco real e inaceitável.

Portanto:
1. **Zero fabricação**: É terminantemente proibido fabricar, estimar ou usar fallback/proxy silencioso para qualquer dado de mercado.
2. **Rastreabilidade total**: Todo e qualquer número manipulado ou exibido deve carregar consigo a origem (`source`), o endpoint de chamada (`endpoint`) e o timestamp exato (`timestamp` ISO-8601 UTC) de sua coleta ou cálculo.
3. **Falha explícita**: Se uma fonte de dados falhar ou retornar nulo/vazio/zero (onde zero indica ausência de cotação), o dado deve ser classificado explicitamente como `INDISPONIVEL`.
4. **Regra de Contágio**: Qualquer valor `DERIVADO` que dependa direta ou indiretamente de um insumo `INDISPONIVEL` torna-se imediata e obrigatoriamente `INDISPONIVEL`. É proibido calcular médias móveis, RSI ou custos de estruturas com dados incompletos.

---

## 2. Taxonomia de Proveniência

| Classificação | Definição | Exemplo de Aplicação | Regra de Aceite |
| :--- | :--- | :--- | :--- |
| **`MEDIDO`** | Dado obtido diretamente da API da Tastytrade ou DXLink sem transformações matemáticas ou suposições. | Preço spot, IV Rank da API, Bid/Ask de opções, Delta, Gamma, Theta, Open Interest, Volume, Candles de fechamento. | Aceito apenas se retornado com código 200 e payload válido. |
| **`DERIVADO`** | Dado calculado exclusivamente a partir de insumos `MEDIDO` através de fórmulas determinísticas e auditáveis. | MM20, MM50, MM200, RSI(14), Custo Máximo a Pagar, Valor Mínimo a Receber, Spread de IV da curva a termo. | Aceito apenas se 100% dos insumos necessários forem `MEDIDO`. Se 1 único insumo for `INDISPONIVEL`, o derivado vira `INDISPONIVEL`. |
| **`ESTIMADO`** | Qualquer valor aproximado, interpolado, suavizado ou substituído por proxy heurístico. | **PROIBIDO**. Não existe neste sistema. | Se o tipo `ESTIMADO` for instanciado ou detectado, o sistema rejeita a operação com erro fatal. |
| **`INDISPONIVEL`** | Fonte consultada, mas dado inexistente, falho, nulo ou incompleto. | Faltam candles para MM200, perna da opção sem Bid/Ask na chain, endpoint de eventos não exposto. | Renderizado obrigatoriamente como `"N/D"` com destaque visual. Nunca ocultado, nunca exibido como `0` ou `0.00`. |

---

## 3. Matriz de Dados do Screener

| Variável | Classificação | Origem / Endpoint | Condição de Indisponibilidade |
| :--- | :--- | :--- | :--- |
| **Preço Spot / Mark** | `MEDIDO` | `GET /market-metrics` ou DXLink `Quote` | Ausência no retorno da API ou valor <= 0 |
| **IV Rank** | `MEDIDO` | `GET /market-metrics` (`implied-volatility-index-rank` * 100) | Campo nulo ou ausente no retorno (ver Nota 1) |
| **IV Percentile** | `MEDIDO` | `GET /market-metrics` (`implied-volatility-index-percentile` * 100) | Campo nulo ou ausente no retorno |
| **Delta da Opção** | `MEDIDO` | DXLink `Greeks` / Option Chains | Campo grega delta ausente ou nulo |
| **Bid da Opção** | `MEDIDO` | DXLink `Quote` / Option Chains | Bid ausente, nulo ou <= 0 em mercado aberto |
| **Ask da Opção** | `MEDIDO` | DXLink `Quote` / Option Chains | Ask ausente, nulo ou <= 0 |
| **Preço Médio (Mid) da Opção** | `DERIVADO` | `calc:mid_price` ((Bid + Ask) / 2) | Se Bid ou Ask for `INDISPONIVEL` ou <= 0 |
| **Open Interest (OI)** | `MEDIDO` | `GET /option-chains/{symbol}/nested` | Campo `open-interest` ausente ou nulo |
| **Volume da Opção** | `MEDIDO` | `GET /option-chains/{symbol}/nested` | Campo volume ausente ou nulo |
| **Candles Históricos (OHLC)** | `MEDIDO` | DXLink Candle Feed (`Candle`) | Série diária com menos de 200 candles ou gap de pregão |
| **MM20, MM50, MM200** | `DERIVADO` | Média aritmética sobre fechamentos reais medidos | Menos de 200 candles medidos válidos |
| **RSI(14)** | `DERIVADO` | Método de Wilder sobre variações de fechamentos | Histórico de candles < 15 barras válidas |
| **Direção (Tendência)** | `DERIVADO` | Comparação MM20/MM50/MM200 + filtro RSI(14) | Se MM20, MM50, MM200 ou RSI for `INDISPONIVEL` |
| **Custo Máximo a Pagar** | `DERIVADO` | $\sum \text{Ask}_{\text{compradas}} - \sum \text{Bid}_{\text{vendidas}}$ (saldo < 0) | Se qualquer Ask ou Bid de perna da estrutura for `INDISPONIVEL` |
| **Valor Mínimo a Receber** | `DERIVADO` | $\sum \text{Bid}_{\text{vendidas}} - \sum \text{Ask}_{\text{compradas}}$ (saldo > 0) | Se qualquer Ask ou Bid de perna da estrutura for `INDISPONIVEL` |
| **IV Curva a Termo (Curto vs Longo)**| `DERIVADO` | Média ponderada da IV das opções ATM nos vencimentos curto e longo | Se strikes ATM não possuírem IV medida |
| **Evento no Horizonte (Earnings)** | `MEDIDO` / `INDISPONIVEL` | Endpoint de Earnings/Eventos da Tastytrade | Endpoint não exposto ou calendário não fornecido pela API |
| **Preço de Liquidação da Posição** | `DERIVADO` | $\sum \text{Bid}_{\text{compradas}} - \sum \text{Ask}_{\text{vendidas}}$ | Se qualquer Bid ou Ask de perna da posição for `INDISPONIVEL` |
| **P&L Não Realizado / Realizado** | `DERIVADO` | $\text{Liquidação} - \text{Entrada}$ (débito) ou $\text{Crédito} + \text{Liquidação}$ | Se preço de liquidação ou entrada for `INDISPONIVEL` |
| **Sinal de Gestão (MANTER / STOPAR / REALIZAR_GAIN)** | `DERIVADO` | Avaliação determinística de P&L % vs metas e DTE | Se P&L for `INDISPONIVEL`, sinal vira obrigatoriamente `INDISPONIVEL` |

> **Nota 1 (Fidelidade Estrita ao IV Rank da Fonte e Anomalias Verificadas):** O valor de IV Rank é capturado diretamente do campo `implied-volatility-index-rank` retornado pela API da Tastytrade (`GET /market-metrics`). Em coletas ao vivo consecutivas, verificou-se empiricamente que a corretora emite valores ligeiramente negativos para ativos específicos (ex: NVDA em -0.21% e -0.95%; ONDS em -1.37% e -1.83%). Em observância estrita ao Princípio de Zero Fabricação, o sistema não presume nem inventa causas matemáticas ou de mercado não confirmadas oficialmente pela corretora, e preserva o dado cru como `MEDIDO` sem trucagem ou clamping sintético. Na interface, esses casos recebem sinalização visual de auditoria via badge animado âmbar `⚠ FORA DA FAIXA` (classe CSS `.iv-anomaly-badge`), renderizado automaticamente por `renderDataValue()` sempre que `options.isIvRank === true` e o valor estiver fora da faixa canônica 0–100%. O tooltip do badge esclarece que o valor foi emitido diretamente pela corretora e preservado sem clamping. Implementação: `scripts/build_ui.py`, função `renderDataValue`, opção `isIvRank`.

---

## 4. Cerca Estrutural e Garantia em Nível de Tipagem

Todo e qualquer valor numérico ou categórico trafegado ou renderizado no sistema deve estar envelopado no container estrutural `DataValue`:

```typescript
// Contrato de Tipo Estrutural (TypeScript / Python Dataclass)
type ProvenanceType = "MEDIDO" | "DERIVADO" | "INDISPONIVEL";

interface DataValue<T> {
  readonly value: T | null;
  readonly provenance: ProvenanceType;
  readonly source: string;     // Ex: "tastytrade:market-metrics", "calc:mm200"
  readonly endpoint: string;   // Ex: "/market-metrics?symbols=SPY"
  readonly timestamp: string;  // Ex: "2026-09-21T10:45:00.000Z"
}
```

### Regras da Cerca:
1. **Construtores Estritos**: Qualquer tentativa de instanciar `DataValue` com `provenance === "ESTIMADO"` lança exceção fatal (`ValueError`).
2. **Propagação de Contágio**: Funções de cálculo derivado recebem instâncias de `DataValue` e verificam antes de operar:
   ```python
   def derive_spread(leg1: DataValue[float], leg2: DataValue[float]) -> DataValue[float]:
       if leg1.provenance == "INDISPONIVEL" or leg2.provenance == "INDISPONIVEL" or leg1.value is None or leg2.value is None:
           return DataValue(
               value=None,
               provenance="INDISPONIVEL",
               source=f"calc:spread({leg1.source},{leg2.source})",
               endpoint=f"{leg1.endpoint}|{leg2.endpoint}",
               timestamp=max(leg1.timestamp, leg2.timestamp)
           )
   ```
3. **Renderização Única**: Nenhuma formatação monetária ou numérica direta (`.toFixed()`, `R$`, `$`, etc.) de dados de mercado pode existir fora do componente estrutural `DataValue`. Se o dado for `INDISPONIVEL`, a renderização será impreterivelmente o badge `"N/D"`.
4. **Especificações Contratuais Fixas**: Parâmetros definidores do contrato de opção (como strike price, tipo CALL/PUT e multiplicador de lote padrão 100) são especificações jurídicas estáticas do derivativo, não medições ou variáveis de mercado sujeitas a erro de amostragem. Todas as cotações, gregas, métricas calculadas e totais monetários (inclusive valor total por lote) submetem-se estritamente ao invólucro DataValue.

---

## 5. Auditoria e Gate Automatizado

O gate de CI e o hook de pre-commit realizam três verificações independentes:
1. **Typecheck Estático**: Verificação de tipos estritos impedindo a passagem de tipos primitivos sem o invólucro `DataValue`.
2. **Linter de Proveniência (AST)**: Varre o código procurando por números formatados ou strings formatadas fora do componente `DataValue`.
3. **Testes Unitários de Proveniência**: Bateria de testes verificando a regra de contágio, o bloqueio a dados parciais e a rejeição de `ESTIMADO`.

Qualquer falha em qualquer uma das três verificações aborta imediatamente o commit e o processo de entrega.

---

## 6. Protocolo de Gestão de Risco e Risco Definido para Ativos de Alto Valor (> US$ 100)

Em contas de custódia típicas de varejo (NetLiq entre US$ 2.000 e US$ 10.000), a exposição a ativos de alto valor nominal unitário (preço spot > US$ 100,00, tais como NVDA, AAPL, SPY, QQQ, MSFT) exige salvaguardas adicionais para evitar consumo excessivo de margem (BPR) e riscos de cauda catastróficos.

### Regras Mandatórias de Risco:
1. **Proibição de Pontas Vendidas a Descoberto em Ativos Caros:**
   - Estratégias que contenham pernas vendidas nuas (como a perna vendida excedente de um *1x2 Put Ratio Spread*) são **sumariamente rejeitadas** quando `spot_price > high_price_threshold` (padrão: US$ 100,00) com a regra habilitada.
   - O screener emite auditoria explícita com a razão de rejeição, orientando o operador a adotar estruturas de **risco estritamente definido** (ex: *Bear Put Spread* ou *Broken Wing Butterfly*).
2. **Teto de Largura de Asas (Wing Width Capping) em Iron Condors:**
   - Em ativos com spot > US$ 100,00, a largura entre pernas vendidas e compradas é limitada a no máximo US$ 5,00 (`max_wing_width_high_price: 5.0`), garantindo que o risco máximo e o BPR não ultrapassem US$ 500,00 por contrato.
3. **Alerta de Alocação de Capital em Estruturas de Débito Elevado:**
   - Estratégias como *Long Strangle* em ativos acima de US$ 100,00 recebem alerta de proveniência nas notas técnicas quando selecionadas, recomendando travas direcionais (*Bull Call* / *Bear Put Spread*) ou *Calendar Spreads* para limitar o desembolso inicial.
4. **Regime de Volatilidade e Vácuo de Catalisador (Caso NVDA):**
   - Ativos com IV Rank no piso histórico (< 20% ou 0%) encontram-se em "vácuo de catalisador". Vender volatilidade nessas condições possui assimetria desfavorável; o screener prioriza travas de débito e compra de volatilidade apenas quando há catalisador binário comprovado no horizonte (`event_in_horizon == TRUE`).

