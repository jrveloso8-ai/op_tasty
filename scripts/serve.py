"""
Servidor Local HTTP para o Screener de Opções Tastytrade.
Fornece:
  - Servidor web estático para o painel 'Financial Dark' (index.html)
  - Endpoint GET /api/data: Retorna o payload JSON auditável mais recente
  - Endpoint GET /api/status: Retorna o estado atual do motor de varredura
  - Endpoint POST /api/refresh: Dispara a coleta ao vivo na Tastytrade e atualiza o estado
  - Suporte a seleção automática de porta disponível (padrão: 8000)
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import threading
import time
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

SCREENER_JSON_PATH = ROOT_DIR / "screener_output.json"
INDEX_HTML_PATH = ROOT_DIR / "index.html"

# Estado compartilhado do servidor
_REFRESH_LOCK = threading.Lock()
_IS_REFRESHING = False
_LAST_REFRESH_TS: str = ""
_LAST_ERROR: str = ""


def get_available_port(preferred_port: int = 8000, max_attempts: int = 10) -> int:
    """Busca uma porta TCP disponível a partir da porta preferencial."""
    for port in range(preferred_port, preferred_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return preferred_port


def execute_market_refresh() -> dict[str, Any]:
    """Executa a varredura quantitativa e reconstrói o index.html."""
    global _IS_REFRESHING, _LAST_REFRESH_TS, _LAST_ERROR

    if not _REFRESH_LOCK.acquire(blocking=False):
        return {
            "success": False,
            "message": "Uma atualização de mercado já está em andamento. Aguarde a conclusão.",
            "is_refreshing": True
        }

    try:
        _IS_REFRESHING = True
        _LAST_ERROR = ""
        start_t = time.time()

        # Import tardio para economizar memória e evitar ciclos
        from scripts.build_ui import main as build_ui_main
        from src.screener import run_screener

        # 1. Executa o motor de varredura
        results, _contexts, is_live = run_screener()
        opps = [r for r in results if r.is_opportunity]

        # 2. Reconstrói o index.html com o novo payload embutido
        build_ui_main()

        duration = round(time.time() - start_t, 2)
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        _LAST_REFRESH_TS = now_iso

        # 3. Lê o payload atualizado
        data: dict[str, Any] = {}
        if SCREENER_JSON_PATH.exists():
            data = json.loads(SCREENER_JSON_PATH.read_text(encoding="utf-8"))

        return {
            "success": True,
            "message": f"Mercado atualizado com sucesso em {duration}s ({len(opps)} oportunidades).",
            "timestamp": now_iso,
            "is_live": is_live,
            "total_screened": len(results),
            "total_opportunities": len(opps),
            "data": data
        }
    except Exception as exc:  # noqa: BLE001
        _LAST_ERROR = str(exc)
        return {
            "success": False,
            "message": f"Erro durante a atualização do mercado: {_LAST_ERROR}",
            "error": _LAST_ERROR
        }
    finally:
        _IS_REFRESHING = False
        _REFRESH_LOCK.release()


class ScreenerHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Handler HTTP customizado com suporte a rotas de API REST."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT_DIR), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        # Log simplificado e limpo
        sys.stdout.write(f"[{time.strftime('%H:%M:%S')}] {self.address_string()} - {format % args}\n")

    def end_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_cors_headers()

    def do_GET(self) -> None:
        path = self.path.split("?")[0]

        if path == "/api/data":
            if not SCREENER_JSON_PATH.exists():
                self.send_response(HTTPStatus.NOT_FOUND)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_cors_headers()
                self.wfile.write(json.dumps({"error": "screener_output.json não encontrado"}).encode("utf-8"))
                return

            payload_bytes = SCREENER_JSON_PATH.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload_bytes)))
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_cors_headers()
            self.wfile.write(payload_bytes)
            return

        if path == "/api/status":
            status_payload = {
                "is_refreshing": _IS_REFRESHING,
                "last_refresh": _LAST_REFRESH_TS,
                "last_error": _LAST_ERROR,
                "server_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            body = json.dumps(status_payload).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_cors_headers()
            self.wfile.write(body)
            return

        # Rota padrão para servir arquivos estáticos (index.html, midia/, etc.)
        if path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        path = self.path.split("?")[0]

        if path == "/api/refresh":
            res = execute_market_refresh()
            status_code = HTTPStatus.OK if res.get("success") else HTTPStatus.INTERNAL_SERVER_ERROR
            if res.get("is_refreshing"):
                status_code = HTTPStatus.CONFLICT

            body = json.dumps(res).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_cors_headers()
            self.wfile.write(body)
            return

        self.send_response(HTTPStatus.NOT_FOUND)
        self.end_cors_headers()


def start_server(port: int = 8000, auto_open: bool = True) -> None:
    """Inicia o servidor HTTP local."""
    actual_port = get_available_port(port)
    server_address = ("127.0.0.1", actual_port)
    httpd = ThreadingHTTPServer(server_address, ScreenerHTTPRequestHandler)

    url = f"http://localhost:{actual_port}"
    print("======================================================================")
    print(" Servidor Tastytrade Options Screener Ativo")
    print(f" URL: {url}")
    print(" Pressione Ctrl+C para encerrar o servidor.")
    print("======================================================================")

    if auto_open:
        # Abre o navegador após um breve delay para garantir que o socket aceita conexões
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Servidor HTTP do Screener Tastytrade")
    parser.add_argument("--port", type=int, default=8000, help="Porta HTTP preferencial (padrão: 8000)")
    parser.add_argument("--no-open", action="store_true", help="Não abrir o navegador automaticamente")
    args = parser.parse_args()

    start_server(port=args.port, auto_open=not args.no_open)
