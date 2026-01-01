
import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta
import random

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.purchase import Purchase, PurchaseDetail
from app.fiscal.services.retention_service import WithholdingTaxService

def run_test():
    print("=== INICIANDO PRUEBA DE RETENCIÓN EN LA FUENTE (FORMULARIO 350) ===")
    
    # 1. Configurar Datos de Prueba
    User = get_user_model()
    user, _ = User.objects.get_or_create(username='test_admin', email='test@admin.com')
    
    # Definir fechas (Mes actual)
    now = timezone.now()
    year = now.year
    month = now.month
    start_date = datetime(year, month, 1)
    
    print(f"Generando datos para el período: {month}/{year}")
    
    # 2. Crear Proveedores (Declarante y No Declarante)
    print("\n[1/5] Creando Proveedores...")
    
    supplier_declarant, _ = Supplier.objects.get_or_create(
        ruc='900111222', 
        defaults={
            'nombre': 'Proveedor Declarante SAS',
            'email': 'declarante@test.com',
            'telefono': '3001112222',
            'is_tax_declarant': True,
            'tax_identification_type': 'NIT',
            'retention_responsibility': 'RESPONSABLE'
        }
    )
    # Actualizar si ya existía
    supplier_declarant.is_tax_declarant = True
    supplier_declarant.save()
    
    supplier_non_declarant, _ = Supplier.objects.get_or_create(
        ruc='800333444', 
        defaults={
            'nombre': 'Proveedor Persona Natural',
            'email': 'natural@test.com',
            'telefono': '3103334444',
            'is_tax_declarant': False,
            'tax_identification_type': 'CEDULA',
            'retention_responsibility': 'NO_RESPONSABLE'
        }
    )
    supplier_non_declarant.is_tax_declarant = False
    supplier_non_declarant.save()
    
    print(f" > Proveedor Declarante: {supplier_declarant.nombre}")
    print(f" > Proveedor No Declarante: {supplier_non_declarant.nombre}")
    
    # 3. Crear Productos (Bienes, Servicios, Honorarios)
    print("\n[2/5] Creando Productos...")
    
    prod_bienes, _ = Product.objects.get_or_create(
        nombre="Computador Portátil HP",
        defaults={
            'precio_compra': Decimal('2000000'), 
            'precio_venta': Decimal('2500000'), 
            'stock_actual': 10, 
            'codigo': 'LAP-001'
        }
    )
    
    prod_servicios, _ = Product.objects.get_or_create(
        nombre="Servicio de Mantenimiento",
        defaults={
            'precio_compra': Decimal('400000'), 
            'precio_venta': Decimal('500000'), 
            'stock_actual': 100, 
            'codigo': 'SRV-001'
        }
    )
    
    prod_honorarios, _ = Product.objects.get_or_create(
        nombre="Honorarios Jurídicos",
        defaults={
            'precio_compra': Decimal('0'), 
            'precio_venta': Decimal('10000000'), 
            'stock_actual': 1, 
            'codigo': 'HON-001'
        }
    )
    
    print(f" > Producto Bienes: {prod_bienes.nombre}")
    print(f" > Producto Servicios: {prod_servicios.nombre}")
    print(f" > Producto Honorarios: {prod_honorarios.nombre}")
    
    # Obtener valores UVT y Umbrales
    uvt = WithholdingTaxService.get_uvt_value(year)
    base_compras = WithholdingTaxService.calculate_threshold_amount(year, 'compras')
    base_servicios = WithholdingTaxService.calculate_threshold_amount(year, 'servicios')
    
    print(f"\n   [INFO] UVT {year}: ${uvt:,.0f}")
    print(f"   [INFO] Base Compras ({WithholdingTaxService.RETENTION_CONCEPTS['compras']['uvt_threshold']} UVT): ${base_compras:,.0f}")
    print(f"   [INFO] Base Servicios ({WithholdingTaxService.RETENTION_CONCEPTS['servicios']['uvt_threshold']} UVT): ${base_servicios:,.0f}")

    # 4. Crear Compras (Escenarios de Prueba)
    print("\n[3/5] Creando Compras (Transacciones)...")
    
    # Limpiar compras del mes para prueba limpia
    Purchase.objects.filter(fecha__year=year, fecha__month=month, usuario=user).delete()
    
    # CASO A: Compra de Bienes > Base (Declarante) -> Retención 2.5%
    # Monto: Base + 100.000
    monto_a = base_compras + Decimal('100000')
    compra_a = Purchase.objects.create(
        proveedor=supplier_declarant,
        usuario=user,
        fecha=now,
        estado='completada',
        numero_factura=f"TEST-RET-A-{int(now.timestamp())}",
        total=Decimal('0') # Se auto-calcula al agregar detalles en teoría, pero lo forzamos
    )
    detail_a = PurchaseDetail.objects.create(
        compra=compra_a,
        producto=prod_bienes,
        cantidad=1,
        precio_unitario=monto_a,
        subtotal=monto_a
    )
    compra_a.total = monto_a
    compra_a.save()
    print(f" > Caso A: Compra Bienes (Declarante) ${monto_a:,.0f} (> Base) -> Esperado: 2.5%")
    
    # CASO B: Compra de Bienes < Base (Declarante) -> Retención 0%
    # Monto: Base - 100.000
    monto_b = base_compras - Decimal('100000') 
    if monto_b < 0: monto_b = Decimal('50000')
    
    compra_b = Purchase.objects.create(
        proveedor=supplier_declarant,
        usuario=user,
        fecha=now,
        estado='completada',
        numero_factura=f"TEST-RET-B-{int(now.timestamp())}",
        total=monto_b
    )
    detail_b = PurchaseDetail.objects.create(
        compra=compra_b,
        producto=prod_bienes,
        cantidad=1,
        precio_unitario=monto_b,
        subtotal=monto_b
    )
    print(f" > Caso B: Compra Bienes (Declarante) ${monto_b:,.0f} (< Base) -> Esperado: 0%")

    # CASO C: Servicios > Base (No Declarante) -> Retención 6% (Asumiendo 6% para no declarante en servicios generales)
    # Nota: El servicio actualmente define service: 4% declarant, 6% non-declarant
    monto_c = base_servicios + Decimal('100000')
    compra_c = Purchase.objects.create(
        proveedor=supplier_non_declarant,
        usuario=user,
        fecha=now,
        estado='completada',
        numero_factura=f"TEST-RET-C-{int(now.timestamp())}",
        total=monto_c
    )
    detail_c = PurchaseDetail.objects.create(
        compra=compra_c,
        producto=prod_servicios,
        cantidad=1,
        precio_unitario=monto_c,
        subtotal=monto_c
    )
    print(f" > Caso C: Servicio (No Declarante) ${monto_c:,.0f} (> Base) -> Esperado: 6%")
    
    # CASO D: Honorarios (Declarante) -> 11% (Si honorarios > 0 UVT, generalmente es base 0 o 100% de retención)
    # Verifiquemos configuración: HONORARIOS base 0 UVT, rate 11% declarant, 10% non-declarant (o al revés, 11% suele ser PJ->PN, 10% PN->PJ, simplificado aquí)
    monto_d = Decimal('5000000')
    compra_d = Purchase.objects.create(
        proveedor=supplier_declarant,
        usuario=user,
        fecha=now,
        estado='completada',
        numero_factura=f"TEST-RET-D-{int(now.timestamp())}",
        total=monto_d
    )
    detail_d = PurchaseDetail.objects.create(
        compra=compra_d,
        producto=prod_honorarios,
        cantidad=1,
        precio_unitario=monto_d,
        subtotal=monto_d
    )
    print(f" > Caso D: Honorarios (Declarante) ${monto_d:,.0f} -> Esperado: 10% (Valor declarant por defecto en config)")

    # 5. Generar Declaración
    print("\n[4/5] Generando Declaración y Verificando Resultados...")
    
    declaracion = WithholdingTaxService.get_declaracion_retefuente(year, month)
    
    # 6. Validaciones
    errores = []
    
    # Validar Caso A (Compras 2.5%)
    # Concepto: Compras
    concepto_compras = declaracion['conceptos'].get('compras')
    if not concepto_compras:
        errores.append("ERROR: No se encontró el concepto de Compras en la declaración")
    else:
        # Debería incluir solo la Compra A, la B es base 0
        tx_a = [t for t in concepto_compras['transactions'] if t['invoice_number'] == compra_a.numero_factura]
        if not tx_a:
             errores.append("ERROR: Compra A no encontrada en el detalle de Compras")
        else:
            t = tx_a[0]
            esperado = (monto_a * Decimal('0.025')).quantize(Decimal('1.00')) # Rounding logic might vary
            if abs(Decimal(str(t['retention'])) - esperado) > Decimal('100'):
                errores.append(f"ERROR: Retención Caso A incorrecta. Calculado: {t['retention']}, Esperado: {esperado}")
            else:
                print(f"   [OK] Caso A: Retención {t['retention']} (2.5%) validada.")
        
        # Validar que Compra B tenga retención 0
        # No debe estar en las transacciones porque el service hace:
        # if base_amount < threshold_amount: continue
        # Verificamos si existe en detalle_completo (aunque si no se agregó al concepto, no debería estar ahí)
        tx_b = [t for t in declaracion['detalle_completo'] if t['invoice_number'] == compra_b.numero_factura]
        if tx_b:
             errores.append(f"ERROR: Caso B apareció en detalle con retención {tx_b[0]['retention']}")
        else:
             print(f"   [OK] Caso B: No aparece en listado de retenidos (Correcto).")

    # Validar Caso C (Servicios 6%)
    concepto_servicios = declaracion['conceptos'].get('servicios')
    if not concepto_servicios:
        errores.append("ERROR: No se encontró el concepto de Servicios")
    else:
        tx_c = [t for t in concepto_servicios['transactions'] if t['invoice_number'] == compra_c.numero_factura]
        if not tx_c:
             errores.append("ERROR: Compra C no encontrada en el detalle de Servicios")
        else:
            t = tx_c[0]
            esperado = (monto_c * Decimal('0.06')).quantize(Decimal('1.00')) 
            if abs(Decimal(str(t['retention'])) - esperado) > Decimal('100'):
                errores.append(f"ERROR: Retención Caso C incorrecta. Calculado: {t['retention']}, Esperado: {esperado}")
            else:
                 print(f"   [OK] Caso C: Retención {t['retention']} (6%) validada.")

    # Validar Caso D (Honorarios 10% - Declarante)
    # Nota: config services dice 'declarant_rate': Decimal('10.0') for honorarios
    concepto_honorarios = declaracion['conceptos'].get('honorarios')
    if not concepto_honorarios:
        errores.append("ERROR: No se encontró el concepto de Honorarios")
    else:
        tx_d = [t for t in concepto_honorarios['transactions'] if t['invoice_number'] == compra_d.numero_factura]
        if not tx_d:
             errores.append("ERROR: Compra D no encontrada en el detalle de Honorarios")
        else:
            t = tx_d[0]
            esperado = (monto_d * Decimal('0.10')).quantize(Decimal('1.00')) # 10.0%
            if abs(Decimal(str(t['retention'])) - esperado) > Decimal('100'):
                errores.append(f"ERROR: Retención Caso D incorrecta. Calculado: {t['retention']}, Esperado: {esperado}")
            else:
                 print(f"   [OK] Caso D: Retención {t['retention']} (10%) validada.")

    # Resumen Final
    print("\n[5/5] Resumen de Resultados:")
    if errores:
        print("❌ SE ENCONTRARON ERRORES:")
        for e in errores:
            print(f"   - {e}")
    else:
        print(f"✅ TODAS LAS PRUEBAS PASARON CORRECTAMENTE")
        print(f"   Total Retención Calculada: ${declaracion['totales']['total_retencion']:,.2f}")
    
    print("\n=== FIN DE LA PRUEBA ===")


if __name__ == '__main__':
    run_test()
