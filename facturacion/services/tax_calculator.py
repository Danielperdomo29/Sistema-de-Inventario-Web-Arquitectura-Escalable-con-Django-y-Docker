from decimal import Decimal

class TaxCalculatorService:
    @staticmethod
    def calculate_sale_totals(sale):
        """
        Calcula los desglose tributarios de una venta basados en los productos.
        Retorna una estructura estandarizada para XML y PDF.
        """
        detalles_productos = []
        totales_impuestos = {} # Key: (tax_type_id, percentage) -> Value: {base, tax}
        
        subtotal_global = Decimal('0.00')
        total_impuestos_global = Decimal('0.00')
        total_factura_global = Decimal('0.00')
        
        # Iterar detalles (usando select_related en la consulta previa idealmente)
        # Asumimos que sale.detalles.all() trae los productos.
        # Si no, deberíamos optimizar la query antes.
        
        detalles = sale.detalles.select_related('producto').all()
        
        for detail in detalles:
            product = detail.producto
            quantity = Decimal(str(detail.cantidad))
            unit_price = Decimal(str(detail.precio_unitario))
            
            tax_rate = product.tax_percentage
            tax_type = product.tax_type_id
            is_included = product.is_tax_included
            
            # 1. Calcular Base y Tax unitario
            if is_included:
                # El precio ya tiene el impuesto: Precio = Base * (1 + rate)
                # Base = Precio / (1 + rate)
                base_unit = unit_price / (1 + (tax_rate / 100))
                tax_unit = unit_price - base_unit
            else:
                # El precio es base: Base = Precio
                base_unit = unit_price
                tax_unit = base_unit * (tax_rate / 100)
            
            # 2. Valores Totales por Ítem
            base_total_item = base_unit * quantity
            tax_total_item = tax_unit * quantity
            total_item = base_total_item + tax_total_item
            
            # Acumuladores Globales
            subtotal_global += base_total_item
            total_impuestos_global += tax_total_item
            total_factura_global += total_item
            
            # 3. Empujar a detalles
            detalles_productos.append({
                "codigo": product.codigo,
                "descripcion": product.nombre,
                "cantidad": float(quantity),
                "valor_unitario": float(round(base_unit, 2)), # DIAN: Valor unitario suele ser Base Unitario
                "tasa_iva": float(tax_rate),
                "valor_iva": float(round(tax_total_item, 2)),
                "total_item": float(round(total_item, 2)),
                "tax_type_id": tax_type # Identificador interno para XML
            })
            
            # 4. Agrupación Tributaria
            key = (tax_type, tax_rate)
            if key not in totales_impuestos:
                totales_impuestos[key] = {
                    "base_imponible": Decimal('0.00'),
                    "valor_total_impuesto": Decimal('0.00'),
                    "nombre": "IVA" if tax_type == '01' else "INC" # Simplificación
                }
            
            totales_impuestos[key]["base_imponible"] += base_total_item
            totales_impuestos[key]["valor_total_impuesto"] += tax_total_item

        # Formatear Totales Impuestos para lista
        lista_impuestos = []
        for (code, rate), values in totales_impuestos.items():
            lista_impuestos.append({
                "codigo_impuesto": code,
                "nombre": values["nombre"],
                "base_imponible": float(round(values["base_imponible"], 2)),
                "valor_total_impuesto": float(round(values["valor_total_impuesto"], 2)),
                "porcentaje": float(rate)
            })

        # Estructura Final JSON Standard
        standard_json = {
            "venta_info": {
                "fecha": sale.fecha.strftime('%Y-%m-%d'),
                "hora": sale.fecha.strftime('%H:%M:%S'),
                "tipo_pago": "1" if sale.tipo_pago == 'efectivo' else "2", # Mapeo simplificado
                "medio_pago": "10", # Efectivo standard
                "notas": sale.notas or ""
            },
            "cliente": {
                "identificacion": sale.cliente.documento,
                "tipo_identificacion": "13" if sale.cliente.documento else "13", # Asumimos CC
                "nombre": sale.cliente.nombre
            },
            "detalles_productos": detalles_productos,
            "totales_impuestos": lista_impuestos,
            "resumen_factura": {
                "subtotal": float(round(subtotal_global, 2)),
                "total_impuestos": float(round(total_impuestos_global, 2)),
                "total_factura": float(round(total_factura_global, 2))
            }
        }
        
        return standard_json
