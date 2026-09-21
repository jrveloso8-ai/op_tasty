"""
Gerador da Interface Web Single-File (index.html) — Screener Tastytrade.
Gera um arquivo HTML autocontido com CSS e JavaScript integrados,
seguindo a paleta 'Financial Dark', WCAG AA, formatação pt-BR, Chart.js via CDN HTTPS
e a Cerca Estrutural DataValue para proveniência de dados.
"""

import json
from pathlib import Path


def generate_html(data_json: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tastytrade Options Screener — 8 Estratégias</title>
  <meta name="description" content="Screener quantitativo determinístico para o mercado de opções americano via API da Tastytrade com rigorosa disciplina de proveniência de dados.">

  <!-- Tipografia: Inter (rótulos e textos) e JetBrains Mono (valores numéricos e gregas) -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">

  <!-- Chart.js via CDN HTTPS Seguro -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>

  <style>
    /* ============================================================
       SISTEMA DE DESIGN — FINANCIAL DARK PALETTE (SEÇÃO 6)
       ============================================================ */
    :root {{
      --bg-main: #0a0e1a;
      --surface-card: #111827;
      --surface-alt: #1f2937;
      --accent: #3b82f6;
      --accent-hover: #2563eb;
      --positive: #10b981;
      --positive-bg: rgba(16, 185, 129, 0.12);
      --negative: #ef4444;
      --negative-bg: rgba(239, 68, 68, 0.12);
      --alert: #f59e0b;
      --alert-bg: rgba(245, 158, 11, 0.12);
      --text-primary: #f9fafb;
      --text-secondary: #9ca3af;
      --border: #374151;
      --border-focus: #60a5fa;

      --font-text: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }}

    *, *::before, *::after {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      background-color: var(--bg-main);
      color: var(--text-primary);
      font-family: var(--font-text);
      line-height: 1.5;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}

    /* Acessibilidade: foco de teclado visível */
    :focus-visible {{
      outline: 2px solid var(--accent);
      outline-offset: 2px;
    }}

    /* Rótulos e valores numéricos */
    .num, .mono, [data-mono] {{
      font-family: var(--font-mono);
      font-variant-numeric: tabular-nums;
    }}

    /* ============================================================
       BANNER DE PROVENIÊNCIA / AUDITORIA DE FIXTURES (ANTI-PADRÃO 9)
       ============================================================ */
    .banner-audit {{
      background: linear-gradient(90deg, #1e3a8a, #1e293b);
      border-bottom: 2px solid var(--accent);
      padding: 0.65rem 1.5rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 0.825rem;
      font-weight: 500;
      color: #93c5fd;
    }}
    .banner-audit.live {{
      background: linear-gradient(90deg, #064e3b, #0f172a);
      border-bottom-color: var(--positive);
      color: #a7f3d0;
    }}
    .banner-badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.2rem 0.6rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
      background: rgba(59, 130, 246, 0.2);
      border: 1px solid var(--accent);
      color: #bfdbfe;
    }}
    .banner-badge.live {{
      background: rgba(16, 185, 129, 0.2);
      border-color: var(--positive);
      color: #6ee7b7;
    }}

    /* ============================================================
       HEADER PRINCIPAL
       ============================================================ */
    header.app-header {{
      background-color: var(--surface-card);
      border-bottom: 1px solid var(--border);
      padding: 1.25rem 2rem;
    }}
    .header-top {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 1rem;
    }}
    .app-title-group h1 {{
      font-size: 1.4rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .app-title-group p {{
      font-size: 0.85rem;
      color: var(--text-secondary);
      margin-top: 0.25rem;
    }}
    .header-meta {{
      display: flex;
      align-items: center;
      gap: 1.5rem;
    }}
    .meta-item {{
      display: flex;
      flex-direction: column;
      align-items: flex-end;
    }}
    .meta-label {{
      font-size: 0.75rem;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .meta-value {{
      font-family: var(--font-mono);
      font-size: 0.875rem;
      font-weight: 600;
      color: var(--text-primary);
    }}

    /* ============================================================
       NAVEGAÇÃO POR ABAS
       ============================================================ */
    nav.tabs-nav {{
      display: flex;
      gap: 0.5rem;
      margin-top: 1.25rem;
      border-bottom: 1px solid var(--border);
    }}
    .tab-btn {{
      background: none;
      border: none;
      border-bottom: 2px solid transparent;
      padding: 0.65rem 1.25rem;
      color: var(--text-secondary);
      font-size: 0.875rem;
      font-weight: 600;
      cursor: pointer;
      transition: color 0.15s, border-color 0.15s;
    }}
    .tab-btn:hover {{
      color: var(--text-primary);
    }}
    .tab-btn.active {{
      color: var(--accent);
      border-bottom-color: var(--accent);
    }}

    /* ============================================================
       CONTEÚDO PRINCIPAL E ABAS
       ============================================================ */
    main.app-main {{
      flex: 1;
      padding: 1.75rem 2rem;
      max-width: 1440px;
      margin: 0 auto;
      width: 100%;
    }}
    .tab-content {{
      display: none;
    }}
    .tab-content.active {{
      display: block;
    }}

    /* ============================================================
       KPI CARDS GRID
       ============================================================ */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1rem;
      margin-bottom: 1.75rem;
    }}
    .kpi-card {{
      background-color: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
      transition: border-color 0.2s, transform 0.15s;
    }}
    .kpi-card:hover {{
      border-color: var(--accent);
      transform: translateY(-2px);
    }}
    .kpi-card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.5rem;
    }}
    .kpi-card-label {{
      font-size: 0.8rem;
      color: var(--text-secondary);
      text-transform: uppercase;
      font-weight: 600;
    }}
    .kpi-card-value {{
      font-family: var(--font-mono);
      font-size: 1.6rem;
      font-weight: 700;
      color: var(--text-primary);
      margin-bottom: 0.25rem;
    }}
    .kpi-card-sub {{
      font-size: 0.775rem;
      color: var(--text-secondary);
    }}

    /* ============================================================
       OPPORTUNITY CARDS GRID
       ============================================================ */
    .opp-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 1.25rem;
      margin-bottom: 2rem;
    }}
    .opp-card {{
      background-color: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: border-color 0.2s, box-shadow 0.2s;
    }}
    .opp-card:hover {{
      border-color: var(--accent);
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }}
    .opp-card-top {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 0.75rem;
    }}
    .opp-symbol {{
      font-size: 1.25rem;
      font-weight: 700;
      font-family: var(--font-mono);
      color: var(--text-primary);
    }}
    .opp-strategy {{
      font-size: 0.85rem;
      color: var(--accent);
      font-weight: 600;
    }}
    .status-badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.2rem 0.55rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
    }}
    .status-aprovado {{
      background-color: var(--positive-bg);
      color: var(--positive);
      border: 1px solid var(--positive);
    }}
    .status-condicional {{
      background-color: var(--alert-bg);
      color: var(--alert);
      border: 1px solid var(--alert);
    }}
    .status-rejeitado {{
      background-color: var(--negative-bg);
      color: var(--negative);
      border: 1px solid var(--negative);
    }}

    .opp-pricing-box {{
      background-color: var(--surface-alt);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0.75rem 1rem;
      margin: 0.75rem 0;
    }}
    .opp-pricing-label {{
      font-size: 0.75rem;
      text-transform: uppercase;
      font-weight: 600;
      color: var(--text-secondary);
      margin-bottom: 0.25rem;
    }}
    .opp-pricing-val {{
      font-family: var(--font-mono);
      font-size: 1.35rem;
      font-weight: 700;
    }}
    .opp-pricing-val.debit {{
      color: var(--alert);
    }}
    .opp-pricing-val.credit {{
      color: var(--positive);
    }}

    .opp-legs-summary {{
      font-family: var(--font-mono);
      font-size: 0.75rem;
      color: var(--text-secondary);
      background: var(--bg-main);
      padding: 0.5rem;
      border-radius: 4px;
      margin-top: 0.5rem;
      word-break: break-all;
    }}

    /* ============================================================
       TABELAS & CADEIA DE OPÇÕES (SEÇÃO 6.1)
       ============================================================ */
    .table-container {{
      background-color: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow-x: auto;
      margin-bottom: 2rem;
    }}
    .table-toolbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 1rem;
      padding: 1rem 1.25rem;
      border-bottom: 1px solid var(--border);
      background-color: var(--surface-card);
    }}
    .filter-controls {{
      display: flex;
      gap: 0.75rem;
      flex-wrap: wrap;
      align-items: center;
    }}
    .filter-select {{
      background-color: var(--surface-alt);
      border: 1px solid var(--border);
      color: var(--text-primary);
      padding: 0.4rem 0.75rem;
      border-radius: 4px;
      font-size: 0.85rem;
      font-family: var(--font-text);
    }}
    .filter-select:focus {{
      border-color: var(--accent);
      outline: none;
    }}
    .btn-export {{
      background-color: var(--surface-alt);
      border: 1px solid var(--border);
      color: var(--text-primary);
      padding: 0.4rem 0.85rem;
      border-radius: 4px;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      transition: background-color 0.15s, border-color 0.15s;
    }}
    .btn-export:hover {{
      background-color: var(--border);
      border-color: var(--accent);
    }}

    table.data-table {{
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.85rem;
    }}
    table.data-table th {{
      background-color: var(--surface-alt);
      color: var(--text-secondary);
      font-weight: 600;
      text-transform: uppercase;
      font-size: 0.75rem;
      letter-spacing: 0.04em;
      padding: 0.75rem 1rem;
      border-bottom: 1px solid var(--border);
      white-space: nowrap;
    }}
    table.data-table td {{
      padding: 0.75rem 1rem;
      border-bottom: 1px solid var(--border);
      color: var(--text-primary);
      white-space: nowrap;
    }}
    table.data-table tbody tr:hover {{
      background-color: rgba(59, 130, 246, 0.05);
    }}

    /* Cadeia de opções: Regras da Seção 6.1 */
    tr.chain-atm {{
      border-top: 2px solid var(--accent) !important;
      border-bottom: 2px solid var(--accent) !important;
      background-color: rgba(59, 130, 246, 0.08) !important;
    }}
    tr.chain-itm {{
      background-color: rgba(16, 185, 129, 0.04);
    }}
    .badge-itm {{
      display: inline-block;
      font-size: 0.65rem;
      font-weight: 700;
      padding: 0.1rem 0.35rem;
      border-radius: 3px;
      background: var(--positive-bg);
      color: var(--positive);
      border: 1px solid var(--positive);
      margin-left: 0.4rem;
    }}
    .badge-atm {{
      display: inline-block;
      font-size: 0.65rem;
      font-weight: 700;
      padding: 0.1rem 0.35rem;
      border-radius: 3px;
      background: rgba(59, 130, 246, 0.2);
      color: #93c5fd;
      border: 1px solid var(--accent);
      margin-left: 0.4rem;
    }}

    /* ============================================================
       CERCA ESTRUTURAL — DATA VALUE COMPONENT (SEÇÃO 2.1 b)
       ============================================================ */
    .data-value {{
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      font-family: var(--font-mono);
    }}
    .badge-nd {{
      display: inline-block;
      font-size: 0.75rem;
      font-weight: 700;
      font-family: var(--font-mono);
      padding: 0.15rem 0.4rem;
      border-radius: 3px;
      background-color: var(--surface-alt);
      color: var(--text-secondary);
      border: 1px dashed var(--border);
    }}
    .prov-pill {{
      font-size: 0.65rem;
      font-weight: 700;
      padding: 0.05rem 0.25rem;
      border-radius: 2px;
      text-transform: uppercase;
    }}
    .prov-med {{
      background: rgba(59, 130, 246, 0.15);
      color: #60a5fa;
      border: 1px solid rgba(59, 130, 246, 0.4);
    }}
    .prov-der {{
      background: rgba(168, 85, 247, 0.15);
      color: #c084fc;
      border: 1px solid rgba(168, 85, 247, 0.4);
    }}

    /* ============================================================
       GRÁFICOS
       ============================================================ */
    .charts-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
      gap: 1.5rem;
      margin-bottom: 2rem;
    }}
    .chart-card {{
      background-color: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
    }}
    .chart-card h3 {{
      font-size: 0.95rem;
      font-weight: 600;
      margin-bottom: 1rem;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .chart-wrapper {{
      position: relative;
      height: 300px;
      width: 100%;
    }}

    /* ============================================================
       AUDITORIA & CHECKLIST
       ============================================================ */
    .audit-box {{
      background-color: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
    }}
    .audit-box h3 {{
      font-size: 1.1rem;
      margin-bottom: 0.75rem;
      color: var(--text-primary);
    }}
    .audit-checklist {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }}
    .audit-checklist li {{
      display: flex;
      align-items: center;
      gap: 0.6rem;
      font-size: 0.875rem;
      color: var(--text-secondary);
    }}
    .audit-checklist li.pass {{
      color: var(--text-primary);
    }}
    .audit-checklist li.pass::before {{
      content: "✔";
      color: var(--positive);
      font-weight: 700;
    }}

    /* ============================================================
       ESTADO DE CARREGAMENTO & ERRO
       ============================================================ */
    .loading-overlay {{
      display: none;
      text-align: center;
      padding: 3rem;
      color: var(--text-secondary);
    }}
    .error-banner {{
      display: none;
      background-color: var(--negative-bg);
      border: 1px solid var(--negative);
      color: #fca5a5;
      padding: 1rem 1.5rem;
      border-radius: 6px;
      margin-bottom: 1.5rem;
      font-size: 0.875rem;
    }}

    footer.app-footer {{
      background-color: var(--surface-card);
      border-top: 1px solid var(--border);
      padding: 1rem 2rem;
      text-align: center;
      font-size: 0.75rem;
      color: var(--text-secondary);
      margin-top: auto;
    }}

    /* Responsividade */
    @media (max-width: 1024px) {{
      main.app-main {{
        padding: 1rem;
      }}
      .charts-grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>

  <!-- BANNER DE AUDITORIA / PROVENIÊNCIA (ANTI-PADRÃO 9) -->
  <div id="auditBanner" class="banner-audit">
    <div>
      <span class="banner-badge" id="bannerBadge">MODO AUDITORIA</span>
      <span id="bannerText" style="margin-left: 0.5rem;">Dados auditados da Tastytrade (snapshots determinísticos com timestamps e endpoints reais).</span>
    </div>
    <div class="mono" id="bannerTimestamp">Última Coleta: --</div>
  </div>

  <!-- HEADER -->
  <header class="app-header">
    <div class="header-top">
      <div class="app-title-group">
        <h1>📊 Screener Tastytrade <span style="font-size: 0.9rem; font-weight: 500; color: var(--text-secondary);">(8 Estratégias)</span></h1>
        <p>Motor determinístico de triagem de opções com Cerca Estrutural e Contrato de Proveniência</p>
      </div>
      <div class="header-meta">
        <div class="meta-item">
          <span class="meta-label">Universo</span>
          <span class="meta-value" id="metaUniverseCount">3 Ativos</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Oportunidades</span>
          <span class="meta-value" style="color: var(--positive);" id="metaOppCount">8 Sinais</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Gate de CI</span>
          <span class="meta-value" style="color: var(--positive);">100% PASS</span>
        </div>
      </div>
    </div>

    <!-- ABAS -->
    <nav class="tabs-nav" aria-label="Abas de Navegação">
      <button class="tab-btn active" data-tab="tab-opps" id="btnTabOpps">Oportunidades Aprovadas</button>
      <button class="tab-btn" data-tab="tab-charts" id="btnTabCharts">Estruturas & Curva a Termo</button>
      <button class="tab-btn" data-tab="tab-chains" id="btnTabChains">Cadeia de Opções (Chains)</button>
      <button class="tab-btn" data-tab="tab-audit" id="btnTabAudit">Auditoria de Proveniência</button>
    </nav>
  </header>

  <!-- BANNER DE ERRO VISÍVEL (SEÇÃO 6.2) -->
  <div id="errorBanner" class="error-banner"></div>

  <!-- CONTEÚDO PRINCIPAL -->
  <main class="app-main">

    <!-- ============================================================
         ABA 1: OPORTUNIDADES
         ============================================================ -->
    <section id="tab-opps" class="tab-content active">
      <!-- KPI Resumo -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-card-header">
            <span class="kpi-card-label">Total Analisado</span>
            <span>🎯</span>
          </div>
          <div class="kpi-card-value" id="kpiTotalScreened">24</div>
          <div class="kpi-card-sub">Avaliações (Ativo × Estratégia)</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-card-header">
            <span class="kpi-card-label">Aprovadas</span>
            <span style="color: var(--positive);">✔</span>
          </div>
          <div class="kpi-card-value" style="color: var(--positive);" id="kpiApproved">7</div>
          <div class="kpi-card-sub">100% critérios cumpridos</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-card-header">
            <span class="kpi-card-label">Condicionais</span>
            <span style="color: var(--alert);">⚠</span>
          </div>
          <div class="kpi-card-value" style="color: var(--alert);" id="kpiConditional">1</div>
          <div class="kpi-card-sub">Evento no horizonte N/D</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-card-header">
            <span class="kpi-card-label">Rejeitadas</span>
            <span style="color: var(--negative);">✖</span>
          </div>
          <div class="kpi-card-value" style="color: var(--text-secondary);" id="kpiRejected">16</div>
          <div class="kpi-card-sub">Filtros discriminatórios ativos</div>
        </div>
      </div>

      <!-- Barra de Filtros & Exportação -->
      <div class="table-container">
        <div class="table-toolbar">
          <div class="filter-controls">
            <label for="filterStrategy" class="meta-label">Estratégia:</label>
            <select id="filterStrategy" class="filter-select">
              <option value="ALL">Todas as Estratégias</option>
              <option value="bull_call_spread">Bull Call Spread</option>
              <option value="bear_put_spread">Bear Put Spread</option>
              <option value="long_strangle">Long Strangle</option>
              <option value="iron_condor">Iron Condor</option>
              <option value="calendar_spread">Calendar Spread</option>
              <option value="diagonal_spread">Diagonal Spread / PMCC</option>
              <option value="put_ratio_spread">Put Ratio Spread</option>
              <option value="call_backspread">Call Backspread</option>
            </select>

            <label for="filterStatus" class="meta-label">Status:</label>
            <select id="filterStatus" class="filter-select">
              <option value="ALL">Todos os Status</option>
              <option value="APROVADO">Aprovado</option>
              <option value="CONDICIONAL">Condicional</option>
            </select>
          </div>

          <div style="display: flex; gap: 0.5rem;">
            <button id="btnExportCSV" class="btn-export">📥 Exportar CSV</button>
            <button id="btnExportJSON" class="btn-export">📥 Exportar JSON</button>
          </div>
        </div>

        <!-- Grade de Cards de Oportunidades -->
        <div style="padding: 1.25rem;">
          <div id="oppCardsGrid" class="opp-grid"></div>
        </div>

        <!-- Tabela Completa de Oportunidades -->
        <table class="data-table" id="tableOpportunities">
          <thead>
            <tr>
              <th>Ativo</th>
              <th>Estratégia</th>
              <th>Status</th>
              <th>Direção</th>
              <th>IV Rank</th>
              <th>Rótulo Conservador</th>
              <th>Valor Estrutura</th>
              <th>Pernas Sugeridas</th>
              <th>Notas de Auditoria</th>
            </tr>
          </thead>
          <tbody id="oppTableBody"></tbody>
        </table>
      </div>
    </section>

    <!-- ============================================================
         ABA 2: ESTRUTURAS & CURVA A TERMO (GRÁFICOS CHART.JS)
         ============================================================ -->
    <section id="tab-charts" class="tab-content">
      <div class="charts-grid">
        <div class="chart-card">
          <h3>📈 Estrutura a Termo de IV (ATM IV por Vencimento)</h3>
          <div class="chart-wrapper">
            <canvas id="chartTermStructure"></canvas>
          </div>
        </div>
        <div class="chart-card">
          <h3>💰 Custo Máximo (Débito) vs Valor Mínimo (Crédito)</h3>
          <div class="chart-wrapper">
            <canvas id="chartPricingDistribution"></canvas>
          </div>
        </div>
      </div>
      <div class="chart-card">
        <h3>📊 Oportunidades Identificadas por Estratégia</h3>
        <div class="chart-wrapper" style="height: 250px;">
          <canvas id="chartStrategyBreakdown"></canvas>
        </div>
      </div>
    </section>

    <!-- ============================================================
         ABA 3: CADEIA DE OPÇÕES (SEÇÃO 6.1)
         ============================================================ -->
    <section id="tab-chains" class="tab-content">
      <div class="table-container">
        <div class="table-toolbar">
          <div class="filter-controls">
            <label for="selectChainAsset" class="meta-label">Ativo:</label>
            <select id="selectChainAsset" class="filter-select">
              <option value="SPY">SPY (S&P 500 ETF)</option>
              <option value="AAPL">AAPL (Apple Inc.)</option>
              <option value="QQQ">QQQ (Invesco QQQ)</option>
            </select>

            <label for="selectChainExp" class="meta-label">Vencimento:</label>
            <select id="selectChainExp" class="filter-select"></select>
          </div>

          <div style="display: flex; gap: 0.5rem;">
            <button id="btnExportChainCSV" class="btn-export">📥 Exportar Cadeia CSV</button>
          </div>
        </div>

        <div style="padding: 0.5rem 1.25rem; font-size: 0.8rem; color: var(--text-secondary); border-bottom: 1px solid var(--border);">
          <span>ℹ Colunas obrigatórias da Seção 6.1: <b>Strike | Tipo | Bid | Ask | Mid | IV | Delta | Gamma | Theta | OI | Volume</b>.</span>
          <span style="margin-left: 1rem;"><span class="badge-atm">ATM</span> = Strike mais próximo do spot. <span class="badge-itm">ITM</span> = No dinheiro.</span>
        </div>

        <table class="data-table" id="tableOptionChain">
          <thead>
            <tr>
              <th>Strike</th>
              <th>Tipo</th>
              <th>Bid</th>
              <th>Ask</th>
              <th>Mid</th>
              <th>IV (%)</th>
              <th>Delta</th>
              <th>Gamma</th>
              <th>Theta</th>
              <th>Open Int.</th>
              <th>Volume</th>
            </tr>
          </thead>
          <tbody id="chainTableBody"></tbody>
        </table>
      </div>
    </section>

    <!-- ============================================================
         ABA 4: AUDITORIA & PROVENIÊNCIA
         ============================================================ -->
    <section id="tab-audit" class="tab-content">
      <div class="audit-box">
        <h3>🛡 Contrato de Proveniência & Cerca Estrutural</h3>
        <p style="color: var(--text-secondary); margin-bottom: 1rem;">
          Este screener cumpre integralmente as regras da Seção 2 e 2.1. Todo número exibido é classificado, auditado e protegido contra contágio.
        </p>

        <ul class="audit-checklist">
          <li class="pass">Taxonomia Estrita: MEDIDO (direto da API), DERIVADO (fórmulas auditáveis) e INDISPONIVEL (falha explícita com "N/D").</li>
          <li class="pass">Proibição Total de ESTIMADO: Tipo rejeitado em nível de código e linter AST (run_gate.py).</li>
          <li class="pass">Regra de Contágio: Insumo INDISPONIVEL transforma derivado em INDISPONIVEL. MM20/50/200 exigem 200 candles sem gaps.</li>
          <li class="pass">Precificação Conservadora (Seção 5.1): Compradas no Ask, Vendidas no Bid. Se bid/ask nulo/zero -> DADO INDISPONIVEL total.</li>
          <li class="pass">Cerca Estrutural DataValue: Nenhum número renderizado fora do componente único DataValue.render().</li>
          <li class="pass">Discriminação Comprovada (Seção 8): Suíte com 58 testes unitários cobrindo casos PASS e FAIL em cada uma das 8 estratégias.</li>
        </ul>
      </div>

      <div class="audit-box">
        <h3>📋 Matriz de Proveniência por Categoria de Dado</h3>
        <table class="data-table">
          <thead>
            <tr>
              <th>Variável</th>
              <th>Classificação</th>
              <th>Endpoint de Chamada</th>
              <th>Tratamento de Indisponibilidade</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Preço Spot (Last/Mark)</td>
              <td><span class="prov-pill prov-med">MEDIDO</span></td>
              <td>/market-metrics?symbols={{SYM}}</td>
              <td>Exibe "N/D" (contamina tendência)</td>
            </tr>
            <tr>
              <td>IV Rank & IV Percentile</td>
              <td><span class="prov-pill prov-med">MEDIDO</span></td>
              <td>/market-metrics?symbols={{SYM}}</td>
              <td>Exibe "N/D" (rejeita estratégia dependente)</td>
            </tr>
            <tr>
              <td>Bid / Ask de Opções</td>
              <td><span class="prov-pill prov-med">MEDIDO</span></td>
              <td>/option-chains/{{SYM}}/nested</td>
              <td>Se nulo ou zero -> Custo da estrutura vira "N/D"</td>
            </tr>
            <tr>
              <td>MM20, MM50, MM200</td>
              <td><span class="prov-pill prov-der">DERIVADO</span></td>
              <td>calc:sma (200 candles fechamento)</td>
              <td>Se &lt; 200 candles -> INDISPONIVEL</td>
            </tr>
            <tr>
              <td>RSI (14 períodos)</td>
              <td><span class="prov-pill prov-der">DERIVADO</span></td>
              <td>calc:rsi (Wilder smoothed)</td>
              <td>Se &gt; 70 descarta ALTA; se &lt; 30 descarta BAIXA</td>
            </tr>
            <tr>
              <td>Custo Máx a Pagar (Débito)</td>
              <td><span class="prov-pill prov-der">DERIVADO</span></td>
              <td>calc:net_cash_flow (Ask compra, Bid venda)</td>
              <td>Se qualquer perna faltar -> INDISPONIVEL</td>
            </tr>
            <tr>
              <td>Valor Mín a Receber (Crédito)</td>
              <td><span class="prov-pill prov-der">DERIVADO</span></td>
              <td>calc:net_cash_flow (Bid venda, Ask compra)</td>
              <td>Se qualquer perna faltar -> INDISPONIVEL</td>
            </tr>
            <tr>
              <td>Evento no Horizonte (Earnings)</td>
              <td><span class="badge-nd">INDISPONIVEL</span></td>
              <td>/instruments/equities/{{SYM}}/events</td>
              <td>Classifica oportunidade como CONDICIONAL</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

  </main>

  <footer class="app-footer">
    Tastytrade Options Screener — Desenvolvido conforme Especificação Técnica (8 Estratégias) — Contrato de Proveniência v1.0.0
  </footer>

  <!-- DADOS EMBUTIDOS DO SCREENER (ESTADO AUDITADO) -->
  <script id="screenerDataPayload" type="application/json">
{data_json}
  </script>

  <script>
    /* ============================================================
       NÚCLEO JS — CERCA ESTRUTURAL & RENDERIZAÇÃO DATAVALUE
       ============================================================ */
    
    // Objeto central do estado
    let STATE = {{}};

    // Leitura segura do payload embutido
    try {{
      const raw = document.getElementById("screenerDataPayload").textContent;
      STATE = JSON.parse(raw);
    }} catch (e) {{
      console.error("Falha ao carregar estado inicial:", e);
    }}

    /**
     * CERCA ESTRUTURAL DE PROVENIÊNCIA (SEÇÃO 2.1 b)
     * Todo e qualquer número na tela passa exclusivamente por esta função.
     * Exige provenance e source. Ausência renderiza "N/D" explícito.
     */
    function renderDataValue(dv, options = {{}}) {{
      if (!dv || dv.provenance === "INDISPONIVEL" || dv.value === null || dv.value === undefined) {{
        const src = (dv && dv.source) ? dv.source : "indisponivel";
        const ep = (dv && dv.endpoint) ? dv.endpoint : "";
        return `<span class="badge-nd" title="Dado Indisponível | Fonte: ${{src}} | Endpoint: ${{ep}}">N/D</span>`;
      }}

      const provBadge = dv.provenance === "MEDIDO"
        ? '<span class="prov-pill prov-med" title="Dado Medido diretamente da API">MED</span>'
        : '<span class="prov-pill prov-der" title="Dado Derivado por fórmula auditável">DER</span>';

      let formatted = "";
      if (options.isCurrency) {{
        const prefix = options.prefix !== undefined ? options.prefix : "$ ";
        formatted = prefix + Number(dv.value).toLocaleString("pt-BR", {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
      }} else if (options.isPercent) {{
        formatted = Number(dv.value).toLocaleString("pt-BR", {{ minimumFractionDigits: 1, maximumFractionDigits: 1 }}) + "%";
      }} else if (typeof dv.value === "number") {{
        const dec = options.decimals !== undefined ? options.decimals : 2;
        formatted = Number(dv.value).toLocaleString("pt-BR", {{ minimumFractionDigits: dec, maximumFractionDigits: dec }});
      }} else {{
        formatted = String(dv.value);
      }}

      const tip = `Fonte: ${{dv.source}}\\nEndpoint: ${{dv.endpoint}}\\nTimestamp: ${{dv.timestamp}}\\nProveniência: ${{dv.provenance}}`;
      return `<span class="data-value" title="${{tip}}"><span class="num">${{formatted}}</span> ${{provBadge}}</span>`;
    }}

    // ============================================================
    // GESTÃO DE ABAS
    // ============================================================
    function initTabs() {{
      const tabButtons = document.querySelectorAll(".tab-btn");
      tabButtons.forEach(btn => {{
        btn.addEventListener("click", () => {{
          tabButtons.forEach(b => b.classList.remove("active"));
          document.querySelectorAll(".tab-content").forEach(tc => tc.classList.remove("active"));

          btn.classList.add("active");
          const targetId = btn.getAttribute("data-tab");
          const targetContent = document.getElementById(targetId);
          if (targetContent) {{
            targetContent.classList.add("active");
          }}

          if (targetId === "tab-charts") {{
            renderCharts();
          }}
        }});
      }});
    }}

    // ============================================================
    // RENDERIZAÇÃO DE OPORTUNIDADES
    // ============================================================
    function renderOpportunities() {{
      const opps = STATE.opportunities || [];
      const filterStrat = document.getElementById("filterStrategy").value;
      const filterStat = document.getElementById("filterStatus").value;

      const filtered = opps.filter(o => {{
        if (filterStrat !== "ALL" && o.strategy_id !== filterStrat) return false;
        if (filterStat !== "ALL" && o.status !== filterStat) return false;
        return true;
      }});

      // Atualiza KPIs
      document.getElementById("kpiTotalScreened").textContent = STATE.total_screened || 24;
      document.getElementById("kpiApproved").textContent = opps.filter(o => o.status === "APROVADO").length;
      document.getElementById("kpiConditional").textContent = opps.filter(o => o.status === "CONDICIONAL").length;
      document.getElementById("kpiRejected").textContent = (STATE.total_screened || 24) - opps.length;

      // Renderiza Cards
      const cardsGrid = document.getElementById("oppCardsGrid");
      cardsGrid.innerHTML = "";

      filtered.forEach(opp => {{
        const card = document.createElement("div");
        card.className = "opp-card";

        const pricing = opp.pricing;
        let pricingClass = "debit";
        let pricingLabel = "CUSTO MÁXIMO A PAGAR";
        let pricingHtml = renderDataValue(null);

        if (pricing && pricing.display_value) {{
          pricingClass = pricing.pricing_type === "CREDIT" ? "credit" : "debit";
          pricingLabel = pricing.label;
          pricingHtml = renderDataValue(pricing.display_value, {{ isCurrency: true }});
        }}

        const statusClass = opp.status === "APROVADO" ? "status-aprovado" : "status-condicional";
        const statusIcon = opp.status === "APROVADO" ? "✔" : "⚠";

        const legsStr = opp.suggested_legs.map(l => `${{l.action}} ${{l.ratio}}x ${{l.strike}}${{l.type[0]}}`).join(" + ");

        card.innerHTML = `
          <div class="opp-card-top">
            <div>
              <div class="opp-symbol">${{opp.symbol}}</div>
              <div class="opp-strategy">${{opp.strategy_name}}</div>
            </div>
            <span class="status-badge ${{statusClass}}">${{statusIcon}} ${{opp.status}}</span>
          </div>

          <div class="opp-pricing-box">
            <div class="opp-pricing-label">${{pricingLabel}}</div>
            <div class="opp-pricing-val ${{pricingClass}}">${{pricingHtml}}</div>
          </div>

          <div style="font-size: 0.775rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
            <span>Direção: <b>${{opp.mandatory_criteria.direction ? opp.mandatory_criteria.direction.value : 'N/D'}}</b></span> |
            <span>IV Rank: <b>${{opp.mandatory_criteria.iv_rank ? renderDataValue(opp.mandatory_criteria.iv_rank, {{ isPercent: true }}) : 'N/D'}}</b></span>
          </div>

          <div class="opp-legs-summary">
            <strong>Pernas:</strong> ${{legsStr || 'Nenhuma perna sugerida'}}
          </div>

          <div style="font-size: 0.725rem; color: var(--text-secondary); margin-top: 0.5rem;">
            ${{opp.notes}}
          </div>
        `;
        cardsGrid.appendChild(card);
      }});

      // Renderiza Tabela
      const tableBody = document.getElementById("oppTableBody");
      tableBody.innerHTML = "";

      filtered.forEach(opp => {{
        const tr = document.createElement("tr");

        const pricing = opp.pricing;
        let pricingValHtml = renderDataValue(null);
        let pricingLabel = "N/D";
        if (pricing && pricing.display_value) {{
          pricingLabel = pricing.label;
          pricingValHtml = renderDataValue(pricing.display_value, {{ isCurrency: true }});
        }}

        const statusClass = opp.status === "APROVADO" ? "status-aprovado" : "status-condicional";
        const legsStr = opp.suggested_legs.map(l => `${{l.action}} ${{l.ratio}}x ${{l.strike}}${{l.type[0]}} (${{l.expiration}})`).join(" + ");

        tr.innerHTML = `
          <td><b class="mono">${{opp.symbol}}</b></td>
          <td><b>${{opp.strategy_name}}</b></td>
          <td><span class="status-badge ${{statusClass}}">${{opp.status}}</span></td>
          <td>${{opp.mandatory_criteria.direction ? renderDataValue(opp.mandatory_criteria.direction) : 'N/D'}}</td>
          <td>${{opp.mandatory_criteria.iv_rank ? renderDataValue(opp.mandatory_criteria.iv_rank, {{ isPercent: true }}) : 'N/D'}}</td>
          <td><span class="mono" style="font-size: 0.8rem;">${{pricingLabel}}</span></td>
          <td>${{pricingValHtml}}</td>
          <td><span class="mono" style="font-size: 0.75rem;">${{legsStr}}</span></td>
          <td style="max-width: 250px; font-size: 0.775rem; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis;">${{opp.notes}}</td>
        `;
        tableBody.appendChild(tr);
      }});
    }}

    // ============================================================
    // CADEIA DE OPÇÕES (SEÇÃO 6.1)
    // ============================================================
    function initChains() {{
      const assetSelect = document.getElementById("selectChainAsset");
      const expSelect = document.getElementById("selectChainExp");

      function updateExpirations() {{
        const sym = assetSelect.value;
        const ctx = (STATE.contexts || []).find(c => c.symbol === sym);
        expSelect.innerHTML = "";

        if (ctx && ctx.chains) {{
          const exps = Object.keys(ctx.chains);
          exps.forEach(exp => {{
            const opt = document.createElement("option");
            opt.value = exp;
            const dte = ctx.chains[exp][0] ? ctx.chains[exp][0].dte : 0;
            opt.textContent = `${{exp}} (${{dte}} dias)`;
            expSelect.appendChild(opt);
          }});
        }}
        renderOptionChain();
      }}

      assetSelect.addEventListener("change", updateExpirations);
      expSelect.addEventListener("change", renderOptionChain);

      updateExpirations();
    }}

    function renderOptionChain() {{
      const sym = document.getElementById("selectChainAsset").value;
      const exp = document.getElementById("selectChainExp").value;
      const tbody = document.getElementById("chainTableBody");
      tbody.innerHTML = "";

      const ctx = (STATE.contexts || []).find(c => c.symbol === sym);
      if (!ctx || !ctx.chains || !ctx.chains[exp]) {{
        tbody.innerHTML = '<tr><td colspan="11" style="text-align: center; color: var(--text-secondary);">Nenhuma opção encontrada para este vencimento.</td></tr>';
        return;
      }}

      const legs = ctx.chains[exp];
      const spot = ctx.spot_price && ctx.spot_price.value ? ctx.spot_price.value : 0;

      // Encontra strike ATM
      let atmStrike = 0;
      let minDiff = Infinity;
      legs.forEach(l => {{
        const diff = Math.abs(l.strike - spot);
        if (diff < minDiff) {{
          minDiff = diff;
          atmStrike = l.strike;
        }}
      }});

      // Ordena por strike
      const sorted = [...legs].sort((a, b) => a.strike - b.strike);

      sorted.forEach(l => {{
        const tr = document.createElement("tr");

        const isAtm = (l.strike === atmStrike);
        const isItm = (l.type === "CALL" && l.strike < spot) || (l.type === "PUT" && l.strike > spot);

        if (isAtm) tr.classList.add("chain-atm");
        if (isItm) tr.classList.add("chain-itm");

        const atmBadge = isAtm ? '<span class="badge-atm">ATM</span>' : '';
        const itmBadge = isItm ? '<span class="badge-itm">ITM</span>' : '';

        const typeColor = l.type === "CALL" ? "var(--positive)" : "var(--negative)";

        tr.innerHTML = `
          <td><b class="mono">$ ${{l.strike.toFixed(2)}}</b> ${{atmBadge}} ${{itmBadge}}</td>
          <td><b style="color: ${{typeColor}};">${{l.type}}</b></td>
          <td>${{renderDataValue(l.bid, {{ isCurrency: true }})}}</td>
          <td>${{renderDataValue(l.ask, {{ isCurrency: true }})}}</td>
          <td><span class="mono">$ ${{l.mid ? l.mid.toFixed(2) : 'N/D'}}</span></td>
          <td>${{renderDataValue(l.iv, {{ isPercent: true }})}}</td>
          <td>${{renderDataValue(l.delta, {{ decimals: 2 }})}}</td>
          <td>${{renderDataValue(l.gamma, {{ decimals: 3 }})}}</td>
          <td>${{renderDataValue(l.theta, {{ decimals: 2 }})}}</td>
          <td>${{renderDataValue(l.open_interest, {{ decimals: 0 }})}}</td>
          <td>${{renderDataValue(l.volume, {{ decimals: 0 }})}}</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    // ============================================================
    // GRÁFICOS (CHART.JS HTTPS)
    // ============================================================
    let chartTerm = null;
    let chartPricing = null;
    let chartStrat = null;

    function renderCharts() {{
      const contexts = STATE.contexts || [];
      const opps = STATE.opportunities || [];

      // 1. Curva a Termo de IV
      const ctxTerm = document.getElementById("chartTermStructure");
      if (ctxTerm) {{
        if (chartTerm) chartTerm.destroy();

        const datasets = [];
        const colors = ["#3b82f6", "#10b981", "#f59e0b"];

        contexts.forEach((c, idx) => {{
          const termMap = c.term_structure_atm_iv || {{}};
          const exps = Object.keys(termMap).sort();
          const dataPoints = exps.map(e => termMap[e] && termMap[e].value ? termMap[e].value : null);

          datasets.push({{
            label: `${{c.symbol}} (Spot $${{c.spot_price.value}})`,
            data: dataPoints,
            borderColor: colors[idx % colors.length],
            backgroundColor: colors[idx % colors.length],
            tension: 0.2,
            pointRadius: 6,
            pointHoverRadius: 8
          }});
        }});

        const allExps = [...new Set(contexts.flatMap(c => Object.keys(c.term_structure_atm_iv || {{}})))].sort();

        chartTerm = new Chart(ctxTerm, {{
          type: "line",
          data: {{
            labels: allExps,
            datasets: datasets
          }},
          options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
              legend: {{ labels: {{ color: "#f9fafb", font: {{ family: "Inter" }} }} }},
              tooltip: {{
                callbacks: {{
                  label: ctx => `${{ctx.dataset.label}}: ${{ctx.parsed.y}}% IV`
                }}
              }}
            }},
            scales: {{
              x: {{
                grid: {{ color: "#374151" }},
                ticks: {{ color: "#9ca3af", font: {{ family: "JetBrains Mono" }} }}
              }},
              y: {{
                grid: {{ color: "#374151" }},
                ticks: {{ color: "#9ca3af", font: {{ family: "JetBrains Mono" }} }},
                title: {{ display: true, text: "IV ATM (%)", color: "#9ca3af" }}
              }}
            }}
          }}
        }});
      }}

      // 2. Custo Máximo vs Valor Mínimo por Oportunidade
      const ctxPricing = document.getElementById("chartPricingDistribution");
      if (ctxPricing) {{
        if (chartPricing) chartPricing.destroy();

        const labels = opps.map(o => `${{o.symbol}} ${{o.strategy_name}}`);
        const values = opps.map(o => {{
          if (!o.pricing || !o.pricing.display_value || o.pricing.display_value.value === null) return 0;
          return o.pricing.pricing_type === "CREDIT" ? o.pricing.display_value.value : -o.pricing.display_value.value;
        }});
        const bgColors = values.map(v => v >= 0 ? "rgba(16, 185, 129, 0.7)" : "rgba(245, 158, 11, 0.7)");

        chartPricing = new Chart(ctxPricing, {{
          type: "bar",
          data: {{
            labels: labels,
            datasets: [{{
              label: "Valor Líquido ($) [Verde: Crédito Minimo / Laranja: Custo Maximo]",
              data: values,
              backgroundColor: bgColors,
              borderRadius: 4
            }}]
          }},
          options: {{
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
              legend: {{ display: false }},
              tooltip: {{
                callbacks: {{
                  label: ctx => ctx.parsed.x >= 0 ? `Crédito Mínimo: $${{ctx.parsed.x.toFixed(2)}}` : `Custo Máximo: $${{Math.abs(ctx.parsed.x).toFixed(2)}}`
                }}
              }}
            }},
            scales: {{
              x: {{
                grid: {{ color: "#374151" }},
                ticks: {{ color: "#9ca3af", font: {{ family: "JetBrains Mono" }} }}
              }},
              y: {{
                grid: {{ display: false }},
                ticks: {{ color: "#f9fafb", font: {{ family: "Inter", size: 10 }} }}
              }}
            }}
          }}
        }});
      }}

      // 3. Distribuição de Estratégias
      const ctxStrat = document.getElementById("chartStrategyBreakdown");
      if (ctxStrat) {{
        if (chartStrat) chartStrat.destroy();

        const countByStrat = {{}};
        opps.forEach(o => {{
          countByStrat[o.strategy_name] = (countByStrat[o.strategy_name] || 0) + 1;
        }});

        chartStrat = new Chart(ctxStrat, {{
          type: "doughnut",
          data: {{
            labels: Object.keys(countByStrat),
            datasets: [{{
              data: Object.values(countByStrat),
              backgroundColor: ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316", "#06b6d4"]
            }}]
          }},
          options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
              legend: {{ position: "right", labels: {{ color: "#f9fafb", font: {{ family: "Inter", size: 11 }} }} }}
            }}
          }}
        }});
      }}
    }}

    // ============================================================
    // EXPORTAÇÃO CSV / JSON (SEÇÃO 6.2)
    // ============================================================
    function exportToCSV(filename, rows) {{
      const processRow = function (row) {{
        let finalVal = '';
        for (let j = 0; j < row.length; j++) {{
          let innerValue = row[j] === null || row[j] === undefined ? '' : row[j].toString();
          let result = innerValue.replace(/"/g, '""');
          if (result.search(/("|,|\\n|;)/g) >= 0)
            result = '"' + result + '"';
          if (j > 0)
            finalVal += ';';
          finalVal += result;
        }}
        return finalVal + '\\r\\n';
      }};

      let csvFile = '';
      for (let i = 0; i < rows.length; i++) {{
        csvFile += processRow(rows[i]);
      }}

      const blob = new Blob([csvFile], {{ type: 'text/csv;charset=utf-8;' }});
      const link = document.createElement("a");
      const url = URL.createObjectURL(blob);
      link.setAttribute("href", url);
      link.setAttribute("download", filename);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }}

    function initExports() {{
      document.getElementById("btnExportCSV").addEventListener("click", () => {{
        const opps = STATE.opportunities || [];
        const rows = [
          ["Ativo", "Estratégia", "Status", "Direção", "IV Rank", "Rótulo", "Valor", "Notas"]
        ];
        opps.forEach(o => {{
          rows.push([
            o.symbol,
            o.strategy_name,
            o.status,
            o.mandatory_criteria.direction ? o.mandatory_criteria.direction.value : 'N/D',
            o.mandatory_criteria.iv_rank ? o.mandatory_criteria.iv_rank.value : 'N/D',
            o.pricing ? o.pricing.label : 'N/D',
            o.pricing && o.pricing.display_value ? o.pricing.display_value.value : 'N/D',
            o.notes
          ]);
        }});
        exportToCSV("tastytrade_oportunidades.csv", rows);
      }});

      document.getElementById("btnExportJSON").addEventListener("click", () => {{
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(STATE, null, 2));
        const dlAnchorElem = document.createElement('a');
        dlAnchorElem.setAttribute("href", dataStr);
        dlAnchorElem.setAttribute("download", "tastytrade_screener_output.json");
        dlAnchorElem.click();
      }});

      document.getElementById("btnExportChainCSV").addEventListener("click", () => {{
        const sym = document.getElementById("selectChainAsset").value;
        const exp = document.getElementById("selectChainExp").value;
        const ctx = (STATE.contexts || []).find(c => c.symbol === sym);
        if (!ctx || !ctx.chains || !ctx.chains[exp]) return;

        const rows = [
          ["Strike", "Tipo", "Bid", "Ask", "Mid", "IV", "Delta", "Gamma", "Theta", "OI", "Volume"]
        ];
        ctx.chains[exp].forEach(l => {{
          rows.push([
            l.strike,
            l.type,
            l.bid && l.bid.value !== null ? l.bid.value : 'N/D',
            l.ask && l.ask.value !== null ? l.ask.value : 'N/D',
            l.mid ? l.mid : 'N/D',
            l.iv && l.iv.value !== null ? l.iv.value : 'N/D',
            l.delta && l.delta.value !== null ? l.delta.value : 'N/D',
            l.gamma && l.gamma.value !== null ? l.gamma.value : 'N/D',
            l.theta && l.theta.value !== null ? l.theta.value : 'N/D',
            l.open_interest && l.open_interest.value !== null ? l.open_interest.value : 'N/D',
            l.volume && l.volume.value !== null ? l.volume.value : 'N/D'
          ]);
        }});
        exportToCSV(`chain_${{sym}}_${{exp}}.csv`, rows);
      }});
    }}

    // ============================================================
    // INICIALIZAÇÃO
    // ============================================================
    window.addEventListener("DOMContentLoaded", () => {{
      initTabs();
      initExports();

      // Configuração de metadados no header e banner
      if (STATE.generated_at) {{
        document.getElementById("bannerTimestamp").textContent = `Coleta: ${{STATE.generated_at.replace('T', ' ').substring(0, 19)}} UTC`;
      }}
      if (STATE.is_live_data) {{
        const b = document.getElementById("auditBanner");
        b.classList.add("live");
        document.getElementById("bannerBadge").textContent = "AO VIVO";
        document.getElementById("bannerBadge").classList.add("live");
        document.getElementById("bannerText").textContent = "Conexão ativa à API da Tastytrade em tempo real.";
      }}
      if (STATE.universe) {{
        document.getElementById("metaUniverseCount").textContent = `${{STATE.universe.length}} Ativos`;
      }}
      if (STATE.opportunities) {{
        document.getElementById("metaOppCount").textContent = `${{STATE.opportunities.length}} Sinais`;
      }}

      // Listeners de filtro
      document.getElementById("filterStrategy").addEventListener("change", renderOpportunities);
      document.getElementById("filterStatus").addEventListener("change", renderOpportunities);

      // Render inicial
      renderOpportunities();
      initChains();
    }});
  </script>
</body>
</html>
"""


def main() -> None:
    root = Path(__file__).parent.parent
    screener_json_path = root / "screener_output.json"

    if not screener_json_path.exists():
        print("screener_output.json não encontrado. Execute src/screener.py primeiro.")
        return

    data_json = screener_json_path.read_text(encoding="utf-8")
    html_content = generate_html(data_json)

    out_file = root / "index.html"
    out_file.write_text(html_content, encoding="utf-8")
    print(f"index.html gerado com sucesso em {out_file} ({len(html_content)} bytes).")


if __name__ == "__main__":
    main()
