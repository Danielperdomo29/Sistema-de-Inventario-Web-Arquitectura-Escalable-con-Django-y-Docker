from django.db import models

class Role(models.Model):
    """Modelo de Rol"""
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = 'roles'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
    
    def __str__(self):
        return self.nombre

    # Métodos estáticos para compatibilidad con controladores existentes
    @staticmethod
    def get_all():
        """Obtiene todos los roles"""
        return list(Role.objects.all().values('id', 'nombre', 'descripcion', 'created_at').order_by('nombre'))
    
    @staticmethod
    def get_by_id(role_id):
        """Obtiene un rol por su ID"""
        try:
            return Role.objects.values('id', 'nombre', 'descripcion').get(id=role_id)
        except Role.DoesNotExist:
            return None
    
    @staticmethod
    def count():
        """Cuenta el total de roles"""
        return Role.objects.count()
    
    @staticmethod
    def create(data):
        """Crea un nuevo rol"""
        role = Role.objects.create(
            nombre=data['nombre'],
            descripcion=data.get('descripcion', '')
        )
        return role.id
    
    @staticmethod
    def update(role_id, data):
        """Actualiza un rol existente"""
        return Role.objects.filter(id=role_id).update(
            nombre=data['nombre'],
            descripcion=data.get('descripcion', '')
        )
    
    @staticmethod
    def delete(role_id):
        """Elimina un rol (hard delete)"""
        return Role.objects.filter(id=role_id).delete()
