"""
Signals para auditoría automática de modelos fiscales.

Registra automáticamente todas las operaciones sobre modelos fiscales.
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from threading import local

from app.fiscal.models.perfil_fiscal import PerfilFiscal
from app.fiscal.models.cuenta_contable import CuentaContable
from app.fiscal.models.impuesto import Impuesto
from app.fiscal.models.audit_log import FiscalAuditLog


# Thread-local storage para request
_thread_locals = local()


def set_current_request(request):
    """Guarda el request actual en thread-local storage"""
    _thread_locals.request = request


def get_current_request():
    """Obtiene el request actual"""
    return getattr(_thread_locals, 'request', None)


# Store para valores anteriores
_old_values_store = {}


@receiver(pre_save, sender=PerfilFiscal)
@receiver(pre_save, sender=CuentaContable)
@receiver(pre_save, sender=Impuesto)
def store_old_values(sender, instance, **kwargs):
    """Guarda valores anteriores antes de actualizar"""
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            _old_values_store[f"{sender.__name__}_{instance.pk}"] = model_to_dict(
                old_instance,
                exclude=['fecha_creacion', 'fecha_actualizacion']
            )
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=PerfilFiscal)
@receiver(post_save, sender=CuentaContable)
@receiver(post_save, sender=Impuesto)
def audit_model_save(sender, instance, created, **kwargs):
    """Audita creación y actualización de modelos fiscales"""
    request = get_current_request()
    
    # Si no hay request (ej: desde shell), usar usuario del sistema
    if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
        return  # No auditar operaciones sin usuario
    
    model_name = sender.__name__
    action = 'CREATE' if created else 'UPDATE'
    
    new_values = model_to_dict(
        instance,
        exclude=['fecha_creacion', 'fecha_actualizacion']
    )
    
    old_values = None
    changes = None
    
    if not created:
        # Es una actualización
        key = f"{model_name}_{instance.pk}"
        old_values = _old_values_store.get(key)
        
        if old_values:
            # Calcular cambios
            changes = {}
            for field, new_value in new_values.items():
                old_value = old_values.get(field)
                if old_value != new_value:
                    changes[field] = {
                        'old': str(old_value) if old_value is not None else None,
                        'new': str(new_value) if new_value is not None else None
                    }
            
            # Limpiar del store
            del _old_values_store[key]
    
    # Crear log de auditoría
    try:
        FiscalAuditLog.log_action(
            action=action,
            model_name=model_name,
            object_id=instance.pk,
            user=request.user,
            request=request,
            old_values=old_values,
            new_values=new_values,
            changes=changes,
            success=True
        )
    except Exception as e:
        # No fallar la operación principal si falla el audit log
        import logging
        logger = logging.getLogger('fiscal_audit')
        logger.error(f"Error creating audit log: {e}")


@receiver(post_delete, sender=PerfilFiscal)
@receiver(post_delete, sender=CuentaContable)
@receiver(post_delete, sender=Impuesto)
def audit_model_delete(sender, instance, **kwargs):
    """Audita eliminación de modelos fiscales"""
    request = get_current_request()
    
    if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
        return
    
    model_name = sender.__name__
    
    old_values = model_to_dict(
        instance,
        exclude=['fecha_creacion', 'fecha_actualizacion']
    )
    
    try:
        FiscalAuditLog.log_action(
            action='DELETE',
            model_name=model_name,
            object_id=instance.pk,
            user=request.user,
            request=request,
            old_values=old_values,
            success=True
        )
    except Exception as e:
        import logging
        logger = logging.getLogger('fiscal_audit')
        logger.error(f"Error creating delete audit log: {e}")
