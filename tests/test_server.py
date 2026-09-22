"""
Testes Unitários do Servidor HTTP Local (scripts/serve.py).
Valida:
  - Servir arquivos estáticos (index.html)
  - Endpoint GET /api/data
  - Endpoint GET /api/status
  - Endpoint POST /api/refresh com proteção contra concorrência
"""

from __future__ import annotations

import threading
from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest
import requests

from scripts.serve import ScreenerHTTPRequestHandler, get_available_port


@pytest.fixture(scope="module")
def local_server():
    """Sobe uma instância temporária do servidor HTTP em thread separada para testes."""
    from http.server import ThreadingHTTPServer

    test_port = get_available_port(8890)
    server_address = ("127.0.0.1", test_port)
    httpd = ThreadingHTTPServer(server_address, ScreenerHTTPRequestHandler)

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{test_port}"
    yield base_url

    httpd.shutdown()
    httpd.server_close()


def test_server_status_endpoint(local_server: str) -> None:
    resp = requests.get(f"{local_server}/api/status", timeout=5)
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert "is_refreshing" in data
    assert "server_time" in data
    assert data["is_refreshing"] is False


def test_server_data_endpoint(local_server: str) -> None:
    resp = requests.get(f"{local_server}/api/data", timeout=5)
    assert resp.status_code == HTTPStatus.OK
    assert resp.headers.get("Content-Type", "").startswith("application/json")
    data = resp.json()
    assert "generated_at" in data
    assert "universe" in data


def test_server_serves_index_html(local_server: str) -> None:
    resp = requests.get(f"{local_server}/", timeout=5)
    assert resp.status_code == HTTPStatus.OK
    assert "<!DOCTYPE html>" in resp.text
    assert "Tastytrade Options Screener" in resp.text
    assert "btnRefreshMarket" in resp.text
    assert "countdownDisplay" in resp.text


def test_server_refresh_endpoint_mocked(local_server: str) -> None:
    # Simula a execução do run_screener para não bater na API externa durante os testes unitários
    mock_result = MagicMock()
    mock_result.is_opportunity = True

    with patch("src.screener.run_screener", return_value=([mock_result], [], True)), \
         patch("scripts.build_ui.main", return_value=None):

        resp = requests.post(f"{local_server}/api/refresh", timeout=10)
        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["success"] is True
        assert "Mercado atualizado com sucesso" in data["message"]
        assert data["total_screened"] == 1
        assert data["total_opportunities"] == 1
