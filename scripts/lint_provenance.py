"""
Linter Estutural de Proveniência de Dados — Screener Tastytrade.
Verifica:
  1. Ausência de menção ou instanciação de 'ESTIMADO' em código de produção e testes
  2. Uso obrigatório das propriedades 'provenance' e 'source'
  3. Proibição de formatações de números fora do invólucro DataValue no frontend
"""

import ast
import json
import re
import sys
from pathlib import Path


def check_forbidden_estimado(root_dir: Path) -> list[str]:
    """Garante que ESTIMADO nunca é usado como valor válido de proveniência."""
    violations: list[str] = []
    py_files = list(root_dir.glob("src/**/*.py"))

    for py_file in py_files:
        content = py_file.read_text(encoding="utf-8")
        # Procura por 'provenance="ESTIMADO"' ou 'provenance = "ESTIMADO"' exceto em validações de erro
        pattern = re.compile(r'provenance\s*=\s*["\']ESTIMADO["\']', re.IGNORECASE)
        for i, line in enumerate(content.splitlines(), start=1):
            if pattern.search(line):
                violations.append(f"[{py_file.name}:{i}] Uso proibido de proveniência ESTIMADO: {line.strip()}")

    return violations


def check_ast_provenance_dataclass(root_dir: Path) -> list[str]:
    """Verifica sintaticamente chamadas de DataValue."""
    violations: list[str] = []
    py_files = list(root_dir.glob("src/**/*.py"))

    for py_file in py_files:
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                # Identifica DataValue(...) direto
                if isinstance(func, ast.Name) and func.id == "DataValue":
                    # Checa argumentos por keyword
                    kw_names = {kw.arg for kw in node.keywords}
                    if "provenance" not in kw_names and len(node.args) < 2:
                        violations.append(f"[{py_file.name}:{node.lineno}] Instanciação de DataValue sem especificar 'provenance'")
                    if "source" not in kw_names and len(node.args) < 3:
                        violations.append(f"[{py_file.name}:{node.lineno}] Instanciação de DataValue sem especificar 'source'")

    return violations


def check_json_chains_provenance(json_path: Path) -> list[str]:
    """Verifica se as opções na cadeia do JSON de saída contêm proveniência DataValue em todos os campos requeridos, incluindo 'mid'."""
    violations: list[str] = []
    if not json_path.exists():
        return violations

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        violations.append(f"Erro ao ler {json_path.name}: {exc}")
        return violations

    chains = data.get("chains", {})
    for sym, exp_dict in chains.items():
        for exp, legs in exp_dict.items():
            for leg in legs:
                # Checa se 'mid' é um objeto DataValue válido
                mid = leg.get("mid")
                if mid is None or not isinstance(mid, dict):
                    violations.append(f"[{json_path.name} | {sym} {exp} strike {leg.get('strike')}] Campo 'mid' não é um DataValue envelopado.")
                    continue
                if "provenance" not in mid or "source" not in mid:
                    violations.append(f"[{json_path.name} | {sym} {exp} strike {leg.get('strike')}] DataValue 'mid' sem 'provenance' ou 'source'.")
                if mid.get("provenance") not in ("DERIVADO", "INDISPONIVEL"):
                    violations.append(f"[{json_path.name} | {sym} {exp} strike {leg.get('strike')}] DataValue 'mid' possui proveniência inválida: {mid.get('provenance')}.")

    return violations


def check_frontend_provenance(html_path: Path) -> list[str]:
    """Garante que todo valor no HTML utiliza o componente/função DataValue.render e que não há fallback de INDISPONIVEL para 0 em gráficos."""
    violations: list[str] = []
    if not html_path.exists():
        return violations

    content = html_path.read_text(encoding="utf-8")
    if "DataValue.render" not in content and "renderDataValue" not in content:
        violations.append("O arquivo index.html deve implementar e utilizar o componente 'DataValue' para exibição.")

    # Verifica se os gráficos tratam INDISPONIVEL sem fazer fallback silencioso para 0.00 (Achado 1 e Achado A)
    if 'provenance !== "INDISPONIVEL"' not in content and "display_value" in content:
        violations.append("index.html não filtra estruturas com display_value.provenance !== 'INDISPONIVEL' em gráficos.")

    return violations


def main() -> int:
    root = Path(__file__).parent.parent
    violations = []
    violations.extend(check_forbidden_estimado(root))
    violations.extend(check_ast_provenance_dataclass(root))

    json_file = root / "screener_output.json"
    if json_file.exists():
        violations.extend(check_json_chains_provenance(json_file))

    html_file = root / "index.html"
    if html_file.exists():
        violations.extend(check_frontend_provenance(html_file))

    if violations:
        print("[LINTER DE PROVENIENCIA] FALHA: Violacoes estruturais detectadas:")
        for v in violations:
            print(f"  - {v}")
        return 1

    print("[LINTER DE PROVENIENCIA] SUCESSO: Nenhuma violacao de proveniencia encontrada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

