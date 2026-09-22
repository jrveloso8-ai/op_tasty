# Parecer Técnico — Auditoria de Lógica das Estratégias e da Gestão de Posições (Rodada 5)

**Papel:** analista sênior de opções (20+ anos de mesa), auditando critério de entrada das 8 estratégias e lógica de gestão (STOPAR/MANTER/REALIZAR GAIN) contra a skill `analista-senior-opcoes-us`.
**Contexto:** quarto follow-up, motivado por um "crash" relatado pelo usuário durante uma sessão de atualização. A causa raiz do crash era técnica (gate de lint travando — ver `AUDITORIA_DADO_FABRICADO.md`), não de lógica de negócio; corrigida nesta rodada.

## 0. Atualização desta rodada — ressalva da Seção 3 abaixo está RESOLVIDA

A ressalva da rodada anterior (Seção 3) — VRP correto na lógica, mas calculado sobre fixture, não mercado ao vivo — está fechada. Rodei `python -m src.screener` do zero nesta sessão: coleta ao vivo real bateu nos 24/24 ativos configurados (antes eram 3/24 em fixture). O `.env` foi restaurado. Detalhe completo em `AUDITORIA_DADO_FABRICADO.md`.

Achado novo desta rodada, de fluxo de dado (não de lógica de estratégia): `src/tracking.py` (módulo novo de rastreamento de posições) não filtra posições por status — uma posição encerrada pode continuar recebendo sinal de gestão "ao vivo" indefinidamente, e some do ranking de performance por divergência de convenção de string (`OPEN` no arquivo real vs `ENCERRADA` esperado pelo código). Registrado como achado Médio em `AUDITORIA_DADO_FABRICADO.md`; não corrigido, pois é decisão de fluxo do usuário.

---

## Conteúdo original da Rodada 4 (mantido como histórico)

---

## 1. As 5 recomendações seguem implementadas e corretas

Reconfirmei ponta a ponta: filtro de liquidez, risco de atribuição por dividendo, unificação backend/frontend na gestão de posição (`pos.evaluation` consumido pela UI), calibração de meta do Iron Condor por largura de asa, VRP como critério em Iron Condor/Put Ratio/Long Strangle, put-call parity ligada ao pipeline. `pytest` 92/92, sem regressão.

## 2. Confirmação nova — VRP dispara de verdade, ponta a ponta

Na rodada anterior eu não conseguia confirmar isso porque o `screener_output.json` disponível era anterior ao código que exporta VRP. Agora, rodando contra o dado mais recente, encontrei o caso real: **SPY, Long Strangle, `VRP = +36,9 pts`**, e a nota do resultado mostra exatamente a mensagem esperada — *"⚠️ VRP ELEVADO (+36.9 pts): IV inflada em relação ao realizado... risco de compressão de vol pós-evento"*. A lógica que critiquei como "infraestrutura morta" há duas rodadas está, agora, funcionando e influenciando o veredito de uma estratégia real. Considero este item fechado.

## 3. Ressalva importante — a base de dado por trás dessa confirmação é fixture, não mercado ao vivo

Aqui a lógica está certa, mas o **dado que a alimenta agora** não é. Detalhei em `AUDITORIA_DADO_FABRICADO.md`: as credenciais (`.env`) sumiram do projeto, então a coleta atual rodou 100% em modo fixture, cobrindo só 3 dos 24 ativos configurados (`SPY`, `AAPL`, `QQQ`), silenciosamente, sem aviso.

Do ponto de vista de análise de opções, isso importa por um motivo específico: **o VRP de +36,9 pts que confirmei acima é calculado sobre um "IV" e um "RV" que vêm de dado de fixture com timestamp fixo em `2026-09-21T10:30:00Z`** — não é uma leitura de mercado do dia. É um número internamente consistente e corretamente rotulado (`DataValue` com `provenance: DERIVADO`, `source: calc:vrp`), mas não representa uma condição de mercado atual, e nada na tela avisa isso de forma proeminente. Um trader olhando essa nota sem saber do problema de credenciais tomaria "VRP elevado, cuidado com compressão pós-evento" como leitura do mercado de agora — quando é leitura de um cenário sintético fixo, criado para teste.

**Isso não é uma falha da lógica de trading** (que fiz questão de separar do lado técnico nas rodadas anteriores) — é o lado técnico contaminando a validade da leitura de mercado. Registro aqui porque a fronteira entre "a estratégia está bem calibrada" e "a estratégia está sendo alimentada com o dado certo" só fica visível quando se olha os dois juntos, e hoje ela quebrou exatamente nesse ponto.

## 4. Nada de novo a criticar nos critérios de entrada ou nos sinais de gestão em si

Não encontrei achado novo de lógica pura nesta rodada — as 8 estratégias e os 5 ramos de gestão de posição continuam consistentes com o que já foi revisado e corrigido. O trabalho de calibração (VRP, dividendo, liquidez, risco não-definido, meta adaptativa) está, no nível de regra de decisão, no ponto.

## 5. Prioridade recomendada

| # | Item | Por quê |
|---|---|---|
| 1 | Restaurar `.env` (ver `AUDITORIA_DADO_FABRICADO.md`) antes de usar qualquer veredito desta coleta para decisão real | Sem isso, toda a calibração de VRP/dividendo/liquidez está correta em teoria e não está sendo testada contra mercado real |
| 2 | Depois de restaurado o acesso ao vivo, rodar de novo e conferir se VRP aparece com valores plausíveis (não extremos) nos 24 ativos, não só nos 3 de fixture | Fecha a verificação de ponta a ponta contra dado real, não sintético |
| 3 | Considerar um aviso na UI quando a coleta rodar em modo fixture (hoje só aparece implicitamente pelo `is_live_data`, que a auditoria técnica já registrou como pouco visível) | Evita alguém ler uma nota de VRP/gregas como leitura de mercado quando é cenário de teste |

Nenhuma correção foi aplicada por mim — isto é só o parecer.
