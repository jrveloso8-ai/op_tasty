# Plano de Implementação: Screener de Opções B3 (Brapi API)

Adaptação da engine de screening de opções do projeto `Op_Tasty` para o mercado brasileiro de ações e opções (B3), integrando a API REST v2 da **brapi.dev**, mantendo as regras estritas de proveniência de dados, precificação conservadora e auditoria sem dados fabricados.

---

## 1. Visão Geral da Arquitetura

O projeto original (`Op_Tasty`) foi desenhado com desacoplamento estrito entre a **camada de mercado/coleta** (`tastytrade_client.py`) e a **camada de inteligência** (`models.py`, `pricing.py`, `indicators.py`, `strategies/`).

No novo projeto (`op_b3`), substituímos a camada Tastytrade pelo **`BrapiClient`**, mantendo os mesmos contratos de dados (`MarketContext`, `OptionLeg`, `DataValue`).

```
[ Brapi API v2 ]
  ├── /api/v2/stocks/historical  ──> Preço Spot + 200 Candles (MM20, MM50, MM200, RSI14, Volatilidade)
  ├── /api/v2/options/expirations──> Datas de Vencimento Disponíveis
  ├── /api/v2/options/chain      ──> Cadeia de Opções (Strikes, Bid, Ask, Volume, Open Interest)
  ├── /api/v2/options/analytics  ──> Gregas (Delta, Gamma, Theta, Vega) e IV por Série
  └── /api/v2/stocks/dividends   ──> Proventos (Data-Ex, Valor por Ação)
           │
           ▼
   [ src/brapi_client.py ] ──(Fallback auditado)──> [ fixtures/*.json ]
           │
           ▼ (produz MarketContext com DataValue auditável)
   [ src/indicators.py ] ──> Tendência (ALTA, BAIXA, NEUTRO) + Vol. Realizada
           │
           ▼
   [ src/strategies/ ] ──> Avaliação das 8 Estratégias + Venda Coberta (B3)
           │
           ▼
   [ src/pricing.py ] ──> Precificação Conservadora (Buy no Ask, Sell no Bid)
           │
           ▼
   [ index.html / json / csv ] ──> Dashboard Executivo em R$ (BRL)
```

---

## 2. Diferenças Estruturais: Tastytrade vs. Brapi (B3)

| Dimensão | Tastytrade (EUA) | Brapi / B3 (Brasil) | Adaptação no Código |
| :--- | :--- | :--- | :--- |
| **Padrão de Tickers** | `SPY`, `AAPL`, `MSFT` | `PETR4`, `VALE3`, `BOVA11` | Universo parametrizável no `config.yaml` com tickers B3. |
| **Séries de Opções** | Códigos OCC (ex: `SPY   240621C00500000`) | Letras de vencimento (ex: `PETRE370`, `PETRQ28`) | Mapeamento nativo da Brapi (`symbol`, `strike`, `side`, `optionStyle`). |
| **Estilo de Exercício** | Quase 100% Americano | Calls em geral Americanas, Puts em geral Europeias | Brapi já retorna `optionStyle: "american" \| "european"`. |
| **Momento dos Dados** | Streaming em tempo real (DXLink) | Fechamento diário (EOD, após as 21h) | Screener configurado para análise de fechamento (Swing Trade / D+1). |
| **Métricas de Volatilidade** | IV Rank e IV Percentile diretos | IV por série no `analytics` | Cálculo do IV ATM ponderado por proximidade do spot + estimativa de IV Rank baseada no histórico de IV/Vol Realizada. |
| **Moeda e Valores** | Dólares ($ / USD) | Reais (R$ / BRL) | Formatação de moeda no frontend e logs. |
| **Liquidez de Puts** | Alta e simétrica | Escassa fora de PETR4/VALE3/BOVA11 | A regra de contágio de indisponibilidade (`bid <= 0` ou `ask <= 0`) protegerá o usuário de opções sem livro aberto. |

---

## 3. Componentes e Alterações Propostas

### 3.1. Configuração e Variáveis de Ambiente
* **`.env`**:
  ```env
  BRAPI_TOKEN=seu_token_aqui
  ENVIRONMENT=production # ou testing/fixtures
  ```
* **`config.yaml`**:
  * Universo de ativos B3: `PETR4`, `VALE3`, `BOVA11`, `ITUB4`, `BBDC4`, `BBAS3`, `RENT3`, `PRIO3`, `SUZB3`.
  * Parâmetros de DTE (dias até vencimento): `dte_min: 15`, `dte_max: 45` (ciclos mensais da B3).
  * Limiares de gestão de risco em R$ (ex: ações acima de R$ 50,00).

### 3.2. Cliente de Dados da Brapi (`src/brapi_client.py`) [NOVO]
* **Autenticação**: Envio do header `Authorization: Bearer <BRAPI_TOKEN>`.
* **Rate Limiting e Resiliência**:
  * Exponential backoff para erros HTTP 429 (quota/concorrência) respeitando o cabeçalho `Retry-After`.
  * Timeout parametrizável (padrão: 15s).
