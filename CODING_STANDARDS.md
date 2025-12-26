# Estándares de Código - Módulo Fiscal

## 🎯 Objetivo

Mantener código limpio, seguro y mantenible siguiendo principios SOLID y mejores prácticas de la industria.

---

## 📏 Estándares Generales

### Formato de Código

- **Longitud de línea:** Máximo 100 caracteres
- **Indentación:** 4 espacios (no tabs)
- **Encoding:** UTF-8
- **Line endings:** LF (Unix style)

### Nomenclatura

#### Variables y Funciones

```python
# ✅ BIEN - snake_case
calcular_impuesto()
total_ventas = 0
nit_cliente = "900123456"

# ❌ MAL - camelCase o PascalCase
calcularImpuesto()
TotalVentas = 0
```

#### Clases

```python
# ✅ BIEN - PascalCase
class PerfilFiscal:
    pass

class NITValidator:
    pass

# ❌ MAL
class perfil_fiscal:
    pass
```

#### Constantes

```python
# ✅ BIEN - UPPER_SNAKE_CASE
IVA_PORCENTAJE = Decimal('19.00')
MAX_INTENTOS_LOGIN = 3

# ❌ MAL
iva_porcentaje = Decimal('19.00')
```

---

## 🏗️ Arquitectura

### Estructura de Directorios

```
app/
├── fiscal/                    # Módulo fiscal
│   ├── __init__.py
│   ├── models/               # Modelos de datos
│   │   ├── __init__.py
│   │   ├── perfil_fiscal.py
│   │   ├── cuenta_contable.py
│   │   └── impuesto.py
│   ├── services/             # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── nit_validator.py
│   │   └── asiento_service.py
│   ├── utils/                # Utilidades
│   │   ├── __init__.py
│   │   └── calculators.py
│   ├── validators/           # Validadores
│   │   ├── __init__.py
│   │   └── fiscal_validators.py
│   └── security/             # Controles de seguridad
│       ├── __init__.py
│       └── fiscal_security.py
└── tests/
    └── fiscal/
        ├── unit/
        ├── integration/
        └── security/
```

### Separación de Responsabilidades

```python
# ✅ BIEN - Responsabilidad única

# models/perfil_fiscal.py
class PerfilFiscal(models.Model):
    """Solo define estructura de datos"""
    nit = models.CharField(max_length=20)
    # ...

# services/nit_validator.py
class NITValidator:
    """Solo valida NITs"""
    @staticmethod
    def calcular_dv(nit: str) -> str:
        # ...

# services/perfil_service.py
class PerfilFiscalService:
    """Lógica de negocio de perfiles"""
    def crear_perfil(self, data: dict) -> PerfilFiscal:
        # Valida, crea y retorna
        pass
```

---

## 📝 Documentación

### Docstrings (Google Style)

```python
def calcular_impuesto(base: Decimal, porcentaje: Decimal) -> Decimal:
    """
    Calcula el valor del impuesto sobre una base imponible.

    Args:
        base: Base imponible en pesos colombianos.
        porcentaje: Porcentaje del impuesto (ej: 19.00 para IVA).

    Returns:
        Valor del impuesto redondeado a 2 decimales.

    Raises:
        ValueError: Si base o porcentaje son negativos.

    Examples:
        >>> calcular_impuesto(Decimal('100'), Decimal('19'))
        Decimal('19.00')

    Note:
        Redondeo según Resolución DIAN 000042/2020.
    """
    if base < 0 or porcentaje < 0:
        raise ValueError("Base y porcentaje deben ser positivos")

    return (base * porcentaje / 100).quantize(Decimal('0.01'))
```

### Comentarios

```python
# ✅ BIEN - Explica el "por qué", no el "qué"
# Usamos Decimal para evitar errores de redondeo en cálculos fiscales
total = Decimal('0.00')

# ❌ MAL - Comentario obvio
# Suma 1 a contador
contador += 1
```

---

## 🧪 Testing

### Convenciones de Nombres

```python
# tests/fiscal/unit/test_nit_validator.py

class TestNITValidator:
    """Tests para NITValidator"""

    def test_calcular_dv_nit_valido(self):
        """Test: Calcula DV correctamente para NIT válido"""
        # Given
        nit = "900123456"

        # When
        dv = NITValidator.calcular_dv(nit)

        # Then
        assert dv == "3"

    def test_calcular_dv_nit_invalido_raise_error(self):
        """Test: Rechaza NIT inválido con error"""
        with pytest.raises(ValidationError):
            NITValidator.calcular_dv("ABC")
```

### Cobertura Mínima

- **Unit tests:** 80% de cobertura mínima
- **Critical paths:** 100% de cobertura
- **Security functions:** 100% de cobertura

---

## 🔒 Seguridad

### Validación de Inputs

```python
# ✅ BIEN - Valida todo input externo
def crear_perfil(nit: str, nombre: str):
    # Validar formato
    if not re.match(r'^\d{9,10}$', nit):
        raise ValidationError("NIT inválido")

    # Sanitizar
    nombre = nombre.strip()[:200]

    # Procesar
    # ...

# ❌ MAL - Confía en el input
def crear_perfil(nit, nombre):
    perfil = PerfilFiscal(nit=nit, nombre=nombre)
    perfil.save()
```

### Manejo de Datos Sensibles

```python
# ✅ BIEN - Enmascara en logs
logger.info(f"Procesando NIT: {mask_nit(nit)}")  # "900***56"

# ❌ MAL - Expone datos sensibles
logger.info(f"Procesando NIT: {nit}")  # "900123456"
```

---

## 🚀 Performance

### Queries Eficientes

```python
# ✅ BIEN - select_related para ForeignKey
perfiles = PerfilFiscal.objects.select_related('cliente').all()

# ✅ BIEN - prefetch_related para ManyToMany
asientos = AsientoContable.objects.prefetch_related('detalles').all()

# ❌ MAL - N+1 queries
for perfil in PerfilFiscal.objects.all():
    print(perfil.cliente.nombre)  # Query por cada perfil
```

### Uso de Cache

```python
from django.core.cache import cache

# ✅ BIEN - Cachea datos estáticos
def get_puc():
    puc = cache.get('puc_completo')
    if not puc:
        puc = CuentaContable.objects.all()
        cache.set('puc_completo', puc, 3600)  # 1 hora
    return puc
```

---

## ✅ Checklist Pre-Commit

Antes de hacer commit, verifica:

- [ ] Código formateado con Black
- [ ] Imports ordenados con isort
- [ ] Sin errores de Pylint (score > 8.0)
- [ ] Sin vulnerabilidades de Bandit
- [ ] Tests unitarios pasan
- [ ] Coverage > 80%
- [ ] Docstrings completos
- [ ] Sin TODOs o FIXMEs
- [ ] Sin print() statements (usar logging)
- [ ] Sin credenciales hardcodeadas

---

## 🛠️ Herramientas

### Auto-fix

```bash
# Formatear código
black app/ config/

# Ordenar imports
isort app/ config/

# Ver problemas
pylint app/fiscal/

# Escanear seguridad
bandit -r app/fiscal/
```

### Verificación Completa

```bash
# Ejecutar todos los checks
python scripts/run_all_checks.py
```

---

## 📚 Referencias

- [PEP 8](https://peps.python.org/pep-0008/) - Style Guide for Python Code
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Django Coding Style](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/)
- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
