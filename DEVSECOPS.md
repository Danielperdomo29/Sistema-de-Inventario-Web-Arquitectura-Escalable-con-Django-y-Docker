# DevSecOps Infrastructure - Fiscal Module

## 🎯 Overview

Infraestructura completa de DevSecOps para el módulo fiscal, incluyendo análisis de código, pruebas de seguridad, y CI/CD automatizado.

---

## 🛠️ Herramientas Instaladas

### Code Quality

- **Black** - Formateador de código automático
- **isort** - Ordenador de imports
- **Pylint** - Analizador estático de código

### Security

- **Bandit** - SAST (Static Application Security Testing)
- **Safety** - SCA (Software Composition Analysis)

### Testing

- **pytest** - Framework de testing
- **pytest-django** - Plugin Django para pytest
- **coverage** - Medición de cobertura de código

---

## 🚀 Quick Start

### 1. Instalación

```bash
# Instalar todas las herramientas
pip install -r requirements.txt
```

### 2. Verificación Rápida

```bash
# Ejecutar todos los checks
python scripts/run_all_checks.py
```

### 3. Auto-fix

```bash
# Formatear código automáticamente
black app/ config/
isort app/ config/
```

---

## 📋 Comandos Disponibles

### Code Formatting

```bash
# Verificar formato
black --check app/ config/

# Aplicar formato
black app/ config/

# Verificar imports
isort --check-only app/ config/

# Ordenar imports
isort app/ config/
```

### Code Quality

```bash
# Analizar código
pylint app/fiscal/

# Análisis completo con score
pylint app/ --exit-zero
```

### Security Scanning

```bash
# Escanear vulnerabilidades en código
bandit -r app/fiscal/

# Escanear vulnerabilidades en dependencias
safety check

# Escaneo completo
bandit -r app/ -ll
```

### Testing

```bash
# Tests unitarios
pytest tests/ -m unit

# Tests de integración
pytest tests/ -m integration

# Tests de seguridad
pytest tests/ -m security

# Todos los tests
pytest tests/ -v

# Con cobertura
coverage run -m pytest tests/
coverage report
coverage html  # Genera reporte HTML en htmlcov/
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions

El pipeline se ejecuta automáticamente en:

- Push a `feature/fiscal-module` o `dev`
- Pull requests a `main` o `dev`

### Jobs del Pipeline

1. **Security Scan**

   - Bandit (SAST)
   - Safety (SCA)

2. **Code Quality**

   - Black (formato)
   - isort (imports)
   - Pylint (análisis)

3. **Unit Tests**

   - pytest con coverage
   - Mínimo 80% coverage

4. **Integration Tests**
   - Tests con MySQL real
   - Verificación de integración

### Ver Resultados

```bash
# En GitHub: Actions tab
# Artifacts descargables:
# - security-reports/
# - pylint-report.txt
# - coverage-report/
```

---

## 📊 Estándares de Calidad

### Métricas Mínimas

| Métrica         | Mínimo     | Objetivo |
| --------------- | ---------- | -------- |
| Pylint Score    | 8.0        | 9.5      |
| Code Coverage   | 80%        | 95%      |
| Security Issues | 0 critical | 0 total  |
| Test Pass Rate  | 100%       | 100%     |

### Pre-Commit Checks

Antes de cada commit, se verifican automáticamente:

- ✅ Formato de código (Black)
- ✅ Orden de imports (isort)
- ✅ Calidad de código (Pylint)
- ✅ Seguridad (Bandit)
- ✅ Tests unitarios

---

## 🔧 Configuración

### pyproject.toml

Configuración centralizada para todas las herramientas:

- Black: line-length=100
- isort: profile="black"
- pytest: markers, settings
- coverage: source, omit, fail_under

### .pylintrc

Configuración específica de Pylint:

- max-line-length=100
- Disabled checks para Django
- Design limits

---

## 🐛 Troubleshooting

### Error: "Black would reformat"

```bash
# Solución: Aplicar formato
black app/ config/
```

### Error: "isort would reorder imports"

```bash
# Solución: Ordenar imports
isort app/ config/
```

### Error: "Pylint score below 8.0"

```bash
# Ver problemas específicos
pylint app/fiscal/ --reports=y

# Ignorar check específico (usar con cuidado)
# pylint: disable=specific-check-name
```

### Error: "Coverage below 80%"

```bash
# Ver qué falta cubrir
coverage report --show-missing

# Generar reporte HTML
coverage html
# Abrir htmlcov/index.html
```

---

## 📚 Recursos

### Documentación

- [CODING_STANDARDS.md](./CODING_STANDARDS.md) - Estándares de código
- [Implementation Plan](./implementation_plan.md) - Plan de implementación

### Herramientas

- [Black](https://black.readthedocs.io/)
- [isort](https://pycqa.github.io/isort/)
- [Pylint](https://pylint.readthedocs.io/)
- [Bandit](https://bandit.readthedocs.io/)
- [pytest](https://docs.pytest.org/)

---

## ✅ Checklist de Setup

- [x] Herramientas instaladas
- [x] pyproject.toml configurado
- [x] .pylintrc configurado
- [x] GitHub Actions workflow creado
- [x] Scripts de verificación creados
- [x] Documentación completa

---

## 🎯 Próximos Pasos

1. Ejecutar verificación inicial:

   ```bash
   python scripts/run_all_checks.py
   ```

2. Formatear código existente:

   ```bash
   black app/ config/
   isort app/ config/
   ```

3. Comenzar desarrollo con TDD:
   - Escribir test primero
   - Implementar código
   - Verificar con checks
   - Commit

---

**Infraestructura DevSecOps lista para desarrollo del módulo fiscal! 🚀**