* **Endpoints integrados**:
  1. `get_historical_candles(symbol, range="1y")`: Coleta 200+ candles diários para alimentação de `src/indicators.py` (cálculo de MM20, MM50, MM200, RSI 14 e Volatilidade Realizada de 20 dias).
  2. `get_expirations(symbol)`: Coleta datas de vencimento disponíveis via `/api/v2/options/expirations`.
  3. `get_option_chain(symbol, expiration_date)`: Coleta todas as séries via `/api/v2/options/chain` (strike, side, bid, ask, volume, openInterest, optionStyle).
  4. `get_option_analytics(symbol, expiration_date)`: Coleta gregas (delta, gamma, theta, vega) e IV via `/api/v2/options/analytics`.
  5. `get_dividends(symbol)`: Coleta eventos de proventos via `/api/v2/stocks/dividends`.
* **Cálculo da IV ATM Ponderada**:
  * Mantém a mesma fórmula de auditoria:
    $$\text{peso}_i = \frac{1}{|\text{strike}_i - \text{spot}| + 1.0}$$
    $$\text{IV}_{\text{ATM}} = \frac{\sum \text{peso}_i \cdot \text{IV}_i}{\sum \text{peso}_i}$$
* **Fallback para Fixtures**:
  * Se o token não for fornecido ou se o sistema rodar com flag `--offline`/em testes, lê dados gravados em `fixtures/brapi_{symbol}.json`, garantindo execução de testes sem consumo de chamadas na API.

### 3.3. Modelos de Dados e Precificação Conservadora
* **`src/models.py`**:
  * Preservação idêntica da estrutura `MarketContext`, `OptionLeg` e `ScreeningResult`.
  * Todos os campos continuam envelopados em `DataValue[T]` (com `value`, `is_available`, `source`, `endpoint`, `timestamp`), garantindo proveniência de ponta a ponta.
* **`src/pricing.py`**:
  * Permanece **100% idêntico**:
    * Perna Comprada $\rightarrow$ Usa **Ask** (preço conservador).
    * Perna Vendida $\rightarrow$ Usa **Bid** (preço conservador).
    * Regra de Contágio: Se qualquer perna tiver bid ou ask nulo, ausente ou $\le 0$, toda a estrutura recebe status `DADO INDISPONIVEL` (nunca usa mid-price como fallback).

### 3.4. Estratégias de Opções (`src/strategies/`)
* **As 8 Estratégias Mantidas**:
  1. Bull Call Spread (Trava de Alta com Call) - *Altamente líquida na B3*
  2. Bear Put Spread (Trava de Baixa com Put)
  3. Bull Put Spread (Trava de Alta com Put - Crédito)
  4. Bear Call Spread (Trava de Baixa com Call - Crédito)
  5. Iron Condor
  6. Long Calendar Spread (Trava de Linha)
  7. Long Diagonal Spread
  8. Ratio Spread (com trava de risco contra cauda)
* **Adição Recomendada para B3**:
  9. **Covered Call (Venda Coberta / Financiamento)**: A estratégia mais operada do mercado brasileiro, ideal para ativos em consolidação ou alta moderada com remuneração de carteira via prêmio de Call OTM.

### 3.5. Dashboard e Apresentação (`index.html` e `src/screener.py`)
* Atualização de símbolos monetários de `$` para `R$`.
* Exibição de estilo de opção: `[Americana]` ou `[Europeia]`.
* Suporte aos filtros por ticker da B3 (`PETR4`, `VALE3`, `BOVA11`, etc.).
* Geração dos artefatos: `screener_output.json` e `screener_output.csv`.

---

## 4. Plano de Verificação e Testes

### Testes Automatizados (Pytest)
1. **`test_brapi_client.py`**:
   * Validação de parsing dos schemas da Brapi v2 (`chain`, `analytics`, `expirations`, `historical`).
   * Teste de cálculo de IV ATM ponderada com fixtures.
   * Teste de resiliência e tratamento de erro 429 / 401 / 404.
2. **`test_pricing_b3.py`**:
   * Garantia de que a regra de contágio de indisponibilidade funciona com opções da B3 que possuem bid/ask zerados.
3. **`test_strategies_b3.py`**:
   * Validação de aprovação/rejeição das estratégias com ativos como PETR4 e VALE3.
4. **`test_gate.py`**:
   * Gate de auditoria sem dados fabricados: nenhuma métrica pode ter número inventado quando a API retornar nulo.

### Verificação Manual / Ao Vivo
* Rodar o screener no modo live:
  ```bash
  python -m src.screener --symbol PETR4
  ```
* Inspecionar o arquivo `index.html` gerado no navegador e conferir a rastreabilidade dos strikes, bids e asks diretamente com o home broker / livro de ofertas da B3.

---

## 5. Como Iniciar no Novo Projeto `op_b3`

Assim que você mudar para a pasta `op_b3`:
1. Copiaremos a base do `Op_Tasty`.
2. Criaremos o `src/brapi_client.py` e os testes unitários.
3. Atualizaremos o `config.yaml` com o universo de ações brasileiras.
4. Rodaremos a suíte de testes com `pytest` para homologar o funcionamento antes da primeira execução oficial.
