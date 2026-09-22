"""
Script de Geração dos PDFs de Instruções:
1. INSTRUCOES_VIDEO_SISTEMA.pdf — Roteiro completo, storyboard e prompts para vídeo explicativo.
2. INSTRUCOES_AVATAR_SISTEMA.pdf — Especificação visual, persona e prompts para avatar de IA.
Gera os PDFs via Chrome Headless com renderização tipográfica profissional A4.
"""

import subprocess
import sys
from pathlib import Path


def get_video_instructions_html() -> str:
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Roteiro e Instruções para Geração de Vídeo — Op_Tasty Screener</title>
  <style>
    @page {
      size: A4;
      margin: 15mm 15mm 18mm 15mm;
      @bottom-right {
        content: counter(page);
        font-size: 8pt;
        font-family: Arial, sans-serif;
        color: #64748b;
      }
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: #0f172a;
      line-height: 1.5;
      font-size: 9.5pt;
      margin: 0;
      padding: 0;
    }
    .header-box {
      border-bottom: 2px solid #2563eb;
      padding-bottom: 12px;
      margin-bottom: 20px;
    }
    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 8pt;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .badge-blue { background: #dbeafe; color: #1e40af; }
    .badge-green { background: #dcfce7; color: #166534; }
    .badge-dark { background: #0f172a; color: #f8fafc; }
    h1 {
      font-size: 18pt;
      color: #0f172a;
      margin: 8px 0 4px 0;
      font-weight: 800;
    }
    .subtitle {
      font-size: 10pt;
      color: #475569;
      margin: 0;
    }
    h2 {
      font-size: 12pt;
      color: #1e3a8a;
      border-left: 4px solid #2563eb;
      padding-left: 8px;
      margin: 18px 0 10px 0;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.3px;
    }
    h3 {
      font-size: 10.5pt;
      color: #0f172a;
      margin: 14px 0 6px 0;
      font-weight: 700;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 10px 0 15px 0;
      font-size: 8.8pt;
    }
    th, td {
      border: 1px solid #cbd5e1;
      padding: 6px 8px;
      text-align: left;
      vertical-align: top;
    }
    th {
      background-color: #f1f5f9;
      color: #1e293b;
      font-weight: 700;
    }
    .callout {
      background-color: #f8fafc;
      border: 1px solid #e2e8f0;
      border-left: 4px solid #2563eb;
      padding: 10px 12px;
      border-radius: 4px;
      margin: 12px 0;
      font-size: 9pt;
    }
    .callout-title {
      font-weight: 700;
      color: #1e3a8a;
      margin-bottom: 4px;
    }
    .scene-card {
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      margin-bottom: 12px;
      page-break-inside: avoid;
      background: #ffffff;
    }
    .scene-header {
      background: #f8fafc;
      padding: 6px 10px;
      border-bottom: 1px solid #cbd5e1;
      display: flex;
      justify-content: space-between;
      font-weight: 700;
      font-size: 9pt;
      color: #1e293b;
    }
    .scene-body {
      padding: 8px 10px;
    }
    .prompt-box {
      background: #0f172a;
      color: #e2e8f0;
      font-family: "Courier New", Courier, monospace;
      padding: 6px 8px;
      border-radius: 4px;
      font-size: 8pt;
      margin-top: 4px;
      white-space: pre-wrap;
      word-break: break-word;
    }
    ul, ol {
      margin: 4px 0 8px 16px;
      padding: 0;
    }
    li { margin-bottom: 3px; }
    .page-break { page-break-before: always; }
  </style>
</head>
<body>

  <!-- CABEÇALHO -->
  <div class="header-box">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <span class="badge badge-dark">DOCUMENTO DE PRODUÇÃO AUDIOVISUAL</span>
      <span class="badge badge-blue">VERSÃO 1.0 — 2026</span>
    </div>
    <h1>Diretrizes e Roteiro de Vídeo Instrucional</h1>
    <p class="subtitle">Plataforma Op_Tasty Screener — Guia Operacional, Boletas e Gestão de Trades na Tastytrade</p>
  </div>

  <!-- SEÇÃO 1: FICHA TÉCNICA -->
  <h2>1. Ficha Técnica do Vídeo</h2>
  <table>
    <tr>
      <th style="width: 25%;">Item</th>
      <th style="width: 75%;">Especificação Recomendada</th>
    </tr>
    <tr>
      <td><b>Título do Vídeo</b></td>
      <td>Dominando o Op_Tasty Screener: Da Triagem Matemática à Execução na Prática</td>
    </tr>
    <tr>
      <td><b>Duração Alvo</b></td>
      <td>6 a 7 minutos (modular, permite cortes em capítulos e Shorts de 60s)</td>
    </tr>
    <tr>
      <td><b>Resolução & Aspecto</b></td>
      <td>16:9 widescreen (1920×1080 Full HD ou 3840×2160 4K, 60fps)</td>
    </tr>
    <tr>
      <td><b>Tom de Voz / Linguagem</b></td>
      <td>Técnico, seguro, institucional e calmo. Foco em disciplina matemática, proteção de capital e consistência, sem promessas fáceis ou jargões vazios.</td>
    </tr>
    <tr>
      <td><b>Blindagem de Risco</b></td>
      <td>Módulo de Proteção de Capital para Ativos Caros (> US$ 100) e Caso Prático NVDA (IV Rank 0% — Vácuo de Catalisador).</td>
    </tr>
    <tr>
      <td><b>Estilo Visual</b></td>
      <td>Financial Dark Mode (#0a0e1a), contrastes em azul neon (#3b82f6) e verde esmeralda (#10b981), telas limpas e tipografia mono para dados.</td>
    </tr>
    <tr>
      <td><b>Softwares Sugeridos</b></td>
      <td>HeyGen / Synthesia (apresentador), ElevenLabs (locução neural), Runway Gen-3 (transições), CapCut / Premiere Pro (montagem final).</td>
    </tr>
  </table>

  <div class="callout">
    <div class="callout-title">Regra de Ouro do Vídeo</div>
    O espectador deve entender que o sistema <b>não faz previsões nem inventa números</b>: todo dado é MEDIDO diretamente na Tastytrade ou DERIVADO por fórmulas matemáticas com precificação conservadora (comprar no Ask, vender no Bid), com veto automático a riscos não-definidos em ativos caros.
  </div>

  <!-- SEÇÃO 2: ROTEIRO CENA A CENA -->
  <h2>2. Roteiro de Produção Cena a Cena (Storyboard & Script)</h2>

  <!-- CENA 1 -->
  <div class="scene-card">
    <div class="scene-header">
      <span>CENA 01 — Abertura e Filosofia Quantitativa</span>
      <span>00:00 – 00:45 (45s)</span>
    </div>
    <div class="scene-body">
      <p><b>Visual na Tela:</b> O avatar aparece em plano médio em um estúdio financeiro moderno escuro. Ao lado dele surge o painel do Op_Tasty Screener em tela cheia com o banner de auditoria e os KPIs do topo brilhando.</p>
      <p><b>Texto da Locução (Voz do Avatar):</b></p>
      <blockquote style="font-style: italic; margin: 4px 0 8px 10px; color: #1e293b;">
        "Olá, operador. Seja muito bem-vindo ao guia operacional do Op_Tasty Screener. Este não é um screener comum que faz adivinhações ou busca prever o topo ou fundo do mercado. Esta plataforma foi concebida sob uma cerca rigorosa de auditoria de dados: aqui, todo número é medido diretamente na API da Tastytrade ou derivado por fórmulas auditáveis. Além disso, aplicamos a regra da precificação conservadora: as pernas de compra são orçadas no Ask e as pernas de venda no Bid. Isso garante que você nunca tenha surpresas na hora de executar. Vamos aprender agora como operar o sistema com segurança máxima de ponta a ponta."
      </blockquote>
      <b>Prompt de B-Roll / Cenário (Midjourney / Runway):</b>
      <div class="prompt-box">Cinematic shot of a sleek quantitative financial trading room, modern dark interface glowing on curved glass monitors, clean reflections, blue and green financial charts, 8k resolution, photorealistic.</div>
    </div>
  </div>

  <!-- CENA 2 -->
  <div class="scene-card">
    <div class="scene-header">
      <span>CENA 02 — Aba Oportunidades: Triagem e Leitura da Boleta</span>
      <span>00:45 – 01:45 (60s)</span>
    </div>
    <div class="scene-body">
      <p><b>Visual na Tela:</b> Captura de tela com zoom suave nos 4 KPIs do topo (Total Analisado, Aprovadas, Condicionais e Rejeitadas). Em seguida, foco em um card de oportunidade aprovado (ex: Bull Call Spread ou Bear Put Spread).</p>
      <p><b>Texto da Locução (Voz do Avatar):</b></p>
      <blockquote style="font-style: italic; margin: 4px 0 8px 10px; color: #1e293b;">
        "Na aba Oportunidades, o motor analisa dezenas de combinações entre ativos e estratégias. Os cards exibem apenas o que passou em 100% dos critérios técnicos: tendência confirmada por médias móveis e RSI, e faixa adequada de IV Rank. Observe o card: em azul ou verde, você vê o Custo Máximo a Pagar ou o Valor Mínimo a Receber. Logo abaixo, a Boleta de Execução de Ordens lista exatamente o que você deve fazer: quais pernas comprar, quais vender, os strikes e o vencimento. E na seção de Instrução Prática, você tem um passo a passo pronto em linguagem natural para digitar no seu aplicativo da Tastytrade sem hesitar."
      </blockquote>
      <b>Destaques Gráficos na Edição:</b>
      <ul>
        <li>Círculo vermelho animado destacando a <em>Boleta de Execução</em>.</li>
        <li>Seta apontando para o <em>Custo Máximo de Débito</em>.</li>
      </ul>
    </div>
  </div>

  <!-- CENA 3 (NOVA: GESTÃO DE RISCO & CASO NVDA) -->
  <div class="scene-card" style="border-left: 4px solid #10b981;">
    <div class="scene-header" style="background: rgba(16, 185, 129, 0.08);">
      <span style="color: #065f46;">CENA 03 — Gestão de Risco em Ativos Caros (> US$ 100) e o Caso NVDA</span>
      <span>01:45 – 03:00 (75s)</span>
    </div>
    <div class="scene-body">
      <p><b>Visual na Tela:</b> Split-screen comparativo. À esquerda, alerta de auditoria com símbolo de escudo vermelho: 'Veto de Risco Não-Definido (Ponta Nua a Descoberto)'. À direita, gráfico de volatilidade de NVDA mostrando IV Rank em 0% e calendário com 8 semanas livres até os próximos earnings.</p>
      <p><b>Texto da Locução (Voz do Avatar):</b></p>
      <blockquote style="font-style: italic; margin: 4px 0 8px 10px; color: #1e293b;">
        "Atenção fundamental agora: a preservação do seu capital. Em contas de custódia de varejo de 2 a 10 mil dólares, uma operação em ativos de alto valor nominal unitário — como Nvidia, Apple ou SPY acima de 100 dólares — pode consumir toda a sua margem ou gerar prejuízos catastróficos se houver risco ilimitado. Por isso, implementamos um Protocolo de Proteção Estrito: em ativos acima de 100 dólares, o sistema veta sumariamente estratégias com pontas vendidas a descoberto, como a perna nua de um Put Ratio Spread 1x2, recomendando travas de risco definido como Bear Put Spreads. Nos Iron Condors, travamos a largura das asas em no máximo 5 dólares para conter o Buying Power Reduction em 500 dólares por lote. E veja o exemplo real da Nvidia: com IV Rank em 0%, a ação está em pleno 'vácuo de catalisador', sem earnings pelos próximos dois meses. Vender opções aqui é uma armadilha matemática de baixa recompensa; o sistema orienta para travas de débito ou Calendar Spreads, garantindo que o tempo e a assimetria joguem a seu favor."
      </blockquote>
      <b>Destaques Gráficos na Edição:</b>
      <ul>
        <li>Infográfico em 3D: Ícone de Escudo de Proteção de Margem (BPR Capped em $500).</li>
        <li>Tabela comparativa: <em>Put Ratio Nua (Risco Indefinido: VETADO)</em> vs <em>Bear Put Spread (Risco Capped: RECOMENDADO)</em>.</li>
        <li>Medidor de IV Rank em 0% com rótulo 'Vácuo de Catalisador'.</li>
      </ul>
    </div>
  </div>

  <div class="page-break"></div>

  <!-- CENA 4 -->
  <div class="scene-card">
    <div class="scene-header">
      <span>CENA 04 — Execução na Corretora & Confirmação no Painel</span>
      <span>03:00 – 03:50 (50s)</span>
    </div>
    <div class="scene-body">
      <p><b>Visual na Tela:</b> Demonstração de clique no botão <code>[🎯 Confirmar Execução no Portfólio]</code>. Abertura do modal interativo preenchendo o preço real executado e os lotes.</p>
      <p><b>Texto da Locução (Voz do Avatar):</b></p>
      <blockquote style="font-style: italic; margin: 4px 0 8px 10px; color: #1e293b;">
        "Assim que sua ordem for executada na Tastytrade, volte ao card e clique em 'Confirmar Execução no Portfólio'. Uma janela se abrirá com os dados preenchidos da sua estrutura. Confirme o preço unitário que você realmente negociou, a quantidade de lotes e ajuste as suas metas de lucro e stop loss. Ao clicar em salvar, o card recebe o selo verde de 'Posição Ativa' e a operação é imediatamente transferida para a sua central de acompanhamento em tempo real."
      </blockquote>
    </div>
  </div>

  <!-- CENA 5 -->
  <div class="scene-card">
    <div class="scene-header">
      <span>CENA 05 — Aba Posições Executadas: Acompanhamento e Sinais</span>
      <span>03:50 – 05:10 (80s)</span>
    </div>
    <div class="scene-body">
      <p><b>Visual na Tela:</b> Navegação para a aba 'Posições Executadas & Histórico'. Foco no card da operação de BAC (Bank of America), destacando os dois preços (Mark Tastytrade de $0,70 vs Saída Conservadora de $0,46) e o badge brilhante de sinal.</p>
      <p><b>Texto da Locução (Voz do Avatar):</b></p>
      <blockquote style="font-style: italic; margin: 4px 0 8px 10px; color: #1e293b;">
        "Na aba de Posições Executadas, temos a nossa cabine de comando. Aqui você encontra dois valores fundamentais: o Preço Mark da Tastytrade, que reflete exatamente o que você vê no painel da sua corretora com o lucro atual, e o Preço de Saída Conservadora, que mostra o pior cenário se você fechar tudo a mercado no Bid/Ask agora mesmo. Além disso, o sistema emite sinais claros: 'MANTER' enquanto a oscilação for normal; 'ALVO PRÓXIMO' e 'REALIZAR GAIN' quando atingir 50% de lucro; e 'STOPAR' caso o limite de perda seja alcançado. O sistema ainda monitora os dias para o vencimento: se o DTE atingir 21 dias em operações de crédito, você receberá um alerta para fechar ou rolar e evitar riscos de cauda."
      </blockquote>
      <b>Tabela Visual na Tela (Sinais):</b>
      <div style="font-size: 8.5pt; margin-top: 4px;">
        <span class="badge badge-green">💰 REALIZAR GAIN</span> Meta atingida: fechar ordem.<br>
        <span class="badge badge-blue">🎯 ALVO PRÓXIMO</span> 90%+ do alvo: aguardar ordem limite.<br>
        <span class="badge" style="background:#fee2e2; color:#991b1b;">🛑 STOPAR</span> Limite atingido: encerrar para proteger capital.
      </div>
    </div>
  </div>

  <!-- CENA 6 -->
  <div class="scene-card">
    <div class="scene-header">
      <span>CENA 06 — Encerramento, Ranking de Sucesso e Rotina Diária</span>
      <span>05:10 – 06:30 (80s)</span>
    </div>
    <div class="scene-body">
      <p><b>Visual na Tela:</b> O operador clica em <code>[✔ Encerrar Posição]</code>. A tabela de Ranking de Estratégias se atualiza com as medalhas de ouro, prata e bronze. Em seguida, rápida passagem pela aba 'Manual do Operador'.</p>
      <p><b>Texto da Locução (Voz do Avatar):</b></p>
      <blockquote style="font-style: italic; margin: 4px 0 8px 10px; color: #1e293b;">
        "Quando sua posição for encerrada na corretora, clique em 'Encerrar Posição' no card para gravar o lucro realizado. Imediatamente, o Ranking de Estratégias é alimentado. Você verá quais modelos geram maior taxa de acerto e maior retorno financeiro consolidado ao longo do tempo. E para não ter dúvidas no dia a dia, consulte a aba 'Manual do Operador', onde deixamos um checklist completo em 5 passos para a sua rotina: da triagem matinal até o encerramento planejado. Opere com método, disciplina e matemática."
      </blockquote>
    </div>
  </div>

  <!-- SEÇÃO 3: DIRETRIZES TÉCNICAS DE ÁUDIO E EDIÇÃO -->
  <h2>3. Diretrizes Técnicas para o Editor de Vídeo</h2>
  <ul>
    <li><b>Configuração de Voz ElevenLabs:</b> Voz sugerida: <em>Adam</em>, <em>Antoni</em> ou <em>George</em> (para avatar masculino) ou <em>Rachel</em> / <em>Charlotte</em> (feminino). Settings: Stability 0.75, Clarity + Similarity 0.85, Style Exaggeration 0.0, Speed 0.98.</li>
    <li><b>Trilha Sonora de Fundo:</b> Música ambiente instrumental corporativa tech (Low-tempo Synthwave / Ambient Chill Tech), volume mixado a <b>-24 dB</b> para manter a voz em destaque absoluto a <b>-6 dB</b>.</li>
    <li><b>Transições:</b> Fade simples de 0.3s ou cortes diretos nos momentos de troca de aba. Evitar efeitos extravagantes que tirem o caráter institucional.</li>
    <li><b>Motion Graphics & Callouts:</b> Inserir selo de 'Risco Definido' e gráficos de pay-off quando o locutor explicar o escudo de proteção para ativos > US$ 100 e o caso NVDA (IV 0%).</li>
  </ul>

  <!-- SEÇÃO 4: PROMPTS DE APOIO PARA B-ROLL & MOTION GRAPHICS -->
  <h2>4. Prompts de Apoio para B-Roll e Motion Graphics (Runway Gen-3 / Midjourney)</h2>
  <div class="callout">
    <div class="callout-title">B-Roll: Proteção de Margem & Escudo de Risco Definido</div>
    <div class="prompt-box">3D cinematic graphic visualization of financial options risk curve, glowing green defined-risk zone with shield icon, dark background with subtle blue volumetric lighting, modern quantitative interface, 8k resolution.</div>
  </div>
  <div class="callout">
    <div class="callout-title">B-Roll: Análise de Volatilidade & Vácuo de Catalisador (Caso NVDA)</div>
    <div class="prompt-box">Cinematic financial chart zooming into compressed implied volatility curve showing IV Rank at zero percent floor, glowing neon cyan data lines, dark glass morphism dashboard, ultra-detailed 8k.</div>
  </div>


</body>
</html>
"""


def get_avatar_instructions_html() -> str:
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Especificação e Prompts para Geração de Avatar — Op_Tasty</title>
  <style>
    @page {
      size: A4;
      margin: 15mm 15mm 18mm 15mm;
      @bottom-right {
        content: counter(page);
        font-size: 8pt;
        font-family: Arial, sans-serif;
        color: #64748b;
      }
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: #0f172a;
      line-height: 1.5;
      font-size: 9.5pt;
      margin: 0;
      padding: 0;
    }
    .header-box {
      border-bottom: 2px solid #3b82f6;
      padding-bottom: 12px;
      margin-bottom: 20px;
    }
    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 8pt;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .badge-blue { background: #dbeafe; color: #1e40af; }
    .badge-purple { background: #f3e8ff; color: #6b21a8; }
    .badge-dark { background: #0f172a; color: #f8fafc; }
    h1 {
      font-size: 18pt;
      color: #0f172a;
      margin: 8px 0 4px 0;
      font-weight: 800;
    }
    .subtitle {
      font-size: 10pt;
      color: #475569;
      margin: 0;
    }
    h2 {
      font-size: 12pt;
      color: #1e3a8a;
      border-left: 4px solid #3b82f6;
      padding-left: 8px;
      margin: 18px 0 10px 0;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.3px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 10px 0 15px 0;
      font-size: 8.8pt;
    }
    th, td {
      border: 1px solid #cbd5e1;
      padding: 6px 8px;
      text-align: left;
      vertical-align: top;
    }
    th {
      background-color: #f1f5f9;
      color: #1e293b;
      font-weight: 700;
    }
    .callout {
      background-color: #f8fafc;
      border: 1px solid #e2e8f0;
      border-left: 4px solid #3b82f6;
      padding: 10px 12px;
      border-radius: 4px;
      margin: 12px 0;
      font-size: 9pt;
    }
    .callout-title {
      font-weight: 700;
      color: #1e3a8a;
      margin-bottom: 4px;
    }
    .prompt-box {
      background: #0f172a;
      color: #e2e8f0;
      font-family: "Courier New", Courier, monospace;
      padding: 8px 10px;
      border-radius: 4px;
      font-size: 8pt;
      margin: 6px 0 12px 0;
      white-space: pre-wrap;
      word-break: break-word;
      border: 1px solid #334155;
    }
    ul, ol {
      margin: 4px 0 8px 16px;
      padding: 0;
    }
    li { margin-bottom: 3px; }
    .page-break { page-break-before: always; }
  </style>
</head>
<body>

  <!-- CABEÇALHO -->
  <div class="header-box">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <span class="badge badge-dark">ESPECIFICAÇÃO DE AVATAR & PERSONA IA</span>
      <span class="badge badge-purple">GUIA DE PROMPTS 2026</span>
    </div>
    <h1>Especificação de Avatar Institucional</h1>
    <p class="subtitle">Persona, Visual, Estilo e Prompts de Geração para o Apresentador Virtual do Op_Tasty</p>
  </div>

  <!-- SEÇÃO 1: CONCEITO E PERSONA -->
  <h2>1. Conceito e Identidade da Persona</h2>
  <p>
    Para que o vídeo tenha máxima credibilidade institucional, o avatar não deve parecer um vendedor animado nem um modelo genérico. A persona precisa transmitir a postura de um <b>Engenheiro Financeiro Sênior / Trader Quantitativo Institucional</b> que domina derivativos e respeita rigorosamente a disciplina matemática.
  </p>

  <table>
    <tr>
      <th style="width: 25%;">Atributo</th>
      <th style="width: 75%;">Definição Conceitual</th>
    </tr>
    <tr>
      <td><b>Nome Sugerido</b></td>
      <td><b>Marcus Vance</b> (Opção Masculina) ou <b>Elena Ross</b> (Opção Feminina)</td>
    </tr>
    <tr>
      <td><b>Idade Aparente</b></td>
      <td>35 a 42 anos (equilíbrio ideal entre maturidade de mercado e inovação tecnológica)</td>
    </tr>
    <tr>
      <td><b>Arquetipo</b></td>
      <td>O Mentor Analítico: calmo, seguro, didático, focado em risco, estatística e processos.</td>
    </tr>
    <tr>
      <td><b>Postura Corporal</b></td>
      <td>Ereta, ombros alinhados, gesticulação moderada e pontual (mãos abertas ao explicar conceitos). Olhar direto para a câmera, transmitindo transparência.</td>
    </tr>
    <tr>
      <td><b>Figurino (Dress Code)</b></td>
      <td><em>Modern Financial Tech</em>: Blazer azul-marinho escuro ou cinza grafite de corte slim, com camisa social branca ou azul claro de gola aberta (sem gravata tradicional engessada, ou suéter gola rolê preto refinado estilo tech executivo).</td>
    </tr>
    <tr>
      <td><b>Acessórios</b></td>
      <td>Relógio clássico discreto de aço escovado. Sem joias chamativas ou adereços reflexivos.</td>
    </tr>
  </table>

  <!-- SEÇÃO 2: CENÁRIO E ILUMINAÇÃO -->
  <h2>2. Cenário de Fundo (Background) & Iluminação</h2>
  <table>
    <tr>
      <th style="width: 25%;">Elemento</th>
      <th style="width: 75%;">Diretriz Visual</th>
    </tr>
    <tr>
      <td><b>Ambiente de Fundo</b></td>
      <td>Mesa de operações quantitativas de alto nível / Trading Room moderna em penumbra controlada. Monitores de alta definição ao fundo exibindo discretamente gráficos escuros com dados em azul e verde (coerente com a paleta do software).</td>
    </tr>
    <tr>
      <td><b>Profundidade de Campo</b></td>
      <td>Foco nítido no avatar com fundo suavemente desfocado (efeito <em>bokeh</em> suave f/2.8), mantendo o apresentador como o foco principal.</td>
    </tr>
    <tr>
      <td><b>Iluminação (Lighting)</b></td>
      <td>Iluminação de estúdio a 3 pontos: luz principal (Key light) suave no rosto; luz de preenchimento (Fill) discreta; e luz de contorno (Rim light) ciano/azul nas bordas dos ombros e cabelo, integrando o avatar à estética dark do screener.</td>
    </tr>
  </table>

  <div class="page-break"></div>

  <!-- SEÇÃO 3: PROMPTS PARA GERAÇÃO DA IMAGEM MATRIZ -->
  <h2>3. Prompts Prontos para Geradores de Imagem (Midjourney v6 / Leonardo AI)</h2>
  <p>Utilize os prompts abaixo para gerar a imagem base fotorrealista que será animada no HeyGen, Synthesia ou D-ID:</p>

  <h3>Opção A — Avatar Masculino (Marcus Vance)</h3>
  <div class="prompt-box">Ultra-realistic 8k medium portrait of a 38-year-old male quantitative options trader, sharp features, well-groomed short dark hair with subtle grey temples, confident and calm expression, looking directly into the camera. Wearing a tailored midnight-navy modern blazer, open-collar crisp white dress shirt, minimalist luxury steel watch. High-end modern quantitative trading desk in background with soft bokeh, dark theme glowing screens displaying options payoff charts in neon blue and green. Professional 3-point studio lighting with subtle cyan rim light on shoulders, cinematic shot, hyperrealistic skin textures, 85mm lens, f/2.8, depth of field, photorealistic, professional color grading --ar 16:9 --style raw --v 6.0</div>

  <h3>Opção B — Avatar Feminino (Elena Ross)</h3>
  <div class="prompt-box">Ultra-realistic 8k medium portrait of a 36-year-old female quantitative portfolio manager, intelligent and trustworthy gaze, neatly styled shoulder-length dark brown hair, natural makeup, confident and calm posture, looking directly into camera. Wearing an elegant tailored charcoal grey modern suit jacket over an ivory silk blouse. Sleek financial technology command room in background with soft bokeh, dark trading monitors showing options chains and volatility smiles. Sophisticated studio lighting with subtle cool blue rim light, natural skin detail, cinematic 85mm portrait, photorealistic, 8k resolution --ar 16:9 --style raw --v 6.0</div>

  <!-- SEÇÃO 4: CONFIGURAÇÃO NAS PLATAFORMAS DE VÍDEO COM IA -->
  <h2>4. Configuração nas Ferramentas de Animação (HeyGen / D-ID / Synthesia)</h2>
  <div class="callout">
    <div class="callout-title">Checklist de Configuração no HeyGen / D-ID</div>
    <ol>
      <li><b>Importação do Avatar:</b> Suba a imagem gerada em 16:9 em formato PNG sem compressão.</li>
      <li><b>Voice Engine:</b> Vincule a API da ElevenLabs ou selecione uma voz neural em Português Brasileiro (PT-BR) com dicção executiva limpa.</li>
      <li><b>Movimentação Labial (Lip-Sync):</b> Ajuste o modelo de sincronização labial para alta fidelidade (v2 ou Enhanced Lip-sync).</li>
      <li><b>Gestos e Expressão:</b> Configure a expressividade para "Natural / Professional" (gestos suaves com as mãos, sem movimentos corporais bruscos ou cabeceios exagerados).</li>
      <li><b>Enquadramento:</b> Posicione o avatar no terço direito ou esquerdo da tela (regra dos terços) para deixar 60% do espaço livre para os B-rolls e capturas do Op_Tasty Screener.</li>
    </ol>
  </div>

  <!-- SEÇÃO 5: GUIA DE DICÇÃO PARA TERMOS DE DERIVATIVOS -->
  <h2>5. Guia de Pronúncia e Fonética para a IA de Voz</h2>
  <table>
    <tr>
      <th>Termo em Inglês</th>
      <th>Como a IA deve pronunciar (Guia Fonético)</th>
      <th>Significado no Sistema</th>
    </tr>
    <tr>
      <td><b>Tastytrade</b></td>
      <td><em>"Têisti-trêid"</em></td>
      <td>Nome da corretora oficial de derivativos</td>
    </tr>
    <tr>
      <td><b>Strike</b></td>
      <td><em>"Istraiki"</em> ou <em>"Straik"</em></td>
      <td>Preço de exercício do contrato</td>
    </tr>
    <tr>
      <td><b>Bid / Ask</b></td>
      <td><em>"Bid / Ésk"</em></td>
      <td>Preço de compra / Preço de venda no book</td>
    </tr>
    <tr>
      <td><b>Bear Put Spread</b></td>
      <td><em>"Bér Pút Spréd"</em></td>
      <td>Trava de baixa com opções de venda</td>
    </tr>
    <tr>
      <td><b>Bull Call Spread</b></td>
      <td><em>"Búl Cól Spréd"</em></td>
      <td>Trava de alta com opções de compra</td>
    </tr>
    <tr>
      <td><b>Iron Condor</b></td>
      <td><em>"Áiron Côm-dor"</em></td>
      <td>Estrutura neutra de crédito em 4 pernas</td>
    </tr>
    <tr>
      <td><b>DTE</b></td>
      <td><em>"D-T-E"</em> ou <em>"Dias para o vencimento"</em></td>
      <td>Days To Expiration</td>
    </tr>
  </table>

</body>
</html>
"""


def generate_pdf_from_html(html_content: str, output_pdf_path: Path, temp_html_path: Path) -> bool:
    temp_html_path.write_text(html_content, encoding="utf-8")
    chrome_path = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")
    edge_path = Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")

    browser_exe = chrome_path if chrome_path.exists() else edge_path
    if not browser_exe.exists():
        print("Erro: Nenhum navegador encontrado para impressão.")
        return False

    file_url = f"file:///{temp_html_path.resolve().as_posix()}"
    cmd = [
        str(browser_exe),
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={output_pdf_path.resolve()}",
        file_url
    ]

    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if res.returncode == 0 and output_pdf_path.exists() and output_pdf_path.stat().st_size > 0:
        print(f"Sucesso: {output_pdf_path.name} gerado ({output_pdf_path.stat().st_size} bytes).")
        return True
    else:
        print(f"Falha ao gerar {output_pdf_path.name}: {res.stderr}")
        return False


def main() -> None:
    root = Path(__file__).parent.parent
    scratch_dir = root / "scratch"
    scratch_dir.mkdir(exist_ok=True)

    pdf1_path = root / "INSTRUCOES_VIDEO_SISTEMA.pdf"
    html1_path = scratch_dir / "temp_video_instrucoes.html"

    pdf2_path = root / "INSTRUCOES_AVATAR_SISTEMA.pdf"
    html2_path = scratch_dir / "temp_avatar_instrucoes.html"

    print("Gerando PDF 1: INSTRUCOES_VIDEO_SISTEMA.pdf...")
    ok1 = generate_pdf_from_html(get_video_instructions_html(), pdf1_path, html1_path)

    print("Gerando PDF 2: INSTRUCOES_AVATAR_SISTEMA.pdf...")
    ok2 = generate_pdf_from_html(get_avatar_instructions_html(), pdf2_path, html2_path)

    if ok1 and ok2:
        print("\nTodos os PDFs solicitados foram gerados com sucesso!")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
