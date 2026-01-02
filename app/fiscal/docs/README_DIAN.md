# Sistema de Facturación Electrónica DIAN

Sistema completo de facturación electrónica para Colombia siguiendo los estándares DIAN UBL 2.1.

## 📋 Índice

- [Arquitectura](#arquitectura)
- [Componentes Principales](#componentes-principales)
- [Configuración Inicial](#configuración-inicial)
- [Flujo de Facturación](#flujo-de-facturación)
- [Certificados](#certificados)
- [Migración a Producción](#migración-a-producción)
- [Troubleshooting](#troubleshooting)

## 🏗 Arquitectura

El sistema está diseñado con una arquitectura modular que separa responsabilidades:

```
app/fiscal/
├── core/dian/              # Componentes centrales DIAN
│   ├── dian_config.py      # Configuración de endpoints y códigos
│   ├── formatters.py       # Formateadores de datos DIAN
│   ├── crypto_manager.py   # Gestión de CUFE y certificados
│   ├── ubl_generator.py    # Generador XML UBL 2.1
│   └── ubl_mapper.py       # Mapeo Sale → UBL
├── models/
│   ├── fiscal_config.py    # Configuración fiscal
│   ├── rango_numeracion.py # Gestión de numeración
│   └── factura_electronica.py
├── services/
│   ├── numeracion_service.py  # Asignación de consecutivos
│   └── invoice_service.py     # Orquestador principal
└── scripts/
    └── generate_test_certificate.py  # Certificados de desarrollo
```

## 🔧 Componentes Principales

### 1. DIANConfig (core/dian/dian_config.py)

Configuración centralizada de:
- Endpoints SOAP por ambiente (Habilitación/Producción)
- Namespaces UBL 2.1
- Códigos de impuestos y documentos DIAN
- Tarifas válidas de IVA

### 2. Rango de Numeración (models/rango_numeracion.py)

Gestiona rangos autorizados por DIAN:
- Control de consecutivos con `select_for_update()` (thread-safe)
- Validación de rangos y vigencias
- Alertas automáticas de agotamiento
- Estados: activo, agotado, vencido, inactivo

### 3. CUFE Generator (core/dian/crypto_manager.py)

Implementación exacta del algoritmo SHA-384 según Anexo Técnico 1.8:

```
Concatenación:
NumFac + FecFac + HorFac + ValFac + 
CodImp1 + ValImp1 + CodImp2 + ValImp2 + CodImp3 + ValImp3 + 
ValPag + NitOFE + TipAdq + NumAdq + ClTec + TipoAmb
```

### 4. UBL Generator (core/dian/ubl_generator.py)

Generador de XML UBL 2.1 completo con:
- Todos los namespaces requeridos
- Estructura AccountingSupplierParty/CustomerParty
- TaxTotal con desglose por impuesto
- LegalMonetaryTotal con todos los totales
- InvoiceLine para cada ítem
- UBLExtensions para firma digital

### 5. Invoice Service (services/invoice_service.py)

Orquestador que integra todo el flujo:
1. Validación de datos
2. Asignación de número
3. Mapeo Sale → UBL
4. Cálculo de CUFE
5. Generación de XML
6. Firma digital (placeholder)
7. Persistencia

## ⚙ Configuración Inicial

### 1. Generar Certificado de Desarrollo

```bash
python scripts/generate_test_certificate.py
```

Esto crea un certificado autofirmado en `media/fiscal/certs/test_certificate.p12` con contraseña `test_password_123`.

### 2. Crear Configuración Fiscal

En el admin de Django (`/admin/`):

1. Ir a **Configuraciones Fiscales → Agregar**
2. Completar datos del emisor:
   - NIT Emisor
   - Dígito de Verificación
   - Razón Social
3. Configurar software:
   - Software ID (proporcionado por DIAN)
   - PIN Software
4. Seleccionar ambiente: **Habilitación (Pruebas)**
5. Cargar certificado `.p12` y contraseña
6. Marcar como **Activo**

### 3. Crear Rango de Numeración

1. Ir a **Rangos de Numeración → Agregar**
2. Asociar a la Configuración Fiscal creada
3. Completar datos de resolución DIAN:
   - Número de resolución
   - Fechas de vigencia
   - Prefijo (ej: `SETP`, `FE`, etc.)
   - Rango autorizado (desde - hasta)
   - Clave técnica
4. Marcar como **Rango por Defecto**
5. Guardar

## 🔄 Flujo de Facturación

### Uso Básico

```python
from app.fiscal.services.invoice_service import InvoiceGenerationService
from app.models.sale import Sale

# Obtener venta
sale = Sale.objects.get(id=123)

# Generar factura electrónica
factura, xml_string = InvoiceGenerationService.generar_factura_electronica(sale)

print(f"Factura: {factura.numero_factura}")
print(f"CUFE: {factura.cufe}")
print(f"XML: {factura.archivo_xml.url}")
```

### Flujo Completo

```python
# 1. Validar disponibilidad de numeración
from app.fiscal.services.numeracion_service import NumeracionService

disponibilidad = NumeracionService.validar_disponibilidad(fiscal_config_id=1)
if not disponibilidad['disponible']:
    raise Exception(disponibilidad['mensaje'])

# 2. Generar factura
factura, xml = InvoiceGenerationService.generar_factura_electronica(sale)

# 3. Verificar estado
estado = InvoiceGenerationService.obtener_estado_factura(sale.id)
print(estado)
# {
#     'numero_factura': 'SETP990001',
#     'cufe': '5a1b2c3d...',
#     'estado': 'generada',
#     'fecha_generacion': datetime(...),
#     'archivo_xml': '/media/fiscal/xml/...',
#     'archivo_pdf': None
# }
```

## 🔐 Certificados

### Certificados Autofirmados (Desarrollo)

**IMPORTANTE**: Los certificados autofirmados son SOLO para desarrollo local. NO usar en producción.

Características:
- Generados con RSA 2048-bit
- Formato PKCS#12 (.p12)
- Validez de 365 días
- Password protegido

### Certificado Oficial DIAN (Producción)

Cuando obtengas el certificado .p12 oficial de la DIAN:

1. En Configuración Fiscal, cargar el archivo .p12 oficial
2. Cambiar ambiente a **Producción**
3. Configurar Test Set ID si aplica
4. El código funciona sin cambios

## 🚀 Migración a Producción

### Checklist

- [ ] Obtener certificado `.p12` oficial de la DIAN
- [ ] Registrar software ante DIAN
- [ ] Obtener Software ID y PIN
- [ ] Solicitar rango de numeración productivo
- [ ] Actualizar FiscalConfig:
  - [ ] Cargar certificado producción
  - [ ] Cambiar ambiente a "Producción" (1)
  - [ ] Actualizar Software ID y PIN
- [ ] Crear RangoNumeracion productivo
- [ ] Realizar pruebas en ambiente de habilitación
- [ ] Generar factura de prueba
- [ ] Validar CUFE contra calculadora DIAN

### Endpoints Producción

Los endpoints se configuran automáticamente según el ambiente en `FiscalConfig`:

- **Webservice**: `https://vpfe.dian.gov.co/WcfDianCustomerServices.svc`
- **Validación**: `https://catalogo-vpfe.dian.gov.co/User/SearchDocument`

## 🐛 Troubleshooting

### Error: "No hay rangos activos disponibles"

**Causa**: No hay un `RangoNumeracion` activo configurado.

**Solución**:
1. Verificar que existe un rango marcado como "Rango por Defecto"
2. Verificar que el rango está en estado "activo"
3. Verificar que la fecha actual está dentro de la vigencia

### Error: "CUFE generado tiene formato inválido"

**Causa**: El CUFE no tiene 96 caracteres hexadecimales.

**Solución**:
1. Verificar que todos los campos requeridos están presentes
2. Revisar el formateo de decimales (deben tener 2 decimales con punto)
3. Verificar que la clave técnica sea correcta

### Error: "El consecutivo ha excedido el rango autorizado"

**Causa**: Se agotaron los números del rango.

**Solución**:
1. Solicitar nuevo rango a la DIAN
2. Crear nuevo `RangoNumeracion` con el rango autorizado
3. Marcar el nuevo como "Rango por Defecto"

### Error al cargar certificado

**Causa**: Contraseña incorrecta o archivo corrupto.

**Solución**:
1. Verificar que el archivo .p12 no esté dañado
2. Verificar la contraseña
3. Regenerar certificado si es de desarrollo

## 📊 Estadísticas de Numeración

```python
from app.fiscal.services.numeracion_service import NumeracionService

# Obtener estadísticas generales
stats = NumeracionService.estadisticas_uso()

print(f"Rangos activos: {stats['rangos_activos']}")
print(f"Números disponibles: {stats['numeros_disponibles_total']}")
print(f"Rangos críticos: {stats['rangos_criticos']}")

# Ver detalle por rango
for rango in stats['rangos']:
    print(f"Prefijo: {rango['prefijo']}")
    print(f"Disponibles: {rango['disponibles']}")
    print(f"Uso: {rango['porcentaje_uso']:.1f}%")
```

## 🔍 Validación de CUFE

Para validar que el CUFE se está calculando correctamente:

1. Generar una factura
2. Extraer todos los datos usados en el cálculo
3. Usar la calculadora oficial DIAN
4. Comparar resultados

Campos clave para validación:
- Número de factura (con prefijo)
- Fecha (YYYY-MM-DD)
- Hora (HH:MM:SS-05:00)
- Valores con 2 decimales exactos
- Clave técnica correcta

## 📚 Referencias

- [DIAN - Facturación Electrónica](https://www.dian.gov.co/facturae)
- [Anexo Técnico 1.8](https://www.dian.gov.co/docs/anexo_tecnico_1_8.pdf)
- [UBL 2.1 Specification](http://docs.oasis-open.org/ubl/UBL-2.1.html)
- [XAdES Digital Signatures](http://uri.etsi.org/01903/v1.3.2/ts_101903v010302p.pdf)

## ⚠️ Notas Importantes

1. **Seguridad**: Nunca commitear certificados ni contraseñas en Git
2. **Concurrencia**: El servicio de numeración usa `select_for_update()` para evitar duplicados
3. **Alertas**: Se envían emails automáticos cuando un rango está por agotarse
4. **Retención**: Los XMLs se guardan automáticamente para cumplir normativa
5. **Zona Horaria**: Todas las fechas usan zona horaria de Colombia (-05:00)

## 📝 Próximos Pasos

- [ ] Implementar firma digital XAdES-BES
- [ ] Integración con servicio SOAP DIAN
- [ ] Generación de PDF representación gráfica
- [ ] Manejo de eventos DIAN (acuse de recibo, aceptación, rechazo)
- [ ] Notas crédito y débito
- [ ] Validación contra XSD DIAN
