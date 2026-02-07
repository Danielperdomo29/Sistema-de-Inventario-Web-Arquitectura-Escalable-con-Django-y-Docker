"""
Django Signals para gestión automática de stock.
Garantiza que el stock se decremente/incremente automáticamente
al crear/eliminar ventas y compras.

Autor: Sistema de Inventario
Fecha: 2026-01-12
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone


@receiver(post_save, sender='app.SaleDetail')
def decrementar_stock_venta(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta DESPUÉS de guardar un SaleDetail.
    Decrementa automáticamente el stock del producto.
    
    Flujo:
    1. Usuario crea venta con 1 unidad de producto X
    2. Se guarda SaleDetail en BD
    3. Este signal se dispara automáticamente
    4. Decrementa Product.stock_actual
    5. Registra movimiento en HistorialStock
    6. Verifica si stock < stock_minimo y crea alerta
    
    Args:
        sender: Clase del modelo (SaleDetail)
        instance: Instancia del SaleDetail creado
        created: True si es creación, False si es actualización
        **kwargs: Argumentos adicionales del signal
    """
    if not created:  # Solo en creación, no en actualización
        return
    
    from app.models.product import Product
    from app.models.historial_stock import HistorialStock
    from app.models.alerta_automatica import AlertaAutomatica
    from django.core.cache import cache
    
    producto = instance.producto
    cantidad_vendida = instance.cantidad
    
    with transaction.atomic():
        # 1. Guardar stock anterior para auditoría
        stock_anterior = producto.stock_actual
        
        # 2. Decrementar stock
        producto.stock_actual -= cantidad_vendida
        
        # 3. Actualizar fecha de última venta
        if hasattr(producto, 'fecha_ultima_venta'):
            producto.fecha_ultima_venta = instance.venta.fecha
            producto.save(update_fields=['stock_actual', 'fecha_ultima_venta'])
        else:
            producto.save(update_fields=['stock_actual'])
        
        # 4. INVALIDAR CACHÉ de productos para que se vea el stock actualizado
        cache.delete('catalog:products:all')
        
        # 5. Registrar en historial (para analytics)
        HistorialStock.objects.create(
            producto=producto,
            tipo_movimiento='venta',
            cantidad=cantidad_vendida,
            stock_anterior=stock_anterior,
            stock_nuevo=producto.stock_actual,
            usuario=instance.venta.usuario,
            metadata={
                'venta_id': instance.venta.id,
                'numero_factura': instance.venta.numero_factura,
                'cliente': instance.venta.cliente.nombre,
                'precio_unitario': float(instance.precio_unitario),
                'subtotal': float(instance.subtotal)
            }
        )
        
        # 6. Verificar si necesita alerta de stock bajo
        if producto.stock_actual <= producto.stock_minimo:
            # Determinar nivel de alerta
            if producto.stock_actual <= 0:
                nivel = 'ROJO'
                tipo = 'STOCK_CRITICO'
                mensaje = f'CRÍTICO: {producto.nombre} SIN STOCK'
            else:
                nivel = 'AMARILLO'
                tipo = 'STOCK_BAJO'
                mensaje = f'Stock bajo: {producto.nombre} ({producto.stock_actual} unidades, mínimo: {producto.stock_minimo})'
            
            # Crear alerta (solo si no existe una pendiente para este producto)
            # get_or_create es atómico y thread-safe
            AlertaAutomatica.objects.get_or_create(
                producto=producto,
                tipo_alerta=tipo,
                estado='PENDIENTE',
                defaults={
                    'nivel': nivel,
                    'mensaje': mensaje,
                    'accion_sugerida': f'Aumentar stock del producto. Stock actual: {producto.stock_actual}, Mínimo requerido: {producto.stock_minimo}'
                }
            )


