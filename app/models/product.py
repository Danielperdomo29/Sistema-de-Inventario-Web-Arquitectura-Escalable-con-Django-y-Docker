from django.db import models
from app.models.category import Category
from app.models.supplier import Supplier

class Product(models.Model):
    """Modelo de Producto"""
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, db_column='categoria_id', related_name='productos')
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    stock_minimo = models.IntegerField(default=10)
    stock_actual = models.IntegerField(default=0)
    proveedor = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, db_column='proveedor_id', related_name='productos')

    activo = models.BooleanField(default=True)
    
    # Campos Tributarios DIAN
    tax_type_id = models.CharField(max_length=4, default='01', verbose_name='Código Impuesto DIAN') # 01=IVA, 04=INC
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=19.00, verbose_name='Porcentaje Impuesto')
    is_tax_included = models.BooleanField(default=False, verbose_name='Impuesto incluido en precio')
    
    class Meta:
        db_table = 'productos'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def __str__(self):
        return self.nombre
    
    @staticmethod
    def get_all():
        """Obtiene todos los productos activos"""
        products = Product.objects.filter(activo=True).select_related('categoria').order_by('-id')
        data = []
        for p in products:
            data.append({
                'id': p.id,
                'codigo': p.codigo,
                'nombre': p.nombre,
                'descripcion': p.descripcion,
                'categoria_id': p.categoria_id,
                'categoria': p.categoria.nombre if p.categoria else None,
                'precio_compra': p.precio_compra,
                'precio_venta': p.precio_venta,
                'stock_minimo': p.stock_minimo,
                'stock_actual': p.stock_actual,
                'proveedor_id': p.proveedor_id,
                'activo': p.activo
            })
        return data
    
    @staticmethod
    def get_by_id(product_id):
        """Obtiene un producto por ID"""
        try:
            p = Product.objects.select_related('categoria').get(id=product_id)
            return {
                'id': p.id,
                'codigo': p.codigo,
                'nombre': p.nombre,
                'descripcion': p.descripcion,
                'categoria_id': p.categoria_id,
                'categoria': p.categoria.nombre if p.categoria else None,
                'precio_compra': p.precio_compra,
                'precio_venta': p.precio_venta,
                'stock_minimo': p.stock_minimo,
                'stock_actual': p.stock_actual,
                'proveedor_id': p.proveedor_id,
                'activo': p.activo
            }
        except Product.DoesNotExist:
            return None
    
    @staticmethod
    def count():
        """Cuenta el total de productos activos"""
        return Product.objects.filter(activo=True).count()
    
    @staticmethod
    def create(data):
        """Crea un nuevo producto"""
        p = Product.objects.create(
            codigo=data['codigo'],
            nombre=data['nombre'],
            descripcion=data.get('descripcion', ''),
            categoria_id=data['categoria_id'],
            precio_compra=data['precio_compra'],
            precio_venta=data['precio_venta'],
            stock_minimo=data.get('stock_minimo', 10),
            stock_actual=data.get('stock_actual', 0),
            proveedor_id=data.get('proveedor_id'),
            activo=data.get('activo', True)
        )
        return p.id
    
    @staticmethod
    def update(product_id, data):
        """Actualiza un producto existente"""
        return Product.objects.filter(id=product_id).update(
            codigo=data['codigo'],
            nombre=data['nombre'],
            descripcion=data.get('descripcion', ''),
            categoria_id=data['categoria_id'],
            precio_compra=data['precio_compra'],
            precio_venta=data['precio_venta'],
            stock_minimo=data.get('stock_minimo', 10),
            stock_actual=data.get('stock_actual', 0),
            proveedor_id=data.get('proveedor_id'),
            activo=data.get('activo', True)
        )
    
    @staticmethod
    def delete(product_id):
        """Elimina un producto (soft delete cambiando activo a 0)"""
        return Product.objects.filter(id=product_id).update(activo=False)
    
    @staticmethod
    def get_low_stock(limit=10):
        """Obtiene productos con stock bajo"""
        products = Product.objects.filter(stock_actual__lt=10, activo=True).select_related('categoria').order_by('stock_actual')[:limit]
        data = []
        for p in products:
            data.append({
                'id': p.id,
                'nombre': p.nombre,
                'stock_actual': p.stock_actual,
                'categoria': p.categoria.nombre if p.categoria else None
            })
        return data
