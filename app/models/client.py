from django.db import models

class Client(models.Model):
    """Modelo de Cliente"""
    nombre = models.CharField(max_length=200)
    documento = models.CharField(max_length=50, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return self.nombre
    
    @staticmethod
    def get_all():
        """Obtiene todos los clientes activos"""
        return list(Client.objects.filter(activo=True).values('id', 'nombre', 'documento', 'telefono', 'email', 'direccion').order_by('nombre'))
    
    @staticmethod
    def get_by_id(client_id):
        """Obtiene un cliente por su ID"""
        try:
            return Client.objects.filter(id=client_id, activo=True).values('id', 'nombre', 'documento', 'telefono', 'email', 'direccion').first()
        except Exception:
            return None
    
    @staticmethod
    def count():
        """Cuenta el total de clientes activos"""
        return Client.objects.filter(activo=True).count()
    
    @staticmethod
    def create(data):
        """Crea un nuevo cliente"""
        client = Client.objects.create(
            nombre=data['nombre'],
            documento=data.get('documento', ''),
            telefono=data.get('telefono', ''),
            email=data.get('email', ''),
            direccion=data.get('direccion', ''),
            activo=data.get('activo', True)
        )
        return client.id
    
    @staticmethod
    def update(client_id, data):
        """Actualiza un cliente existente"""
        return Client.objects.filter(id=client_id).update(
            nombre=data['nombre'],
            documento=data.get('documento', ''),
            telefono=data.get('telefono', ''),
            email=data.get('email', ''),
            direccion=data.get('direccion', ''),
            activo=data.get('activo', True)
        )
    
    @staticmethod
    def delete(client_id):
        """Elimina un cliente (soft delete cambiando activo a 0)"""
        return Client.objects.filter(id=client_id).update(activo=False)
