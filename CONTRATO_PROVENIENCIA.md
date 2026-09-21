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
| **IV Rank** | `MEDIDO` | `GET /market-metrics` (`implied-volatility-index-rank`) | Campo nulo ou ausente no retorno |
| **IV Percentile** | `MEDIDO` | `GET /market-metrics` (`implied-volatility-index-percentile`) | Campo nulo ou ausente no retorno |
| **Delta da Opção** | `MEDIDO` | DXLink `Greeks` / Option Chains | Campo grega delta ausente ou nulo |
| **Bid da Opção** | `MEDIDO` | DXLink `Quote` / Option Chains | Bid ausente, nulo ou <= 0 em mercado aberto |
| **Ask da Opção** | `MEDIDO` | DXLink `Quote` / Option Chains | Ask ausente, nulo ou <= 0 |
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
3. **Renderização Única**: Nenhuma formatação monetária ou numérica direta (`.toFixed()`, `R$`, `$`, etc.) pode existir fora do componente estrutural `DataValue`. Se o dado for `INDISPONIVEL`, a renderização será impreterivelmente o badge `"N/D"`.

---

## 5. Auditoria e Gate Automatizado

O gate de CI e o hook de pre-commit realizam três verificações independentes:
1. **Typecheck Estático**: Verificação de tipos estritos impedindo a passagem de tipos primitivos sem o invólucro `DataValue`.
2. **Linter de Proveniência (AST)**: Varre o código procurando por números formatados ou strings formatadas fora do componente `DataValue`.
3. **Testes Unitários de Proveniência**: Bateria de testes verificando a regra de contágio, o bloqueio a dados parciais e a rejeição de `ESTIMADO`.

Qualquer falha em qualquer uma das três verificações aborta imediatamente o commit e o processo de entrega.
