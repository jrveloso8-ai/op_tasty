"""
Gerador da Interface Web Single-File (index.html) — Screener Tastytrade.
Gera um arquivo HTML autocontido com CSS e JavaScript integrados,
seguindo a paleta 'Financial Dark', WCAG AA, formatação pt-BR, Chart.js via CDN HTTPS
e a Cerca Estrutural DataValue para proveniência de dados.
"""

import json
from pathlib import Path


def generate_html(data_json: str, sample_positions_json: str = "[]") -> str:
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
    .banner-badge.partial {{
      background: rgba(245, 158, 11, 0.2);
      border-color: #f59e0b;
      color: #fcd34d;
    }}
    .data-source-tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.3rem;
      margin-top: 0.35rem;
    }}
    .data-source-tag {{
      display: inline-flex;
      align-items: center;
      gap: 0.2rem;
      font-size: 0.65rem;
      font-weight: 600;
      font-family: var(--font-mono);
      padding: 0.1rem 0.35rem;
      border-radius: 3px;
    }}
    .data-source-tag.live {{
      background: rgba(16, 185, 129, 0.12);
      color: #6ee7b7;
      border: 1px solid rgba(16, 185, 129, 0.35);
    }}
    .data-source-tag.fixture {{
      background: rgba(245, 158, 11, 0.12);
      color: #fcd34d;
      border: 1px solid rgba(245, 158, 11, 0.35);
    }}
    .data-source-tag.indisponivel {{
      background: rgba(239, 68, 68, 0.12);
      color: #f87171;
      border: 1px solid rgba(239, 68, 68, 0.35);
      opacity: 0.85;
    }}
    .banner-badge.alert {{
      background: rgba(239, 68, 68, 0.2);
      border-color: var(--alert);
      color: #fca5a5;
    }}
    .iv-anomaly-badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.2rem;
      font-size: 0.6rem;
      font-weight: 700;
      padding: 0.08rem 0.25rem;
      border-radius: 2px;
      background: rgba(245, 158, 11, 0.18);
      color: #fbbf24;
      border: 1px solid rgba(245, 158, 11, 0.45);
      animation: anomalyPulse 2s ease-in-out infinite;
      margin-left: 0.2rem;
    }}
    @keyframes anomalyPulse {{
      0%, 100% {{ opacity: 1; }}
      50% {{ opacity: 0.6; }}
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
      overflow-x: auto;
      white-space: nowrap;
      -webkit-overflow-scrolling: touch;
      scrollbar-width: thin;
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
       BOLETA DE EXECUÇÃO DE ORDENS NO CARD
       ============================================================ */
    .opp-boleta {{
      background: var(--bg-main);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 6px;
      padding: 0.75rem;
      margin-top: 0.75rem;
    }}
    .opp-boleta-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 0.725rem;
      font-weight: 700;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-bottom: 0.5rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      padding-bottom: 0.35rem;
    }}
    .opp-boleta-legs {{
      display: flex;
      flex-direction: column;
      gap: 0.45rem;
    }}
    .opp-leg-row {{
      display: flex;
      align-items: center;
      gap: 0.6rem;
      padding: 0.45rem 0.6rem;
      border-radius: 5px;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(255, 255, 255, 0.04);
      transition: background 0.15s;
    }}
    .opp-leg-row:hover {{
      background: rgba(255, 255, 255, 0.04);
    }}
    .opp-leg-row.leg-buy {{
      border-left: 3px solid var(--positive);
    }}
    .opp-leg-row.leg-sell {{
      border-left: 3px solid var(--alert);
    }}
    .leg-action-badge {{
      font-family: var(--font-mono);
      font-size: 0.7rem;
      font-weight: 700;
      padding: 0.18rem 0.45rem;
      border-radius: 3px;
      white-space: nowrap;
    }}
    .leg-action-badge.leg-buy {{
      background: var(--positive-bg);
      color: var(--positive);
      border: 1px solid var(--positive);
    }}
    .leg-action-badge.leg-sell {{
      background: var(--alert-bg);
      color: var(--alert);
      border: 1px solid var(--alert);
    }}
    .leg-type-badge {{
      font-family: var(--font-mono);
      font-size: 0.7rem;
      font-weight: 700;
      padding: 0.12rem 0.38rem;
      border-radius: 3px;
      text-transform: uppercase;
    }}
    .leg-type-badge.opt-call {{
      background: rgba(59, 130, 246, 0.18);
      color: #93c5fd;
      border: 1px solid rgba(59, 130, 246, 0.4);
    }}
    .leg-type-badge.opt-put {{
      background: rgba(168, 85, 247, 0.18);
      color: #d8b4fe;
      border: 1px solid rgba(168, 85, 247, 0.4);
    }}
    .leg-col-info {{
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 0.15rem;
      min-width: 0;
    }}
    .leg-main-line {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;
      font-size: 0.825rem;
      color: var(--text-primary);
    }}
    .leg-strike {{
      font-weight: 600;
      font-family: var(--font-mono);
    }}
    .leg-exp {{
      font-size: 0.775rem;
      color: var(--text-secondary);
      margin-left: auto;
      font-family: var(--font-mono);
    }}
    .leg-sub-line {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
      font-size: 0.7rem;
      color: var(--text-secondary);
      font-family: var(--font-mono);
    }}
    .leg-symbol-code {{
      color: #64748b;
      font-size: 0.675rem;
    }}
    .opp-boleta-total {{
      font-size: 0.75rem;
      color: var(--text-secondary);
      margin-top: 0.5rem;
      padding-top: 0.4rem;
      border-top: 1px dashed rgba(255, 255, 255, 0.08);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .opp-boleta-total b {{
      color: var(--text-primary);
      font-family: var(--font-mono);
    }}
    .opp-instrucao-pratica {{
      margin-top: 0.65rem;
      padding: 0.5rem 0.65rem;
      background: rgba(59, 130, 246, 0.06);
      border-left: 3px solid var(--accent);
      border-radius: 0 4px 4px 0;
      font-size: 0.75rem;
      color: #cbd5e1;
      line-height: 1.4;
    }}
    .opp-instrucao-pratica strong {{
      color: #93c5fd;
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

    /* Botão de Atualização Manual & Auto-Refresh */
    .btn-refresh-market {{
      background: linear-gradient(135deg, #2563eb, #1d4ed8);
      border: 1px solid #60a5fa;
      color: #ffffff;
      padding: 0.45rem 0.95rem;
      border-radius: 6px;
      font-size: 0.8rem;
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      box-shadow: 0 2px 10px rgba(37, 99, 235, 0.35);
      transition: all 0.2s ease;
      white-space: nowrap;
    }}
    .btn-refresh-market:hover {{
      background: linear-gradient(135deg, #1d4ed8, #1e40af);
      box-shadow: 0 4px 14px rgba(37, 99, 235, 0.55);
      transform: translateY(-1px);
    }}
    .btn-refresh-market:active {{
      transform: translateY(0);
    }}
    .btn-refresh-market.loading {{
      opacity: 0.8;
      cursor: wait;
      pointer-events: none;
      background: #374151 !important;
      border-color: #4b5563 !important;
      box-shadow: none;
    }}
    .auto-refresh-box {{
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 0.2rem;
    }}
    .auto-refresh-controls {{
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }}
    .btn-toggle-timer {{
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      color: var(--text-secondary);
      font-size: 0.65rem;
      padding: 1px 6px;
      border-radius: 3px;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .btn-toggle-timer:hover {{
      border-color: var(--accent);
      color: #93c5fd;
      background: rgba(59, 130, 246, 0.15);
    }}
    /* Toast Notifications */
    .toast-container {{
      position: fixed;
      bottom: 1.5rem;
      right: 1.5rem;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      pointer-events: none;
    }}
    .toast-item {{
      background: var(--surface-card);
      border: 1px solid var(--border);
      color: var(--text-primary);
      padding: 0.75rem 1.25rem;
      border-radius: 8px;
      font-size: 0.825rem;
      font-weight: 600;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
      pointer-events: auto;
      display: flex;
      align-items: center;
      gap: 0.6rem;
      animation: toastIn 0.25s ease-out forwards;
      max-width: 420px;
    }}
    .toast-positive {{
      border-color: var(--positive);
      background: rgba(17, 24, 39, 0.96);
      color: #6ee7b7;
    }}
    .toast-alert {{
      border-color: var(--alert);
      background: rgba(17, 24, 39, 0.96);
      color: #fde68a;
    }}
    .toast-negative {{
      border-color: var(--negative);
      background: rgba(17, 24, 39, 0.96);
      color: #fca5a5;
    }}
    @keyframes toastIn {{
      from {{ opacity: 0; transform: translateY(12px); }}
      to {{ opacity: 1; transform: translateY(0); }}
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

    /* ============================================================
       MODAL & TRACKING SYSTEM
       ============================================================ */
    .modal-overlay {{
      display: none;
      position: fixed;
      inset: 0;
      background-color: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(4px);
      z-index: 9999;
      align-items: center;
      justify-content: center;
      padding: 1rem;
    }}
    .modal-overlay.active {{
      display: flex;
    }}
    .modal-box {{
      background-color: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 10px;
      max-width: 580px;
      width: 100%;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
      animation: modalFadeIn 0.2s ease-out;
      overflow: hidden;
    }}
    @keyframes modalFadeIn {{
      from {{ opacity: 0; transform: translateY(-12px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    .modal-header {{
      padding: 1.25rem 1.5rem;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background-color: var(--surface-alt);
    }}
    .modal-header h3 {{
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--text-primary);
    }}
    .modal-close {{
      background: transparent;
      border: none;
      color: var(--text-secondary);
      font-size: 1.3rem;
      cursor: pointer;
      line-height: 1;
    }}
    .modal-close:hover {{
      color: var(--text-primary);
    }}
    .modal-body {{
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
      max-height: 75vh;
      overflow-y: auto;
    }}
    .modal-footer {{
      padding: 1rem 1.5rem;
      border-top: 1px solid var(--border);
      display: flex;
      justify-content: flex-end;
      gap: 0.75rem;
      background-color: var(--surface-alt);
    }}
    .form-group {{
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }}
    .form-group label {{
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}
    .form-input {{
      background-color: var(--surface-alt);
      border: 1px solid var(--border);
      color: var(--text-primary);
      padding: 0.5rem 0.75rem;
      border-radius: 4px;
      font-size: 0.9rem;
      font-family: var(--font-text);
    }}
    .form-input:focus {{
      border-color: var(--accent);
      outline: none;
    }}
    .form-row {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }}

    /* Badges de Sinal em Tempo Real */
    .signal-pill {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.35rem 0.8rem;
      border-radius: 9999px;
      font-size: 0.825rem;
      font-weight: 700;
      letter-spacing: 0.03em;
      text-transform: uppercase;
    }}
    .signal-gain {{
      background: rgba(16, 185, 129, 0.2);
      border: 1px solid var(--positive);
      color: #6ee7b7;
      box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
    }}
    .signal-stop {{
      background: rgba(239, 68, 68, 0.2);
      border: 1px solid var(--negative);
      color: #fca5a5;
      box-shadow: 0 0 10px rgba(239, 68, 68, 0.3);
    }}
    .signal-manter {{
      background: rgba(245, 158, 11, 0.2);
      border: 1px solid var(--warning);
      color: #fde68a;
    }}
    .signal-indisp {{
      background: rgba(100, 116, 139, 0.2);
      border: 1px solid #64748b;
      color: #cbd5e1;
    }}

    /* Tracking Card & Progress */
    .tracking-card {{
      background-color: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
      transition: border-color 0.2s, box-shadow 0.2s;
    }}
    .tracking-card:hover {{
      border-color: var(--accent);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }}
    .tracking-progress-bar {{
      height: 8px;
      background: #1e293b;
      border-radius: 4px;
      overflow: hidden;
      display: flex;
      margin-top: 0.4rem;
    }}
    .tracking-progress-fill {{
      height: 100%;
      transition: width 0.3s ease;
    }}
    .badge-rank {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      font-weight: 700;
      font-size: 0.8rem;
    }}

    /* ============================================================
       MANUAL DO OPERADOR (ESTILOS VISUAIS)
       ============================================================ */
    .manual-container {{
      display: flex;
      flex-direction: column;
      gap: 2rem;
      max-width: 1200px;
      margin: 0 auto;
      padding-bottom: 3rem;
    }}
    .manual-hero {{
      background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.9));
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1.5rem;
    }}
    .manual-hero-title {{
      font-size: 1.6rem;
      font-weight: 700;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}
    .manual-hero-subtitle {{
      font-size: 0.95rem;
      color: var(--text-secondary);
      margin-top: 0.5rem;
      max-width: 680px;
      line-height: 1.5;
    }}
    .manual-toc {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 1rem;
    }}
    .manual-toc-card {{
      background: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1rem 1.25rem;
      text-decoration: none;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 0.85rem;
      transition: all 0.2s ease;
      cursor: pointer;
    }}
    .manual-toc-card:hover {{
      border-color: var(--accent);
      background: rgba(59, 130, 246, 0.08);
      transform: translateY(-2px);
    }}
    .manual-toc-icon {{
      font-size: 1.5rem;
    }}
    .manual-section {{
      background: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.75rem;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }}
    .manual-section-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--border);
      padding-bottom: 1rem;
      flex-wrap: wrap;
      gap: 0.75rem;
    }}
    .manual-section-title {{
      font-size: 1.25rem;
      font-weight: 700;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 0.65rem;
    }}
    .manual-grid-2 {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 1.25rem;
    }}
    .manual-subcard {{
      background: var(--surface-alt);
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: 8px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }}
    .manual-subcard-title {{
      font-size: 0.95rem;
      font-weight: 700;
      color: #93c5fd;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .manual-subcard-body {{
      font-size: 0.85rem;
      color: #d1d5db;
      line-height: 1.6;
    }}
    .manual-subcard-body ul, .manual-subcard-body ol {{
      margin-left: 1.25rem;
      margin-top: 0.5rem;
    }}
    .manual-subcard-body li {{
      margin-bottom: 0.35rem;
    }}
    .manual-callout {{
      padding: 1rem 1.25rem;
      border-radius: 6px;
      font-size: 0.85rem;
      line-height: 1.5;
      display: flex;
      gap: 0.75rem;
      align-items: flex-start;
    }}
    .manual-callout-info {{
      background: rgba(59, 130, 246, 0.1);
      border-left: 4px solid var(--accent);
      color: #bfdbfe;
    }}
    .manual-callout-success {{
      background: rgba(16, 185, 129, 0.1);
      border-left: 4px solid var(--positive);
      color: #a7f3d0;
    }}
    .manual-callout-warning {{
      background: rgba(245, 158, 11, 0.1);
      border-left: 4px solid var(--alert);
      color: #fde68a;
    }}
    .step-number {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 24px;
      height: 24px;
      background: var(--accent);
      color: #fff;
      border-radius: 50%;
      font-size: 0.75rem;
      font-weight: 700;
      margin-right: 0.4rem;
      flex-shrink: 0;
    }}

    /* ============================================================
       CENTRAL AUDIOVISUAL DO MANUAL (ESTILOS PROFISSIONAIS)
       ============================================================ */
    .manual-media-container {{
      background: linear-gradient(135deg, rgba(17, 24, 39, 0.95), rgba(15, 23, 42, 0.98));
      border: 1px solid rgba(59, 130, 246, 0.3);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05);
      border-radius: 12px;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }}
    .manual-media-grid {{
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 1.5rem;
      align-items: stretch;
    }}
    .avatar-card {{
      background: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
      position: relative;
      overflow: hidden;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }}
    .avatar-photo-wrapper {{
      position: relative;
      width: 100%;
      height: 250px;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid rgba(59, 130, 246, 0.35);
      box-shadow: 0 0 25px rgba(37, 99, 235, 0.15);
      background: #000;
    }}
    .avatar-img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: center 20%;
      transition: transform 0.3s ease;
    }}
    .avatar-card:hover .avatar-img {{
      transform: scale(1.02);
    }}
    .avatar-status-pill {{
      position: absolute;
      bottom: 10px;
      left: 10px;
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(6px);
      border: 1px solid rgba(16, 185, 129, 0.4);
      color: #6ee7b7;
      font-size: 0.7rem;
      font-weight: 700;
      padding: 0.3rem 0.65rem;
      border-radius: 9999px;
      display: flex;
      align-items: center;
      gap: 0.4rem;
      letter-spacing: 0.05em;
    }}
    .status-dot-pulse {{
      width: 8px;
      height: 8px;
      background-color: #10b981;
      border-radius: 50%;
      box-shadow: 0 0 8px #10b981;
      display: inline-block;
      animation: pulseGreen 2s infinite;
    }}
    @keyframes pulseGreen {{
      0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }}
      70% {{ transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }}
      100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
    }}
    .avatar-name {{
      font-size: 1.15rem;
      font-weight: 700;
      color: #fff;
    }}
    .avatar-role {{
      font-size: 0.78rem;
      color: #93c5fd;
      font-weight: 600;
      margin-top: 0.15rem;
    }}
    .avatar-quote {{
      font-size: 0.8rem;
      color: #cbd5e1;
      line-height: 1.45;
      background: rgba(59, 130, 246, 0.06);
      border-left: 3px solid var(--accent);
      padding: 0.6rem 0.75rem;
      border-radius: 0 6px 6px 0;
      font-style: italic;
    }}
    .avatar-meta-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.5rem;
      font-size: 0.75rem;
    }}
    .avatar-meta-item {{
      background: var(--surface-alt);
      padding: 0.4rem 0.6rem;
      border-radius: 4px;
      display: flex;
      flex-direction: column;
      gap: 0.15rem;
    }}
    .avatar-meta-label {{
      font-size: 0.65rem;
      color: var(--text-secondary);
      font-weight: 600;
    }}
    .avatar-meta-val {{
      color: #e2e8f0;
      font-weight: 600;
    }}
    .btn-avatar-pdf {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.4rem;
      background: rgba(59, 130, 246, 0.12);
      border: 1px solid var(--accent);
      color: #93c5fd;
      font-size: 0.78rem;
      font-weight: 600;
      padding: 0.5rem 0.85rem;
      border-radius: 6px;
      text-decoration: none;
      transition: background 0.15s, border-color 0.15s;
    }}
    .btn-avatar-pdf:hover {{
      background: var(--accent);
      color: #fff;
    }}

    .video-showcase-card {{
      background: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }}
    .video-player-wrapper {{
      position: relative;
      width: 100%;
      background: #000;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.08);
      aspect-ratio: 16 / 9;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }}
    .manual-video-element {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      border-radius: 8px;
    }}
    .video-info-box {{
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }}
    .video-chapters-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 0.5rem;
    }}
    .chapter-btn {{
      background: var(--surface-alt);
      border: 1px solid var(--border);
      color: var(--text-primary);
      padding: 0.5rem 0.65rem;
      border-radius: 6px;
      font-size: 0.75rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      cursor: pointer;
      text-align: left;
      transition: all 0.15s ease;
    }}
    .chapter-btn:hover {{
      border-color: var(--accent);
      background: rgba(59, 130, 246, 0.12);
      transform: translateY(-1px);
    }}
    .chapter-time {{
      font-family: var(--font-mono);
      font-weight: 700;
      color: #93c5fd;
      background: rgba(59, 130, 246, 0.15);
      padding: 0.15rem 0.35rem;
      border-radius: 4px;
      font-size: 0.7rem;
    }}
    .chapter-label {{
      flex: 1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      color: #e2e8f0;
    }}

    /* ============================================================
       RESPONSIVIDADE COMPLETA PARA TODOS OS APARELHOS
       (Desktop, Notebook, Tablets e Smartphones)
       ============================================================ */
    @media (max-width: 1024px) {{
      .manual-media-grid {{
        grid-template-columns: 1fr;
      }}
      .avatar-photo-wrapper {{
        height: 220px;
      }}
      .manual-hero {{
        flex-direction: column;
        align-items: flex-start;
      }}
      .kpi-grid {{
        grid-template-columns: repeat(2, 1fr);
      }}
    }}

    @media (max-width: 768px) {{
      header.app-header {{
        padding: 1rem 1.25rem;
      }}
      .header-top {{
        flex-direction: column;
        align-items: flex-start;
        gap: 0.75rem;
      }}
      .header-meta {{
        width: 100%;
        justify-content: space-between;
      }}
      main.app-main {{
        padding: 1rem 0.75rem;
      }}
      nav.tabs-nav {{
        gap: 0.25rem;
        padding-bottom: 6px;
      }}
      .tab-btn {{
        padding: 0.5rem 0.75rem;
        font-size: 0.8rem;
      }}
      .kpi-grid {{
        grid-template-columns: 1fr 1fr;
        gap: 0.75rem;
      }}
      .kpi-card {{
        padding: 0.85rem;
      }}
      .kpi-card-value {{
        font-size: 1.35rem;
      }}
      .opp-grid {{
        grid-template-columns: 1fr;
      }}
      .table-toolbar {{
        flex-direction: column;
        align-items: flex-start;
        gap: 0.75rem;
      }}
      .filter-controls {{
        width: 100%;
      }}
      .filter-select {{
        flex: 1;
      }}
      .manual-container {{
        gap: 1.25rem;
      }}
      .manual-hero {{
        padding: 1.25rem;
      }}
      .manual-hero-title {{
        font-size: 1.25rem;
      }}
      .manual-section {{
        padding: 1.25rem;
      }}
      .manual-grid-2 {{
        grid-template-columns: 1fr;
      }}
      .video-chapters-grid {{
        grid-template-columns: 1fr;
      }}
      .modal-box {{
        width: 95vw !important;
        max-width: 95vw !important;
        padding: 1.25rem 1rem !important;
      }}
    }}

    @media (max-width: 480px) {{
      .banner-audit {{
        flex-direction: column;
        align-items: flex-start;
        gap: 0.35rem;
        padding: 0.5rem 0.75rem;
        font-size: 0.75rem;
      }}
      .kpi-grid {{
        grid-template-columns: 1fr;
      }}
      .header-meta {{
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
      }}
      .meta-item {{
        align-items: flex-start;
      }}
      .app-title-group h1 {{
        font-size: 1.15rem;
      }}
      .manual-hero-title {{
        font-size: 1.15rem;
      }}
      .avatar-card {{
        padding: 1rem;
      }}
      .avatar-photo-wrapper {{
        height: 200px;
      }}
      .video-showcase-card {{
        padding: 1rem;
      }}
      .opp-card-actions {{
        flex-direction: column;
      }}
      .opp-card-actions button {{
        width: 100%;
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
          <span class="meta-value" id="metaUniverseCount">-- Ativos</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Oportunidades</span>
          <span class="meta-value" style="color: var(--positive);" id="metaOppCount">-- Sinais</span>
        </div>
        <div class="meta-item auto-refresh-box">
          <div class="auto-refresh-controls">
            <span class="meta-label">Auto-Refresh (30m)</span>
            <button class="btn-toggle-timer" id="btnToggleAutoRefresh" onclick="toggleAutoRefresh()" title="Pausar ou retomar auto-refresh">⏸ Pausar</button>
          </div>
          <span class="meta-value mono" id="countdownDisplay" style="color: #60a5fa;">30:00</span>
        </div>
        <div class="meta-item" style="justify-content: center;">
          <button class="btn-refresh-market" id="btnRefreshMarket" onclick="triggerMarketRefresh()" title="Disparar varredura imediata na Tastytrade">
            <span id="refreshIcon">🔄</span> <span id="refreshLabel">Atualizar Cotações</span>
          </button>
        </div>
      </div>
    </div>

    <!-- ABAS -->
    <nav class="tabs-nav" aria-label="Abas de Navegação">
      <button class="tab-btn active" data-tab="tab-opps" id="btnTabOpps">Oportunidades Aprovadas</button>
      <button class="tab-btn" data-tab="tab-tracking" id="btnTabTracking">Posições Executadas & Histórico</button>
      <button class="tab-btn" data-tab="tab-charts" id="btnTabCharts">Estruturas & Curva a Termo</button>
      <button class="tab-btn" data-tab="tab-chains" id="btnTabChains">Cadeia de Opções (Chains)</button>
      <button class="tab-btn" data-tab="tab-audit" id="btnTabAudit">Auditoria de Proveniência</button>
      <button class="tab-btn" data-tab="tab-manual" id="btnTabManual" style="color: #60a5fa; font-weight: 600;">📖 Manual do Operador</button>
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
          <li class="pass">Cerca Estrutural DataValue: Todas as cotações, gregas, métricas calculadas e totais de lote passam exclusivamente pelo invólucro auditado DataValue (strikes são especificações contratuais fixas).</li>
          <li class="pass">Discriminação Comprovada (Seção 8): Suíte com testes unitários cobrindo casos PASS e FAIL em cada uma das 8 estratégias.</li>
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
              <td>Preço Médio (Mid) de Opções</td>
              <td><span class="prov-pill prov-der">DERIVADO</span></td>
              <td>calc:mid_price ((Bid + Ask) / 2)</td>
              <td>Se bid ou ask nulo/zero -> INDISPONIVEL</td>
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

    <!-- ============================================================
         ABA 5: POSIÇÕES EXECUTADAS & HISTÓRICO (TRADE MANAGEMENT)
         ============================================================ -->
    <section id="tab-tracking" class="tab-content">
      <!-- KPI Resumo do Portfólio -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-label">Posições Ativas</div>
          <div class="kpi-value" id="kpiActiveCount">0</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">P&L Não Realizado Atual</div>
          <div class="kpi-value" id="kpiUnrealizedPnl">$ 0,00</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">P&L Realizado Total</div>
          <div class="kpi-value" id="kpiRealizedPnlTotal">$ 0,00</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Taxa de Acerto (Win Rate)</div>
          <div class="kpi-value" id="kpiWinRateTotal">-- %</div>
        </div>
      </div>

      <!-- Barra de Ferramentas -->
      <div class="table-toolbar" style="margin-bottom: 1.5rem; border-radius: 8px;">
        <div style="font-size: 0.9rem; font-weight: 600; color: var(--text-primary);">
          🎯 Gestão de Trades e Acompanhamento em Tempo Real
        </div>
        <div class="filter-controls">
          <button class="btn-export" style="background: rgba(59, 130, 246, 0.15); border-color: var(--accent); color: #93c5fd; font-weight: 600;" onclick="openManualTradeModal()">➕ Nova Operação Manual</button>
          <button class="btn-export" style="background: rgba(16, 185, 129, 0.12); border-color: var(--positive); color: var(--positive); font-weight: 600;" onclick="loadSampleTrades()">📌 Carregar Posições Salvas (Carteira de Demonstração)</button>
          <button class="btn-export" onclick="exportPositionsJson()">📥 Exportar JSON</button>
          <button class="btn-export" onclick="document.getElementById('fileImportPositions').click()">📤 Importar JSON</button>
          <input type="file" id="fileImportPositions" style="display: none;" accept=".json" onchange="importPositionsJson(event)">
          <button class="btn-export" style="color: var(--negative);" onclick="clearAllTrackingData()">🗑 Limpar Dados</button>
        </div>
      </div>

      <!-- Subseção 1: Posições em Acompanhamento Ativo -->
      <div style="margin-bottom: 2.5rem;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem;">
          <h2 style="font-size: 1.15rem; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
            <span>🟢</span> Posições Abertas (Tempo Real)
          </h2>
          <span style="font-size: 0.775rem; color: var(--text-secondary);">
            Preço de Liquidação calculado conservadoramente (Venda no Bid, Recompra no Ask)
          </span>
        </div>
        <div id="trackingCardsGrid" class="opp-grid">
          <!-- Injetado dinamicamente via JS -->
        </div>
      </div>

      <!-- Subseção 2: Ranking de Estratégias -->
      <div class="table-container" style="margin-bottom: 2.5rem;">
        <div class="table-toolbar">
          <h2 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
            <span>🏆</span> Ranking de Sucesso por Estratégia
          </h2>
          <span style="font-size: 0.775rem; color: var(--text-secondary);">Estatísticas consolidadas de trades encerrados no histórico</span>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th style="width: 70px;">Posição</th>
              <th>Estratégia</th>
              <th>Total Trades</th>
              <th>Vitórias (Gain)</th>
              <th>Derrotas (Stop)</th>
              <th>Taxa de Acerto</th>
              <th>P&L Consolidado</th>
            </tr>
          </thead>
          <tbody id="rankingTableBody">
            <!-- Injetado dinamicamente -->
          </tbody>
        </table>
      </div>

      <!-- Subseção 3: Histórico de Trades Encerrados -->
      <div class="table-container">
        <div class="table-toolbar">
          <h2 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
            <span>📜</span> Histórico de Trades Encerrados
          </h2>
          <span style="font-size: 0.775rem; color: var(--text-secondary);">Registro permanente de execução com P&L realizado</span>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Ativo</th>
              <th>Estratégia</th>
              <th>Data Entrada</th>
              <th>Data Saída</th>
              <th>Preço Entrada</th>
              <th>Preço Saída</th>
              <th>P&L Realizado ($)</th>
              <th>Notas</th>
            </tr>
          </thead>
          <tbody id="historyTableBody">
            <!-- Injetado dinamicamente -->
          </tbody>
        </table>
      </div>
    </section>

    <!-- ============================================================
         ABA 6: MANUAL DO OPERADOR (GUIA DE PONTA A PONTA)
         ============================================================ -->
    <section id="tab-manual" class="tab-content">
      <div class="manual-container">

        <!-- Hero Header -->
        <div class="manual-hero">
          <div>
            <div class="manual-hero-title">
              <span>📖</span> Manual do Operador — Op_Tasty Screener
            </div>
            <div class="manual-hero-subtitle">
              Guia prático e analítico de ponta a ponta: entenda a filosofia quantitativa, como navegar em cada tela, interpretar métricas, executar ordens na Tastytrade e gerenciar seus trades até o encerramento.
            </div>
          </div>
          <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
            <span class="prov-pill prov-med" style="padding: 0.4rem 0.8rem; font-size: 0.8rem;">Taxonomia Estrita</span>
            <span class="prov-pill prov-der" style="padding: 0.4rem 0.8rem; font-size: 0.8rem;">Cerca Estrutural</span>
            <span class="status-badge status-aprovado" style="padding: 0.4rem 0.8rem; font-size: 0.8rem;">Auditoria 100% PASS</span>
          </div>
        </div>

        <!-- CENTRAL AUDIOVISUAL: APRESENTADOR VIRTUAL & VÍDEO OFICIAL -->
        <div class="manual-media-container" id="sec-audiovisual">
          <div class="manual-section-header" style="border-bottom: none; padding-bottom: 0;">
            <div class="manual-section-title">
              <span>🎬</span> Central Audiovisual: Guia do Operador & Apresentador Virtual
            </div>
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
              <span class="badge badge-blue">HD 1080p</span>
              <span class="badge badge-green">Locução Neural Integrada</span>
              <span class="badge badge-dark">Modelo de Risco Homologado</span>
            </div>
          </div>

          <div class="manual-media-grid">
            <!-- Card 1: Avatar Institucional -->
            <div class="avatar-card">
              <div class="avatar-photo-wrapper">
                <img src="midia/Man_looking_at_camera_2K_20260922131644.jpeg" alt="Marcus Vance — Apresentador Virtual e Trader Quantitativo" class="avatar-img" />
                <div class="avatar-status-pill">
                  <span class="status-dot-pulse"></span> AVATAR HOMOLOGADO
                </div>
              </div>
              <div class="avatar-details">
                <div class="avatar-name">Marcus Vance</div>
                <div class="avatar-role">Engenheiro Financeiro Sênior & Trader Quantitativo</div>

                <div class="avatar-quote">
                  "Bem-vindo à cabine de comando do Op_Tasty. Nossa premissa inegociável é a disciplina matemática: zero fabricação de dados, precificação conservadora no Bid/Ask e veto automático a riscos de cauda em ativos caros. Assista ao vídeo de demonstração ao lado."
                </div>

                <div class="avatar-meta-grid">
                  <div class="avatar-meta-item">
                    <span class="avatar-meta-label">VOZ NEURAL</span>
                    <span class="avatar-meta-val">ElevenLabs (Adam/Antoni)</span>
                  </div>
                  <div class="avatar-meta-item">
                    <span class="avatar-meta-label">DIRETRIZ</span>
                    <span class="avatar-meta-val">WCAG AA & Institucional</span>
                  </div>
                </div>

                <a href="INSTRUCOES_AVATAR_SISTEMA.pdf" target="_blank" class="btn-avatar-pdf">
                  <span>👤</span> Ver Manual Técnico do Avatar (PDF)
                </a>
              </div>
            </div>

            <!-- Card 2: Vídeo Oficial de Demonstração & Capítulos -->
            <div class="video-showcase-card">
              <div class="video-player-wrapper">
                <video id="manualVideoPlayer" class="manual-video-element" controls preload="metadata" poster="midia/Man_looking_at_camera_2K_20260922131644.jpeg">
                  <source src="midia/Trader_executing_trades_at_desk_20260922132453.mp4" type="video/mp4">
                  Seu navegador não suporta a tag de vídeo HTML5.
                </video>
              </div>

              <div class="video-info-box">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                  <div style="font-weight: 700; font-size: 0.95rem; color: #fff; display: flex; align-items: center; gap: 0.4rem;">
                    <span>🎥</span> Dominando o Op_Tasty: Triagem, Boleta e Acompanhamento
                  </div>
                  <a href="INSTRUCOES_VIDEO_SISTEMA.pdf" target="_blank" class="btn-export" style="background: rgba(37, 99, 235, 0.15); border-color: var(--accent); color: #93c5fd; font-weight: 600;">
                    <span>📄</span> Roteiro & Storyboard (PDF)
                  </a>
                </div>

                <p style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.4; margin-top: 0.4rem;">
                  Navegue pelos capítulos do roteiro oficial abaixo para assistir aos trechos específicos de cada rotina:
                </p>

                <div class="video-chapters-grid">
                  <button class="chapter-btn" onclick="seekManualVideo(0)">
                    <span class="chapter-time">00:00</span>
                    <span class="chapter-label">1. Filosofia & Cerca de Dados</span>
                  </button>
                  <button class="chapter-btn" onclick="seekManualVideo(45)">
                    <span class="chapter-time">00:45</span>
                    <span class="chapter-label">2. Triagem & Boleta na Tasty</span>
                  </button>
                  <button class="chapter-btn" onclick="seekManualVideo(105)" style="border-color: rgba(16, 185, 129, 0.4); background: rgba(16, 185, 129, 0.08);">
                    <span class="chapter-time" style="color: #6ee7b7;">01:45</span>
                    <span class="chapter-label">3. Risco > $100 & Caso NVDA</span>
                  </button>
                  <button class="chapter-btn" onclick="seekManualVideo(180)">
                    <span class="chapter-time">03:00</span>
                    <span class="chapter-label">4. Confirmação no Painel</span>
                  </button>
                  <button class="chapter-btn" onclick="seekManualVideo(230)">
                    <span class="chapter-time">03:50</span>
                    <span class="chapter-label">5. Cabine de Sinais em Tempo Real</span>
                  </button>
                  <button class="chapter-btn" onclick="seekManualVideo(310)">
                    <span class="chapter-time">05:10</span>
                    <span class="chapter-label">6. Encerramento & Ranking</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Sumário Rápido (TOC) -->
        <div class="manual-toc">
          <a class="manual-toc-card" href="#sec-audiovisual" style="border-color: rgba(59, 130, 246, 0.35); background: rgba(59, 130, 246, 0.06);">
            <span class="manual-toc-icon">🎬</span>
            <div>
              <div style="font-weight: 700; font-size: 0.9rem; color: #93c5fd;">Guia Audiovisual</div>
              <div style="font-size: 0.75rem; color: var(--text-secondary);">Vídeo oficial e Apresentador IA</div>
            </div>
          </a>
          <a class="manual-toc-card" href="#sec-filosofia">
            <span class="manual-toc-icon">🧭</span>
            <div>
              <div style="font-weight: 700; font-size: 0.9rem;">1. Filosofia & Proveniência</div>
              <div style="font-size: 0.75rem; color: var(--text-secondary);">Regras de dados e preços conservadores</div>
            </div>
          </a>
          <a class="manual-toc-card" href="#sec-triagem">
            <span class="manual-toc-icon">📋</span>
            <div>
              <div style="font-weight: 700; font-size: 0.9rem;">2. Aba Oportunidades</div>
              <div style="font-size: 0.75rem; color: var(--text-secondary);">Triagem, boleta e execução</div>
            </div>
          </a>
          <a class="manual-toc-card" href="#sec-graficos">
            <span class="manual-toc-icon">📈</span>
            <div>
              <div style="font-weight: 700; font-size: 0.9rem;">3. Estruturas & Term Structure</div>
              <div style="font-size: 0.75rem; color: var(--text-secondary);">Leitura da curva de IV e custos</div>
            </div>
          </a>
          <a class="manual-toc-card" href="#sec-chains">
            <span class="manual-toc-icon">⛓</span>
            <div>
              <div style="font-weight: 700; font-size: 0.9rem;">4. Cadeia de Opções</div>
              <div style="font-size: 0.75rem; color: var(--text-secondary);">Auditoria de gregas e cotações brutas</div>
            </div>
          </a>
          <a class="manual-toc-card" href="#sec-gestao">
            <span class="manual-toc-icon">🎯</span>
            <div>
              <div style="font-weight: 700; font-size: 0.9rem;">5. Acompanhamento & Gestão</div>
              <div style="font-size: 0.75rem; color: var(--text-secondary);">Sinais de saída, P&L e ranking</div>
            </div>
          </a>
          <a class="manual-toc-card" href="#sec-rotina">
            <span class="manual-toc-icon">🚀</span>
            <div>
              <div style="font-weight: 700; font-size: 0.9rem;">6. Checklist Diário</div>
              <div style="font-size: 0.75rem; color: var(--text-secondary);">Rotina operacional em 5 passos</div>
            </div>
          </a>
        </div>

        <!-- SEÇÃO 1: FILOSOFIA & PROVENIÊNCIA -->
        <div class="manual-section" id="sec-filosofia">
          <div class="manual-section-header">
            <div class="manual-section-title">
              <span>🧭</span> 1. Filosofia Operacional e Cerca de Dados
            </div>
            <span class="prov-pill prov-med">Conceito Fundamental</span>
          </div>

          <p style="font-size: 0.875rem; color: var(--text-secondary); line-height: 1.6;">
            O <b>Op_Tasty</b> foi projetado como uma ferramenta profissional de grau institucional. Diferente de plataformas comuns que exibem números médios ou extrapolam dados não disponíveis, nosso motor segue regras matemáticas invioláveis descritas no <b>Contrato de Proveniência v1.0.0</b>:
          </p>

          <div class="manual-grid-2">
            <div class="manual-subcard">
              <div class="manual-subcard-title">🏷 Taxonomia Estrita de Dados</div>
              <div class="manual-subcard-body">
                Todo valor exibido no sistema pertence exclusivamente a uma das três categorias:
                <ul>
                  <li><b style="color: var(--positive);">MEDIDO (MED):</b> Coletado diretamente da API oficial da Tastytrade (preço spot, bid, ask, IV Rank, gregas). Nenhum ajuste é feito.</li>
                  <li><b style="color: var(--accent);">DERIVADO (DER):</b> Calculado a partir de insumos medidos através de fórmulas determinísticas auditáveis (médias móveis, RSI, spread líq., P&L).</li>
                  <li><b style="color: var(--alert);">INDISPONÍVEL (N/D):</b> Quando a API não fornece o dado ou o mercado está sem liquidez. <em>Proibição total de números inventados ou estimados</em>.</li>
                </ul>
              </div>
            </div>

            <div class="manual-subcard">
              <div class="manual-subcard-title">💰 Precificação Conservadora (Seção 5.1)</div>
              <div class="manual-subcard-body">
                Para evitar surpresas na hora de executar na corretora:
                <ul>
                  <li><b>Pernas Compradas (Long):</b> São precificadas no <b>Ask</b> (pior preço de compra a mercado).</li>
                  <li><b>Pernas Vendidas (Short):</b> São precificadas no <b>Bid</b> (pior preço de venda a mercado).</li>
                  <li><b>Estruturas a Débito:</b> O valor exibido é o <b>Custo Máximo a Pagar</b>. Na prática você pagará igual ou menos se negociar no mid.</li>
                  <li><b>Estruturas a Crédito:</b> O valor exibido é o <b>Valor Mínimo a Receber</b>. Na prática você receberá igual ou mais.</li>
                </ul>
              </div>
            </div>
          </div>

          <div class="manual-callout manual-callout-warning">
            <span>⚠</span>
            <div>
              <b>Regra de Contágio de Insumos:</b> Se qualquer perna de uma estrutura de opções não tiver cotação válida de Bid ou Ask, o valor financeiro da operação se torna <b>INDISPONÍVEL</b> imediatamente. O sistema nunca exibirá $0,00 ou estimativas fictícias para evitar decisões baseadas em alucinações.
            </div>
          </div>

          <div class="manual-callout" style="border-left-color: #10b981; background: rgba(16, 185, 129, 0.05); margin-top: 10px;">
            <span>🛡</span>
            <div>
              <b>Proteção de Capital em Ativos Caros (> US$ 100) & Vácuo de IV (Caso NVDA):</b>
              Para contas de varejo, o screener veta pontas vendidas a descoberto (ex: perna vendida nua de Put Ratio 1x2) em ativos como NVDA, AAPL e SPY, além de travar a largura das asas de Iron Condor em no máximo US$ 5,00 (limitando o BPR a US$ 500 por lote). Em ativos com IV Rank no piso histórico (como NVDA a 0% em vácuo de catalisador pré-earnings), vender opções possui assimetria desfavorável extrema; o sistema orienta o operador para travas de débito direcionais ou Calendar Spreads.
            </div>
          </div>
        </div>

        <!-- SEÇÃO 2: ABA OPORTUNIDADES -->
        <div class="manual-section" id="sec-triagem">
          <div class="manual-section-header">
            <div class="manual-section-title">
              <span>📋</span> 2. Aba "Oportunidades Aprovadas": Triagem e Execução
            </div>
            <span class="status-badge status-aprovado">Fluxo de Entrada</span>
          </div>

          <div class="manual-grid-2">
            <div class="manual-subcard">
              <div class="manual-subcard-title">📊 Os 4 KPIs do Topo</div>
              <div class="manual-subcard-body">
                <ul>
                  <li><b>Total Analisado:</b> Quantidade de pares (Ativo × Estratégia) auditados na varredura.</li>
                  <li><b>Aprovadas:</b> Estratégias que cumpriram 100% dos filtros técnicos (tendência, médias móveis, RSI, IV Rank e liquidez de pernas).</li>
                  <li><b>Condicionais:</b> Estratégias aprovadas tecnicamente, mas com pendência de verificação em eventos de earnings no horizonte.</li>
                  <li><b>Rejeitadas:</b> Combinações descartadas por violarem os filtros de disciplina operacional.</li>
                </ul>
              </div>
            </div>

            <div class="manual-subcard">
              <div class="manual-subcard-title">🔍 Como Usar os Filtros</div>
              <div class="manual-subcard-body">
                <ul>
                  <li><b>Filtro por Estratégia:</b> Permite isolar estratégias específicas (ex: apenas <em>Iron Condor</em> para alta volatilidade, ou apenas <em>Bull Call Spread</em> para direção de alta).</li>
                  <li><b>Filtro por Status:</b> Alterne entre <em>Todos</em>, <em>Aprovado</em> e <em>Condicional</em> para priorizar ordens prontas para envio imediato.</li>
                </ul>
              </div>
            </div>
          </div>

          <div class="manual-subcard" style="margin-top: 0.5rem;">
            <div class="manual-subcard-title">🎯 Anatomia de um Card de Oportunidade</div>
            <div class="manual-subcard-body">
              Cada card reúne tudo o que você precisa para tomar a decisão e digitar na corretora:
              <ol style="margin-left: 1.25rem; margin-top: 0.5rem;">
                <li><b>Identificação & Status:</b> Ticker do ativo (ex: BAC, AAPL), nome da estratégia e badge de validação (✔ APROVADO).</li>
                <li><b>Caixa de Custo/Crédito:</b> Destaque em verde (crédito mínimo a receber) ou azul (custo máximo a pagar), com link auditável de proveniência.</li>
                <li><b>Parâmetros Técnicos:</b> Direção confirmada (ALTA, BAIXA ou NEUTRO) e IV Rank medido na Tastytrade.</li>
                <li><b>📋 Boleta de Execução de Ordens:</b> Detalhamento claro de cada perna da operação com:
                  <ul>
                    <li>Ação exata: <b>COMPRAR (Buy)</b> ou <b>VENDER (Sell)</b>;</li>
                    <li>Tipo: <b>CALL</b> ou <b>PUT</b>;</li>
                    <li>Strike em negrito e Data de Vencimento com DTE;</li>
                    <li>Preço unitário por cota e subtotal por lote padrão de 100 ações.</li>
                  </ul>
                </li>
                <li><b>Instrução Prática para o Operador:</b> Guia em linguagem natural de como montar a estrutura no software da corretora passo a passo.</li>
                <li><b>Botão [🎯 Confirmar Execução no Portfólio]:</b> Ao executar a ordem na Tastytrade, clique neste botão para abrir o modal de confirmação. O sistema salvará o preço real negociado, a quantidade de lotes e ativará o monitoramento em tempo real.</li>
              </ol>
            </div>
          </div>
        </div>

        <!-- SEÇÃO 3: ABA ESTRUTURAS & GRÁFICOS -->
        <div class="manual-section" id="sec-graficos">
          <div class="manual-section-header">
            <div class="manual-section-title">
              <span>📈</span> 3. Aba "Estruturas & Curva a Termo": Análise de Volatilidade
            </div>
            <span class="prov-pill prov-der">Inteligência Visual</span>
          </div>

          <p style="font-size: 0.875rem; color: var(--text-secondary); line-height: 1.6;">
            A volatilidade implícita (IV) varia ao longo do tempo e entre vencimentos. Esta aba oferece três gráficos essenciais:
          </p>

          <div class="manual-grid-2">
            <div class="manual-subcard">
              <div class="manual-subcard-title">📉 Estrutura a Termo de IV (Term Structure)</div>
              <div class="manual-subcard-body">
                Plota o IV ATM ponderado para cada data de vencimento:
                <ul>
                  <li><b>Contango (Curva Ascendente):</b> Vencimentos curtos têm IV menor que os longos. É o regime natural do mercado. Favorável para Spreads direcionais e Iron Condor.</li>
                  <li><b>Inversão / Backwardation (Curva Descendente):</b> Vencimento curto com IV significativamente mais alta que o longo. Típico de pré-divulgação de balanço (earnings) ou choque pontual. <em>Condição obrigatória para aprovação de Calendar Spreads</em>.</li>
                </ul>
              </div>
            </div>

            <div class="manual-subcard">
              <div class="manual-subcard-title">💰 Distribuição de Precificação & Estratégias</div>
              <div class="manual-subcard-body">
                <ul>
                  <li><b>Gráfico Custo Máx vs Valor Mín:</b> Compara visualmente os desembolsos de débito com as receitas de crédito de todas as estruturas aprovadas.</li>
                  <li><b>Gráfico de Pizza:</b> Proporção de oportunidades identificadas entre as 8 estratégias monitoradas.</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- SEÇÃO 4: ABA CADEIA DE OPÇÕES -->
        <div class="manual-section" id="sec-chains">
          <div class="manual-section-header">
            <div class="manual-section-title">
              <span>⛓</span> 4. Aba "Cadeia de Opções (Chains)": Auditoria de Dados Brutos
            </div>
            <span class="prov-pill prov-med">Transparência Total</span>
          </div>

          <p style="font-size: 0.875rem; color: var(--text-secondary); line-height: 1.6;">
            Permite ao operador inspecionar cada contrato de opção negociado, conferindo se os dados usados no cálculo correspondem exatamente ao mercado:
          </p>

          <div class="manual-subcard">
            <div class="manual-subcard-title">📖 Dicionário de Colunas Obrigatórias (Seção 6.1)</div>
            <div class="manual-subcard-body">
              <ul style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 0.75rem; list-style: none; margin-left: 0;">
                <li><b>Strike:</b> Preço de exercício do contrato. Linhas <span class="badge-atm">ATM</span> marcam o strike mais próximo do spot e <span class="badge-itm">ITM</span> marcam opções no dinheiro.</li>
                <li><b>Tipo:</b> CALL (Verde) ou PUT (Vermelho).</li>
                <li><b>Bid:</b> Melhor preço de compra na bolsa (onde você vende a mercado).</li>
                <li><b>Ask:</b> Melhor preço de venda na bolsa (onde você compra a mercado).</li>
                <li><b>Mid:</b> Média aritmética entre Bid e Ask.</li>
                <li><b>IV (%):</b> Volatilidade implícita anualizada daquele strike específico.</li>
                <li><b>Delta:</b> Variação esperada no preço da opção para cada $1 de oscilação da ação.</li>
                <li><b>Gamma:</b> Taxa de aceleração do Delta.</li>
                <li><b>Theta:</b> Decaimento financeiro diário por contrato em decorrência da passagem do tempo.</li>
                <li><b>Open Interest (OI):</b> Número total de contratos em aberto na clearing (indica liquidez estrutural).</li>
                <li><b>Volume:</b> Contratos negociados na sessão corrente.</li>
              </ul>
            </div>
          </div>
        </div>

        <!-- SEÇÃO 5: ABA POSIÇÕES EXECUTADAS & HISTÓRICO -->
        <div class="manual-section" id="sec-gestao">
          <div class="manual-section-header">
            <div class="manual-section-title">
              <span>🎯</span> 5. Aba "Posições Executadas & Histórico": Gestão em Tempo Real & Ranking
            </div>
            <span class="status-badge status-aprovado">Monitoramento Ativo</span>
          </div>

          <p style="font-size: 0.875rem; color: var(--text-secondary); line-height: 1.6;">
            Esta aba é a central de comando diária do operador após a execução das ordens na corretora. Aqui você acompanha a evolução de cada posição, recebe alertas determinísticos de saída e constrói o histórico de ranking de estratégias.
          </p>

          <div class="manual-grid-2">
            <div class="manual-subcard">
              <div class="manual-subcard-title">🏷 Dualidade de Preços no Card de Posição</div>
              <div class="manual-subcard-body">
                Nosso sistema exibe dois preços simultâneos para dar segurança total:
                <ul>
                  <li><b>Mark Tastytrade (Mid):</b> Cotação de mercado calculada pela média entre Bid e Ask das pernas. É o número exato que aparece no painel da sua corretora como <em>P/L Open</em>.</li>
                  <li><b>Saída Conservadora (Bid/Ask):</b> Preço de liquidação no pior cenário (vendendo as compradas no Bid e recomprando as vendidas no Ask). Garante que você saiba o valor real de saída se fechar a mercado agora.</li>
                </ul>
              </div>
            </div>

            <div class="manual-subcard">
              <div class="manual-subcard-title">🚨 Catálogo de Sinais e Conduta Recomendada</div>
              <div class="manual-subcard-body">
                <ul>
                  <li><b style="color: var(--positive);">💰 REALIZAR GAIN:</b> A posição atingiu ou ultrapassou a meta de lucro (ex: +50%).<br><em>Conduta:</em> Abra a boleta de encerramento e realize o ganho.</li>
                  <li><b style="color: #6ee7b7;">🎯 ALVO PRÓXIMO:</b> O lucro atingiu 90%+ da meta (ex: 48,9% de 50%).<br><em>Conduta:</em> Verifique se a ordem limite GTC de saída já está aberta na corretora.</li>
                  <li><b style="color: var(--negative);">🛑 STOPAR:</b> A operação atingiu o limite de perda planejado (ex: -50% ou -200%).<br><em>Conduta:</em> Feche a estrutura imediatamente para preservar o capital.</li>
                  <li><b style="color: var(--alert);">⏳ MANTER:</b> A oscilação está dentro da faixa operacional planejada.<br><em>Conduta:</em> Não intervir, deixar o tempo agir a seu favor.</li>
                </ul>
              </div>
            </div>
          </div>

          <div class="manual-grid-2" style="margin-top: 0.5rem;">
            <div class="manual-subcard">
              <div class="manual-subcard-title">⏳ Alertas de DTE (Dias para o Vencimento)</div>
              <div class="manual-subcard-body">
                O sistema monitora os dias restantes para o vencimento:
                <ul>
                  <li><b>DTE &le; 21 dias (Estratégias de Crédito):</b> Alerta de risco de cauda e gama acelerado. A recomendação da Tastytrade é encerrar ou rolar a posição por volta de 21 DTE para evitar risco de exercício indesejado.</li>
                  <li><b>DTE &le; 14 dias (Estratégias de Débito):</b> Alerta de erosão rápida de teta. Se a direção não andou a favor, avalie encerrar antes da perda total do prêmio pago.</li>
                </ul>
              </div>
            </div>

            <div class="manual-subcard">
              <div class="manual-subcard-title">🏆 Ranking de Sucesso por Estratégia</div>
              <div class="manual-subcard-body">
                Consolida todos os trades encerrados:
                <ul>
                  <li><b>Pódio com Medalhas:</b> 🥇 1º Lugar, 🥈 2º Lugar e 🥉 3º Lugar por P&L acumulado em dólares.</li>
                  <li><b>Métricas de Desempenho:</b> Total de trades, vitórias (gain), derrotas (stop), taxa de acerto (Win Rate %) e lucro financeiro líquido.</li>
                  <li><b>Objetivo Estratégico:</b> Identificar quais das 8 estratégias trazem mais consistência à sua conta para alocar mais lotes no futuro.</li>
                </ul>
              </div>
            </div>
          </div>

          <div class="manual-callout manual-callout-info">
            <span>💾</span>
            <div>
              <b>Persistência & Portabilidade:</b> Seus trades ficam salvos automaticamente no navegador (`localStorage`). Use os botões <b>📥 Exportar JSON</b> e <b>📤 Importar JSON</b> na barra de ferramentas para criar backups periódicos, transferir seus dados entre computadores ou recuperar o histórico completo.
            </div>
          </div>
        </div>

        <!-- SEÇÃO 6: CHECKLIST DIÁRIO DO OPERADOR -->
        <div class="manual-section" id="sec-rotina">
          <div class="manual-section-header">
            <div class="manual-section-title">
              <span>🚀</span> 6. Checklist Operacional Diário (Rotina em 5 Passos)
            </div>
            <span class="status-badge status-aprovado">Procedimento Padrão</span>
          </div>

          <p style="font-size: 0.875rem; color: var(--text-secondary); line-height: 1.6;">
            Siga este fluxo rigorosamente em todas as sessões para garantir consistência e aderência aos requisitos de auditoria:
          </p>

          <div style="display: flex; flex-direction: column; gap: 0.85rem;">
            <div style="display: flex; gap: 0.75rem; background: var(--surface-alt); padding: 1rem; border-radius: 8px; border: 1px solid var(--border);">
              <span class="step-number">1</span>
              <div>
                <b style="color: #fff;">Triagem na Abertura do Mercado:</b>
                <div style="font-size: 0.825rem; color: var(--text-secondary); margin-top: 0.25rem;">
                  Acesse a aba <em>Oportunidades Aprovadas</em> e filtre por status <b>APROVADO</b>. Priorize ativos com IV Rank condizente com a estratégia (IV alto para crédito, IV baixo para débito).
                </div>
              </div>
            </div>

            <div style="display: flex; gap: 0.75rem; background: var(--surface-alt); padding: 1rem; border-radius: 8px; border: 1px solid var(--border);">
              <span class="step-number">2</span>
              <div>
                <b style="color: #fff;">Conferência da Boleta e Instrução Prática:</b>
                <div style="font-size: 0.825rem; color: var(--text-secondary); margin-top: 0.25rem;">
                  Abra o card da oportunidade escolhida. Leia a <em>📋 Boleta de Execução de Ordens</em> e a <em>Instrução Prática</em>. Verifique se o custo máximo a pagar ou valor mínimo a receber está de acordo com o limite de risco da sua conta.
                </div>
              </div>
            </div>

            <div style="display: flex; gap: 0.75rem; background: var(--surface-alt); padding: 1rem; border-radius: 8px; border: 1px solid var(--border);">
              <span class="step-number">3</span>
              <div>
                <b style="color: #fff;">Digitação na Tastytrade & Confirmação de Execução:</b>
                <div style="font-size: 0.825rem; color: var(--text-secondary); margin-top: 0.25rem;">
                  Monte a estrutura na Tastytrade com os strikes e vencimento indicados. Tente executar no Mid ou melhor. Assim que a ordem for preenchida (Filled), clique no botão <b>[🎯 Confirmar Execução no Portfólio]</b> do card, digite o preço unitário real executado e salve.
                </div>
              </div>
            </div>

            <div style="display: flex; gap: 0.75rem; background: var(--surface-alt); padding: 1rem; border-radius: 8px; border: 1px solid var(--border);">
              <span class="step-number">4</span>
              <div>
                <b style="color: #fff;">Programação da Ordem Limite GTC de Saída:</b>
                <div style="font-size: 0.825rem; color: var(--text-secondary); margin-top: 0.25rem;">
                  Logo após a entrada, abra uma ordem oposta na Tastytrade (STC / BTC) do tipo Limit com validade <b>GTC (Good 'Til Canceled)</b> com o preço correspondente à sua meta de lucro (ex: fechar o spread de débito com 50% de ganho ou recomprar o spread de crédito por 50% do prêmio).
                </div>
              </div>
            </div>

            <div style="display: flex; gap: 0.75rem; background: var(--surface-alt); padding: 1rem; border-radius: 8px; border: 1px solid var(--border);">
              <span class="step-number">5</span>
              <div>
                <b style="color: #fff;">Monitoramento na Aba de Acompanhamento & Encerramento:</b>
                <div style="font-size: 0.825rem; color: var(--text-secondary); margin-top: 0.25rem;">
                  Monitore os cards na aba <em>Posições Executadas & Histórico</em>. Quando a ordem for executada ou o sinal emitir <b>REALIZAR GAIN</b> ou <b>STOPAR</b>, clique em <b>[✔ Encerrar Posição]</b>, confirme o valor de saída e grave no histórico permanente para alimentar o Ranking.
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </section>

  </main>

  <!-- MODAL: CONFIRMAÇÃO DE EXECUÇÃO DE TRADE -->
  <div id="modalExecution" class="modal-overlay">
    <div class="modal-box">
      <div class="modal-header">
        <h3 id="modalExecTitle">Confirmar Execução de Trade</h3>
        <button class="modal-close" onclick="closeExecutionModal()">&times;</button>
      </div>
      <div class="modal-body">
        <div id="modalExecSummary" style="background: var(--surface-alt); padding: 0.85rem; border-radius: 6px; font-size: 0.825rem; border: 1px solid var(--border);"></div>

        <div class="form-row">
          <div class="form-group">
            <label for="inputExecPrice">Preço Executado Unitário ($)</label>
            <input type="number" step="0.01" id="inputExecPrice" class="form-input">
            <span style="font-size: 0.7rem; color: var(--text-secondary);">Débito pago ou crédito recebido por cota</span>
          </div>
          <div class="form-group">
            <label for="inputExecLots">Quantidade de Lotes</label>
            <input type="number" min="1" step="1" id="inputExecLots" class="form-input" value="1">
            <span style="font-size: 0.7rem; color: var(--text-secondary);">1 lote = 100 cotas por perna</span>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="inputTargetGain">Meta de Lucro (Take Profit %)</label>
            <input type="number" step="5" id="inputTargetGain" class="form-input" value="50">
            <span style="font-size: 0.7rem; color: var(--positive);">Alerta REALIZAR GAIN ao atingir</span>
          </div>
          <div class="form-group">
            <label for="inputStopLoss">Limite de Perda (Stop Loss %)</label>
            <input type="number" step="10" id="inputStopLoss" class="form-input" value="50">
            <span style="font-size: 0.7rem; color: var(--negative);">Alerta STOPAR ao atingir</span>
          </div>
        </div>

        <div class="form-group">
          <label for="inputExecNotes">Notas de Execução (Opcional)</label>
          <input type="text" id="inputExecNotes" class="form-input" placeholder="Ex: Executado na Tastytrade com spread ajustado">
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn-export" onclick="closeExecutionModal()">Cancelar</button>
        <button class="btn-export" style="background-color: var(--accent); color: #fff; border-color: var(--accent);" onclick="confirmSaveExecution()">Salvar e Iniciar Acompanhamento</button>
      </div>
    </div>
  </div>

  <!-- MODAL: ENCERRAMENTO DE TRADE -->
  <div id="modalCloseTrade" class="modal-overlay">
    <div class="modal-box">
      <div class="modal-header">
        <h3 id="modalCloseTitle">Encerrar Posição</h3>
        <button class="modal-close" onclick="closeCloseTradeModal()">&times;</button>
      </div>
      <div class="modal-body">
        <div id="modalCloseSummary" style="background: var(--surface-alt); padding: 0.85rem; border-radius: 6px; font-size: 0.825rem; border: 1px solid var(--border);"></div>

        <div class="form-group">
          <label for="inputExitPrice">Preço Unitário de Saída / Liquidação ($)</label>
          <input type="number" step="0.01" id="inputExitPrice" class="form-input">
          <span style="font-size: 0.7rem; color: var(--text-secondary);">Valor final negociado para liquidar todas as pernas</span>
        </div>

        <div class="form-group">
          <label for="inputCloseNotes">Notas de Encerramento (Opcional)</label>
          <input type="text" id="inputCloseNotes" class="form-input" placeholder="Ex: Saída por atingimento de meta de 50% de ganho">
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn-export" onclick="closeCloseTradeModal()">Cancelar</button>
        <button class="btn-export" style="background-color: var(--positive); color: #fff; border-color: var(--positive);" onclick="confirmCloseTrade()">Confirmar Encerramento e Gravar Histórico</button>
      </div>
    </div>
  </div>

  <!-- MODAL: REGISTRO MANUAL DE POSIÇÃO -->
  <div id="modalManualPosition" class="modal-overlay">
    <div class="modal-box" style="max-width: 580px;">
      <div class="modal-header">
        <h3>➕ Registrar Operação Executada Manualmente</h3>
        <button class="modal-close" onclick="closeManualTradeModal()">&times;</button>
      </div>
      <div class="modal-body">
        <div class="form-row">
          <div class="form-group">
            <label for="manualInputSymbol">Ticker / Ativo</label>
            <input type="text" id="manualInputSymbol" class="form-input" placeholder="Ex: BAC" style="text-transform: uppercase;">
          </div>
          <div class="form-group">
            <label for="manualInputStrategy">Estratégia</label>
            <select id="manualInputStrategy" class="form-select">
              <option value="bear_put_spread">Bear Put Spread</option>
              <option value="bull_call_spread">Bull Call Spread</option>
              <option value="iron_condor">Iron Condor</option>
              <option value="long_strangle">Long Strangle</option>
              <option value="calendar_spread">Calendar Spread</option>
              <option value="diagonal_spread">Diagonal Spread / PMCC</option>
              <option value="put_ratio_spread">Put Ratio Spread</option>
              <option value="call_backspread">Call Backspread</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="manualInputType">Tipo de Estrutura</label>
            <select id="manualInputType" class="form-select">
              <option value="DEBIT">Débito (Custo pago)</option>
              <option value="CREDIT">Crédito (Valor recebido)</option>
            </select>
          </div>
          <div class="form-group">
            <label for="manualInputPrice">Preço Unitário Executado ($)</label>
            <input type="number" step="0.01" id="manualInputPrice" class="form-input" placeholder="Ex: 0.47">
          </div>
          <div class="form-group">
            <label for="manualInputLots">Lotes</label>
            <input type="number" min="1" step="1" id="manualInputLots" class="form-input" value="1">
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="manualInputGain">Meta Lucro (%)</label>
            <input type="number" step="5" id="manualInputGain" class="form-input" value="50">
          </div>
          <div class="form-group">
            <label for="manualInputStop">Stop Loss (%)</label>
            <input type="number" step="10" id="manualInputStop" class="form-input" value="50">
          </div>
          <div class="form-group">
            <label for="manualInputDte">DTE (Dias)</label>
            <input type="number" min="0" step="1" id="manualInputDte" class="form-input" value="30">
          </div>
        </div>

        <div class="form-group">
          <label for="manualInputLegs">Pernas (Descrição ou Strikes)</label>
          <input type="text" id="manualInputLegs" class="form-input" placeholder="Ex: +1 PUT 59 @ 2.07 / -1 PUT 58 @ 1.60">
        </div>

        <div class="form-group">
          <label for="manualInputNotes">Notas de Execução / Ordem GTC</label>
          <input type="text" id="manualInputNotes" class="form-input" placeholder="Ex: Ordem GTC aberta para fechar a 0.74">
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn-export" onclick="closeManualTradeModal()">Cancelar</button>
        <button class="btn-export" style="background-color: var(--accent); color: #fff; border-color: var(--accent);" onclick="confirmSaveManualTrade()">Salvar e Acompanhar</button>
      </div>
    </div>
  </div>

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
        formatted = prefix + Number(dv.value).toLocaleString("pt-BR", {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
      }} else if (options.isPercent) {{
        formatted = Number(dv.value).toLocaleString("pt-BR", {{minimumFractionDigits: 1, maximumFractionDigits: 1}}) + "%";
      }} else if (typeof dv.value === "number") {{
        const dec = options.decimals !== undefined ? options.decimals : 2;
        formatted = Number(dv.value).toLocaleString("pt-BR", {{minimumFractionDigits: dec, maximumFractionDigits: dec}});
      }} else {{
        formatted = String(dv.value);
      }}

      const tip = `Fonte: ${{dv.source}}\nEndpoint: ${{dv.endpoint}}\nTimestamp: ${{dv.timestamp}}\nProveniência: ${{dv.provenance}}`;

      // Sinalização visual de auditoria: IV Rank fora da faixa canônica 0-100%
      // (Nota 1 do CONTRATO_PROVENIENCIA.md — valor cru emitido pela corretora preservado sem clamping)
      let anomalyBadge = "";
      if (options.isIvRank && typeof dv.value === "number" && (dv.value < 0 || dv.value > 100)) {{
        anomalyBadge = '<span class="iv-anomaly-badge" title="IV Rank fora da faixa canônica 0-100%. Valor cru emitido pela Tastytrade (implied-volatility-index-rank). Preservado sem clamping em conformidade com o Contrato de Proveniência.">⚠ FORA DA FAIXA</span>';
      }}

      return `<span class="data-value" title="${{tip}}"><span class="num">${{formatted}}</span> ${{provBadge}}${{anomalyBadge}}</span>`;
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
          if (targetId === "tab-tracking") {{
            renderTrackingTab();
          }}
        }});
      }});

      // Suporte a hash de URL direta (ex: index.html#tab-manual)
      if (window.location.hash) {{
        const hashId = window.location.hash.substring(1);
        const hashBtn = document.querySelector(`.tab-btn[data-tab="${{hashId}}"]`);
        if (hashBtn) {{
          hashBtn.click();
        }}
      }}
    }}

    // ============================================================
    // BOLETA DE EXECUÇÃO DE ORDENS
    // ============================================================
    function renderLegsBoleta(opp) {{
      if (!opp.suggested_legs || opp.suggested_legs.length === 0) {{
        return '<div class="opp-legs-summary" style="color: var(--text-secondary); font-style: italic;">Nenhuma perna sugerida calculada para esta estrutura.</div>';
      }}

      let legsHtml = "";
      let plainInstructions = [];

      opp.suggested_legs.forEach(leg => {{
        const isBuy = leg.action === "BUY";
        const actionLabel = isBuy ? "COMPRAR" : "VENDER";
        const actionClass = isBuy ? "leg-buy" : "leg-sell";
        const typeLabel = leg.type === "CALL" ? "CALL" : "PUT";
        const typeClass = leg.type === "CALL" ? "opt-call" : "opt-put";
        const strikeNum = typeof leg.strike === "number" ? leg.strike : parseFloat(leg.strike);
        const strikeFormatted = isNaN(strikeNum) ? leg.strike : `$${{strikeNum.toFixed(2)}}`;
        const dteFormatted = leg.dte !== undefined ? `${{leg.dte}} dias` : "";

        const deltaHtml = renderDataValue(leg.delta);
        const priceHtml = isBuy
          ? renderDataValue(leg.ask, {{ isCurrency: true }})
          : renderDataValue(leg.bid, {{ isCurrency: true }});
        const priceLabel = isBuy ? "Ask" : "Bid";

        plainInstructions.push(`${{actionLabel}} ${{leg.ratio}}x ${{typeLabel}} Strike ${{strikeFormatted}}`);

        legsHtml += `
          <div class="opp-leg-row ${{actionClass}}">
            <span class="leg-action-badge ${{actionClass}}">${{actionLabel}} ${{leg.ratio}}x</span>
            <div class="leg-col-info">
              <div class="leg-main-line">
                <span class="leg-type-badge ${{typeClass}}">${{typeLabel}}</span>
                <span class="leg-strike">Strike <b>${{strikeFormatted}}</b></span>
                <span class="leg-exp">Venc: <b>${{leg.expiration}}</b> (${{dteFormatted}})</span>
              </div>
              <div class="leg-sub-line">
                <span class="leg-symbol-code">${{leg.symbol}}</span>
                <span class="leg-metric">Δ: ${{deltaHtml}}</span>
                <span class="leg-metric">${{priceLabel}}: ${{priceHtml}}</span>
              </div>
            </div>
          </div>
        `;
      }});

      let totalInfoHtml = "";
      if (opp.pricing && opp.pricing.display_value && opp.pricing.display_value.value !== null) {{
        const valPerShare = Number(opp.pricing.display_value.value);
        const valLotNum = Math.round(valPerShare * 100 * 100) / 100;
        const isDebit = opp.pricing.pricing_type === "DEBIT";
        const flowLabel = isDebit ? "Débito Máximo Estimado (Lote 100)" : "Crédito Mínimo Estimado (Lote 100)";
        const valLotDv = {{
          value: valLotNum,
          provenance: "DERIVADO",
          source: "calc:lot_total(x100)",
          endpoint: opp.pricing.display_value.endpoint,
          timestamp: opp.pricing.display_value.timestamp
        }};
        totalInfoHtml = `
          <div class="opp-boleta-total">
            <span>${{flowLabel}}:</span>
            <b>${{renderDataValue(valLotDv, {{ isCurrency: true }})}}</b>
          </div>
        `;
      }}

      const expDates = [...new Set(opp.suggested_legs.map(l => l.expiration))];
      const expStr = expDates.join(" / ");
      const dtes = [...new Set(opp.suggested_legs.map(l => l.dte))];
      const dteStr = dtes.map(d => `${{d}} dias`).join(" / ");

      const instrText = `<strong>🎯 Instrução Prática:</strong> Ordem com ${{plainInstructions.join(" + ")}} para vencimento em <strong>${{expStr}}</strong> (${{dteStr}}).`;

      return `
        <div class="opp-boleta">
          <div class="opp-boleta-header">
            <span>📋 Boleta de Execução de Ordens</span>
            <span>${{opp.suggested_legs.length}} ${{opp.suggested_legs.length > 1 ? 'Pernas' : 'Perna'}}</span>
          </div>
          <div class="opp-boleta-legs">
            ${{legsHtml}}
          </div>
          ${{totalInfoHtml}}
        </div>
        <div class="opp-instrucao-pratica">
          ${{instrText}}
        </div>
      `;
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
        const isActive = isTradeAlreadyActive(opp.symbol, opp.strategy_id);

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
            <span>IV Rank: <b>${{opp.mandatory_criteria.iv_rank ? renderDataValue(opp.mandatory_criteria.iv_rank, {{ isPercent: true, isIvRank: true }}) : 'N/D'}}</b></span>
          </div>

          ${{renderLegsBoleta(opp)}}

          <div style="font-size: 0.725rem; color: var(--text-secondary); margin-top: 0.5rem;">
            ${{opp.notes}}
          </div>

          <div style="margin-top: 0.85rem; padding-top: 0.75rem; border-top: 1px solid var(--border);">
            ${{isActive
              ? '<div style="text-align: center; font-size: 0.775rem; font-weight: 700; color: var(--positive); padding: 0.45rem; background: rgba(16, 185, 129, 0.1); border-radius: 4px; border: 1px solid rgba(16, 185, 129, 0.25);">✔ Posição Ativa em Acompanhamento</div>'
              : `<button class="btn-export" style="width: 100%; justify-content: center; background: rgba(59, 130, 246, 0.12); border-color: var(--accent); color: #93c5fd; font-weight: 600;" onclick="openExecutionModal('${{opp.symbol}}', '${{opp.strategy_id}}')">🎯 Confirmar Execução no Portfólio</button>`
            }}
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
        const legsTableHtml = opp.suggested_legs.map(l => {{
          const isBuy = l.action === "BUY";
          const act = isBuy ? "COMPRAR" : "VENDER";
          const actColor = isBuy ? "var(--positive)" : "var(--alert)";
          const typeColor = l.type === "CALL" ? "#93c5fd" : "#d8b4fe";
          const strikeFmt = typeof l.strike === "number" ? `$${{l.strike.toFixed(2)}}` : l.strike;
          return `<div style="margin-bottom: 0.25rem;"><b style="color: ${{actColor}};">${{act}} ${{l.ratio}}x</b> <b style="color: ${{typeColor}};">${{l.type}}</b> ${{strikeFmt}} <span style="color: var(--text-secondary); font-size: 0.75rem;">(Venc: ${{l.expiration}}, ${{l.dte}}d)</span></div>`;
        }}).join("");

        tr.innerHTML = `
          <td><b class="mono">${{opp.symbol}}</b></td>
          <td><b>${{opp.strategy_name}}</b></td>
          <td><span class="status-badge ${{statusClass}}">${{opp.status}}</span></td>
          <td>${{opp.mandatory_criteria.direction ? renderDataValue(opp.mandatory_criteria.direction) : 'N/D'}}</td>
          <td>${{opp.mandatory_criteria.iv_rank ? renderDataValue(opp.mandatory_criteria.iv_rank, {{ isPercent: true, isIvRank: true }}) : 'N/D'}}</td>
          <td><span class="mono" style="font-size: 0.8rem;">${{pricingLabel}}</span></td>
          <td>${{pricingValHtml}}</td>
          <td><span class="mono" style="font-size: 0.8rem;">${{legsTableHtml || 'Nenhuma'}}</span></td>
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
          <td>${{renderDataValue(l.mid, {{ isCurrency: true }})}}</td>
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
        // Filtra apenas oportunidades com precificação mensurada e disponível (Achado 1: nunca plota INDISPONIVEL como 0.00 verde; Achado A: campos reais do JSON)
        const validPricedOpps = opps.filter(o => o.pricing && o.pricing.display_value && o.pricing.display_value.value !== null && o.pricing.display_value.provenance !== "INDISPONIVEL");
        const labels = validPricedOpps.map(o => `${{o.symbol}} ${{o.strategy_name}}`);
        const values = validPricedOpps.map(o => {{
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
    // MÓDULO DE RASTREAMENTO & GESTÃO DE TRADES (SEÇÃO 5)
    // ============================================================
    const POSITIONS_STORAGE_KEY = "op_tasty_tracked_positions";
    let currentModalOpp = null;
    let currentClosePosId = null;

    // Carteira de Operações de Demonstração (com proveniência e timestamps explícitos de snapshot)
    const SAMPLE_TRADES = {sample_positions_json};
    const SAMPLE_BAC_TRADE = SAMPLE_TRADES.length > 0 ? SAMPLE_TRADES[0] : null;

    function getStoredPositions() {{
      try {{
        const raw = localStorage.getItem(POSITIONS_STORAGE_KEY);
        if (!raw) {{
          saveStoredPositions(SAMPLE_TRADES);
          return SAMPLE_TRADES;
        }}
        const parsed = JSON.parse(raw);
        if (!Array.isArray(parsed) || parsed.length === 0) {{
          saveStoredPositions(SAMPLE_TRADES);
          return SAMPLE_TRADES;
        }}
        return parsed;
      }} catch (e) {{
        console.error("Erro ao carregar posições do localStorage:", e);
        return SAMPLE_TRADES;
      }}
    }}

    function saveStoredPositions(positions) {{
      try {{
        localStorage.setItem(POSITIONS_STORAGE_KEY, JSON.stringify(positions));
      }} catch (e) {{
        console.error("Erro ao salvar posições no localStorage:", e);
      }}
    }}

    function loadSampleTrades() {{
      const positions = getStoredPositions();
      let added = 0;
      SAMPLE_TRADES.forEach(sample => {{
        if (!positions.some(p => p.id === sample.id)) {{
          positions.push(sample);
          added++;
        }}
      }});
      saveStoredPositions(positions);
      renderOpportunities();
      renderTrackingTab();
      if (added > 0) {{
        alert(`${{added}} novas operações reais dos prints da Tastytrade foram carregadas com sucesso!`);
      }} else {{
        alert("Todas as 7 operações dos prints já estão carregadas no seu acompanhamento.");
      }}
    }}
    window.loadSampleTrades = loadSampleTrades;
    window.loadSampleBacTrade = loadSampleTrades;

    function isTradeAlreadyActive(symbol, strategyId) {{
      const positions = getStoredPositions();
      return positions.some(p => p.symbol === symbol && p.strategy_id === strategyId && p.status === "OPEN");
    }}

    function formatBRLCurrency(num) {{
      if (num === null || num === undefined || isNaN(num)) return "N/D";
      const sign = num < 0 ? "-$ " : "$ ";
      return sign + Math.abs(num).toFixed(2).replace(".", ",");
    }}

    // --- REGISTRO MANUAL DE OPERAÇÕES ---
    function openManualTradeModal() {{
      document.getElementById("manualInputSymbol").value = "";
      document.getElementById("manualInputPrice").value = "";
      document.getElementById("manualInputLots").value = "1";
      document.getElementById("manualInputGain").value = "50";
      document.getElementById("manualInputStop").value = "50";
      document.getElementById("manualInputDte").value = "30";
      document.getElementById("manualInputLegs").value = "";
      document.getElementById("manualInputNotes").value = "";
      document.getElementById("modalManualPosition").classList.add("active");
    }}

    function closeManualTradeModal() {{
      document.getElementById("modalManualPosition").classList.remove("active");
    }}

    function confirmSaveManualTrade() {{
      const sym = document.getElementById("manualInputSymbol").value.trim().toUpperCase();
      if (!sym) {{
        alert("Informe o Ticker / Ativo.");
        return;
      }}
      const priceVal = parseFloat(document.getElementById("manualInputPrice").value);
      if (isNaN(priceVal) || priceVal <= 0) {{
        alert("Informe um preço unitário de execução válido.");
        return;
      }}
      const stratSelect = document.getElementById("manualInputStrategy");
      const stratId = stratSelect.value;
      const stratName = stratSelect.options[stratSelect.selectedIndex].text;
      const stratType = document.getElementById("manualInputType").value;
      const lotsVal = parseInt(document.getElementById("manualInputLots").value, 10) || 1;
      const targetGain = parseFloat(document.getElementById("manualInputGain").value) || 50;
      const stopLoss = parseFloat(document.getElementById("manualInputStop").value) || 50;
      const dteVal = parseInt(document.getElementById("manualInputDte").value, 10) || 30;
      const legsText = document.getElementById("manualInputLegs").value.trim();
      const notes = document.getElementById("manualInputNotes").value.trim();

      const posId = "pos_man_" + Date.now();
      const newPos = {{
        id: posId,
        symbol: sym,
        strategy_id: stratId,
        strategy_name: stratName,
        strategy_type: stratType,
        entry_date: new Date().toISOString(),
        entry_price: priceVal,
        quantity: lotsVal,
        target_gain_percent: targetGain,
        stop_loss_percent: stopLoss,
        notes: notes ? notes + (legsText ? " | Pernas: " + legsText : "") : (legsText ? "Pernas: " + legsText : "Registro manual"),
        legs: [],
        status: "OPEN",
        exit_date: null,
        exit_price: null,
        exit_notes: null,
        realized_pnl: null
      }};

      const positions = getStoredPositions();
      positions.push(newPos);
      saveStoredPositions(positions);

      closeManualTradeModal();
      renderOpportunities();
      renderTrackingTab();
    }}

    // --- CONFIRMAÇÃO VIA OPORTUNIDADE SCREENER ---
    function openExecutionModal(symbol, strategyId) {{
      const opp = (STATE.opportunities || []).find(o => o.symbol === symbol && o.strategy_id === strategyId);
      if (!opp) return;

      currentModalOpp = opp;
      document.getElementById("modalExecTitle").textContent = `🎯 Confirmar Execução: ${{opp.symbol}} — ${{opp.strategy_name}}`;

      const pricing = opp.pricing;
      let defaultPrice = "";
      if (pricing && pricing.display_value && pricing.display_value.value !== null) {{
        defaultPrice = pricing.display_value.value.toFixed(2);
      }}

      let legsDesc = "";
      if (opp.suggested_legs && opp.suggested_legs.length > 0) {{
        legsDesc = opp.suggested_legs.map(l =>
          `<li><b>${{l.action}}</b> ${{l.option_type}} Strike <b>$${{l.strike.toFixed(2)}}</b> (Venc: ${{l.expiration}})</li>`
        ).join("");
      }}

      document.getElementById("modalExecSummary").innerHTML = `
        <div style="margin-bottom: 0.5rem; font-weight: 600; color: var(--text-primary);">
          Ativo: <span class="mono">${{opp.symbol}}</span> | Estratégia: <b>${{opp.strategy_name}}</b>
        </div>
        <div style="font-size: 0.775rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
          Tipo: <b>${{pricing ? pricing.pricing_type : 'DEBIT'}}</b> | Referência Conservadora: <b>${{pricing ? pricing.label : 'N/D'}}</b> (${{pricing && pricing.display_value ? renderDataValue(pricing.display_value, {{ isCurrency: true }}) : 'N/D'}})
        </div>
        <ul style="margin-left: 1.25rem; font-size: 0.75rem; color: var(--text-primary);">
          ${{legsDesc}}
        </ul>
      `;

      document.getElementById("inputExecPrice").value = defaultPrice;
      document.getElementById("inputExecLots").value = "1";

      const isCredit = (pricing && pricing.pricing_type === "CREDIT");
      let defaultGain = "50";
      let defaultStop = isCredit ? "200" : "50";
      let guidelineNotes = "";
      if (opp.strategy_id === "bull_call_spread" || opp.strategy_id === "bear_put_spread") {{
        guidelineNotes = "Manejo: Alvo +50% Mark Mid. Manter com DTE > 14d e spot favorável. Stop defensivo DTE <= 14d se OTM.";
      }} else if (opp.strategy_id === "iron_condor") {{
        const callStrikes = (opp.suggested_legs || []).filter(l => l.option_type === "CALL" || l.type === "CALL").map(l => l.strike).sort((a, b) => a - b);
        const putStrikes = (opp.suggested_legs || []).filter(l => l.option_type === "PUT" || l.type === "PUT").map(l => l.strike).sort((a, b) => a - b);
        const callWing = callStrikes.length >= 2 ? (callStrikes[1] - callStrikes[0]) : 0;
        const putWing = putStrikes.length >= 2 ? (putStrikes[1] - putStrikes[0]) : 0;
        const wingW = Math.max(callWing, putWing);
        if (wingW > 0 && wingW <= 5.0) {{
          defaultGain = "30";
          guidelineNotes = `Manejo: Alvo calibrado em +30% do crédito no Mark (Asa estreita $${{wingW.toFixed(1)}}). Stop 200% do crédito. Risco gama DTE <= 21d.`;
        }} else {{
          guidelineNotes = `Manejo: Alvo padrão +50% do crédito no Mark (Asa larga $${{wingW.toFixed(1)}}). Stop 200% do crédito. Risco gama DTE <= 21d.`;
        }}
      }} else if (opp.strategy_id === "put_ratio_spread") {{
        guidelineNotes = "Manejo: Alvo +50% do crédito no Mark. Stop 200% do crédito. Ponta vendida excedente com risco não-definido; monitorar rompimento abaixo do strike vendido.";
      }} else if (opp.strategy_id === "long_strangle") {{
        const hasEv = opp.mandatory_criteria && opp.mandatory_criteria.event_in_horizon && (opp.mandatory_criteria.event_in_horizon.value === true || (opp.mandatory_criteria.event_in_horizon && opp.mandatory_criteria.event_in_horizon.value === "true"));
        if (hasEv) {{
          guidelineNotes = "Manejo: Alvo +50% Mark. Evento catalisador confirmado no horizonte: MANTER estrutura até o evento antes de aplicar stop temporal.";
        }} else {{
          guidelineNotes = "Manejo: Alvo +50% Mark. Sem evento confirmado: Stop temporal com DTE <= 14d para evitar precipício de decaimento teta.";
        }}
      }} else if (opp.strategy_id === "call_backspread") {{
        guidelineNotes = "Manejo: Alvo +50% Mark. Stop temporal DTE <= 14d para evitar precipício de decaimento teta.";
      }} else if (opp.strategy_id === "calendar_spread" || opp.strategy_id === "diagonal_spread") {{
        defaultGain = "30";
        guidelineNotes = "Manejo: Alvo +30% Mark. Fechar perna curta com DTE <= 3d para evitar risco de atribuição.";
      }}

      document.getElementById("inputTargetGain").value = defaultGain;
      document.getElementById("inputStopLoss").value = defaultStop;
      document.getElementById("inputExecNotes").value = guidelineNotes;

      document.getElementById("modalExecution").classList.add("active");
    }}

    function closeExecutionModal() {{
      document.getElementById("modalExecution").classList.remove("active");
      currentModalOpp = null;
    }}

    function confirmSaveExecution() {{
      if (!currentModalOpp) return;

      const priceVal = parseFloat(document.getElementById("inputExecPrice").value);
      if (isNaN(priceVal) || priceVal <= 0) {{
        alert("Informe um preço de execução unitário válido maior que zero.");
        return;
      }}

      const lotsVal = parseInt(document.getElementById("inputExecLots").value, 10) || 1;
      const targetGain = parseFloat(document.getElementById("inputTargetGain").value) || 50;
      const stopLoss = parseFloat(document.getElementById("inputStopLoss").value) || 50;
      const notes = document.getElementById("inputExecNotes").value || "";

      const pricing = currentModalOpp.pricing;
      const strategyType = pricing ? pricing.pricing_type : "DEBIT";

      const posId = "pos_" + Date.now() + "_" + Math.random().toString(36).substring(2, 7);
      const newPos = {{
        id: posId,
        symbol: currentModalOpp.symbol,
        strategy_id: currentModalOpp.strategy_id,
        strategy_name: currentModalOpp.strategy_name,
        strategy_type: strategyType,
        entry_date: new Date().toISOString(),
        entry_price: priceVal,
        quantity: lotsVal,
        target_gain_percent: targetGain,
        stop_loss_percent: stopLoss,
        notes: notes,
        legs: (currentModalOpp.suggested_legs || []).map(l => ({{
          symbol: l.symbol || currentModalOpp.symbol,
          strike: l.strike,
          option_type: l.option_type,
          action: l.action,
          expiration: l.expiration,
          dte: l.dte || 0
        }})),
        status: "OPEN",
        exit_date: null,
        exit_price: null,
        exit_notes: null,
        realized_pnl: null
      }};

      const positions = getStoredPositions();
      positions.push(newPos);
      saveStoredPositions(positions);

      closeExecutionModal();
      renderOpportunities();
      renderTrackingTab();
    }}

    // --- AVALIAÇÃO DE LIQUIDAÇÃO & SINAIS (BID/ASK + TASTYTRADE MARK) ---
    function evaluatePositionLiquidation(pos) {{
      const ctx = (STATE.contexts || []).find(c => c.symbol === pos.symbol);
      let minDte = 999;
      let totalExitCashConservative = 0; // Venda no Bid, Recompra no Ask
      let totalExitCashMid = 0;          // Cotação Mark / Mid
      let anyIndisp = false;
      let allLive = true;
      let quoteTs = "";

      if (!pos.legs || pos.legs.length === 0) {{
        return {{
          isAvailable: false,
          isLiveQuote: false,
          quoteSource: "indisponivel",
          quoteTimestamp: "",
          signal: "MANTER",
          reason: "Posição manual sem pernas detalhadas. Acompanhamento direto pelo histórico.",
          dteRemaining: 30,
          timeWarning: ""
        }};
      }}

      for (const leg of pos.legs) {{
        let bidVal = null;
        let askVal = null;
        let midVal = null;
        let dteVal = leg.dte || 0;
        let isLegLive = false;

        // 1. Tenta buscar cotação na cadeia carregada ao vivo do screener
        if (ctx && ctx.chains && ctx.chains[leg.expiration]) {{
          const q = ctx.chains[leg.expiration].find(item => Math.abs(item.strike - leg.strike) < 0.001 && item.type === leg.option_type);
          if (q) {{
            if (q.bid && q.bid.value !== null) bidVal = q.bid.value;
            if (q.ask && q.ask.value !== null) askVal = q.ask.value;
            if (q.mid) midVal = (typeof q.mid === 'object' && q.mid !== null) ? q.mid.value : q.mid;
            if (q.dte) dteVal = q.dte;
            if (bidVal !== null && askVal !== null) {{
              isLegLive = true;
            }}
          }}
        }}

        // 2. Fallback para cotações anexadas à própria perna (Snapshot Manual)
        if (!isLegLive) {{
          allLive = false;
          if (leg.quote_timestamp) quoteTs = leg.quote_timestamp;
          if (bidVal === null && leg.current_bid !== undefined) {{
            bidVal = (typeof leg.current_bid === 'object' && leg.current_bid !== null) ? leg.current_bid.value : leg.current_bid;
          }}
          if (askVal === null && leg.current_ask !== undefined) {{
            askVal = (typeof leg.current_ask === 'object' && leg.current_ask !== null) ? leg.current_ask.value : leg.current_ask;
          }}
          if (midVal === null && leg.current_mid !== undefined) {{
            midVal = (typeof leg.current_mid === 'object' && leg.current_mid !== null) ? leg.current_mid.value : leg.current_mid;
          }}
          if (midVal === null && bidVal !== null && askVal !== null) midVal = (bidVal + askVal) / 2;
        }}

        if (dteVal < minDte) minDte = dteVal;

        if (leg.action === "BUY") {{
          if (bidVal === null) {{
            anyIndisp = true;
            break;
          }}
          totalExitCashConservative += bidVal;
          totalExitCashMid += (midVal !== null ? midVal : bidVal);
        }} else {{
          if (askVal === null) {{
            anyIndisp = true;
            break;
          }}
          totalExitCashConservative -= askVal;
          totalExitCashMid -= (midVal !== null ? midVal : askVal);
        }}
      }}

      if (minDte === 999) minDte = 0;

      if (anyIndisp) {{
        return {{
          isAvailable: false,
          isLiveQuote: false,
          quoteSource: "indisponivel",
          quoteTimestamp: "",
          signal: "INDISPONIVEL",
          reason: "Cotação de uma ou mais pernas indisponível (contágio de proveniência ativado).",
          dteRemaining: minDte,
          timeWarning: ""
        }};
      }}

      let liquidatePrice = 0;
      let midPrice = 0;
      let pnlUnit = 0;
      let pnlUnitMid = 0;

      if (pos.strategy_type === "CREDIT") {{
        liquidatePrice = -totalExitCashConservative;
        midPrice = -totalExitCashMid;
        pnlUnit = pos.entry_price - liquidatePrice;
        pnlUnitMid = pos.entry_price - midPrice;
      }} else {{
        liquidatePrice = totalExitCashConservative;
        midPrice = totalExitCashMid;
        pnlUnit = liquidatePrice - pos.entry_price;
        pnlUnitMid = midPrice - pos.entry_price;
      }}

      const pnlPercent = pos.entry_price > 0 ? (pnlUnit / pos.entry_price) * 100 : 0;
      const pnlPercentMid = pos.entry_price > 0 ? (pnlUnitMid / pos.entry_price) * 100 : 0;
      const totalPnl = pnlUnit * pos.quantity * 100;
      const totalPnlMid = pnlUnitMid * pos.quantity * 100;

      // Spot e Moneyness
      let spotVal = null;
      if (ctx && ctx.spot_price && ctx.spot_price.value !== null) {{
        spotVal = ctx.spot_price.value;
      }} else if (pos.current_spot && pos.current_spot.value !== null) {{
        spotVal = pos.current_spot.value;
      }}

      // Avaliação Especializada por Família de Estratégia (Delta, Gamma, Theta, Vega e DTE)
      const stratId = pos.strategy_id || "";
      const isCredit = (pos.strategy_type === "CREDIT" || stratId === "iron_condor" || stratId === "put_ratio_spread");

      let timeWarning = "";
      let signal = "MANTER";
      let reason = "";

      // 1. TRAVAS VERTICAIS DE DÉBITO (Bull Call Spread, Bear Put Spread)
      if (stratId === "bull_call_spread" || stratId === "bear_put_spread") {{
        const longLeg = (pos.legs || []).find(l => l.action === "BUY");
        let isFavorableSpot = false;
        let spotDesc = "";

        if (spotVal !== null && longLeg) {{
          if (stratId === "bull_call_spread") {{
            isFavorableSpot = (spotVal >= longLeg.strike * 0.99);
            if (spotVal >= longLeg.strike) {{
              spotDesc = `Spot $${{spotVal.toFixed(2)}} ITM acima do strike comprado $${{longLeg.strike.toFixed(2)}}.`;
            }} else {{
              spotDesc = `Spot $${{spotVal.toFixed(2)}} próximo ao strike comprado $${{longLeg.strike.toFixed(2)}}.`;
            }}
          }} else {{
            isFavorableSpot = (spotVal <= longLeg.strike * 1.01);
            if (spotVal <= longLeg.strike) {{
              spotDesc = `Spot $${{spotVal.toFixed(2)}} ITM abaixo do strike comprado $${{longLeg.strike.toFixed(2)}}.`;
            }} else {{
              spotDesc = `Spot $${{spotVal.toFixed(2)}} próximo ao strike comprado $${{longLeg.strike.toFixed(2)}}.`;
            }}
          }}
        }}

        if (pnlPercentMid >= pos.target_gain_percent) {{
          signal = "REALIZAR_GAIN";
          reason = `Meta de lucro atingida no Mark (+${{pnlPercentMid.toFixed(1)}}% >= +${{pos.target_gain_percent}}%).`;
        }} else if (pnlPercentMid >= pos.target_gain_percent * 0.85) {{
          signal = "ALVO_PROXIMO";
          reason = `Próximo ao alvo de lucro (+${{pnlPercentMid.toFixed(1)}}% de +${{pos.target_gain_percent}}%). ${{spotDesc}}`;
        }} else if (minDte > 14) {{
          signal = "MANTER";
          if (isFavorableSpot) {{
            reason = `Maturação saudável aos ${{minDte}}d DTE (${{pnlPercentMid >= 0 ? '+' : ''}}${{pnlPercentMid.toFixed(1)}}% Mark). ${{spotDesc}} Aguardar decaimento do valor extrínseco da perna vendida.`;
          }} else {{
            reason = `Em maturação aos ${{minDte}}d DTE (${{pnlPercentMid >= 0 ? '+' : ''}}${{pnlPercentMid.toFixed(1)}}% Mark). Tese técnica em andamento; risco limitado ao débito pago.`;
          }}
        }} else {{
          timeWarning = `⚠️ Alerta DTE=${{minDte}}d (<=14d): Aceleração do decaimento teta contra a posição.`;
          if (pnlPercentMid <= -pos.stop_loss_percent && !isFavorableSpot) {{
            signal = "STOPAR";
            reason = `Encerramento defensivo: DTE avançado (${{minDte}}d <= 14d) com ativo fora do dinheiro (${{pnlPercentMid.toFixed(1)}}% <= -${{pos.stop_loss_percent}}%).`;
          }} else {{
            signal = "MANTER";
            reason = `Reta final (${{minDte}}d DTE) com P&L Mark em ${{pnlPercentMid >= 0 ? '+' : ''}}${{pnlPercentMid.toFixed(1)}}%. ${{spotDesc}}`;
          }}
        }}
      }}
      // 2. ESTRATÉGIAS A CRÉDITO (Iron Condor, Put Ratio, Spreads de Crédito)
      else if (isCredit) {{
        if (minDte <= 21) {{
          timeWarning = `⚠️ Alerta DTE=${{minDte}}d (<=21d): Risco gama terminal. Considere encerrar ou rolar no Mark.`;
        }}
        let creditTarget = pos.target_gain_percent;
        let targetNote = "";
        if (stratId === "iron_condor") {{
          const callStrikes = pos.legs.filter(l => l.option_type === "CALL").map(l => l.strike).sort((a, b) => a - b);
          const putStrikes = pos.legs.filter(l => l.option_type === "PUT").map(l => l.strike).sort((a, b) => a - b);
          const callWing = callStrikes.length >= 2 ? (callStrikes[1] - callStrikes[0]) : 0;
          const putWing = putStrikes.length >= 2 ? (putStrikes[1] - putStrikes[0]) : 0;
          const wingW = Math.max(callWing, putWing);
          if (wingW > 0 && wingW <= 5.0) {{
            creditTarget = Math.min(pos.target_gain_percent, 30.0);
            targetNote = ` (Alvo calibrado pela largura de asa estreita $${{wingW.toFixed(1)}} = ${{creditTarget.toFixed(0)}}%)`;
          }}
        }}

        if (pnlPercentMid >= creditTarget) {{
          signal = "REALIZAR_GAIN";
          reason = `Meta de crédito atingida (+${{pnlPercentMid.toFixed(1)}}% >= +${{creditTarget}}%)${{targetNote}}.`;
        }} else if (pnlPercentMid <= -pos.stop_loss_percent) {{
          signal = "STOPAR";
          reason = `Limite de perda atingido (${{pnlPercentMid.toFixed(1)}}% <= -${{pos.stop_loss_percent}}%).`;
        }} else if (minDte <= 21) {{
          signal = "MANTER";
          reason = `Operação a crédito em zona de defesa temporal (${{minDte}}d DTE). ${{timeWarning}}`;
        }} else {{
          signal = "MANTER";
          reason = `Operação a crédito maturando com teta positivo (${{pnlPercentMid >= 0 ? '+' : ''}}${{pnlPercentMid.toFixed(1)}}% Mark).`;
        }}
      }}
      // 3. COMPRA DE VOLATILIDADE (Long Strangle, Call Backspread)
      else if (stratId === "long_strangle" || stratId === "call_backspread") {{
        if (pnlPercentMid >= pos.target_gain_percent) {{
          signal = "REALIZAR_GAIN";
          reason = `Meta de expansão de volatilidade atingida (+${{pnlPercentMid.toFixed(1)}}% >= +${{pos.target_gain_percent}}%).`;
        }} else if (minDte <= 14) {{
          const hasEvent = (ctx && ctx.event_in_horizon && ctx.event_in_horizon.value === true);
          if (hasEvent) {{
            timeWarning = `⚠️ Alerta DTE=${{minDte}}d (<=14d): Evento catalisador pendente no horizonte. Manter estrutura até a realização do evento antes de aplicar stop temporal.`;
            signal = "MANTER";
            reason = `Aguardando realização do catalisador/evento no horizonte antes do stop temporal (${{pnlPercentMid >= 0 ? '+' : ''}}${{pnlPercentMid.toFixed(1)}}% Mark, ${{minDte}}d DTE).`;
          }} else {{
            timeWarning = `⚠️ Alerta DTE=${{minDte}}d (<=14d): Precipício de decaimento teta em opções compradas.`;
            signal = "STOPAR";
            reason = `Stop temporal por esgotamento de DTE (${{minDte}}d <= 14d) para evitar precipício de decaimento teta.`;
          }}
        }} else if (pnlPercentMid <= -pos.stop_loss_percent) {{
          signal = "STOPAR";
          reason = `Limite de perda atingido (${{pnlPercentMid.toFixed(1)}}% <= -${{pos.stop_loss_percent}}%).`;
        }} else {{
          signal = "MANTER";
          reason = `Aguardando expansão de volatilidade (${{pnlPercentMid >= 0 ? '+' : ''}}${{pnlPercentMid.toFixed(1)}}% Mark, ${{minDte}}d DTE).`;
        }}
      }}
      // 4. ESTRUTURAS TEMPORAIS E HÍBRIDAS (Calendar Spread, Diagonal Spread)
      else if (stratId === "calendar_spread" || stratId === "diagonal_spread") {{
        const calTarget = pos.target_gain_percent;
        if (pnlPercentMid >= calTarget) {{
          signal = "REALIZAR_GAIN";
          reason = `Meta de calendar/diagonal atingida (+${{pnlPercentMid.toFixed(1)}}% >= +${{calTarget}}%).`;
        }} else if (minDte <= 3) {{
          signal = "STOPAR";
          reason = `Perna curta expirando em ${{minDte}}d. Encerrar para evitar risco de atribuição.`;
        }} else if (pnlPercentMid <= -pos.stop_loss_percent) {{
          signal = "STOPAR";
          reason = `Limite de perda atingido (${{pnlPercentMid.toFixed(1)}}% <= -${{pos.stop_loss_percent}}%).`;
        }} else {{
          signal = "MANTER";
          reason = `Spread temporal maturando via decaimento da perna curta (${{pnlPercentMid >= 0 ? '+' : ''}}${{pnlPercentMid.toFixed(1)}}% Mark, ${{minDte}}d DTE).`;
        }}
      }}
      // 5. DEFAULT
      else {{
        if (pnlPercentMid >= pos.target_gain_percent) {{
          signal = "REALIZAR_GAIN";
          reason = `Meta de ganho atingida (+${{pnlPercentMid.toFixed(1)}}% >= +${{pos.target_gain_percent}}%).`;
        }} else if (pnlPercentMid <= -pos.stop_loss_percent) {{
          signal = "STOPAR";
          reason = `Limite de perda atingido (${{pnlPercentMid.toFixed(1)}}% <= -${{pos.stop_loss_percent}}%).`;
        }} else {{
          signal = "MANTER";
          reason = `Operação dentro da faixa operacional (${{pnlPercentMid >= 0 ? '+' : ''}}${{pnlPercentMid.toFixed(1)}}% Mark).`;
        }}
      }}

      if (!allLive) {{
        const dtLabel = quoteTs ? quoteTs.substring(0, 10) : "22/09/2026";
        reason = `${{reason}} [⚠️ COTAÇÃO DE SNAPSHOT MANUAL (${{dtLabel}}) — requer cotação ao vivo da corretora para confirmação de sinal].`;
      }}

      return {{
        isAvailable: true,
        isLiveQuote: allLive,
        quoteSource: allLive ? "live:chain" : "snapshot:manual",
        quoteTimestamp: quoteTs || (allLive ? (STATE.generated_at || "") : "2026-09-22"),
        liquidatePrice: liquidatePrice,
        midPrice: midPrice,
        pnlUnit: pnlUnit,
        pnlPercent: pnlPercent,
        totalPnl: totalPnl,
        pnlUnitMid: pnlUnitMid,
        pnlPercentMid: pnlPercentMid,
        totalPnlMid: totalPnlMid,
        signal: signal,
        reason: reason,
        dteRemaining: minDte,
        timeWarning: timeWarning,
        spotPrice: spotVal
      }};
    }}

    function openCloseTradeModal(posId) {{
      const positions = getStoredPositions();
      const pos = positions.find(p => p.id === posId);
      if (!pos) return;

      currentClosePosId = posId;
      const evalRes = evaluatePositionLiquidation(pos);

      document.getElementById("modalCloseTitle").textContent = `Encerrar Posição: ${{pos.symbol}} — ${{pos.strategy_name}}`;

      let summaryHtml = `
        <div style="margin-bottom: 0.4rem; font-weight: 600;">Ativo: <span class="mono">${{pos.symbol}}</span> | Lotes: <b>${{pos.quantity}}</b></div>
        <div style="font-size: 0.775rem; color: var(--text-secondary); margin-bottom: 0.4rem;">
          Entrada em: <b>${{pos.entry_date.substring(0, 10)}}</b> | Preço Entrada: <b>$ ${{pos.entry_price.toFixed(2)}}</b> (${{pos.strategy_type}})
        </div>
      `;

      if (evalRes.isAvailable) {{
        const color = evalRes.totalPnlMid >= 0 ? "var(--positive)" : "var(--negative)";
        summaryHtml += `
          <div style="font-size: 0.8rem; margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid var(--border);">
            Preço Mark (Tastytrade Mid): <b class="mono">$ ${{evalRes.midPrice.toFixed(2)}}</b> | P&L Mark: <b class="mono" style="color: ${{color}};">${{formatBRLCurrency(evalRes.totalPnlMid)}} (${{evalRes.pnlPercentMid >= 0 ? '+' : ''}}${{evalRes.pnlPercentMid.toFixed(1)}}%)</b>
          </div>
          <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.25rem;">
            Liquidação Conservadora (Bid/Ask): <b class="mono">$ ${{evalRes.liquidatePrice.toFixed(2)}}</b>
          </div>
        `;
        document.getElementById("inputExitPrice").value = evalRes.midPrice.toFixed(2);
      }} else {{
        summaryHtml += `
          <div style="font-size: 0.775rem; color: var(--alert); margin-top: 0.5rem;">
            ⚠ Cotação de saída indisponível em tempo real. Informe manualmente o valor executado.
          </div>
        `;
        document.getElementById("inputExitPrice").value = "";
      }}

      document.getElementById("modalCloseSummary").innerHTML = summaryHtml;
      document.getElementById("inputCloseNotes").value = evalRes.isAvailable ? evalRes.reason : "";
      document.getElementById("modalCloseTrade").classList.add("active");
    }}

    function closeCloseTradeModal() {{
      document.getElementById("modalCloseTrade").classList.remove("active");
      currentClosePosId = null;
    }}

    function confirmCloseTrade() {{
      if (!currentClosePosId) return;

      const exitPrice = parseFloat(document.getElementById("inputExitPrice").value);
      if (isNaN(exitPrice) || exitPrice < 0) {{
        alert("Informe um preço de liquidação unitário válido.");
        return;
      }}

      const notes = document.getElementById("inputCloseNotes").value || "";
      const positions = getStoredPositions();
      const posIndex = positions.findIndex(p => p.id === currentClosePosId);
      if (posIndex === -1) return;

      const pos = positions[posIndex];
      let pnlUnit = 0;
      if (pos.strategy_type === "CREDIT") {{
        pnlUnit = pos.entry_price - exitPrice;
      }} else {{
        pnlUnit = exitPrice - pos.entry_price;
      }}

      const realizedPnl = Math.round(pnlUnit * pos.quantity * 100 * 100) / 100;

      pos.status = "CLOSED";
      pos.exit_date = new Date().toISOString();
      pos.exit_price = exitPrice;
      pos.exit_notes = notes;
      pos.realized_pnl = realizedPnl;

      saveStoredPositions(positions);
      closeCloseTradeModal();
      renderOpportunities();
      renderTrackingTab();
    }}

    function deletePosition(posId) {{
      if (!confirm("Deseja realmente remover esta posição do registro?")) return;
      let positions = getStoredPositions();
      positions = positions.filter(p => p.id !== posId);
      saveStoredPositions(positions);
      renderOpportunities();
      renderTrackingTab();
    }}

    function renderTrackingTab() {{
      const positions = getStoredPositions();
      const openPositions = positions.filter(p => p.status === "OPEN" || p.status === "ABERTA");
      const closedPositions = positions.filter(p => p.status === "CLOSED" || p.status === "ENCERRADA");

      // Atualiza KPIs
      document.getElementById("kpiActiveCount").textContent = openPositions.length;

      let totalUnrealized = 0;
      let hasUnrealized = false;

      const cardsGrid = document.getElementById("trackingCardsGrid");
      cardsGrid.innerHTML = "";

      if (openPositions.length === 0) {{
        cardsGrid.innerHTML = `
          <div style="grid-column: 1 / -1; padding: 2.5rem; text-align: center; color: var(--text-secondary); background: var(--surface-card); border-radius: 8px; border: 1px dashed var(--border);">
            <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">📋</div>
            <div style="font-size: 1rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.25rem;">Nenhuma posição ativa em acompanhamento</div>
            <div style="font-size: 0.8rem;">Vá até a aba <b>"Oportunidades"</b> ou clique em <b>"➕ Nova Operação Manual"</b> ou <b>"📌 Carregar BAC (Print)"</b>.</div>
          </div>
        `;
      }} else {{
        openPositions.forEach(pos => {{
          let evalRes;
          if (pos.evaluation && pos.evaluation.signal) {{
            const ev = pos.evaluation;
            const liqVal = (ev.liquidate_price && typeof ev.liquidate_price.value === 'number') ? ev.liquidate_price.value : 0;
            const midVal = (ev.mid_price && typeof ev.mid_price.value === 'number') ? ev.mid_price.value : (ev.mid_price || liqVal);
            const pnlMidPct = (ev.pnl_mid_percent && typeof ev.pnl_mid_percent.value === 'number') ? ev.pnl_mid_percent.value : 0;
            const pnlMidUnit = (ev.pnl_mid_unit && typeof ev.pnl_mid_unit.value === 'number') ? ev.pnl_mid_unit.value : 0;
            evalRes = {{
              isAvailable: ev.signal !== "INDISPONIVEL",
              isLiveQuote: ev.is_live_quote !== false,
              quoteSource: ev.quote_source || "live:chain",
              quoteTimestamp: ev.quote_timestamp || "",
              signal: ev.signal,
              reason: ev.signal_reason,
              dteRemaining: ev.dte_remaining,
              timeWarning: ev.time_warning || "",
              liquidatePrice: liqVal,
              midPrice: midVal,
              pnlPercentMid: pnlMidPct,
              totalPnlMid: pnlMidUnit * (pos.quantity || 1) * 100,
              spotPrice: (pos.current_spot && typeof pos.current_spot.value === 'number') ? pos.current_spot.value : null
            }};
          }} else {{
            evalRes = evaluatePositionLiquidation(pos);
          }}

          if (evalRes.isAvailable) {{
            totalUnrealized += (evalRes.totalPnlMid !== undefined ? evalRes.totalPnlMid : evalRes.totalPnl);
            hasUnrealized = true;
          }}

          let signalHtml = "";
          if (evalRes.signal === "REALIZAR_GAIN") {{
            signalHtml = '<span class="signal-pill signal-gain">💰 REALIZAR GAIN</span>';
          }} else if (evalRes.signal === "ALVO_PROXIMO") {{
            signalHtml = `<span class="signal-pill signal-gain" style="box-shadow: 0 0 10px rgba(16, 185, 129, 0.4);">🎯 ALVO PRÓXIMO (${{evalRes.pnlPercentMid.toFixed(1)}}%)</span>`;
          }} else if (evalRes.signal === "STOPAR") {{
            signalHtml = '<span class="signal-pill signal-stop">🛑 STOPAR</span>';
          }} else if (evalRes.signal === "MANTER") {{
            signalHtml = '<span class="signal-pill signal-manter">⏳ MANTER</span>';
          }} else {{
            signalHtml = '<span class="signal-pill signal-indisp">⚠ INDISPONÍVEL</span>';
          }}

          if (!evalRes.isLiveQuote) {{
            signalHtml += `<div style="font-size: 0.65rem; color: #f59e0b; margin-top: 3px; font-weight: 500; text-align: right;">⚠️ Cotação Estática (${{evalRes.quoteTimestamp ? evalRes.quoteTimestamp.substring(0, 10) : 'Snapshot'}})</div>`;
          }}

          const markLabel = evalRes.isLiveQuote 
            ? 'Mark Corretora (Mid) <span class="badge badge-med" style="font-size: 0.65rem; padding: 1px 4px;">AO VIVO</span>'
            : 'Cotação Snapshot (Mid) <span class="badge" style="font-size: 0.625rem; padding: 1px 4px; background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b;">ESTÁTICO</span>';

          let pnlColor = "var(--text-secondary)";
          let pnlText = "N/D";
          let liqText = "N/D";
          let midText = "N/D";

          if (evalRes.isAvailable) {{
            pnlColor = evalRes.totalPnlMid >= 0 ? "var(--positive)" : "var(--negative)";
            pnlText = `${{formatBRLCurrency(evalRes.totalPnlMid)}} (${{evalRes.pnlPercentMid >= 0 ? '+' : ''}}${{evalRes.pnlPercentMid.toFixed(1)}}%)`;
            liqText = `$ ${{evalRes.liquidatePrice.toFixed(2)}}`;
            midText = `$ ${{evalRes.midPrice.toFixed(2)}}`;
          }}

          let legsListHtml = "";
          if (pos.legs && pos.legs.length > 0) {{
            legsListHtml = pos.legs.map(l => {{
              const bVal = (typeof l.current_bid === 'object' && l.current_bid !== null) ? l.current_bid.value : l.current_bid;
              const aVal = (typeof l.current_ask === 'object' && l.current_ask !== null) ? l.current_ask.value : l.current_ask;
              const isLegLive = (l.quote_provenance === "MEDIDO" || (typeof l.current_bid === 'object' && l.current_bid && l.current_bid.provenance === "MEDIDO"));
              const badge = isLegLive 
                ? '<span class="badge badge-med" style="font-size: 0.6rem; padding: 1px 4px;">MED</span>'
                : '<span class="badge" style="font-size: 0.6rem; padding: 1px 4px; background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b;">SNAPSHOT</span>';
              return `<li><b>${{l.action}}</b> ${{l.option_type}} Strike <b>$${{l.strike.toFixed(2)}}</b> (Venc: ${{l.expiration || 'Oct 23'}} | Bid: ${{bVal !== undefined && bVal !== null ? '$' + bVal.toFixed(2) : 'N/D'}} / Ask: ${{aVal !== undefined && aVal !== null ? '$' + aVal.toFixed(2) : 'N/D'}}) ${{badge}}</li>`;
            }}).join("");
          }}

          const card = document.createElement("div");
          card.className = "tracking-card";
          card.innerHTML = `
            <div class="tracking-card-header">
              <div>
                <div class="opp-symbol">${{pos.symbol}}</div>
                <div class="opp-strategy">${{pos.strategy_name}}</div>
              </div>
              <div>${{signalHtml}}</div>
            </div>

            <div style="display: flex; gap: 0.5rem; margin-bottom: 0.85rem; font-size: 0.775rem; color: var(--text-secondary); flex-wrap: wrap;">
              <span>Entrada: <b>${{pos.entry_date.substring(0, 10)}}</b></span> |
              <span>Lotes: <b>${{pos.quantity}}</b></span> |
              <span>Tipo: <b>${{pos.strategy_type}}</b></span>
              ${{evalRes.spotPrice !== null && evalRes.spotPrice !== undefined ? `| <span>Spot: <b class="mono">$ ${{evalRes.spotPrice.toFixed(2)}}</b></span>` : ''}}
            </div>

            <div class="tracking-metrics">
              <div class="tracking-metric-item">
                <span class="tracking-metric-label">Preço Entrada</span>
                <span class="tracking-metric-val mono">$ ${{pos.entry_price.toFixed(2)}}</span>
              </div>
              <div class="tracking-metric-item">
                <span class="tracking-metric-label">${{markLabel}}</span>
                <span class="tracking-metric-val mono">${{midText}}</span>
              </div>
              <div class="tracking-metric-item">
                <span class="tracking-metric-label">P&L Mark</span>
                <span class="tracking-metric-val mono" style="color: ${{pnlColor}};">${{pnlText}}</span>
              </div>
              <div class="tracking-metric-item">
                <span class="tracking-metric-label">Saída Conservadora</span>
                <span class="tracking-metric-val mono">${{liqText}}</span>
              </div>
            </div>

            <div style="font-size: 0.775rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
              <b>Diagnóstico:</b> ${{evalRes.reason}}
            </div>

            ${{evalRes.timeWarning ? `<div style="font-size: 0.725rem; color: var(--alert); background: var(--alert-bg); padding: 0.35rem 0.5rem; border-radius: 4px; margin-bottom: 0.65rem;">${{evalRes.timeWarning}}</div>` : ''}}

            ${{legsListHtml ? `
              <div style="background: var(--surface-alt); padding: 0.5rem 0.65rem; border-radius: 6px; font-size: 0.725rem; margin-bottom: 0.85rem;">
                <div style="font-weight: 600; margin-bottom: 0.25rem; color: var(--text-secondary);">Pernas Estruturadas:</div>
                <ul style="margin-left: 1rem; color: var(--text-primary);">
                  ${{legsListHtml}}
                </ul>
              </div>
            ` : ''}}

            ${{pos.notes ? `<div style="font-size: 0.725rem; color: #93c5fd; background: rgba(59, 130, 246, 0.08); padding: 0.4rem 0.6rem; border-radius: 4px; margin-bottom: 0.85rem; border-left: 3px solid var(--accent);"><em>Info / GTC:</em> ${{pos.notes}}</div>` : ''}}

            <div class="tracking-card-actions">
              <button class="btn-export" style="color: var(--negative); padding: 0.4rem 0.65rem;" onclick="deletePosition('${{pos.id}}')">🗑 Excluir</button>
              <button class="btn-export" style="background: var(--positive-bg); color: var(--positive); border-color: var(--positive); font-weight: 600; padding: 0.4rem 0.85rem;" onclick="openCloseTradeModal('${{pos.id}}')">✔ Encerrar Posição</button>
            </div>
          `;
          cardsGrid.appendChild(card);
        }});
      }}

      // KPI P&L Não Realizado
      const elUnrealized = document.getElementById("kpiUnrealizedPnl");
      if (hasUnrealized) {{
        elUnrealized.textContent = formatBRLCurrency(totalUnrealized);
        elUnrealized.style.color = totalUnrealized >= 0 ? "var(--positive)" : "var(--negative)";
      }} else {{
        elUnrealized.textContent = "$ 0,00";
        elUnrealized.style.color = "var(--text-primary)";
      }}

      // KPI P&L Realizado & Win Rate
      let totalRealized = 0;
      let totalWins = 0;
      closedPositions.forEach(p => {{
        const pnl = (typeof p.realized_pnl === 'object' && p.realized_pnl !== null) ? (p.realized_pnl.value || 0) : (p.realized_pnl || 0);
        if (p.realized_pnl !== null && p.realized_pnl !== undefined) {{
          totalRealized += pnl;
          if (pnl > 0) totalWins++;
        }}
      }});

      const elRealized = document.getElementById("kpiRealizedPnlTotal");
      elRealized.textContent = formatBRLCurrency(totalRealized);
      elRealized.style.color = totalRealized >= 0 ? "var(--positive)" : "var(--negative)";

      const elWinRate = document.getElementById("kpiWinRateTotal");
      if (closedPositions.length > 0) {{
        const wr = ((totalWins / closedPositions.length) * 100).toFixed(1);
        elWinRate.textContent = `${{wr}} %`;
      }} else {{
        elWinRate.textContent = "-- %";
      }}

      // Renderiza Tabela de Ranking
      renderRankingTable(closedPositions);

      // Renderiza Tabela de Histórico
      renderHistoryTable(closedPositions);
    }}

    function renderRankingTable(closedPositions) {{
      const tbody = document.getElementById("rankingTableBody");
      tbody.innerHTML = "";

      if (closedPositions.length === 0) {{
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-secondary); padding: 1.5rem;">Nenhum trade encerrado ainda. Encerre posições para consolidar o ranking de sucesso.</td></tr>';
        return;
      }}

      const byStrat = {{}};
      closedPositions.forEach(p => {{
        if (!byStrat[p.strategy_name]) {{
          byStrat[p.strategy_name] = {{
            name: p.strategy_name,
            trades: 0,
            wins: 0,
            losses: 0,
            totalPnl: 0
          }};
        }}
        byStrat[p.strategy_name].trades++;
        const pnl = (typeof p.realized_pnl === 'object' && p.realized_pnl !== null) ? (p.realized_pnl.value || 0) : (p.realized_pnl || 0);
        byStrat[p.strategy_name].totalPnl += pnl;
        if (pnl > 0) byStrat[p.strategy_name].wins++;
        else if (pnl < 0) byStrat[p.strategy_name].losses++;
      }});

      const ranked = Object.values(byStrat).sort((a, b) => b.totalPnl - a.totalPnl);

      ranked.forEach((r, idx) => {{
        const tr = document.createElement("tr");
        let medal = `${{idx + 1}}º`;
        if (idx === 0) medal = '<span class="rank-medal rank-gold">🥇 1º</span>';
        else if (idx === 1) medal = '<span class="rank-medal rank-silver">🥈 2º</span>';
        else if (idx === 2) medal = '<span class="rank-medal rank-bronze">🥉 3º</span>';

        const winRate = r.trades > 0 ? ((r.wins / r.trades) * 100).toFixed(1) : "0.0";
        const pnlColor = r.totalPnl >= 0 ? "var(--positive)" : "var(--negative)";

        tr.innerHTML = `
          <td>${{medal}}</td>
          <td><b>${{r.name}}</b></td>
          <td class="mono">${{r.trades}}</td>
          <td class="mono" style="color: var(--positive);">${{r.wins}}</td>
          <td class="mono" style="color: var(--negative);">${{r.losses}}</td>
          <td class="mono"><b>${{winRate}} %</b></td>
          <td class="mono" style="color: ${{pnlColor}}; font-weight: 700;">${{formatBRLCurrency(r.totalPnl)}}</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function renderHistoryTable(closedPositions) {{
      const tbody = document.getElementById("historyTableBody");
      tbody.innerHTML = "";

      if (closedPositions.length === 0) {{
        tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: var(--text-secondary); padding: 1.5rem;">Nenhum trade encerrado no histórico.</td></tr>';
        return;
      }}

      // Ordena por data de saída decrescente
      const sorted = [...closedPositions].sort((a, b) => (b.exit_date || "").localeCompare(a.exit_date || ""));

      sorted.forEach(p => {{
        const tr = document.createElement("tr");
        const pnl = (typeof p.realized_pnl === 'object' && p.realized_pnl !== null) ? (p.realized_pnl.value || 0) : (p.realized_pnl || 0);
        const pnlColor = pnl >= 0 ? "var(--positive)" : "var(--negative)";
        const entryPriceVal = (typeof p.entry_price === 'object' && p.entry_price !== null) ? (p.entry_price.value || 0) : (p.entry_price || 0);
        const exitPriceVal = (typeof p.exit_price === 'object' && p.exit_price !== null) ? p.exit_price.value : p.exit_price;

        tr.innerHTML = `
          <td class="mono" style="font-size: 0.725rem; color: var(--text-secondary);">${{p.id}}</td>
          <td><b class="mono">${{p.symbol}}</b></td>
          <td>${{p.strategy_name}}</td>
          <td>${{p.entry_date ? p.entry_date.substring(0, 10) : 'N/D'}}</td>
          <td>${{p.exit_date ? p.exit_date.substring(0, 10) : 'N/D'}}</td>
          <td class="mono">$ ${{entryPriceVal.toFixed(2)}}</td>
          <td class="mono">${{exitPriceVal !== null && exitPriceVal !== undefined ? `$ ${{exitPriceVal.toFixed(2)}}` : 'N/D'}}</td>
          <td class="mono" style="color: ${{pnlColor}}; font-weight: 700;">${{formatBRLCurrency(pnl)}}</td>
          <td style="font-size: 0.775rem; color: var(--text-secondary);">${{p.exit_notes || p.notes || '-'}}</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function exportPositionsJson() {{
      const positions = getStoredPositions();
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(positions, null, 2));
      const dlAnchorElem = document.createElement('a');
      dlAnchorElem.setAttribute("href", dataStr);
      dlAnchorElem.setAttribute("download", "op_tasty_posicoes.json");
      dlAnchorElem.click();
    }}

    function importPositionsJson(event) {{
      const file = event.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = function(e) {{
        try {{
          const imported = JSON.parse(e.target.result);
          if (!Array.isArray(imported)) {{
            alert("Arquivo JSON inválido. Esperado um array de posições.");
            return;
          }}
          saveStoredPositions(imported);
          alert(`Sucesso! ${{imported.length}} posições carregadas.`);
          renderOpportunities();
          renderTrackingTab();
        }} catch (err) {{
          alert("Erro ao ler o arquivo JSON: " + err.message);
        }}
      }};
      reader.readAsText(file);
    }}

    function clearAllTrackingData() {{
      if (!confirm("Atenção: Esta ação apagará todas as posições abertas e o histórico de trades deste navegador.\\nDeseja continuar?")) return;
      localStorage.removeItem(POSITIONS_STORAGE_KEY);
      renderOpportunities();
      renderTrackingTab();
    }}

    // ============================================================
    // AUTO-REFRESH (30 MINUTOS) & ATUALIZAÇÃO SOB DEMANDA
    // ============================================================
    let autoRefreshRemaining = 1800; // 30 minutos em segundos
    let autoRefreshActive = true;
    let refreshTimerInterval = null;

    function showToastNotification(message, type = "positive") {{
      const container = document.getElementById("toastContainer");
      if (!container) return;

      const toast = document.createElement("div");
      toast.className = `toast-item toast-${{type}}`;
      toast.innerHTML = `<span>${{message}}</span>`;
      container.appendChild(toast);

      setTimeout(() => {{
        toast.style.opacity = "0";
        toast.style.transform = "translateY(10px)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 350);
      }}, 4000);
    }}

    function applyNewMarketData(newData) {{
      if (!newData) return;
      STATE = newData;

      // 1. Metadados do topo
      if (STATE.generated_at) {{
        const dtStr = STATE.generated_at.replace('T', ' ').substring(0, 19);
        document.getElementById("bannerTimestamp").textContent = `Coleta: ${{dtStr}} UTC`;
      }}
      if (STATE.universe) {{
        document.getElementById("metaUniverseCount").textContent = `${{STATE.universe.length}} Ativos`;
      }}
      if (STATE.opportunities) {{
        document.getElementById("metaOppCount").textContent = `${{STATE.opportunities.length}} Sinais`;
      }}

      // 2. Sincroniza posições rastreadas recebidas com o localStorage
      if (Array.isArray(newData.tracked_positions) && newData.tracked_positions.length > 0) {{
        try {{
          const storedPositions = getStoredPositions();
          const updatedPositions = storedPositions.map(pos => {{
            const fresh = newData.tracked_positions.find(p => (p.id || p.position_id) === (pos.id || pos.position_id));
            if (!fresh) return pos;

            // Preserva status encerrado pelo usuário localmente
            if (pos.status === "CLOSED" || pos.status === "ENCERRADA") {{
              return pos;
            }}

            return {{
              ...pos,
              current_spot: fresh.current_spot || pos.current_spot,
              evaluation: fresh.evaluation || pos.evaluation,
              legs: pos.legs.map((leg, idx) => {{
                const freshLeg = fresh.legs && fresh.legs[idx];
                if (!freshLeg) return leg;
                return {{
                  ...leg,
                  current_bid: freshLeg.current_bid !== undefined ? freshLeg.current_bid : leg.current_bid,
                  current_ask: freshLeg.current_ask !== undefined ? freshLeg.current_ask : leg.current_ask,
                  current_mid: freshLeg.current_mid !== undefined ? freshLeg.current_mid : leg.current_mid,
                  quote_timestamp: freshLeg.quote_timestamp || leg.quote_timestamp,
                  quote_provenance: freshLeg.quote_provenance || leg.quote_provenance
                }};
              }})
            }};
          }});
          saveStoredPositions(updatedPositions);
        }} catch (err) {{
          console.error("Erro ao sincronizar posições rastreadas no refresh:", err);
        }}
      }}

      // 3. Re-renderiza abas preservando estado
      renderOpportunities();
      initChains();
      renderTrackingTab();

      const chartsTab = document.getElementById("tab-charts");
      if (chartsTab && chartsTab.classList.contains("active")) {{
        renderCharts();
      }}
    }}

    async function triggerMarketRefresh() {{
      const btn = document.getElementById("btnRefreshMarket");
      const icon = document.getElementById("refreshIcon");
      const label = document.getElementById("refreshLabel");

      if (btn && btn.disabled) return;

      if (btn) {{
        btn.disabled = true;
        btn.classList.add("loading");
      }}
      if (icon) icon.textContent = "⏳";
      if (label) label.textContent = "Atualizando...";

      // Reseta contagem do timer para não disparar logo em seguida
      autoRefreshRemaining = 1800;

      try {{
        if (window.location.protocol.startsWith("http")) {{
          const res = await fetch("/api/refresh", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }}
          }});

          const resData = await res.json().catch(() => ({{}}));

          if (!res.ok) {{
            throw new Error(resData.message || `Erro ${{res.status}} ao atualizar mercado.`);
          }}

          if (resData.success && resData.data) {{
            applyNewMarketData(resData.data);
            showToastNotification(resData.message || "✔ Cotações atualizadas em tempo real!", "positive");
          }} else {{
            throw new Error(resData.message || "Falha ao processar nova varredura.");
          }}
        }} else {{
          showToastNotification(
            "ℹ Modo Arquivo Local: Para habilitar a atualização em tempo real por botão, inicie pelo 'executar_screener.bat'.",
            "alert"
          );
        }}
      }} catch (err) {{
        console.error("Erro no refresh:", err);
        showToastNotification(`⚠ ${{err.message || "Falha na conexão com a Tastytrade"}}`, "negative");
      }} finally {{
        if (btn) {{
          btn.disabled = false;
          btn.classList.remove("loading");
        }}
        if (icon) icon.textContent = "🔄";
        if (label) label.textContent = "Atualizar Cotações";
      }}
    }}

    function initAutoRefreshTimer() {{
      const display = document.getElementById("countdownDisplay");
      if (refreshTimerInterval) clearInterval(refreshTimerInterval);

      refreshTimerInterval = setInterval(() => {{
        if (!autoRefreshActive) return;

        autoRefreshRemaining--;
        if (autoRefreshRemaining <= 0) {{
          autoRefreshRemaining = 1800;
          triggerMarketRefresh();
        }}

        const mins = Math.floor(autoRefreshRemaining / 60);
        const secs = autoRefreshRemaining % 60;
        const fmt = `${{String(mins).padStart(2, '0')}}:${{String(secs).padStart(2, '0')}}`;
        if (display) {{
          display.textContent = fmt;
        }}
      }}, 1000);
    }}

    function toggleAutoRefresh() {{
      autoRefreshActive = !autoRefreshActive;
      const display = document.getElementById("countdownDisplay");
      const btnToggle = document.getElementById("btnToggleAutoRefresh");

      if (autoRefreshActive) {{
        if (display) display.style.color = "#60a5fa";
        if (btnToggle) btnToggle.textContent = "⏸ Pausar";
        showToastNotification("Auto-Refresh reativado (ciclo de 30 min).", "positive");
      }} else {{
        if (display) {{
          display.textContent = "PAUSADO";
          display.style.color = "var(--alert)";
        }}
        if (btnToggle) btnToggle.textContent = "▶ Retomar";
        showToastNotification("Auto-Refresh pausado temporariamente.", "alert");
      }}
    }}

    // ============================================================
    // INICIALIZAÇÃO
    // ============================================================
    window.addEventListener("DOMContentLoaded", () => {{
      initTabs();
      initExports();
      initAutoRefreshTimer();

      // Configuração de metadados no header e banner
      if (STATE.generated_at) {{
        document.getElementById("bannerTimestamp").textContent = `Coleta: ${{STATE.generated_at.replace('T', ' ').substring(0, 19)}} UTC`;
      }}
      // Sinalização granular de proveniência de dados por símbolo (Achado B — Auditoria Técnica)
      const srcMap = STATE.data_source_by_symbol || {{}};
      const liveSymbols = Object.entries(srcMap).filter(([_, v]) => v === \"LIVE\").map(([k]) => k);
      const fixtureSymbols = Object.entries(srcMap).filter(([_, v]) => v === \"FIXTURE\").map(([k]) => k);
      const unavailSymbols = Object.entries(srcMap).filter(([_, v]) => v === \"INDISPONIVEL\").map(([k]) => k);
      const skippedList = STATE.skipped_symbols || [];
      const totalConfigured = STATE.total_configured_assets || (STATE.configured_universe ? STATE.configured_universe.length : (STATE.universe ? STATE.universe.length : 0));
      const totalScreened = STATE.total_screened_assets || (STATE.universe ? STATE.universe.length : 0);
      const isPartial = STATE.is_partial_universe || (totalConfigured > totalScreened);
      const allLive = STATE.is_live_data === true && !isPartial;
      const anyLive = STATE.any_live_data === true || liveSymbols.length > 0;

      const auditBanner = document.getElementById(\"auditBanner\");
      const bannerBadge = document.getElementById(\"bannerBadge\");
      const bannerText = document.getElementById(\"bannerText\");

      if (allLive) {{
        auditBanner.classList.add(\"live\");
        bannerBadge.textContent = \"AO VIVO 100%\";
        bannerBadge.className = \"banner-badge live\";
        bannerText.innerHTML = `<strong>Conexão Ativa:</strong> Todos os <strong>${{totalScreened}}</strong> ativos configurados foram coletados em tempo real via API oficial da Tastytrade (OAuth2 + DXLink).`;
      }} else if (anyLive) {{
        auditBanner.classList.add(\"live\");
        bannerBadge.textContent = isPartial ? \"AO VIVO PARCIAL\" : \"MISTO\";
        bannerBadge.className = \"banner-badge partial\";
        let msg = `<strong>Execução Mista / Parcial:</strong> <strong>${{liveSymbols.length}}</strong> ativo(s) ao vivo (${{liveSymbols.join(\", \")}})`;
        if (fixtureSymbols.length > 0) {{
          msg += `, <strong>${{fixtureSymbols.length}}</strong> em fixture auditada (${{fixtureSymbols.join(\", \")}})`;
        }}
        if (isPartial) {{
          msg += `. <span style=\"color:#f87171; font-weight:700;\">⚠️ ${{totalConfigured - totalScreened}} ativos configurados descartados sem dados de mercado</span>.`;
        }}
        bannerText.innerHTML = msg;
      }} else {{
        // Modo 100% fixture
        bannerBadge.textContent = isPartial ? \"FIXTURE PARCIAL\" : \"FIXTURE (TESTE)\";
        bannerBadge.className = \"banner-badge \" + (isPartial ? \"alert\" : \"badge-nd\");
        let msg = `⚠️ <strong>MODO FIXTURE DE TESTE:</strong> Dados extraídos de arquivos locais auditados (21/09/2026). Nenhuma decisão financeira deve ser tomada sem conexão ao vivo ativa.`;
        if (isPartial) {{
          msg += ` <br/><span style=\"color:#fca5a5; font-weight:600;\">Apenas <strong>${{totalScreened}} de ${{totalConfigured}}</strong> ativos do config.yaml analisados (${{totalConfigured - totalScreened}} descartados por falta de dados).</span>`;
        }}
        bannerText.innerHTML = msg;
      }}

      // Renderiza tags individuais de fonte e status de todos os símbolos
      if (Object.keys(srcMap).length > 0) {{
        let tagsHtml = '<div class=\"data-source-tags\">';
        for (const [sym, src] of Object.entries(srcMap)) {{
          let cls = \"fixture\";
          let icon = \"🟡\";
          let label = sym;
          if (src === \"LIVE\") {{
            cls = \"live\";
            icon = \"🟢\";
          }} else if (src === \"INDISPONIVEL\") {{
            cls = \"indisponivel\";
            icon = \"🔴\";
            label = `${{sym}} (SEM DADOS)`;
          }}
          tagsHtml += `<span class=\"data-source-tag ${{cls}}\" title=\"Origem: ${{src}}\">${{icon}} ${{label}}</span>`;
        }}
        tagsHtml += '</div>';
        bannerText.insertAdjacentHTML(\"afterend\", tagsHtml);
      }}

      // Meta contadores com transparência de cobertura do universo
      if (document.getElementById(\"metaUniverseCount\")) {{
        if (isPartial) {{
          const covPct = STATE.coverage_pct !== undefined ? STATE.coverage_pct : Math.round(totalScreened / totalConfigured * 100);
          document.getElementById(\"metaUniverseCount\").innerHTML = `${{totalScreened}} / ${{totalConfigured}} <span style=\"font-size:0.65rem; color:#f59e0b; font-weight:700;\">(${{covPct}}% - PARCIAL)</span>`;
          document.getElementById(\"metaUniverseCount\").title = `Universo parcial: ${{totalScreened}} de ${{totalConfigured}} ativos varridos. ${{totalConfigured - totalScreened}} descartados por ausência de dados.`;
        }} else {{
          document.getElementById(\"metaUniverseCount\").textContent = `${{totalScreened}} Ativos (100%)`;
        }}
      }}
      if (STATE.opportunities) {{
        document.getElementById(\"metaOppCount\").textContent = `${{STATE.opportunities.length}} Sinais`;
      }}

      // Listeners de filtro
      document.getElementById("filterStrategy").addEventListener("change", renderOpportunities);
      document.getElementById("filterStatus").addEventListener("change", renderOpportunities);

      // Função global de navegação do vídeo do manual
      window.seekManualVideo = function(seconds) {{
        const vid = document.getElementById("manualVideoPlayer");
        if (vid) {{
          vid.currentTime = seconds;
          vid.play().catch(() => {{}});
        }}
      }};

      // Render inicial
      renderOpportunities();
      initChains();
      renderTrackingTab();
    }});
  </script>

  <!-- Container de Notificações Toast Flutuantes -->
  <div id="toastContainer" class="toast-container" aria-live="polite"></div>
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
    data_dict = json.loads(data_json)
    eval_positions = data_dict.get("tracked_positions", [])
    if eval_positions:
        pos_json = json.dumps(eval_positions, ensure_ascii=False)
    else:
        pos_file = root / "op_tasty_posicoes.json"
        pos_json = pos_file.read_text(encoding="utf-8") if pos_file.exists() else "[]"
    html_content = generate_html(data_json, sample_positions_json=pos_json)

    out_file = root / "index.html"
    out_file.write_text(html_content, encoding="utf-8")
    print(f"index.html gerado com sucesso em {out_file} ({len(html_content)} bytes).")


if __name__ == "__main__":
    main()
