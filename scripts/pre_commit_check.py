#!/usr/bin/env python
"""
Pre-commit hook para verificar calidad y seguridad del código.
Ejecuta automáticamente antes de cada commit.
"""
import subprocess
import sys


def run_command(cmd, description):
    """Ejecuta un comando y retorna el resultado"""
    print(f"\n{'='*70}")
    print(f"🔍 {description}")
    print(f"{'='*70}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)  # nosec B602

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    return result.returncode == 0


def main():
    """Ejecuta todas las verificaciones pre-commit"""
    print("\n" + "🚀 PRE-COMMIT CHECKS".center(70))

    checks = [
        ("black --check app/ config/", "Verificando formato de código (Black)"),
        ("isort --check-only app/ config/", "Verificando orden de imports (isort)"),
        ("pylint app/fiscal/ --fail-under=8.0", "Analizando código (Pylint)"),
        ("bandit -r app/fiscal/ -ll", "Escaneando seguridad (Bandit)"),
        ("pytest tests/fiscal/ -m unit --tb=short -q", "Ejecutando tests unitarios"),
    ]

    failed_checks = []

    for cmd, description in checks:
        if not run_command(cmd, description):
            failed_checks.append(description)

    print("\n" + "=" * 70)

    if failed_checks:
        print("❌ PRE-COMMIT FAILED")
        print("\nChecks que fallaron:")
        for check in failed_checks:
            print(f"  - {check}")
        print("\nPor favor, corrige los errores antes de hacer commit.")
        print("\nComandos para auto-fix:")
        print("  black app/ config/")
        print("  isort app/ config/")
        return 1
    else:
        print("✅ ALL CHECKS PASSED!")
        print("Commit permitido.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