@receiver(post_delete, sender='app.SaleDetail')
def incrementar_stock_devolucion(sender, instance, **kwargs):
    """
    Signal que se ejecuta al ELIMINAR un SaleDetail.
    Incrementa el stock (devolución de venta).
    
    Args:
        sender: Clase del modelo (SaleDetail)
        instance: Instancia del SaleDetail eliminado
        **kwargs: Argumentos adicionales del signal
    """
    from app.models.product import Product
    from app.models.historial_stock import HistorialStock
    from app.models.alerta_automatica import AlertaAutomatica
    from django.core.cache import cache
    
    producto = instance.producto
    cantidad_devuelta = instance.cantidad
    
    with transaction.atomic():
        stock_anterior = producto.stock_actual
        producto.stock_actual += cantidad_devuelta
        producto.save(update_fields=['stock_actual'])
        
        # Invalidar caché
        cache.delete('catalog:products:all')
        
        # Registrar en historial
        HistorialStock.objects.create(
            producto=producto,
            tipo_movimiento='devolucion',
            cantidad=cantidad_devuelta,
            stock_anterior=stock_anterior,
            stock_nuevo=producto.stock_actual,
            usuario=instance.venta.usuario,
            metadata={
                'venta_id': instance.venta.id,
                'motivo': 'Eliminación de detalle de venta',
                'numero_factura': instance.venta.numero_factura
            }
        )
        
        # Resolver alertas de stock bajo si el stock ahora es suficiente
        if producto.stock_actual > producto.stock_minimo:
            AlertaAutomatica.objects.filter(
                producto=producto,
                tipo_alerta__in=['STOCK_BAJO', 'STOCK_CRITICO'],
                estado='PENDIENTE'
            ).update(
                estado='RESUELTA',
                fecha_resolucion=timezone.now()
            )


@receiver(post_save, sender='app.PurchaseDetail')
def incrementar_stock_compra(sender, instance, created, **kwargs):
    """
    Signal para incrementar stock al registrar compras.
    
    Args:
        sender: Clase del modelo (PurchaseDetail)
        instance: Instancia del PurchaseDetail creado
        created: True si es creación, False si es actualización
        **kwargs: Argumentos adicionales del signal
    """
    if not created:
        return
    
    from app.models.product import Product
    from app.models.historial_stock import HistorialStock
    from app.models.alerta_automatica import AlertaAutomatica
    from django.core.cache import cache
    
    producto = instance.producto
    cantidad_comprada = instance.cantidad
    
    with transaction.atomic():
        stock_anterior = producto.stock_actual
        producto.stock_actual += cantidad_comprada
        producto.save(update_fields=['stock_actual'])
        
        # Invalidar caché
        cache.delete('catalog:products:all')
        
        # Registrar en historial
        proveedor_nombre = None
        if hasattr(instance.compra, 'proveedor') and instance.compra.proveedor:
            proveedor_nombre = instance.compra.proveedor.nombre
        
        HistorialStock.objects.create(
            producto=producto,
            tipo_movimiento='compra',
            cantidad=cantidad_comprada,
            stock_anterior=stock_anterior,
            stock_nuevo=producto.stock_actual,
            usuario=instance.compra.usuario,
            metadata={
                'compra_id': instance.compra.id,
                'proveedor': proveedor_nombre,
                'precio_compra': float(instance.precio_compra) if hasattr(instance, 'precio_compra') else None
            }
        )
        
        # Resolver alertas de stock bajo si el stock ahora es suficiente
        if producto.stock_actual > producto.stock_minimo:
            AlertaAutomatica.objects.filter(
                producto=producto,
                tipo_alerta__in=['STOCK_BAJO', 'STOCK_CRITICO'],
                estado='PENDIENTE'
            ).update(
                estado='RESUELTA',
                fecha_resolucion=timezone.now()
            )


@receiver(post_delete, sender='app.PurchaseDetail')
def decrementar_stock_compra_eliminada(sender, instance, **kwargs):
    """
    Signal que se ejecuta al ELIMINAR un PurchaseDetail.
    Decrementa el stock (cancelación de compra).
    
    Args:
        sender: Clase del modelo (PurchaseDetail)
        instance: Instancia del PurchaseDetail eliminado
        **kwargs: Argumentos adicionales del signal
    """
    from app.models.product import Product
    from app.models.historial_stock import HistorialStock
    from django.core.cache import cache
    
    producto = instance.producto
    cantidad_cancelada = instance.cantidad
    
    with transaction.atomic():
        stock_anterior = producto.stock_actual
        producto.stock_actual -= cantidad_cancelada
        producto.save(update_fields=['stock_actual'])
        
        # Invalidar caché
        cache.delete('catalog:products:all')
        
        # Registrar en historial
        HistorialStock.objects.create(
            producto=producto,
            tipo_movimiento='ajuste',
            cantidad=-cantidad_cancelada,
            stock_anterior=stock_anterior,
            stock_nuevo=producto.stock_actual,
            usuario=instance.compra.usuario,
            metadata={
                'compra_id': instance.compra.id,
                'motivo': 'Cancelación de compra'
            }
        )
