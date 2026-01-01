from django.db.models import Sum, Q
from decimal import Decimal
from datetime import datetime, date
from django.conf import settings
from app.models import Purchase, PurchaseDetail, Supplier

class WithholdingTaxService:
    """
    Servicio para calcular retención en la fuente según Formulario 350 DIAN
    
    Notas:
    - UVT 2024: $42,412 (ajustar según año)
    - Tarifas según Resolución 000042 de 2023
    """
    
    # UVT por año (actualizar anualmente)
    UVT_VALUES = {
        2023: Decimal('42412'),
        2024: Decimal('43805'),
        2025: Decimal('45308'),
    }
    
    # Conceptos de retención según DIAN
    RETENTION_CONCEPTS = {
        'compras': {
            'code': '01',
            'name': 'Compras',
            'declarant_rate': Decimal('2.5'),  # 2.5% para declarantes
            'non_declarant_rate': Decimal('3.5'),  # 3.5% para no declarantes
            'uvt_threshold': 27,  # Base en UVT
            'min_amount': Decimal('0.01'),  # Mínimo para retener
        },
        'servicios': {
            'code': '02',
            'name': 'Servicios',
            'declarant_rate': Decimal('4.0'),
            'non_declarant_rate': Decimal('6.0'),
            'uvt_threshold': 4,
            'min_amount': Decimal('0.01'),
        },
        'honorarios': {
            'code': '03',
            'name': 'Honorarios',
            'declarant_rate': Decimal('10.0'),
            'non_declarant_rate': Decimal('11.0'),
            'uvt_threshold': 10,
            'min_amount': Decimal('0.01'),
        },
        'arrendamientos': {
            'code': '04',
            'name': 'Arrendamientos',
            'declarant_rate': Decimal('3.5'),
            'non_declarant_rate': Decimal('3.5'),
            'uvt_threshold': 0,
            'min_amount': Decimal('0.01'),
        },
    }
    
    @classmethod
    def get_uvt_value(cls, year):
        """Obtiene el valor del UVT para el año dado"""
        return cls.UVT_VALUES.get(year, cls.UVT_VALUES[2024])  # Default 2024
    
    @classmethod
    def calculate_threshold_amount(cls, year, concept_key):
        """Calcula el monto mínimo en pesos para aplicar retención"""
        uvt_value = cls.get_uvt_value(year)
        concept = cls.RETENTION_CONCEPTS[concept_key]
        return uvt_value * Decimal(str(concept['uvt_threshold']))
    
    @classmethod
    def determine_concept(cls, purchase_detail):
        """
        Determina el concepto de retención basado en el producto/proveedor
        
        Nota: En una implementación real, esto debería basarse en:
        1. Categoría del producto
        2. Naturaleza del proveedor
        3. Información de la factura
        """
        # Por ahora, usamos una lógica simple basada en descripción
        product_name = purchase_detail.producto.nombre.lower() if purchase_detail.producto else ""
        supplier = purchase_detail.compra.proveedor if purchase_detail.compra else None
        
        # Lógica de mapeo (simplificada para MVP)
        if any(keyword in product_name for keyword in ['servicio', 'consultoría', 'asesoría', 'mantenimiento']):
            return 'servicios'
        elif any(keyword in product_name for keyword in ['honorario', 'profesional', 'abogado', 'contador']):
            return 'honorarios'
        elif any(keyword in product_name for keyword in ['arriendo', 'alquiler', 'renta']):
            return 'arrendamientos'
        else:
            return 'compras'  # Default para compras de bienes
    
    @classmethod
    def is_declarant(cls, supplier):
        """Determina si un proveedor es declarante de renta"""
        if not supplier:
            return False
        
        # Lógica para determinar si es declarante
        # En producción, esto debería venir de un campo en el modelo Supplier
        return getattr(supplier, 'is_tax_declarant', False)
    
    @classmethod
    def calculate_withholding_for_purchase(cls, purchase, year):
        """
        Calcula la retención en la fuente para una compra específica
        
        Args:
            purchase: Objeto Purchase
            year: Año para cálculo de UVT
        
        Returns:
            dict con retención calculada por concepto
        """
        supplier = purchase.proveedor
        is_declarant = cls.is_declarant(supplier)
        
        # Inicializar resultados
        retention_by_concept = {}
        
        for detail in purchase.detalles.all():
            concept_key = cls.determine_concept(detail)
            concept = cls.RETENTION_CONCEPTS[concept_key]
            
            # Calcular base
            base_amount = Decimal(str(detail.subtotal))
            
            # Verificar si supera el umbral en UVT
            threshold_amount = cls.calculate_threshold_amount(year, concept_key)
            
            if base_amount < threshold_amount:
                # No aplica retención
                continue
            
            # Determinar tarifa
            rate = concept['declarant_rate'] if is_declarant else concept['non_declarant_rate']
            
            # Calcular retención
            retention_amount = base_amount * (rate / Decimal('100.0'))
            
            # Aplicar mínimo
            if retention_amount < concept['min_amount']:
                continue
            
            # Acumular por concepto
            if concept_key not in retention_by_concept:
                retention_by_concept[concept_key] = {
                    'concept': concept,
                    'base_amount': Decimal('0.00'),
                    'retention_amount': Decimal('0.00'),
                    'transactions': [],
                    'supplier_type': 'declarant' if is_declarant else 'non_declarant',
                    'rate_applied': rate,
                }
            
            retention_by_concept[concept_key]['base_amount'] += base_amount
            retention_by_concept[concept_key]['retention_amount'] += retention_amount
            retention_by_concept[concept_key]['transactions'].append({
                'purchase_id': purchase.id,
                'invoice_number': purchase.numero_factura,
                'date': purchase.fecha,
                'supplier': supplier.nombre if supplier else 'No especificado',
                'product': detail.producto.nombre if detail.producto else 'No especificado',
                'base': base_amount,
                'retention': retention_amount,
            })
        
        return retention_by_concept
    
    @classmethod
    def get_declaracion_retefuente(cls, year, month):
        """
        Genera la declaración de retención en la fuente para un mes específico
        
        Args:
            year: Año
            month: Mes (1-12)
        
        Returns:
            dict con declaración completa
        """
        # Validar parámetros
        if not (1 <= month <= 12):
            raise ValueError("Mes debe estar entre 1 y 12")
        
        # Determinar rango de fechas
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year, 12, 31)
        else:
            end_date = date(year, month + 1, 1) - date.resolution
        
        # Obtener compras del período
        purchases = Purchase.objects.filter(
            fecha__range=[start_date, end_date],
            estado='completada'
        ).select_related('proveedor').prefetch_related('detalles')
        
        # Inicializar estructura de resultados
        declaracion = {
            'periodo': {
                'year': year,
                'month': month,
                'start_date': start_date,
                'end_date': end_date,
                'label': f"{month:02d}/{year}",
            },
            'conceptos': {},
            'totales': {
                'total_base': Decimal('0.00'),
                'total_retencion': Decimal('0.00'),
                'total_transacciones': 0,
                'total_proveedores': set(),
            },
            'detalle_completo': [],
            'metadata': {
                'uvt_value': cls.get_uvt_value(year),
                'generated_at': datetime.now(),
                'version': '1.0',
            }
        }
        
        # Inicializar conceptos
        for concept_key, concept in cls.RETENTION_CONCEPTS.items():
            declaracion['conceptos'][concept_key] = {
                'concept': concept,
                'base_amount': Decimal('0.00'),
                'retention_amount': Decimal('0.00'),
                'transactions': [],
                'declarant_count': 0,
                'non_declarant_count': 0,
                'uvt_threshold': cls.calculate_threshold_amount(year, concept_key),
            }
        
        # Procesar cada compra
        for purchase in purchases:
            retention_by_concept = cls.calculate_withholding_for_purchase(purchase, year)
            
            for concept_key, retention_data in retention_by_concept.items():
                # Acumular en concepto general
                declaracion['conceptos'][concept_key]['base_amount'] += retention_data['base_amount']
                declaracion['conceptos'][concept_key]['retention_amount'] += retention_data['retention_amount']
                declaracion['conceptos'][concept_key]['transactions'].extend(retention_data['transactions'])
                
                if retention_data['supplier_type'] == 'declarant':
                    declaracion['conceptos'][concept_key]['declarant_count'] += 1
                else:
                    declaracion['conceptos'][concept_key]['non_declarant_count'] += 1
                
                # Agregar a detalle completo
                for transaction in retention_data['transactions']:
                    declaracion['detalle_completo'].append({
                        'concept_key': concept_key,
                        'concept_name': cls.RETENTION_CONCEPTS[concept_key]['name'],
                        **transaction
                    })
                
                # Actualizar totales generales
                declaracion['totales']['total_base'] += retention_data['base_amount']
                declaracion['totales']['total_retencion'] += retention_data['retention_amount']
                declaracion['totales']['total_transacciones'] += len(retention_data['transactions'])
                
                # Agregar proveedor al conjunto
                if purchase.proveedor:
                    declaracion['totales']['total_proveedores'].add(purchase.proveedor.id)
        
        # Convertir set a contador
        declaracion['totales']['total_proveedores'] = len(declaracion['totales']['total_proveedores'])
        
        # Formatear montos
        for key in declaracion['totales']:
            if isinstance(declaracion['totales'][key], Decimal):
                declaracion['totales'][key] = declaracion['totales'][key].quantize(Decimal('0.01'))
        
        for concept_key in declaracion['conceptos']:
            declaracion['conceptos'][concept_key]['base_amount'] = declaracion['conceptos'][concept_key]['base_amount'].quantize(Decimal('0.01'))
            declaracion['conceptos'][concept_key]['retention_amount'] = declaracion['conceptos'][concept_key]['retention_amount'].quantize(Decimal('0.01'))
        
        return declaracion
    
    @classmethod
    def get_monthly_summary(cls, year):
        """
        Obtiene un resumen mensual de retenciones para todo el año
        
        Args:
            year: Año
        
        Returns:
            dict con resumen mensual
        """
        summary = {
            'year': year,
            'months': {},
            'annual_total': Decimal('0.00'),
            'annual_base': Decimal('0.00'),
        }
        
        for month in range(1, 13):
            try:
                declaracion = cls.get_declaracion_retefuente(year, month)
                summary['months'][month] = {
                    'retencion': declaracion['totales']['total_retencion'],
                    'base': declaracion['totales']['total_base'],
                    'transacciones': declaracion['totales']['total_transacciones'],
                }
                summary['annual_total'] += declaracion['totales']['total_retencion']
                summary['annual_base'] += declaracion['totales']['total_base']
            except Exception as e:
                summary['months'][month] = {
                    'retencion': Decimal('0.00'),
                    'base': Decimal('0.00'),
                    'transacciones': 0,
                    'error': str(e),
                }
        
        return summary
    
    @classmethod
    def export_formulario_350_format(cls, declaracion):
        """
        Formatea la declaración en estructura similar al Formulario 350
        
        Returns:
            dict en formato para exportación
        """
        period = declaracion['periodo']
        
        # Estructura del Formulario 350
        formulario = {
            'encabezado': {
                'tipo_formulario': '350',
                'periodo': period['label'],
                'fecha_generacion': declaracion['metadata']['generated_at'].strftime('%Y-%m-%d'),
                'uvt_valor': float(declaracion['metadata']['uvt_value']),
                'uvt_anio': period['year'],
            },
            'retenciones_calculadas': [],
            'resumen_general': {
                'total_base_gravable': float(declaracion['totales']['total_base']),
                'total_retencion': float(declaracion['totales']['total_retencion']),
                'total_transacciones': declaracion['totales']['total_transacciones'],
                'total_proveedores': declaracion['totales']['total_proveedores'],
            }
        }
        
        # Agregar cada concepto
        for concept_key, data in declaracion['conceptos'].items():
            if data['retention_amount'] > 0:
                formulario['retenciones_calculadas'].append({
                    'codigo_concepto': data['concept']['code'],
                    'nombre_concepto': data['concept']['name'],
                    'base_gravable': float(data['base_amount']),
                    'valor_retenido': float(data['retention_amount']),
                    'num_transacciones': len(data['transactions']),
                    'num_declarantes': data['declarant_count'],
                    'num_no_declarantes': data['non_declarant_count'],
                    'uvt_minimo': float(data['uvt_threshold']),
                })
        
        return formulario
