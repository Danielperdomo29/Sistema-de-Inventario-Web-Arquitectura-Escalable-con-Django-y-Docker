"""
Modelo FiscalAuditLog - Registro de auditoría para operaciones fiscales.

Cumple con requisitos DIAN de trazabilidad y retención de 7 años.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


User = get_user_model()


class FiscalAuditLog(models.Model):
    """
    Registro de auditoría para operaciones fiscales.
    
    Registra TODAS las operaciones sobre datos fiscales para cumplir con:
    - Requisitos DIAN de trazabilidad
    - Retención de 7 años
    - Auditorías internas y externas
    
    Attributes:
        action: Tipo de acción (CREATE, UPDATE, DELETE, VIEW)
        model_name: Nombre del modelo afectado
        object_id: ID del objeto afectado
        user: Usuario que realizó la acción
        user_ip: IP del usuario
        user_agent: User agent del navegador
        timestamp: Momento exacto de la acción
        old_values: Valores anteriores (para UPDATE)
        new_values: Valores nuevos (para CREATE/UPDATE)
        changes: Cambios específicos (para UPDATE)
        session_id: ID de sesión
        request_path: Ruta de la petición
        success: Si la operación fue exitosa
        error_message: Mensaje de error si falló
    
    Examples:
        >>> FiscalAuditLog.objects.create(
        ...     action='UPDATE',
        ...     model_name='PerfilFiscal',
        ...     object_id='123',
        ...     user=request.user,
        ...     user_ip='192.168.1.1',
        ...     changes={'numero_documento': {'old': '123', 'new': '456'}}
        ... )
    """
    
    # Choices
    ACTION_CHOICES = [
        ('CREATE', 'Crear'),
        ('UPDATE', 'Actualizar'),
        ('DELETE', 'Eliminar'),
        ('VIEW', 'Ver'),
        ('EXPORT', 'Exportar'),
    ]
    
    # Qué se hizo
    action = models.CharField(
        max_length=10,
        choices=ACTION_CHOICES,
        db_index=True,
        help_text='Tipo de acción realizada'
    )
    
    model_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text='Nombre del modelo afectado'
    )
    
    object_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text='ID del objeto afectado'
    )
    
    # Quién lo hizo
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='fiscal_audit_logs',
        help_text='Usuario que realizó la acción'
    )
    
    user_ip = models.GenericIPAddressField(
        help_text='Dirección IP del usuario'
    )
    
    user_agent = models.TextField(
        blank=True,
        help_text='User agent del navegador'
    )
    
    # Cuándo
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text='Momento exacto de la acción'
    )
    
    # Detalles de los cambios
    old_values = models.JSONField(
        null=True,
        blank=True,
        help_text='Valores anteriores (para UPDATE/DELETE)'
    )
    
    new_values = models.JSONField(
        null=True,
        blank=True,
        help_text='Valores nuevos (para CREATE/UPDATE)'
    )
    
    changes = models.JSONField(
        null=True,
        blank=True,
        help_text='Cambios específicos con old/new'
    )
    
    # Contexto de la petición
    session_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='ID de sesión'
    )
    
    request_path = models.CharField(
        max_length=500,
        blank=True,
        help_text='Ruta de la petición HTTP'
    )
    
    request_method = models.CharField(
        max_length=10,
        blank=True,
        help_text='Método HTTP (GET, POST, etc.)'
    )
    
    # Resultado
    success = models.BooleanField(
        default=True,
        help_text='Si la operación fue exitosa'
    )
    
    error_message = models.TextField(
        blank=True,
        help_text='Mensaje de error si falló'
    )
    
    # Metadata adicional
    notes = models.TextField(
        blank=True,
        help_text='Notas adicionales'
    )
    
    class Meta:
        db_table = 'fiscal_audit_log'
        verbose_name = 'Registro de Auditoría Fiscal'
        verbose_name_plural = 'Registros de Auditoría Fiscal'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action} - {self.model_name}:{self.object_id} by {self.user.username} at {self.timestamp}"
    
    @classmethod
    def log_action(cls, action, model_name, object_id, user, request=None, 
                   old_values=None, new_values=None, changes=None, 
                   success=True, error_message=''):
        """
        Método helper para crear logs de auditoría fácilmente.
        
        Args:
            action: Tipo de acción (CREATE, UPDATE, DELETE, VIEW)
            model_name: Nombre del modelo
            object_id: ID del objeto
            user: Usuario que realiza la acción
            request: Objeto request de Django (opcional)
            old_values: Valores anteriores
            new_values: Valores nuevos
            changes: Diccionario de cambios
            success: Si fue exitosa
            error_message: Mensaje de error
        
        Returns:
            FiscalAuditLog: Instancia creada
        """
        # Extraer información del request si está disponible
        user_ip = '0.0.0.0'
        user_agent = ''
        session_id = ''
        request_path = ''
        request_method = ''
        
        if request:
            user_ip = cls.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            session_id = request.session.session_key or ''
            request_path = request.path[:500]
            request_method = request.method
        
        return cls.objects.create(
            action=action,
            model_name=model_name,
            object_id=str(object_id),
            user=user,
            user_ip=user_ip,
            user_agent=user_agent,
            session_id=session_id,
            request_path=request_path,
            request_method=request_method,
            old_values=old_values,
            new_values=new_values,
            changes=changes,
            success=success,
            error_message=error_message
        )
    
    @staticmethod
    def get_client_ip(request):
        """Obtiene la IP real del cliente considerando proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @classmethod
    def get_object_history(cls, model_name, object_id):
        """
        Obtiene el historial completo de un objeto.
        
        Args:
            model_name: Nombre del modelo
            object_id: ID del objeto
        
        Returns:
            QuerySet: Logs ordenados por timestamp
        """
        return cls.objects.filter(
            model_name=model_name,
            object_id=str(object_id)
        ).order_by('-timestamp')
    
    @classmethod
    def get_user_activity(cls, user, start_date=None, end_date=None):
        """
        Obtiene la actividad de un usuario en un rango de fechas.
        
        Args:
            user: Usuario
            start_date: Fecha inicio (opcional)
            end_date: Fecha fin (opcional)
        
        Returns:
            QuerySet: Logs del usuario
        """
        queryset = cls.objects.filter(user=user)
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset.order_by('-timestamp')
