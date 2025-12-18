from django.db import models
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.user_account import UserAccount

class InventoryMovement(models.Model):
    """Modelo de Movimiento de Inventario"""
    producto = models.ForeignKey(Product, on_delete=models.CASCADE, db_column='producto_id')
    almacen = models.ForeignKey(Warehouse, on_delete=models.CASCADE, db_column='almacen_id')
    # tipo_movimiento: 'entrada', 'salida', 'transferencia'
    tipo_movimiento = models.CharField(max_length=20)
    cantidad = models.IntegerField()
    usuario = models.ForeignKey(UserAccount, on_delete=models.PROTECT, db_column='usuario_id')
    referencia = models.CharField(max_length=100, blank=True, null=True)
    motivo = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'movimientos_inventario'
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'
    
    @staticmethod
    def get_all():
        """Obtener todos los movimientos de inventario"""
        movements = InventoryMovement.objects.select_related('producto', 'almacen', 'usuario').order_by('-fecha', '-id')
        data = []
        for m in movements:
            data.append({
                'id': m.id,
                'producto_id': m.producto_id,
                'almacen_id': m.almacen_id,
                'tipo_movimiento': m.tipo_movimiento,
                'cantidad': m.cantidad,
                'usuario_id': m.usuario_id,
                'referencia': m.referencia,
                'motivo': m.motivo,
                'fecha': m.fecha,
                'producto_nombre': m.producto.nombre,
                'almacen_nombre': m.almacen.nombre,
                'usuario_nombre': m.usuario.username
            })
        return data
    
    @staticmethod
    def get_by_id(movement_id):
        """Obtener un movimiento por ID"""
        try:
            m = InventoryMovement.objects.select_related('producto', 'almacen', 'usuario').get(id=movement_id)
            return {
                'id': m.id,
                'producto_id': m.producto_id,
                'almacen_id': m.almacen_id,
                'tipo_movimiento': m.tipo_movimiento,
                'cantidad': m.cantidad,
                'usuario_id': m.usuario_id,
                'referencia': m.referencia,
                'motivo': m.motivo,
                'fecha': m.fecha,
                'producto_nombre': m.producto.nombre,
                'almacen_nombre': m.almacen.nombre,
                'usuario_nombre': m.usuario.username
            }
        except InventoryMovement.DoesNotExist:
            return None
    
    @staticmethod
    def count():
        return InventoryMovement.objects.count()
    
    @staticmethod
    def create(data):
        """Crear un nuevo movimiento de inventario"""
        m = InventoryMovement.objects.create(
            producto_id=data['producto_id'],
            almacen_id=data['almacen_id'],
            tipo_movimiento=data['tipo_movimiento'],
            cantidad=data['cantidad'],
            usuario_id=data['usuario_id'],
            referencia=data.get('referencia', ''),
            motivo=data.get('motivo', '')
        )
        return m.id
    
    @staticmethod
    def update(movement_id, data):
        """Actualizar un movimiento de inventario"""
        return InventoryMovement.objects.filter(id=movement_id).update(
            producto_id=data['producto_id'],
            almacen_id=data['almacen_id'],
            tipo_movimiento=data['tipo_movimiento'],
            cantidad=data['cantidad'],
            referencia=data.get('referencia', ''),
            motivo=data.get('motivo', '')
        )
    
    @staticmethod
    def delete(movement_id):
        """Eliminar un movimiento de inventario"""
        return InventoryMovement.objects.filter(id=movement_id).delete()
    
    @staticmethod
    def get_by_product(product_id):
        """Obtener movimientos por producto"""
        movements = InventoryMovement.objects.filter(producto_id=product_id).select_related('almacen', 'usuario').order_by('-fecha')
        data = []
        for m in movements:
            data.append({
                'id': m.id,
                'almacen_nombre': m.almacen.nombre,
                'usuario_nombre': m.usuario.username,
                # Add other fields if needed by view
                 'tipo_movimiento': m.tipo_movimiento,
                 'cantidad': m.cantidad,
                 'fecha': m.fecha,
                 'referencia': m.referencia,
                 'motivo': m.motivo
            })
        return data
    
    @staticmethod
    def get_by_warehouse(warehouse_id):
        """Obtener movimientos por almacén"""
        movements = InventoryMovement.objects.filter(almacen_id=warehouse_id).select_related('producto', 'usuario').order_by('-fecha')
        data = []
        for m in movements:
            data.append({
                'id': m.id,
                'producto_nombre': m.producto.nombre,
                'usuario_nombre': m.usuario.username,
                 'tipo_movimiento': m.tipo_movimiento,
                 'cantidad': m.cantidad,
                 'fecha': m.fecha,
                 'referencia': m.referencia,
                 'motivo': m.motivo
            })
        return data
