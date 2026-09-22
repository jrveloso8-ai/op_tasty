# Auditoria de Sistema Existente Contra Dado Fabricado — Relatório Consolidado

**Sistema:** Op_Tasty Screener (8 estratégias de opções + rastreamento de posições)
**Método:** skills `anti-fabricacao-de-dados` / `arquitetura-proveniencia-dados` e `auditoria-sistema-existente-dado-fabricado` / `auditoria-sistema-existente` — inventário completo, classificação contra o código real, priorização por risco de decisão, verificação independente (nunca por relatório agregado de terceiros).
**Contexto desta rodada:** o usuário reportou um "crash" durante uma sessão de atualização do sistema. Esta rodada re-executa a auditoria completa de ponta a ponta (não apenas leitura de código) para confirmar o que está funcionando, o que quebrou, e o que ainda é dado real.
**Última verificação:** 2026-09-22, quarta rodada nesta sessão — `python -m src.screener` (coleta ao vivo real, 24/24 ativos) e `scripts/run_gate.py` (mypy + ruff + pytest 96/96 + `lint_provenance.py`) reexecutados após uma correção de terceiros ao achado "bid/ask por perna nunca atualiza, badge MED enganoso" (ver seção correspondente abaixo). Todos os achados críticos e médios abertos nesta sessão estão **RESOLVIDOS e verificados de forma independente com dado de produção real**, não apenas por relatório de quem implementou.
**Este arquivo substitui todas as versões anteriores.**

---

## O "crash": causa raiz identificada e corrigida nesta rodada

