# Módulo Fiscal - Sistema de Inventario

## 📋 Descripción

Módulo fiscal completo para gestión tributaria y contable conforme a normativa DIAN colombiana. Incluye validación de NIT, perfiles fiscales, plan único de cuentas (PUC), y cálculo automático de impuestos.

## ✨ Características

### Modelos Implementados

#### 1. **NITValidator**

Validador de NIT colombiano con algoritmo módulo 11.

```python
from app.fiscal.validators import NITValidator

# Calcular dígito verificador
dv = NITValidator.calcular_dv("900123456")  # Returns: "8"

# Validar NIT completo
es_valido = NITValidator.validar("900123456", "8")  # Returns: True

# Formatear NIT
nit_formateado = NITValidator.formatear("900123456")  # Returns: "900123456-8"
```

#### 2. **PerfilFiscal**

Información tributaria de clientes y proveedores.

```python
from app.fiscal.models import PerfilFiscal

# Crear perfil fiscal
perfil = PerfilFiscal.objects.create(
    cliente=cliente,
    tipo_documento='31',  # NIT
    numero_documento='900123456',
    tipo_persona='J',  # Jurídica
    regimen='48',  # Responsable de IVA
    responsabilidades=['R-99-PN'],
    departamento='11',  # Bogotá
    municipio='11001'
)

# El DV se calcula automáticamente
print(perfil.dv)  # "8"
```

#### 3. **CuentaContable**

Plan Único de Cuentas (PUC) jerárquico de 5 niveles.

```python
from app.fiscal.models import CuentaContable

# Obtener cuenta
cuenta = CuentaContable.objects.get(codigo='1305')

# Navegar jerarquía
print(cuenta.get_ruta_jerarquica())
# ['1 - ACTIVO', '13 - DEUDORES', '1305 - CLIENTES']

# Obtener subcuentas
subcuentas = cuenta.get_subcuentas()
```

#### 4. **Impuesto**

Configuración y cálculo automático de impuestos.

```python
from app.fiscal.models import Impuesto
from decimal import Decimal

# Obtener impuesto
iva = Impuesto.objects.get(codigo='IVA19')

# Calcular impuesto
valor_impuesto = iva.calcular(Decimal('1000.00'))
# Returns: Decimal('190.00')

# Verificar aplicabilidad
if iva.es_aplicable('venta'):
    # Aplicar impuesto
    pass
```

## 🚀 Instalación

### 1. Configurar App

La app ya está registrada en `INSTALLED_APPS`:

```python
# config/settings/base.py
INSTALLED_APPS = [
    ...
    'app.fiscal.apps.FiscalConfig',
]
```

### 2. Aplicar Migraciones

```bash
python manage.py migrate fiscal
```

### 3. Cargar Datos Iniciales

```bash
# Cargar PUC básico (21 cuentas)
python manage.py load_puc

# Cargar impuestos básicos (6 impuestos)
python manage.py load_impuestos
```

## 📊 Datos Iniciales

### Plan Único de Cuentas (PUC)

21 cuentas principales:

- **Clase 1**: Activo (Disponible, Deudores)
- **Clase 2**: Pasivo (Cuentas por pagar, Impuestos)
- **Clase 3**: Patrimonio
- **Clase 4**: Ingresos
- **Clase 5**: Gastos
- **Clase 6**: Costos

### Impuestos Configurados

- **IVA 19%**: Tarifa general
- **IVA 5%**: Tarifa reducida
- **IVA 0%**: Excluidos
- **Retención 2.5%**: Servicios
- **Retención 4%**: Compras
- **ReteIVA 15%**: Régimen simplificado

## 🔒 Seguridad

### Características Implementadas

1. **Audit Trail Completo**

   - Trazabilidad de todas las operaciones
   - Retención 7 años (DIAN)
   - Registro automático vía signals

2. **Encriptación de Datos**

   - Campos sensibles encriptados (AES-128)
   - Datos protegidos en reposo

