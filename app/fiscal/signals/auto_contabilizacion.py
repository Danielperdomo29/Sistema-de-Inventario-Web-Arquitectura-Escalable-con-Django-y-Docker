from django.db.models.signals import post_save
from django.dispatch import receiver
from app.models.sale import Sale as Venta
from app.models.purchase import Purchase as Compra
from app.fiscal.services.contador_automatico import ContadorAutomatico

@receiver(post_save, sender=Venta)
def crear_asiento_venta(sender, instance, created, **kwargs):
    """Crea asiento contable automáticamente al crear/actualizar venta"""
    # Solo procesar ventas completadas
    if instance.estado == 'completada':
        ContadorAutomatico.contabilizar_venta(instance)

@receiver(post_save, sender=Compra)
def crear_asiento_compra(sender, instance, created, **kwargs):
    """Crea asiento contable automáticamente al crear/actualizar compra"""
    # Placeholder para implementación futura
    if instance.estado == 'recibida': 
        pass
