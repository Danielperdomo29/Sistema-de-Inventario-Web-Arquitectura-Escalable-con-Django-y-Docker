from django.db.models import Sum, F, FloatField, ExpressionWrapper
from django.db.models.functions import Coalesce
from decimal import Decimal
from datetime import datetime, timedelta
from app.models import Sale, SaleDetail, Purchase, PurchaseDetail, Product

class TaxCalculatorService:
    """Servicio para calcular impuestos, específicamente IVA para el Formulario 300"""
    
    @staticmethod
    def calculate_tax_on_sale(sale_detail):
        """
        Calcula el impuesto para un detalle de venta basado en la configuración del producto.
        
        Args:
            sale_detail: Objeto SaleDetail
        
        Returns:
            dict con base, tarifa e impuesto calculado
        """
        product = sale_detail.producto
        if not product:
            return {'base': Decimal('0.00'), 'tax': Decimal('0.00'), 'rate': Decimal('0.00')}
        
        tax_percentage = product.tax_percentage or Decimal('0.00')
        is_tax_included = getattr(product, 'is_tax_included', False)
        subtotal = Decimal(str(sale_detail.subtotal))
        
        if is_tax_included:
            # El subtotal incluye el impuesto
            if tax_percentage > 0:
                base = subtotal / (1 + (tax_percentage / Decimal('100.00')))
                tax = subtotal - base
            else:
                base = subtotal
                tax = Decimal('0.00')
        else:
            # El subtotal no incluye el impuesto
            base = subtotal
            tax = base * (tax_percentage / Decimal('100.00'))
        
        return {
            'base': base.quantize(Decimal('0.01')),
            'tax': tax.quantize(Decimal('0.01')),
            'rate': tax_percentage
        }
    
    @staticmethod
    def calculate_tax_on_purchase(purchase_detail):
        """
        Calcula el impuesto para un detalle de compra.
        Similar a ventas pero para compras.
        """
        product = purchase_detail.producto
        if not product:
            return {'base': Decimal('0.00'), 'tax': Decimal('0.00'), 'rate': Decimal('0.00')}
        
        tax_percentage = product.tax_percentage or Decimal('0.00')
        is_tax_included = getattr(product, 'is_tax_included', False)
        subtotal = Decimal(str(purchase_detail.subtotal))
        
        if is_tax_included:
            if tax_percentage > 0:
                base = subtotal / (1 + (tax_percentage / Decimal('100.00')))
                tax = subtotal - base
            else:
                base = subtotal
                tax = Decimal('0.00')
        else:
            base = subtotal
            tax = base * (tax_percentage / Decimal('100.00'))
        
        return {
            'base': base.quantize(Decimal('0.01')),
            'tax': tax.quantize(Decimal('0.01')),
            'rate': tax_percentage
        }
    
    @staticmethod
    def get_iva_generado(start_date, end_date):
        """
        Calcula el IVA generado (ventas) en el período dado.
        
        Args:
            start_date (datetime.date): Fecha de inicio
            end_date (datetime.date): Fecha de fin
        
        Returns:
            dict: Estructura con IVA agrupado por tarifa y totales
        """
        # Obtener ventas completadas en el período
        sales = Sale.objects.filter(
            fecha__range=[start_date, end_date],
            estado='completada'
        ).select_related('cliente').prefetch_related('detalles')
        
        # Inicializar estructuras para agrupar por tarifa
        tarifas = {
            '19': {'base': Decimal('0.00'), 'tax': Decimal('0.00'), 'ventas': []},
            '5': {'base': Decimal('0.00'), 'tax': Decimal('0.00'), 'ventas': []},
            '0': {'base': Decimal('0.00'), 'tax': Decimal('0.00'), 'ventas': []},
            'exento': {'base': Decimal('0.00'), 'tax': Decimal('0.00'), 'ventas': []},
        }
        
        ventas_detalle = []
        total_base = Decimal('0.00')
        total_tax = Decimal('0.00')
        
        for sale in sales:
            for detail in sale.detalles.all():
                if detail.producto:
                    tax_calc = TaxCalculatorService.calculate_tax_on_sale(detail)
                    
                    # Determinar tarifa
                    rate = tax_calc['rate']
                    if rate == Decimal('19.00'):
                        tarifa_key = '19'
                    elif rate == Decimal('5.00'):
                        tarifa_key = '5'
                    elif rate == Decimal('0.00'):
                        tarifa_key = '0'
                    else:
                        tarifa_key = 'exento'
                    
                    # Acumular por tarifa
                    tarifas[tarifa_key]['base'] += tax_calc['base']
                    tarifas[tarifa_key]['tax'] += tax_calc['tax']
                    
                    # Agregar a detalle de ventas
                    venta_info = {
                        'sale_id': sale.id,
                        'invoice_number': sale.numero_factura or f"Venta-{sale.id}",
                        'client': sale.cliente.nombre if sale.cliente else 'Cliente varios',
                        'date': sale.fecha,
                        'product': detail.producto.nombre,
                        'quantity': detail.cantidad,
                        'unit_price': detail.precio_unitario,
                        'subtotal': detail.subtotal,
                        'tax_base': tax_calc['base'],
                        'tax_amount': tax_calc['tax'],
                        'tax_rate': f"{rate}%",
                    }
                    tarifas[tarifa_key]['ventas'].append(venta_info)
                    ventas_detalle.append(venta_info)
                    
                    # Acumular totales
                    total_base += tax_calc['base']
                    total_tax += tax_calc['tax']
        
        return {
            'tarifas': tarifas,
            'total_base': total_base.quantize(Decimal('0.01')),
            'total_tax': total_tax.quantize(Decimal('0.01')),
            'ventas_detalle': ventas_detalle,
            'periodo': f"{start_date} al {end_date}",
            'total_ventas': len(sales),
        }
    
    @staticmethod
    def get_iva_descontable(start_date, end_date):
        """
        Calcula el IVA descontable (compras) en el período dado.
        
        Args:
            start_date (datetime.date): Fecha de inicio
            end_date (datetime.date): Fecha de fin
        
        Returns:
            dict: Estructura con IVA descontable agrupado por tarifa
        """
        # Obtener compras en el período
        purchases = Purchase.objects.filter(
            fecha__range=[start_date, end_date],
            estado='completada'
        ).select_related('proveedor').prefetch_related('detalles')
        
        # Inicializar estructuras
        tarifas = {
            '19': {'base': Decimal('0.00'), 'tax': Decimal('0.00'), 'compras': []},
            '5': {'base': Decimal('0.00'), 'tax': Decimal('0.00'), 'compras': []},
            '0': {'base': Decimal('0.00'), 'tax': Decimal('0.00'), 'compras': []},
            'exento': {'base': Decimal('0.00'), 'tax': Decimal('0.00'), 'compras': []},
        }
        
        compras_detalle = []
        total_base = Decimal('0.00')
        total_tax = Decimal('0.00')
        
        for purchase in purchases:
            for detail in purchase.detalles.all():
                if detail.producto:
                    tax_calc = TaxCalculatorService.calculate_tax_on_purchase(detail)
                    
                    # Determinar tarifa
                    rate = tax_calc['rate']
                    if rate == Decimal('19.00'):
                        tarifa_key = '19'
                    elif rate == Decimal('5.00'):
                        tarifa_key = '5'
                    elif rate == Decimal('0.00'):
                        tarifa_key = '0'
                    else:
                        tarifa_key = 'exento'
                    
                    # Acumular por tarifa
                    tarifas[tarifa_key]['base'] += tax_calc['base']
                    tarifas[tarifa_key]['tax'] += tax_calc['tax']
                    
                    # Agregar a detalle de compras
                    compra_info = {
                        'purchase_id': purchase.id,
                        'invoice_number': purchase.numero_factura or f"Compra-{purchase.id}",
                        'supplier': purchase.proveedor.nombre if purchase.proveedor else 'Proveedor varios',
                        'date': purchase.fecha,
                        'product': detail.producto.nombre,
                        'quantity': detail.cantidad,
                        'unit_price': detail.precio_unitario,
                        'subtotal': detail.subtotal,
                        'tax_base': tax_calc['base'],
                        'tax_amount': tax_calc['tax'],
                        'tax_rate': f"{rate}%",
                    }
                    tarifas[tarifa_key]['compras'].append(compra_info)
                    compras_detalle.append(compra_info)
                    
                    # Acumular totales
                    total_base += tax_calc['base']
                    total_tax += tax_calc['tax']
        
        return {
            'tarifas': tarifas,
            'total_base': total_base.quantize(Decimal('0.01')),
            'total_tax': total_tax.quantize(Decimal('0.01')),
            'compras_detalle': compras_detalle,
            'periodo': f"{start_date} al {end_date}",
            'total_compras': len(purchases),
        }
    
    @staticmethod
    def get_period_dates(year, period_type, period_number):
        """
        Obtiene las fechas de inicio y fin para un período específico.
        
        Args:
            year: Año
            period_type: 'bimestral' o 'cuatrimestral'
            period_number: Número del período (1-6 para bimestral, 1-3 para cuatrimestral)
        
        Returns:
            tuple: (start_date, end_date)
        """
        if period_type == 'bimestral':
            # Bimestral: 6 períodos al año
            bimestre_meses = {
                1: (1, 2),   # Enero-Febrero
                2: (3, 4),   # Marzo-Abril
                3: (5, 6),   # Mayo-Junio
                4: (7, 8),   # Julio-Agosto
                5: (9, 10),  # Septiembre-Octubre
                6: (11, 12), # Noviembre-Diciembre
            }
            
            if period_number not in bimestre_meses:
                raise ValueError("Número de bimestre inválido. Debe ser 1-6.")
            
            start_month, end_month = bimestre_meses[period_number]
            start_date = datetime(year, start_month, 1).date()
            
            # Último día del mes final
            if end_month == 12:
                end_date = datetime(year, 12, 31).date()
            else:
                end_date = (datetime(year, end_month + 1, 1) - timedelta(days=1)).date()
        
        elif period_type == 'cuatrimestral':
            # Cuatrimestral: 3 períodos al año
            cuatrimestre_meses = {
                1: (1, 4),   # Enero-Abril
                2: (5, 8),   # Mayo-Agosto
                3: (9, 12),  # Septiembre-Diciembre
            }
            
            if period_number not in cuatrimestre_meses:
                raise ValueError("Número de cuatrimestre inválido. Debe ser 1-3.")
            
            start_month, end_month = cuatrimestre_meses[period_number]
            start_date = datetime(year, start_month, 1).date()
            
            # Último día del mes final
            if end_month == 12:
                end_date = datetime(year, 12, 31).date()
            else:
                end_date = (datetime(year, end_month + 1, 1) - timedelta(days=1)).date()
        
        else:
            raise ValueError("Tipo de período inválido. Use 'bimestral' o 'cuatrimestral'.")
        
        return start_date, end_date
    
    @staticmethod
    def get_declaracion_iva(year, period_type, period_number):
        """
        Genera la declaración completa de IVA para el período.
        
        Args:
            year: Año
            period_type: 'bimestral' o 'cuatrimestral'
            period_number: Número del período
        
        Returns:
            dict: Declaración completa de IVA
        """
        # Obtener fechas del período
        start_date, end_date = TaxCalculatorService.get_period_dates(year, period_type, period_number)
        
        # Calcular IVA generado y descontable
        iva_generado = TaxCalculatorService.get_iva_generado(start_date, end_date)
        iva_descontable = TaxCalculatorService.get_iva_descontable(start_date, end_date)
        
        # Calcular neto a pagar
        iva_neto = iva_generado['total_tax'] - iva_descontable['total_tax']
        
        # Calcular porcentaje de cumplimiento
        total_ventas_con_iva = sum(
            tarifa['tax'] for tarifa_key, tarifa in iva_generado['tarifas'].items() 
            if tarifa_key != '0' and tarifa_key != 'exento'
        )
        
        total_compras_con_iva = sum(
            tarifa['tax'] for tarifa_key, tarifa in iva_descontable['tarifas'].items() 
            if tarifa_key != '0' and tarifa_key != 'exento'
        )
        
        cumplimiento = Decimal('0.00')
        if total_compras_con_iva > 0:
            cumplimiento = (total_compras_con_iva / total_ventas_con_iva * 100) if total_ventas_con_iva > 0 else Decimal('100.00')
        
        return {
            'periodo': {
                'year': year,
                'type': period_type,
                'number': period_number,
                'start_date': start_date,
                'end_date': end_date,
                'label': f"{period_type.capitalize()} {period_number} - {year}",
            },
            'iva_generado': iva_generado,
            'iva_descontable': iva_descontable,
            'resumen': {
                'total_iva_generado': iva_generado['total_tax'],
                'total_iva_descontable': iva_descontable['total_tax'],
                'iva_neto_a_pagar': iva_neto,
                'porcentaje_cumplimiento': cumplimiento.quantize(Decimal('0.01')),
                'saldo_favor': iva_neto if iva_neto < 0 else Decimal('0.00'),
                'saldo_pagar': iva_neto if iva_neto > 0 else Decimal('0.00'),
            },
            'metadata': {
                'generated_at': datetime.now(),
                'version': '1.0',
                'formato': 'Formulario 300 DIAN',
            }
        }