3. **Control de Acceso**
   - Permisos granulares
   - RBAC con 3 grupos predefinidos
   - Decoradores de seguridad

### Configurar Permisos

```bash
# Crear grupos y permisos
python manage.py setup_fiscal_permissions

# Asignar usuario a grupo
from django.contrib.auth.models import Group
contador_group = Group.objects.get(name='Contador')
user.groups.add(contador_group)
```

### Grupos Disponibles

- **Contador**: Acceso completo
- **Auditor Fiscal**: Solo lectura + auditoría
- **Operador Fiscal**: Lectura + escritura

## 🧪 Tests

### Ejecutar Tests

```bash
# Todos los tests
python -m pytest tests/fiscal/unit/ -v

# Tests específicos
python -m pytest tests/fiscal/unit/test_nit_validator.py -v
python -m pytest tests/fiscal/unit/test_perfil_fiscal.py -v
python -m pytest tests/fiscal/unit/test_cuenta_contable.py -v
python -m pytest tests/fiscal/unit/test_impuesto.py -v
```

### Cobertura

```bash
# Generar reporte de cobertura
python -m coverage run -m pytest tests/fiscal/unit/
python -m coverage report --include="app/fiscal/*"
```

**Resultado**: 72/72 tests (100%), Cobertura: 86%

## 📖 API Reference

### Decoradores de Seguridad

```python
from app.fiscal.decorators import (
    require_fiscal_permission,
    audit_fiscal_action,
    rate_limit_fiscal
)

# Requiere permiso específico
@require_fiscal_permission('change_fiscal_data')
def update_perfil(request, pk):
    ...

# Audita automáticamente
@audit_fiscal_action('VIEW', 'PerfilFiscal')
def view_perfil(request, pk):
    ...

# Rate limiting
@rate_limit_fiscal(max_requests=50, window_seconds=60)
def export_data(request):
    ...
```

### Audit Log

```python
from app.fiscal.models import FiscalAuditLog

# Ver historial de un objeto
logs = FiscalAuditLog.get_object_history('PerfilFiscal', '123')

# Ver actividad de un usuario
logs = FiscalAuditLog.get_user_activity(user, start_date, end_date)

# Crear log manual
FiscalAuditLog.log_action(
    action='EXPORT',
    model_name='PerfilFiscal',
    object_id='123',
    user=request.user,
    request=request
)
```

## 🔧 Configuración

### Variables de Entorno

```bash
# .env
FISCAL_ENCRYPTION_KEY=your-fernet-key-here
```

### Generar Clave de Encriptación

```python
from app.fiscal.encryption import FiscalEncryption
key = FiscalEncryption.generate_key()
print(key)  # Copiar a .env
```

## 📈 Roadmap

### Fase A (Completada) ✅

- [x] NITValidator
- [x] PerfilFiscal
- [x] CuentaContable
- [x] Impuesto
- [x] Seguridad (Audit + Encryption + Access Control)
- [x] Tests (72/72 - 100%)
- [x] Migraciones
- [x] Datos iniciales

### Fase B (Próxima)

- [ ] AsientoContable (doble partida)
- [ ] MovimientoContable
- [ ] Auto-contabilización desde facturas
- [ ] Reportes (Balance, Libro Diario)

## 🤝 Contribuir

### Estándares de Código

- TDD (Test-Driven Development)
- Cobertura mínima: 80%
- Cumplimiento DIAN
- Seguridad OWASP Top 10

### Ejecutar Checks

```bash
# Pre-commit checks
python scripts/pre_commit_check.py

# Todos los checks
python scripts/run_all_checks.py
```

## 📝 Licencia

Ver archivo LICENSE en la raíz del proyecto.

## 📞 Soporte

Para reportar bugs o solicitar features, crear un issue en GitHub.

---

**Versión**: 1.0.0  
**Última actualización**: Diciembre 2025  
**Estado**: Producción Ready ✅
