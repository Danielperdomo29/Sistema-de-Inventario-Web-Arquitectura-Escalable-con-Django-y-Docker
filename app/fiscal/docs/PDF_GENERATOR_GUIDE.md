# Generador de PDF - Guía de Uso

## Descripción

El `InvoicePDFGenerator` crea PDFs profesionales de facturas electrónicas DIAN con diseño tipo ticket térmico (80mm), optimizado para impresión en POS.

## Características

✅ Diseño profesional tipo ticket térmico  
✅ Código de barras Code128 del número de factura  
✅ Información completa de empresa y cliente  
✅ Tabla de productos con cantidades y valores  
✅ Cálculo de impuestos (IVA, INC, ICA)  
✅ Código QR para validación DIAN  
✅ CUFE completo  
✅ Información de resolución DIAN

## Uso Básico

### Generación Automática (Recomendado)

```python
from app.fiscal.services.invoice_service import InvoiceGenerationService
from app.models.sale import Sale

# Generar factura completa (XML + PDF)
sale = Sale.objects.get(id=123)
factura, xml = InvoiceGenerationService.generar_factura_electronica(sale)

# Acceder a archivos
print(f"XML: {factura.archivo_xml.url}")
print(f"PDF: {factura.archivo_pdf.url}")
```

### Generación Manual

```python
from app.fiscal.services.pdf_generator import InvoicePDFGenerator
from app.fiscal.models import FiscalConfig
from app.fiscal.core.dian.ubl_mapper import UBLMapper

# Obtener configuración
fiscal_config = FiscalConfig.objects.filter(is_active=True).first()

# Mapear datos
ubl_data = UBLMapper.map_sale_to_ubl_data(
    sale=sale,
    fiscal_config=fiscal_config,
    numero_factura="SETP001",
    cufe="abc123..."
)

# Generar PDF
pdf_gen = InvoicePDFGenerator(ubl_data, fiscal_config)
pdf_buffer = pdf_gen.generar_pdf()

# Guardar archivo
with open('factura.pdf', 'wb') as f:
    f.write(pdf_buffer.getvalue())
```

## Estructura del PDF

### 1. Encabezado

- Nombre de la empresa (bold, centrado)
- NIT con dígito de verificación
- Dirección
- Teléfono y email

### 2. Código de Barras

- Code128 del número de factura
- Escaneable para identificación rápida

### 3. Información de la Factura

- Número de factura electrónica
- Fecha y hora de emisión
- Tipo de documento

### 4. Datos del Cliente

- Nombre/Razón social
- NIT/CC
- Dirección

### 5. Forma de Pago

- Contado/Crédito
- Medio de pago

### 6. Tabla de Productos

| Art    | Cant     | Descripción     | Vr.Unit | Total    |
| ------ | -------- | --------------- | ------- | -------- |
| Código | Cantidad | Nombre producto | Precio  | Subtotal |

### 7. Totales

- Subtotal
- IVA (19%, 5%, 0%)
- **TOTAL** (bold)

### 8. Resolución DIAN

- Número de resolución
- Fecha de resolución
- Prefijo autorizado
- Rango de numeración (desde-hasta)

### 9. Código QR

- QR grande (50mm x 50mm)
- Contiene: NumFac, FecFac, NitFac, DocAdq, ValFac, CUFE
- Escaneable para validación en línea

### 10. CUFE

- Código completo SHA-384
- Dividido en líneas para legibilidad

### 11. Pie de Página

- Mensaje de agradecimiento
- Instrucciones de validación

## Personalización

### Tamaño de Página

```python
# Ticket 80mm (default)
page_width = 80 * mm
page_height = 297 * mm

# Carta (si se requiere)
from reportlab.lib.pagesizes import letter
doc = SimpleDocTemplate(buffer, pagesize=letter)
```

### Márgenes

```python
doc = SimpleDocTemplate(
    buffer,
    rightMargin=5*mm,   # Ajustar según necesidad
    leftMargin=5*mm,
    topMargin=5*mm,
    bottomMargin=5*mm
)
```

### Estilos de Texto

```python
# Agregar estilo personalizado
self.styles.add(ParagraphStyle(
    name='MiEstilo',
    fontSize=10,
    textColor=colors.blue,
    alignment=TA_CENTER
))
```

### Logo de Empresa

```python
# Agregar en _build_header()
from reportlab.platypus import Image

logo = Image('path/to/logo.png', width=40*mm, height=20*mm)
logo.hAlign = 'CENTER'
elements.append(logo)
```

## Formatos de Datos

### factura_data (dict)

```python
{
    'numero_factura': 'SETP001',
    'fecha_emision': '2024-01-15',
    'hora_emision': '14:30:00-05:00',
    'cufe': 'abc123...',
    'supplier': {
        'name': 'Mi Empresa SAS',
        'address': 'Calle 123 #45-67',
        'phone': '(601) 1234567',
        'email': 'info@empresa.com'
    },
    'customer': {
        'name': 'Cliente XYZ',
        'nit': '900123456-7',
        'address': 'Av Principal #10-20'
    },
    'payment_means': 'CONTADO',
    'items': [
        {
            'code': 'PROD001',
            'description': 'Producto de ejemplo',
            'quantity': 2,
            'price': 50000,
            'line_total': 100000
        }
    ],
    'tax_totals': {
        'iva': {
            'total': 19000,
            'breakdown': [...]
        }
    },
    'totals': {
        'subtotal': 100000,
        'total': 119000
    }
}
```

## Requisitos

```python
# requirements.txt
reportlab>=4.0.0
qrcode[pil]>=7.0.0
pillow>=10.0.0
```

## Testing

```python
python -m pytest app/fiscal/tests/test_pdf_generator.py -v
```

## Troubleshooting

### Error: "No module named 'reportlab'"

```bash
pip install reportlab qrcode[pil]
```

### PDF vacío o corrupto

- Verificar que `pdf_buffer.seek(0)` se llame antes de leer
- Verificar permisos de escritura en directorio de destino

### QR code no se genera

- Instalar: `pip install qrcode[pil] pillow`
- Verificar que los datos del QR no excedan límite

### Fuentes no encontradas

- ReportLab incluye fuentes básicas (Helvetica, Times)
- Para fuentes custom: `pdfmetrics.registerFont()`

## Mejoras Futuras

- [ ] Soporte para múltiples idiomas
- [ ] Temas/plantillas personalizables
- [ ] Generación de PDF/A para archivo
- [ ] Marca de agua opcional
- [ ] Múltiples formatos (A4, Carta, 58mm)

## Referencias

- [ReportLab Documentation](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [QRCode Library](https://pypi.org/project/qrcode/)
- [DIAN Especificaciones](https://www.dian.gov.co/facturae)
