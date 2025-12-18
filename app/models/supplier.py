from django.db import models

class Supplier(models.Model):
    """Modelo de Proveedor"""
    nombre = models.CharField(max_length=200)
    ruc = models.CharField(max_length=50, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'proveedores'
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'

    def __str__(self):
        return self.nombre
    
    @staticmethod
    def get_all():
        """Obtener todos los proveedores activos"""
        return list(Supplier.objects.filter(activo=True).values().order_by('nombre'))
    
    @staticmethod
    def get_by_id(supplier_id):
        """Obtener un proveedor por ID"""
        try:
            return Supplier.objects.filter(id=supplier_id, activo=True).values().first()
        except Exception:
            return None
    
    @staticmethod
    def count():
        """Contar total de proveedores activos"""
        return Supplier.objects.filter(activo=True).count()
    
    @staticmethod
    def create(data):
        """Crear un nuevo proveedor"""
        supplier = Supplier.objects.create(
            nombre=data['nombre'],
            ruc=data.get('ruc', ''),
            telefono=data.get('telefono', ''),
            email=data.get('email', ''),
            direccion=data.get('direccion', ''),
             activo=True
        )
        return supplier.id
    
    @staticmethod
    def update(supplier_id, data):
        """Actualizar un proveedor"""
        return Supplier.objects.filter(id=supplier_id).update(
            nombre=data['nombre'],
            ruc=data.get('ruc', ''),
            telefono=data.get('telefono', ''),
            email=data.get('email', ''),
            direccion=data.get('direccion', '')
        )
    
    @staticmethod
    def delete(supplier_id):
        """Eliminar lógicamente un proveedor"""
        return Supplier.objects.filter(id=supplier_id).update(activo=False)
