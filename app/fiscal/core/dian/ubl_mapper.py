"""
Servicio de mapeo de datos de Venta a estructura UBL 2.1 DIAN.
Transforma modelos Django en diccionarios listos para generación XML.
"""
from typing import Dict, List, Any
from decimal import Decimal
from app.models.sale import Sale
from app.fiscal.core.dian.formatters import DIANFormatter
import logging

logger = logging.getLogger(__name__)


class UBLMapper:
    """
    Servicio de mapeo Venta → UBL 2.1.
    Convierte modelos Django a diccionarios con la estructura
    exacta requerida por UBLGeneratorService.
    """
    
    @staticmethod
    def map_sale_to_ubl_data(
        sale: Sale,
        fiscal_config: 'FiscalConfig',
        numero_factura: str,
        cufe: str
    ) -> Dict[str, Any]:
        """Mapea una venta completa a estructura UBL."""
        from django.utils import timezone
        
        # Obtener timestamp de emisión
        fecha_hora = timezone.now()
        fecha_str, hora_str = DIANFormatter.formatear_datetime_completo(fecha_hora)
        
        # Mapear líneas de ítems
        lineas = UBLMapper._mapear_lineas(sale)
        
        # Calcular impuestos
        impuestos = UBLMapper._calcular_impuestos(sale)
        
        # Calcular totales
        totales = UBLMapper._determinar_totales(sale, impuestos)
        
        return {
            'numero_factura': numero_factura,
            'cufe': cufe,
            'fecha_emision': fecha_str,
            'hora_emision': hora_str,
            'tipo_factura': '01',
            'moneda': 'COP',
            'emisor': {
                'nit': fiscal_config.nit_emisor,
                'dv': fiscal_config.dv_emisor,
                'razon_social': fiscal_config.razon_social,
            },
            'cliente': UBLMapper._mapear_cliente(sale.cliente),
            'items': lineas,
            'impuestos': impuestos,
            'totales': totales,
        }
    
    @staticmethod
    def _mapear_cliente(cliente) -> Dict[str, Any]:
        """Mapea datos del cliente."""
        return {
            'tipo_documento': '13',  # NIT
            'numero_identificacion': cliente.documento or '222222222222',
            'nombre': cliente.nombre,
            'email': getattr(cliente, 'email', ''),
            'telefono': getattr(cliente, 'telefono', ''),
        }
    
    @staticmethod
    def _mapear_lineas(sale):
        """Mapea líneas de detalle de la venta usando campos reales de IVA."""
        from decimal import Decimal
        
        items = sale.detalles.all()
        lineas = []
        
        for idx, item in enumerate(items, 1):
            precio_unit = item.precio_unitario or Decimal('0')
            cantidad = item.cantidad or 1
            subtotal_sin_iva = item.subtotal_sin_iva or (precio_unit * cantidad)
            iva_tasa = item.iva_tasa or Decimal('19.00')
            iva_valor = item.iva_valor or Decimal('0')
            subtotal_con_iva = item.subtotal or (subtotal_sin_iva + iva_valor)
            
            lineas.append({
                'numero': idx,
                'codigo': item.producto.codigo if hasattr(item.producto, 'codigo') else f'PROD-{item.producto_id}',
                'descripcion': item.producto.nombre,
                'cantidad': float(cantidad),
                'unidad': 'UND',
                'precio_unitario': DIANFormatter.formatear_decimal(precio_unit),
                'subtotal_linea': DIANFormatter.formatear_decimal(subtotal_sin_iva),
                'total_linea': DIANFormatter.formatear_decimal(subtotal_con_iva),
                'impuestos': [{
                    'tipo': 'IVA',
                    'tasa': float(iva_tasa),
                    'base': DIANFormatter.formatear_decimal(subtotal_sin_iva),
                    'valor': DIANFormatter.formatear_decimal(iva_valor)
                }]
            })
        
        return lineas
    
    @staticmethod
    def _calcular_impuestos(sale):
        """Calcula impuestos desde los datos reales de Sale."""
        from decimal import Decimal
        
        detalles = sale.detalles.all()
        iva_por_tasa = {}
        
        for detalle in detalles:
            tasa = detalle.iva_tasa or Decimal('19.00')
            tasa_str = str(int(tasa))
            
            if tasa_str not in iva_por_tasa:
                iva_por_tasa[tasa_str] = {
                    'base': Decimal('0'),
                    'valor': Decimal('0'),
                    'tasa': tasa
                }
            
            iva_por_tasa[tasa_str]['base'] += (detalle.subtotal_sin_iva or Decimal('0'))
            iva_por_tasa[tasa_str]['valor'] += (detalle.iva_valor or Decimal('0'))
        
        iva_total = sum(item['valor'] for item in iva_por_tasa.values())
        
        return {
            'iva': {
                'total': float(iva_total),
                'detalles': [
                    {
                        'tasa': float(item['tasa']),
                        'base': float(item['base']),
                        'valor': float(item['valor'])
                    }
                    for item in iva_por_tasa.values()
                ]
            },
            'inc': {'total': 0, 'detalles': []},
            'ica': {'total': 0, 'detalles': []}
        }
    
    @staticmethod
    def _determinar_totales(sale, tax_totals):
        """Determina totales monetarios usando campos reales del modelo Sale."""
        from decimal import Decimal
        
        subtotal = sale.subtotal or Decimal('0')
        iva_total = sale.iva_total or Decimal('0')
        total = sale.total or Decimal('0')
        
        if not subtotal:
            subtotal = total / Decimal('1.19')
            iva_total = total - subtotal
        
        return {
            'subtotal': DIANFormatter.formatear_decimal(subtotal),
            'total_bruto': DIANFormatter.formatear_decimal(subtotal),
            'total_iva': DIANFormatter.formatear_decimal(iva_total),
            'total': DIANFormatter.formatear_decimal(total),
            'total_pagar': DIANFormatter.formatear_decimal(total)
        }
