#!/usr/bin/env python3
"""
Script para probar manualmente la declaración de IVA
"""
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.fiscal.services.tax_service import TaxCalculatorService
from app.models import Product, Sale, SaleDetail, Purchase, PurchaseDetail, Client, Supplier, UserAccount

def crear_datos_prueba():
    """Crear datos de prueba para el Formulario 300"""
    print("TEST: CREANDO DATOS DE PRUEBA PARA FORMULARIO 300")
    print("=" * 60)
    
    # Crear usuario si no existe
    user, _ = UserAccount.objects.get_or_create(
        username='testfiscal_script',
        defaults={'email': 'test_script@fiscal.com', 'first_name': 'Test', 'last_name': 'Script'}
    )

    # Crear productos
    productos = []
    
    # Producto 19% no incluido
    p1, created = Product.objects.get_or_create(
        nombre="Laptop Gamer",
        defaults={
            'precio_venta': Decimal('1500.00'),
            'tax_percentage': Decimal('19.00'),
            'is_tax_included': False,
            'precio_compra': Decimal('1000.00'),
            'descripcion': 'Laptop para gaming',
            'stock_actual': 100,
            'stock_minimo': 5,
            'codigo': 'LAPTOP-01'
        }
    )
    productos.append(p1)
    print(f"Producto creado: {p1.nombre} - IVA {p1.tax_percentage}%")
    
    # Producto 5% no incluido
    p2, created = Product.objects.get_or_create(
        nombre="Libros Educativos",
        defaults={
            'precio_venta': Decimal('50.00'),
            'tax_percentage': Decimal('5.00'),
            'is_tax_included': False,
            'precio_compra': Decimal('30.00'),
            'descripcion': 'Libros con IVA reducido',
            'stock_actual': 200,
            'stock_minimo': 10,
            'codigo': 'LIBRO-01'
        }
    )
    productos.append(p2)
    print(f"Producto creado: {p2.nombre} - IVA {p2.tax_percentage}%")
    
    # Producto 19% incluido
    p3, created = Product.objects.get_or_create(
        nombre="Servicio Técnico",
        defaults={
            'precio_venta': Decimal('119.00'),
            'tax_percentage': Decimal('19.00'),
            'is_tax_included': True,
            'precio_compra': Decimal('50.00'),
            'descripcion': 'Servicio con IVA incluido',
            'stock_actual': 1000,
            'stock_minimo': 1,
            'codigo': 'SERV-01'
        }
    )
    productos.append(p3)
    print(f"Producto creado: {p3.nombre} - IVA {p3.tax_percentage}% incluido")
    
    # Cliente
    cliente, _ = Client.objects.get_or_create(
        nombre="Empresa ABC SAS",
        defaults={'email': 'abc@empresa.com', 'telefono': '3001234567', 'documento': '900123456'}
    )
    print(f"Cliente creado: {cliente.nombre}")
    
    # Proveedor
    proveedor, _ = Supplier.objects.get_or_create(
        nombre="Distribuidora XYZ",
        defaults={'email': 'xyz@proveedor.com', 'telefono': '3109876543', 'ruc': '800123456-1'}
    )
    print(f"Proveedor creado: {proveedor.nombre}")
    
    # Fechas para el bimestre actual
    hoy = datetime.now().date()
    start_date = hoy.replace(day=1)  # Primer día del mes
    if hoy.month % 2 == 0:  # Mes par (febrero, abril, etc.)
        start_date = start_date.replace(month=hoy.month-1)
    
    # Crear ventas
    print(f"\nCREANDO VENTAS PARA EL PERÍODO: {start_date} al {hoy}")
    
    
    # Asegurar que las fechas caigan dentro del bimestre actual
    # Si estamos a inicio de año (Enero 1), restar dias nos lleva al año anterior.
    # Mejor sumar días desde start_date
    
    ventas_data = [
        {'producto': p1, 'cantidad': 2, 'precio': 1500.00},  # $3,000 + $570 IVA
        {'producto': p2, 'cantidad': 10, 'precio': 50.00},   # $500 + $25 IVA
        {'producto': p3, 'cantidad': 5, 'precio': 119.00},   # $595 (IVA incluido: $95)
    ]
    
    total_ventas = 0
    total_iva_generado = Decimal('0.00')
    
    for i, venta_data in enumerate(ventas_data, 1):
        sale = Sale.objects.create(
            cliente=cliente,
            usuario=user,
            fecha=start_date + timedelta(days=i), # Usar start_date + i días
            estado='completada',
            numero_factura=f"TEST-SCRIPT-{i}-{int(datetime.now().timestamp())}",
            total=0 # Se calculara despues
        )
        
        subtotal = Decimal(str(venta_data['precio'])) * Decimal(str(venta_data['cantidad']))
        
        # Calcular IVA
        if venta_data['producto'].is_tax_included:
            base = subtotal / (1 + venta_data['producto'].tax_percentage / Decimal('100.00'))
            tax = subtotal - base
        else:
            base = subtotal
            tax = base * (venta_data['producto'].tax_percentage / Decimal('100.00'))
        
        detail = SaleDetail.objects.create(
            venta=sale,
            producto=venta_data['producto'],
            cantidad=venta_data['cantidad'],
            precio_unitario=venta_data['precio'],
            subtotal=subtotal
        )
        
        # Actualizar totales (el modelo no tiene campo 'tax' explícito en Sale, asumo que 'total' incluye impuesto)
        # Revertir logica: total = subtotal + tax si no incluido.
        # Si incluido, total = subtotal (porque subtotal ya tiene precio con iva * cantidad)
        
        total_venta = subtotal
        if not venta_data['producto'].is_tax_included:
             total_venta += tax
             
        sale.total = total_venta
        sale.save()
        
        total_ventas += 1
        total_iva_generado += tax
        
        print(f"  -> Venta {i}: {venta_data['producto'].nombre} x{venta_data['cantidad']}")
        print(f"    Subtotal: ${subtotal:,.2f} | IVA: ${tax:,.2f} | Total: ${sale.total:,.2f}")
    
    # Crear compras
    print(f"\nCREANDO COMPRAS PARA EL PERÍODO")
    
    compras_data = [
        {'producto': p1, 'cantidad': 1, 'precio': 1000.00},  # $1,000 + $190 IVA descontable
        {'producto': p2, 'cantidad': 5, 'precio': 30.00},    # $150 + $7.50 IVA descontable
    ]
    
    total_compras = 0
    total_iva_descontable = Decimal('0.00')
    
    for i, compra_data in enumerate(compras_data, 1):
        purchase = Purchase.objects.create(
            proveedor=proveedor,
            usuario=user,
            fecha=start_date + timedelta(days=i+3), # Usar start_date + offset
            estado='completada',
            # total=0, # total argument seems correct, removing comments about subtotal
            total=0,
            numero_factura=f"TEST-SCRIPT-BUY-{i}-{int(datetime.now().timestamp())}"
        )
        
        subtotal = Decimal(str(compra_data['precio'])) * Decimal(str(compra_data['cantidad']))
        
        # Calcular IVA descontable
        if compra_data['producto'].is_tax_included:
            base = subtotal / (1 + compra_data['producto'].tax_percentage / Decimal('100.00'))
            tax = subtotal - base
        else:
            base = subtotal
            tax = base * (compra_data['producto'].tax_percentage / Decimal('100.00'))
        
        detail = PurchaseDetail.objects.create(
            compra=purchase,
            producto=compra_data['producto'],
            cantidad=compra_data['cantidad'],
            precio_unitario=compra_data['precio'],
            subtotal=subtotal
        )
        
        # Actualizar totales
        total_compra = subtotal
        if not compra_data['producto'].is_tax_included:
             total_compra += tax
             
        purchase.total = total_compra
        purchase.save()
        
        total_compras += 1
        total_iva_descontable += tax
        
        print(f"  -> Compra {i}: {compra_data['producto'].nombre} x{compra_data['cantidad']}")
        print(f"    Subtotal: ${subtotal:,.2f} | IVA Descontable: ${tax:,.2f}")
    
    print("\n" + "=" * 60)
    print("RESUMEN DE DATOS CREADOS:")
    print(f"  Productos: {len(productos)}")
    print(f"  Ventas: {total_ventas}")
    print(f"  Compras: {total_compras}")
    print(f"  IVA Generado estimado: ${total_iva_generado:,.2f}")
    print(f"  IVA Descontable estimado: ${total_iva_descontable:,.2f}")
    print(f"  IVA Neto estimado: ${total_iva_generado - total_iva_descontable:,.2f}")
    print("=" * 60)
    
    return {
        'start_date': start_date,
        'end_date': hoy,
        'year': hoy.year,
        'period_type': 'bimestral',
        'period_number': ((hoy.month - 1) // 2) + 1,
    }

def probar_declaracion_iva():
    """Probar la generación de la declaración de IVA"""
    print("\nGENERANDO DECLARACIÓN DE IVA")
    print("=" * 60)
    
    # Obtener parámetros del período actual
    hoy = datetime.now().date()
    year = hoy.year
    period_type = 'bimestral'
    period_number = ((hoy.month - 1) // 2) + 1
    
    print(f"Parámetros:")
    print(f"  Año: {year}")
    print(f"  Tipo de período: {period_type}")
    print(f"  Período: {period_number}")
    
    try:
        # Generar declaración
        declaracion = TaxCalculatorService.get_declaracion_iva(
            year=year,
            period_type=period_type,
            period_number=period_number
        )
        
        print("\nDECLARACIÓN GENERADA EXITOSAMENTE")
        print("=" * 60)
        
        # Mostrar resumen
        print("\nRESUMEN DE LA DECLARACIÓN:")
        print(f"  Período: {declaracion['periodo']['label']}")
        print(f"  Fechas: {declaracion['periodo']['start_date']} al {declaracion['periodo']['end_date']}")
        print(f"  Total IVA Generado: ${declaracion['iva_generado']['total_tax']:,.2f}")
        print(f"  Total IVA Descontable: ${declaracion['iva_descontable']['total_tax']:,.2f}")
        print(f"  IVA Neto a Pagar: ${declaracion['resumen']['iva_neto_a_pagar']:,.2f}")
        print(f"  Porcentaje Cumplimiento: {declaracion['resumen']['porcentaje_cumplimiento']}%")
        
        # Mostrar detalle por tarifa
        print("\nDETALLE POR TARIFA - IVA GENERADO:")
        for tarifa_key, tarifa in declaracion['iva_generado']['tarifas'].items():
            if tarifa['tax'] > 0:
                print(f"  Tarifa {tarifa_key}%:")
                print(f"    Base: ${tarifa['base']:,.2f}")
                print(f"    IVA: ${tarifa['tax']:,.2f}")
                print(f"    Transacciones: {len(tarifa['ventas'])}")
        
        print("\nDETALLE POR TARIFA - IVA DESCONTABLE:")
        for tarifa_key, tarifa in declaracion['iva_descontable']['tarifas'].items():
            if tarifa['tax'] > 0:
                print(f"  Tarifa {tarifa_key}%:")
                print(f"    Base: ${tarifa['base']:,.2f}")
                print(f"    IVA: ${tarifa['tax']:,.2f}")
                print(f"    Transacciones: {len(tarifa['compras'])}")
        
        # Verificar cálculos
        print("\nVERIFICACIÓN DE CÁLCULOS:")
        iva_generado_total = declaracion['iva_generado']['total_tax']
        iva_descontable_total = declaracion['iva_descontable']['total_tax']
        iva_neto_calculado = declaracion['resumen']['iva_neto_a_pagar']
        iva_neto_esperado = iva_generado_total - iva_descontable_total
        
        print(f"  IVA Generado: ${iva_generado_total:,.2f}")
        print(f"  IVA Descontable: ${iva_descontable_total:,.2f}")
        print(f"  IVA Neto (calculado): ${iva_neto_calculado:,.2f}")
        print(f"  IVA Neto (esperado): ${iva_neto_esperado:,.2f}")
        
        if abs(iva_neto_calculado - iva_neto_esperado) < Decimal('0.01'):
            print("  Los cálculos son correctos")
        else:
            print(f"  Diferencia: ${abs(iva_neto_calculado - iva_neto_esperado):,.2f}")
        
        # Mostrar metadata
        print(f"\nMetadata:")
        print(f"  Generado: {declaracion['metadata']['generated_at']}")
        print(f"  Versión: {declaracion['metadata']['version']}")
        print(f"  Formato: {declaracion['metadata']['formato']}")
        
        return declaracion
        
    except Exception as e:
        print(f"\nERROR AL GENERAR DECLARACIÓN:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

def ejecutar_pruebas_completas():
    """Ejecutar pruebas completas del módulo de IVA"""
    print("EJECUTANDO PRUEBAS DEL MÓDULO DE IVA")
    print("=" * 60)
    
    # 1. Crear datos de prueba
    params = crear_datos_prueba()
    
    # 2. Probar declaración
    declaracion = probar_declaracion_iva()
    
    if declaracion:
        # 3. Exportar a diferentes formatos
        print("\nPROBANDO EXPORTACIÓN:")
        
        # Exportar a JSON
        print("  Exportando a JSON...")
        import json
        json_data = {
            'success': True,
            'declaracion': declaracion
        }
        
        # Guardar archivo de prueba
        import tempfile
        temp_dir = tempfile.gettempdir()
        json_path = f"{temp_dir}/declaracion_iva_prueba.json"
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        print(f"  JSON guardado en: {json_path}")
        
        # 4. Probar diferentes períodos
        print("\nPROBANDO DIFERENTES PERÍODOS:")
        
        periodos_prueba = [
            (2024, 'bimestral', 1),
            (2024, 'bimestral', 6),
            (2024, 'cuatrimestral', 1),
            (2024, 'cuatrimestral', 3),
        ]
        
        for year, period_type, period_number in periodos_prueba:
            try:
                declaracion_test = TaxCalculatorService.get_declaracion_iva(
                    year, period_type, period_number
                )
                print(f"  {period_type} {period_number} - {year}: Generado exitosamente")
            except Exception as e:
                print(f"  {period_type} {period_number} - {year}: Error - {e}")
    
    print("\n" + "=" * 60)
    print("PRUEBAS COMPLETADAS")
    print("=" * 60)
    
    # Instrucciones para probar en el navegador
    print("\nPARA PROBAR EN EL NAVEGADOR:")
    print(f"  1. Accede a: http://localhost:8000/reportes/declaracion-iva/")
    print(f"  2. Selecciona el año y período")
    print(f"  3. Haz clic en 'Calcular'")

if __name__ == "__main__":
    ejecutar_pruebas_completas()
