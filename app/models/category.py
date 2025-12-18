from django.db import models

class Category(models.Model):
    """Modelo de Categoría"""
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'categorias'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.nombre
    
    @staticmethod
    def get_all():
        """Obtiene todas las categorías"""
        return list(Category.objects.filter(activo=True).values('id', 'nombre', 'descripcion').order_by('nombre'))
    
    @staticmethod
    def get_by_id(category_id):
        """Obtiene una categoría por su ID"""
        try:
            return Category.objects.filter(id=category_id, activo=True).values('id', 'nombre', 'descripcion').first()
        except Exception:
            return None
    
    @staticmethod
    def count():
        """Cuenta el total de categorías"""
        return Category.objects.filter(activo=True).count()
    
    @staticmethod
    def create(data):
        """Crea una nueva categoría"""
        cat = Category.objects.create(
            nombre=data['nombre'],
            descripcion=data.get('descripcion', ''),
            activo=data.get('activo', True)
        )
        return cat.id
    
    @staticmethod
    def update(category_id, data):
        """Actualiza una categoría existente"""
        return Category.objects.filter(id=category_id).update(
            nombre=data['nombre'],
            descripcion=data.get('descripcion', ''),
            activo=data.get('activo', True)
        )
    
    @staticmethod
    def delete(category_id):
        """Elimina una categoría (soft delete cambiando activo a 0)"""
        return Category.objects.filter(id=category_id).update(activo=False)
