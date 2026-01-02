# Generated migration - DO NOT EDIT MANUALLY
from django.db import migrations
from decimal import Decimal


def calculate_taxes_for_existing_sales(apps, schema_editor):
    """
    Calcula IVA para ventas existentes.
    Asume que precios actuales son SIN IVA y aplica tasa del 19%.
    """
    Sale = apps.get_model('app', 'Sale')
    SaleDetail = apps.get_model('app', 'SaleDetail')
    
    print("Calculando IVA para ventas existentes...")
    
    sales_updated = 0
    details_updated = 0
    
    # Procesar cada detalle de venta
    for detail in SaleDetail.objects.all():
        # Precio unitario ya es sin IVA (según confirmación del usuario)
        subtotal_sin_iva = detail.precio_unitario * detail.cantidad
        iva_valor = subtotal_sin_iva * Decimal('0.19')  # 19% IVA
        subtotal_con_iva = subtotal_sin_iva + iva_valor
        
        # Actualizar campos
        detail.iva_tasa = Decimal('19.00')
        detail.subtotal_sin_iva = subtotal_sin_iva
        detail.iva_valor = iva_valor
        detail.subtotal = subtotal_con_iva
        detail.save()
        
        details_updated += 1
    
    # Procesar cada venta
    for sale in Sale.objects.all():
        # Calcular totales desde detalles
        details = SaleDetail.objects.filter(venta_id=sale.id)
        
        subtotal_total = sum(d.subtotal_sin_iva for d in details)
        iva_total = sum(d.iva_valor for d in details)
        total_con_iva = subtotal_total + iva_total
        
        sale.subtotal = subtotal_total
        sale.iva_total = iva_total
        sale.total = total_con_iva
        sale.save()
        
        sales_updated += 1
    
    print(f"Actualizadas {sales_updated} ventas y {details_updated} detalles con calculo de IVA")


def reverse_taxes(apps, schema_editor):
    """Revertir cambios (establecer en NULL)."""
    Sale = apps.get_model('app', 'Sale')
    SaleDetail = apps.get_model('app', 'SaleDetail')
    
    Sale.objects.all().update(subtotal=None, iva_total=None)
    SaleDetail.objects.all().update(
        iva_tasa=Decimal('19.00'),
        subtotal_sin_iva=None,
        iva_valor=None
    )


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_add_tax_fields'),
    ]

    operations = [
        migrations.RunPython(calculate_taxes_for_existing_sales, reverse_taxes),
    ]
