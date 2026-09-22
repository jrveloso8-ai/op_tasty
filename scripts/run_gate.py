"""
Gate Automatizado de Auditoria — Screener Tastytrade (8 Estratégias).
Executa em sequência estrita:
  1. Typecheck Estático (mypy)
  2. Linter de Código (ruff)
  3. Linter de Proveniência (scripts/lint_provenance.py)
  4. Suíte Completa de Testes Unitários e Discriminação (pytest)
Bloqueia o commit ou merge em caso de qualquer falha.
"""

import subprocess
import sys
import time


def run_step(step_name: str, command: list[str]) -> bool:
    print(f"\n{'='*70}")
    print(f" GATE STEP: {step_name}")
    print(f" COMMAND: {' '.join(command)}")
    print(f"{'='*70}")

    start_time = time.time()
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    duration = time.time() - start_time

    if proc.stdout:
        print(proc.stdout.strip())
    if proc.stderr:
        print(proc.stderr.strip(), file=sys.stderr)

    if proc.returncode == 0:
        print(f"\n[OK] {step_name} concluído com sucesso ({duration:.2f}s).")
        return True
    else:
        print(f"\n[FALHA] {step_name} retornou código de erro {proc.returncode} ({duration:.2f}s).")
        return False


def main() -> int:
    print("\n" + "#"*70)
    print(" INICIANDO GATE DE AUDITORIA AUTOMATIZADO — OP_TASTY SCREENER")
    print("#"*70)

    steps = [
        ("Typecheck Estático (mypy)", [sys.executable, "-m", "mypy", "src", "tests"]),
        ("Linter de Código (ruff)", [sys.executable, "-m", "ruff", "check", "src", "tests"]),
        ("Linter Estrutural de Proveniência", [sys.executable, "scripts/lint_provenance.py"]),
        ("Suíte de Testes e Discriminação (pytest)", [sys.executable, "-m", "pytest", "tests", "-v"])
    ]

    for name, cmd in steps:
        success = run_step(name, cmd)
        if not success:
            print("\n" + "!"*70)
            print(f" GATE DE AUDITORIA ABORTADO: Falha na etapa '{name}'.")
            print(" Corrija os erros acima antes de commitar ou prosseguir.")
            print("!"*70 + "\n")
            return 1

    print("\n" + "#"*70)
    print(" SUCESSO TOTAL: Todas as 4 etapas do gate de auditoria passaram!")
    print(" Cerca estrutural e integridade matemática confirmadas.")
    print("#"*70 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
