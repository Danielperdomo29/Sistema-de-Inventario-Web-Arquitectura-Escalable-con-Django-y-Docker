#!/usr/bin/env python
"""
Script para ejecutar todas las verificaciones de calidad y seguridad.
Uso: python scripts/run_all_checks.py
"""
import subprocess
import sys
from pathlib import Path


class Colors:
    """Colores para output en terminal"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Imprime un header formateado"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}{Colors.ENDC}\n")


def run_command(cmd, description, critical=True):
    """
    Ejecuta un comando y retorna el resultado
    
    Args:
        cmd: Comando a ejecutar
        description: Descripción del check
        critical: Si es True, falla el script si el comando falla
    """
    print(f"{Colors.OKBLUE}🔍 {description}...{Colors.ENDC}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"{Colors.OKGREEN}✅ {description} - PASSED{Colors.ENDC}")
        if result.stdout:
            print(result.stdout)
        return True
    else:
        if critical:
            print(f"{Colors.FAIL}❌ {description} - FAILED{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}⚠️  {description} - WARNING{Colors.ENDC}")
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        return False


def main():
    """Ejecuta todas las verificaciones"""
    print_header("🚀 RUNNING ALL QUALITY & SECURITY CHECKS")
    
    results = {}
    
    # 1. Code Formatting
    print_header("1️⃣  CODE FORMATTING")
    results['black'] = run_command(
        "black --check app/ config/",
        "Black (Code Formatter)",
        critical=False
    )
    results['isort'] = run_command(
        "isort --check-only app/ config/",
        "isort (Import Sorter)",
        critical=False
    )
    
    # 2. Code Quality
    print_header("2️⃣  CODE QUALITY")
    results['pylint'] = run_command(
        "pylint app/ --exit-zero",
        "Pylint (Code Linter)",
        critical=False
    )
    
    # 3. Security Scanning
    print_header("3️⃣  SECURITY SCANNING")
    results['bandit'] = run_command(
        "bandit -r app/ -ll",
        "Bandit (SAST - Static Application Security Testing)",
        critical=True
    )
    results['safety'] = run_command(
        "safety check",
        "Safety (SCA - Software Composition Analysis)",
        critical=False
    )
    
    # 4. Unit Tests
    print_header("4️⃣  UNIT TESTS")
    results['unit_tests'] = run_command(
        "pytest tests/ -m unit -v",
        "Unit Tests",
        critical=True
    )
    
    # 5. Integration Tests
    print_header("5️⃣  INTEGRATION TESTS")
    results['integration_tests'] = run_command(
        "pytest tests/ -m integration -v",
        "Integration Tests",
        critical=False
    )
    
    # 6. Coverage
    print_header("6️⃣  CODE COVERAGE")
    run_command(
        "coverage run -m pytest tests/ -m unit",
        "Running tests with coverage",
        critical=False
    )
    results['coverage'] = run_command(
        "coverage report --fail-under=80",
        "Coverage Report (minimum 80%)",
        critical=True
    )
    
    # Summary
    print_header("📊 SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"Total checks: {total}")
    print(f"Passed: {Colors.OKGREEN}{passed}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{total - passed}{Colors.ENDC}")
    print(f"Success rate: {passed/total*100:.1f}%\n")
    
    for check, result in results.items():
        status = f"{Colors.OKGREEN}✅ PASSED{Colors.ENDC}" if result else f"{Colors.FAIL}❌ FAILED{Colors.ENDC}"
        print(f"  {check:<20} {status}")
    
    print("\n" + "="*70)
    
    if passed == total:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✅ ALL CHECKS PASSED!{Colors.ENDC}")
        print(f"{Colors.OKGREEN}Code is ready for commit/push.{Colors.ENDC}\n")
        return 0
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}❌ SOME CHECKS FAILED{Colors.ENDC}")
        print(f"{Colors.WARNING}Please fix the issues before committing.{Colors.ENDC}\n")
        
        print("Quick fixes:")
        if not results['black']:
            print("  black app/ config/")
        if not results['isort']:
            print("  isort app/ config/")
        print()
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