**`scripts/run_gate.py` estava abortando na etapa de lint (`ruff`).** Uma mudança em `src/screener.py` (linha 121) adicionou um `except Exception as exc:` genérico para capturar qualquer falha de coleta por símbolo e logá-la explicitamente (implementação correta da recomendação #2 da rodada anterior — ver abaixo). Mas essa captura ampla dispara a regra `BLE001` do ruff ("Do not catch blind exception"), que o próprio projeto já reconhece como necessária em `src/tastytrade_client.py:603` (mesma situação: chamada de rede que precisa de fallback controlado) — lá, o padrão correto (`# noqa: BLE001`) já estava aplicado; em `screener.py` não estava. Resultado: `run_gate.py` (o script que o usuário roda antes de confiar em qualquer build) travava com **"GATE DE AUDITORIA ABORTADO"** a cada execução, mesmo com o `pytest` e o `mypy` 100% verdes — isto é consistente com uma sensação de "o sistema travou" no meio das atualizações.

**Correção aplicada nesta auditoria:** adicionado `# noqa: BLE001` em `src/screener.py:121`, seguindo o mesmo padrão já estabelecido no projeto. Reverificado:
- `scripts/run_gate.py` → **SUCESSO TOTAL: as 4 etapas do gate passaram** (mypy limpo, ruff limpo, pytest 92/92, `lint_provenance.py` sem violação).
- Nenhuma outra correção de código foi necessária para o gate passar.

---

## ACHADO CRÍTICO DA RODADA ANTERIOR — CONFIRMADO RESOLVIDO

A rodada anterior registrou como **Crítico**: `.env` ausente, sistema rodando 100% sobre fixtures (apenas 3 de 24 ativos), sem aviso visível ao usuário.

**Nesta rodada, rodei o pipeline completo do zero (não apenas inspecionei código) e confirmei, com evidência de execução real:**
- `.env` está presente e válido; `python -m src.screener` coletou dado ao vivo real da Tastytrade para os **24/24 ativos** configurados em `config.yaml` (incluindo os 17 novos: OPEN, AMC, GRAB, MPT, NIO, KEEL, LCID, JBLU, SNAP, CONL, ONDS, BULL, SMR, BB, BAC, KO, PLTR).
- `screener_output.json` resultante: `is_live_data: true`, `execution_mode: "AO_VIVO_COMPLETO"`, `total_configured_assets: 24`, `total_screened_assets: 24`, `coverage_pct: 100.0`, `is_partial_universe: false`, `skipped_symbols: []`.
- A varredura identificou 11 oportunidades reais (Long Strangle em MSFT/NVDA/TSLA/OPEN/JBLU/SNAP/ONDS/BULL/SMR/PLTR, Calendar Spread em BAC), todas com preços vindos da cadeia de opções ao vivo, não de fixture.
- As duas recomendações técnicas da rodada anterior (log explícito de ativo descartado + campo de cobertura parcial) **foram implementadas**: `src/screener.py` agora expõe `data_source_by_symbol`, `skipped_symbols`, `coverage_pct` e `execution_mode`, e imprime `[AUDITORIA - ATIVO DESCARTADO]` para qualquer símbolo sem fixture/sem coleta — comportamento hoje testável (nenhum símbolo caiu nesse caminho nesta execução, porque a coleta ao vivo funcionou para todos).
- A nota da rodada anterior sobre o `CONTRATO_PROVENIENCIA.md` alegar uma "sinalização visual de auditoria" (badge de IV Rank fora da faixa 0–100%) que não existia em `scripts/build_ui.py` também **foi implementada**: confirmei `isIvRank`/`.iv-anomaly-badge`/"FORA DA FAIXA" presentes e conectados em `build_ui.py` (linhas 160, 2772-2773, 2967, 3016).

**Este achado crítico está fechado.** Os três itens pendentes da rodada anterior (crítico + médio + baixo) foram todos corrigidos e reverificados por execução real, não apenas por leitura de código.

---

## ACHADO NOVO — MÉDIO — status de posição rastreada usa convenções divergentes e não é filtrado em lugar nenhum (RESOLVIDO)

`src/tracking.py` foi adicionado nesta rodada (módulo novo de rastreamento de posições executadas). A lógica de cálculo (liquidação conservadora bid/ask, regra de contágio, `DataValue` com proveniência correta, distinção `live:chain` vs `snapshot:manual`) está correta e segue o contrato à risca — não há dado fabricado no cálculo em si.

O problema era estrutural, na camada de status:

1. **Convenção divergente:** o arquivo real de posições (`op_tasty_posicoes.json`) usava `"status": "OPEN"` enquanto o backend usava `"ABERTA"`/`"ENCERRADA"`.
2. **Nenhum filtro por status existia no pipeline:** posições eram avaliadas contra cotação ao vivo independente do status.
3. **Desserialização incompleta de trades encerrados:** `realized_pnl` e `exit_price` não eram carregados do JSON.

**Resolução Implementada e Reverificada:**
1. Criada a função `normalize_position_status()` com constantes canônicas `STATUS_OPEN = "OPEN"` e `STATUS_CLOSED = "CLOSED"`. Mapeia com segurança tanto inglês (`OPEN`/`CLOSED`) quanto português (`ABERTA`/`ENCERRADA`), levantando `ValueError`/`TypeError` explícito para status inválidos.
2. `load_tracked_positions_from_json()` agora desserializa `exit_unit_price` e `realized_pnl` (como `DataValue` com proveniência) e calcula o P&L determinístico caso a posição esteja fechada mas sem P&L pré-calculado.
3. `evaluate_tracked_positions_against_market()` agora ignora avaliação de pernas e cadeias de mercado para posições com status `CLOSED`, gerando um payload estático com `signal: "ENCERRADA"`, `is_live_quote: False` e `quote_source: "closed:static"`.
4. `scripts/build_ui.py` atualizado para filtrar defensivamente tanto por `OPEN`/`ABERTA` quanto `CLOSED`/`ENCERRADA`, e suportar `realized_pnl` tanto como número direto quanto como objeto `DataValue`.
5. Adicionados testes de regressão em `tests/test_tracking.py` cobrindo normalização, carga/avaliação de posições fechadas e integridade do ranking de estratégias (gate 100% verde: 95/95 testes).

---

## Verificação independente da correção acima (Etapa 5 da metodologia — nunca aceitar relatório agregado)

A correção de status descrita na seção anterior foi implementada por outra sessão/agente entre a rodada passada e esta. Segui a disciplina de nunca aceitar "todos os testes passaram" como prova: li o diff real de `src/tracking.py` e `scripts/build_ui.py`, e rodei eu mesmo o gate e um pipeline completo do zero.

**Confirmado, linha por linha, não apenas pelo relatório:**
- `normalize_position_status()` (linha 106) mapeia `OPEN`/`ABERTA` → `OPEN` e `CLOSED`/`ENCERRADA` → `CLOSED`, levantando `ValueError`/`TypeError` explícito para qualquer outro valor — sem fallback silencioso.
- `evaluate_tracked_positions_against_market` (linha 711-712) agora checa `normalize_position_status(pos.status) == STATUS_CLOSED` e, se verdadeiro, pula toda avaliação de mercado, retornando um payload estático com `signal: "ENCERRADA"`, `is_live_quote: False`, `quote_source: "closed:static"`.
- `calculate_strategy_ranking` (linha 541) agora filtra pelo status normalizado, não pela string crua.
- `scripts/build_ui.py` (linhas 4019-4020) filtra `openPositions`/`closedPositions` aceitando ambas as convenções, e a grade "Posições Abertas" usa a lista já filtrada.
- Rodei `python scripts/run_gate.py` eu mesmo (não confiei na saída relatada): **SUCESSO TOTAL** — mypy limpo, ruff limpo (incluindo `scripts/`, que o gate padrão não cobre — rodei `ruff check src scripts tests` à parte e também veio limpo), pytest **95/95**. Li os 3 testes novos (`test_normalize_position_status_valid_and_invalid`, `test_load_and_evaluate_closed_position_pipeline`, `test_to_dict_includes_flat_and_dv_fields`) e confirmei que fazem asserções reais sobre o comportamento (não são testes vazios).
- Rodei `python -m src.screener` do zero de novo (coleta ao vivo real, 24/24 ativos, `is_live_data: true`, `execution_mode: AO_VIVO_COMPLETO`, `coverage_pct: 100.0`) para confirmar que a correção de status não quebrou o caminho ao vivo. As 7 posições reais de `op_tasty_posicoes.json` (todas `"OPEN"`) foram avaliadas corretamente contra cotação ao vivo (`quote_source: "live:chain"` em 6 das 7 pernas; SNAP caiu em `snapshot:manual` porque a cadeia ao vivo não tinha aquele strike específico — fallback correto e rotulado, não fabricado).

**Veredito: a correção é real, está corretamente integrada ponta a ponta, e não introduziu regressão.** Considero este achado fechado.

---

## ACHADO ANTERIOR — o botão "Atualizar Cotações" nunca atualiza a aba de posições rastreadas (RESOLVIDO PARCIALMENTE — ver ressalva abaixo)

Encontrado ao verificar a correção acima: `scripts/build_ui.py`, função `applyNewMarketData` (linha 4370), é chamada após todo refresh ao vivo bem-sucedido (`POST /api/refresh`). Ela faz `STATE = newData` e chama `renderTrackingTab()` — mas `renderTrackingTab()` (linha 4017) lia posições exclusivamente de `getStoredPositions()`, que lê do `localStorage` do navegador (chave `op_tasty_tracked_positions`). Esse `localStorage` só é semeado **uma única vez**, no primeiro carregamento da página sem dado salvo, a partir do payload embutido no HTML na hora do build (`SAMPLE_TRADES`).

### Correção aplicada (nova rodada) — verificada de forma independente

`applyNewMarketData` agora tem um bloco novo (linhas 4386-4421) que, a cada refresh, mescla `newData.tracked_positions` (o payload recém-recalculado pelo backend) para dentro do `localStorage`, casando por `id`/`position_id`, preservando localmente qualquer posição que o usuário já tenha marcado como `CLOSED`/`ENCERRADA` (para não ressuscitar uma posição fechada com dado do servidor). Confirmei, lendo o código: `evaluation` (o sinal MANTER/STOPAR/REALIZAR_GAIN e o P&L agregado) é substituído pelo valor fresco do servidor a cada refresh. Testei ao vivo: rodei o pipeline (`screener` → `tracked_positions` no JSON de saída) e confirmei que BAC aparece com `evaluation.signal: "ALVO_PROXIMO"` e `quote_source: "live:chain"` — dado que só existe porque foi recalculado nesta execução. **O problema original (sinal e P&L agregados congelados) está corrigido.**

### Ressalva nova, encontrada ao auditar esta correção — MÉDIO — cotação de bid/ask por perna nunca é atualizada, mas o badge ao lado diz "MED" (medido/ao vivo) (RESOLVIDO)

Ao ler o merge de perto (linhas 4403-4414), percebi que ele copia `freshLeg.current_bid`/`current_ask`/`current_mid` de `fresh.legs[idx]` — mas rastreei a origem desse campo no backend e confirmei que **ele nunca era atualizado**. Em `src/tracking.py`, a função `evaluate_tracked_positions_against_market` buscava a cotação ao vivo da cadeia de opções para calcular a avaliação agregada, mas guardava em lista local (`quote_legs`) sem reatribuir a `pos.legs`.

**Resolução Implementada e Reverificada:**
1. Em `src/tracking.py:evaluate_tracked_positions_against_market`: as pernas correspondidas da cadeia ao vivo agora geram instâncias atualizadas de `ExecutedLeg` via `dataclasses.replace` com `current_bid`, `current_ask`, `current_mid` (derivado), `quote_timestamp` e `quote_provenance="MEDIDO"`. Essas pernas atualizadas são atribuídas a `pos.legs` antes de `pos.to_dict()`, propagando as cotações vivas de cada perna.
2. Em `scripts/build_ui.py`: o badge por perna foi desacoplado de `evalRes.isLiveQuote` e agora reflete estritamente a proveniência da perna (`quote_provenance === "MEDIDO"` exibe `MED`, caso contrário `SNAPSHOT`).
3. Adicionado teste unitário `test_evaluate_tracked_positions_updates_leg_quotes` em `tests/test_tracking.py` garantindo que cotações vivas da cadeia atualizam os campos de pernas e o rótulo de proveniência (gate 100% verde: 96/96 testes).

### Verificação independente desta correção (quarta rodada desta sessão) — confirmada com dado de produção real, não só teste unitário

Segui a mesma disciplina de não aceitar o relatório de terceiros como prova: li o código de `evaluate_tracked_positions_against_market` linha por linha (confirmei `pos.legs = updated_legs` antes de `pos.to_dict()`, e `replace()` corretamente importado de `dataclasses` para não violar a imutabilidade do `ExecutedLeg` frozen), li o teste novo (`test_evaluate_tracked_positions_updates_leg_quotes`, linha 635) e confirmei que ele testa exatamente o cenário de regressão (bid/ask de snapshot antigo 3.50/3.60 vs. bid/ask ao vivo 4.80/4.90, e asserta ambos os valores E o `quote_provenance == "MEDIDO"`). Rodei `python scripts/run_gate.py` eu mesmo: **96/96 testes, mypy limpo, ruff limpo** (`ruff check src scripts tests` também limpo).

Fui além do teste unitário: rodei `python -m src.screener` do zero contra a API real da Tastytrade (24/24 ativos, `is_live_data: true`) e inspecionei o `tracked_positions` resultante. Resultado, com evidência de produção:
- BAC, BULL, KO, NVDA, PLTR, QQQ: todas as pernas vieram com `quote_provenance: "MEDIDO"`, bid/ask frescos e `quote_timestamp` de segundos atrás (ex.: `2026-09-22T21:48:19Z`) — não mais o valor estático do `op_tasty_posicoes.json`.
- **SNAP produziu, naturalmente, o caso misto que mais importa validar:** a perna PUT (strike 5.0) casou com a cadeia ao vivo e veio `MEDIDO` com timestamp fresco; a perna CALL (strike 6.5) não tinha correspondência na cadeia ao vivo e corretamente manteve `quote_provenance: "SNAPSHOT_MANUAL"` com o timestamp antigo (`2026-09-22T12:00:00Z`) — provando que o fallback por perna individual funciona mesmo dentro da mesma posição, não só entre posições.

**Veredito: correção real, completa, e comprovada com dado de mercado real, não apenas com fixture de teste.** O badge por perna agora diz a verdade sobre a idade daquele bid/ask específico.

---

## Avaliação do núcleo — sem mudança

`src/provenance.py`, `src/models.py`, `src/indicators.py`, `src/pricing.py` continuam mais rígidos que o mínimo exigido. Nenhum achado novo no núcleo de cálculo. `src/tracking.py` (novo) segue a mesma disciplina — ver achado acima, que é estrutural/de fluxo, não de fórmula.

---

## Resumo de prioridade

| # | Achado | Status |
|---|---|---|
| Herdado | `.env` ausente — sistema rodando só 3/24 ativos, 100% fixture, sem aviso visível | **RESOLVIDO** (confirmado por execução real: 24/24 ao vivo) |
| Herdado | `is_live_data` agregado, sem granularidade por símbolo | **RESOLVIDO** (`data_source_by_symbol`, `execution_mode`, `coverage_pct` implementados) |
| Herdado | Nota 1 do contrato com alegação de UI não implementada (badge IV Rank) | **RESOLVIDO** (badge confirmado em `build_ui.py`) |
| Novo (causa do "crash") | `run_gate.py` abortando por violação de lint (`except Exception` sem `# noqa`) em `src/screener.py` | **CORRIGIDO NESTA AUDITORIA** |
| Novo | Status de posição rastreada (`OPEN`/`ABERTA`) sem normalização e sem filtro | **RESOLVIDO** (normalização canônica, desserialização de P&L, filtro de mercado e testes 95/95 — verificado de forma independente nesta rodada) |
| Novo | Botão "Atualizar Cotações" não propagava `tracked_positions` recalculado para a aba de posições — sinal/P&L agregado ficava parado no primeiro carregamento | **RESOLVIDO** (merge por id em `applyNewMarketData`, verificado nesta rodada) |
| Novo | Bid/Ask por perna no card de posição nunca é atualizado (backend nunca escreve o `quote_legs` de volta em `pos.legs`), mas exibe badge `MED` como se fosse medição corrente | **RESOLVIDO** (reatribuição via `dataclasses.replace` com live quotes das cadeias, badge por perna desacoplado e teste no gate 96/96) |

---

## Nota de método

Esta auditoria acumulou quatro rodadas de execução real nesta sessão (não apenas leitura de código):
1. Rodou `python -m src.screener` do zero, `python scripts/build_ui.py` e `scripts/run_gate.py` para confirmar a correção do `.env`/fixture e corrigir o `# noqa: BLE001` que causava o "crash" relatado.
2. Verificou de forma independente — sem aceitar relatório de terceiros como prova — a correção de status de posição (`OPEN`/`CLOSED`) feita por outra sessão entre as rodadas: leu o diff linha por linha, rodou o gate e o pipeline de coleta ao vivo de novo, conferiu que os testes novos fazem asserções reais. Encontrou, nesse processo, o achado do botão de refresh não propagar `tracked_positions`.
3. Verificou a correção do achado #2 — também aplicada por outra sessão entre rodadas — lendo o merge por `id` em `applyNewMarketData` e confirmando via execução ao vivo que sinal/P&L agregado agora atualiza. Ao rastrear essa correção até a origem do dado (`quote_legs` em `evaluate_tracked_positions_against_market`), encontrou que o bid/ask **por perna** nunca era escrito de volta em `pos.legs` antes da serialização — logo permanecia congelado indefinidamente atrás de um badge `MED` que implicava atualidade.
4. (Esta rodada) Verificou a correção do achado #3 — igualmente aplicada por outra sessão entre rodadas — lendo a reatribuição via `dataclasses.replace` em `pos.legs` e o desacoplamento do badge para usar `quote_provenance` por perna. Foi além do teste unitário: rodou a coleta ao vivo real contra a Tastytrade e conferiu o `tracked_positions` resultante, encontrando naturalmente (não forçado) um caso misto — a posição SNAP com uma perna `MEDIDO`/fresca e outra `SNAPSHOT_MANUAL`/antiga dentro da mesma posição — que prova o fallback por perna funciona corretamente. **Nenhum achado novo surgiu nesta rodada de verificação**, primeira vez nesta sessão em que verificar uma correção não revelou a instância seguinte do mesmo problema. Todos os itens do "Resumo de prioridade" abaixo estão RESOLVIDOS. Cada rodada anterior, ao verificar a correção da rodada passada, tinha encontrado um achado nível abaixo — padrão esperado pela metodologia (a Etapa 4 da skill já avisa: uma correção pontual normalmente revela a próxima instância da mesma classe de problema); esta rodada é a primeira em que essa cadeia não se repetiu, o que é o sinal mais forte disponível de que a classe de problema (frescor/proveniência de cotação em posições rastreadas) foi de fato esgotada, não só empurrada uma camada adiante.
5. (Esta rodada — encerramento do dia) Nenhum arquivo relevante mudou no disco desde a rodada 4 (confirmado por `mtime`: `src/tracking.py` e `scripts/build_ui.py` datados de antes do último fechamento). Rodei `scripts/run_gate.py` mais uma vez para fechar o dia com estado confirmado: **96/96 testes, mypy limpo, ruff limpo.** Não repeti a coleta ao vivo de 24 ativos (~3 min) porque nada no caminho de dado mudou desde a verificação anterior já feita com evidência de produção — repetir teria custo sem nova informação.

   Dois itens de higiene encontrados nesta varredura final, fora do escopo de fabricação de dado (não afetam nenhum número exibido ao usuário), registrados para não ficarem esquecidos:
   - `scratch/` contém arquivos de teste/rascunho (`temp_avatar_instrucoes.html`, `test.html`, `test.pdf`) e não está no `.gitignore` — um `git add -A` os incluiria no commit por engano.
   - `CONTRATO_PROVENIENCIA.md` ainda não documenta a atualização de cotação por perna (`current_bid`/`current_ask`/`quote_provenance` em `ExecutedLeg`) implementada na rodada 4 — o comportamento está correto no código e testado, só falta a mesma entrada de tabela que outros campos `DERIVADO`/`MEDIDO` já têm.

## Critério de fechamento desta sessão

Todos os achados Críticos e Médios abertos nas quatro rodadas anteriores estão **RESOLVIDOS**, verificados de forma independente (nunca só pelo relatório de quem implementou) e confirmados com execução real — gate limpo e coleta ao vivo contra a API real da Tastytrade, não apenas fixture. Os dois itens de higiene acima ficam registrados como pendência de baixa prioridade, fora do escopo desta auditoria de dado fabricado — não bloqueiam o fechamento do dia.
