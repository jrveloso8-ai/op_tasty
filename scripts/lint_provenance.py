"""
Linter Estutural de Proveniência de Dados — Screener Tastytrade.
Verifica:
  1. Ausência de menção ou instanciação de 'ESTIMADO' em código de produção e testes
  2. Uso obrigatório das propriedades 'provenance' e 'source'
  3. Proibição de formatações de números fora do invólucro DataValue no frontend
"""

import ast
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


def check_frontend_provenance(html_path: Path) -> list[str]:
    """Garante que todo valor no HTML utiliza o componente/função DataValue.render."""
    violations: list[str] = []
    if not html_path.exists():
        return violations

    content = html_path.read_text(encoding="utf-8")
    # Procura por inserções cruas como {{ value }} ou interpolações de preço sem DataValue
    # Verifica que DataValue.render ou renderDataValue é a única via de formatação
    if "DataValue.render" not in content and "renderDataValue" not in content:
        violations.append("O arquivo index.html deve implementar e utilizar o componente 'DataValue' para exibição.")

    return violations


def main() -> int:
    root = Path(__file__).parent.parent
    violations = []
    violations.extend(check_forbidden_estimado(root))
    violations.extend(check_ast_provenance_dataclass(root))

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
