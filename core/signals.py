"""
Core Signals - Integración de eventos con módulos existentes

IMPORTANTE: Estas señales NO modifican la lógica existente,
solo agregan eventos para los nuevos módulos (Contabilidad, Analytics, IA).

En caso de error, las excepciones NO se propagan para no romper
el flujo existente del sistema.
"""

import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

logger = logging.getLogger(__name__)


def _safe_publish_event(event_type: str, data: dict, persistent: bool = False):
    """
    Publica evento de forma segura sin propagar excepciones

    Esta función existe para garantizar que el sistema existente
    no se vea afectado por errores en el EventBus.
    """
    try:
        from core.event_bus import EventTypes, event_bus

        if event_bus:
            event_bus.publish(event_type, data, persistent=persistent)
            logger.debug(f"✅ Evento publicado: {event_type}")

    except ImportError:
        logger.debug("EventBus no disponible, ignorando evento")
    except Exception as e:
        # NUNCA propagar excepciones - No romper flujo existente
        logger.error(f"⚠️  Error publicando evento {event_type}: {e}")


# =============================================================================
# Señales para Ventas
# =============================================================================


@receiver(post_save, sender="app.Sale")
def publicar_evento_venta(sender, instance, created, **kwargs):
    """
    Publica evento cuando se crea/actualiza una venta

    Eventos publicados:
    - VENTA_REGISTRADA: Cuando se crea una venta completada
    - VENTA_ANULADA: Cuando una venta cambia a estado anulada
    """
    try:
        from core.event_bus import EventTypes

        if created:
            # Nueva venta
            event_data = {
                "venta_id": instance.id,
                "cliente_id": instance.cliente_id if hasattr(instance, "cliente_id") else None,
                "total": float(instance.total) if instance.total else 0,
                "fecha": (
                    instance.fecha.isoformat()
                    if hasattr(instance.fecha, "isoformat")
                    else str(instance.fecha or timezone.now())
                ),
                "usuario_id": instance.usuario_id if hasattr(instance, "usuario_id") else None,
                "estado": getattr(instance, "estado", "COMPLETADA"),
            }

            estado = getattr(instance, "estado", "COMPLETADA")
            if estado in ["COMPLETADA", "PAGADA"]:
                _safe_publish_event(EventTypes.VENTA_REGISTRADA, event_data, persistent=True)
                logger.info(f"📤 Evento VENTA_REGISTRADA para venta #{instance.id}")

        else:
            # Actualización de venta existente
            estado = getattr(instance, "estado", None)

            if estado == "ANULADA":
                event_data = {
                    "venta_id": instance.id,
                    "motivo": getattr(instance, "motivo_anulacion", "No especificado"),
                    "fecha_anulacion": timezone.now().isoformat(),
                }
                _safe_publish_event(EventTypes.VENTA_ANULADA, event_data)
                logger.info(f"📤 Evento VENTA_ANULADA para venta #{instance.id}")

    except Exception as e:
        # NO propagar - No romper flujo existente
        logger.error(f"Error en señal de venta: {e}")


# =============================================================================
# Señales para Inventario
# =============================================================================


@receiver(post_save, sender="app.Product")
def publicar_evento_producto(sender, instance, created, **kwargs):
    """
    Publica evento cuando se crea/actualiza un producto

    Eventos publicados:
    - PRODUCTO_CREADO: Cuando se crea un nuevo producto
    - STOCK_BAJO_DETECTADO: Cuando el stock baja del mínimo
    """
    try:
        from core.event_bus import EventTypes

        if created:
            event_data = {
                "producto_id": instance.id,
                "nombre": instance.nombre,
                "codigo": getattr(instance, "codigo", ""),
                "stock_inicial": getattr(instance, "stock", 0),
            }
            _safe_publish_event(EventTypes.PRODUCTO_CREADO, event_data)

        else:
            # Verificar si stock está bajo
            stock = getattr(instance, "stock", 0)
            stock_minimo = getattr(instance, "stock_minimo", 0)

            if stock <= stock_minimo and stock_minimo > 0:
                event_data = {
                    "producto_id": instance.id,
                    "nombre": instance.nombre,
                    "stock_actual": stock,
                    "stock_minimo": stock_minimo,
                    "diferencia": stock_minimo - stock,
                }
                _safe_publish_event(EventTypes.STOCK_BAJO_DETECTADO, event_data)

    except Exception as e:
        logger.error(f"Error en señal de producto: {e}")


# =============================================================================
# Señales para Compras
# =============================================================================


@receiver(post_save, sender="app.Purchase")
def publicar_evento_compra(sender, instance, created, **kwargs):
    """
    Publica evento cuando se registra una compra

    Eventos publicados:
    - COMPRA_REGISTRADA: Cuando se crea una nueva compra
    """
    try:
        from core.event_bus import EventTypes

        if created:
            event_data = {
                "compra_id": instance.id,
                "proveedor_id": getattr(instance, "proveedor_id", None),
                "total": float(instance.total) if hasattr(instance, "total") else 0,
                "fecha": instance.fecha.isoformat() if hasattr(instance, "fecha") else timezone.now().isoformat(),
            }
            _safe_publish_event(EventTypes.COMPRA_REGISTRADA, event_data)

    except Exception as e:
        logger.error(f"Error en señal de compra: {e}")


# =============================================================================
# Señales para Alertas (Sistema Existente)
# =============================================================================


@receiver(post_save, sender="app.AlertaAutomatica")
def publicar_evento_alerta(sender, instance, created, **kwargs):
    """
    Publica evento cuando se genera una alerta automática

    Este evento permite que el módulo de IA reaccione a alertas.
    """
    try:
        from core.event_bus import EventTypes

        if created:
            event_data = {
                "alerta_id": instance.id,
                "tipo": instance.tipo_alerta,
                "mensaje": instance.mensaje,
                "producto_id": instance.producto_id,
                "fecha": instance.fecha_creacion.isoformat(),
            }
            _safe_publish_event(EventTypes.STOCK_BAJO_DETECTADO, event_data)

    except Exception as e:
        logger.error(f"Error en señal de alerta: {e}")


# =============================================================================
# Funciones de utilidad para publicación manual de eventos
# =============================================================================


def publicar_evento_sistema(tipo: str, mensaje: str, datos: dict = None):
    """
    Función de utilidad para publicar eventos del sistema manualmente

    Uso:
        from core.signals import publicar_evento_sistema
        publicar_evento_sistema('BACKUP_COMPLETADO', 'Backup exitoso', {'archivo': 'backup.sql'})
    """
    from core.event_bus import EventTypes

    event_data = {"tipo": tipo, "mensaje": mensaje, "datos": datos or {}, "timestamp": timezone.now().isoformat()}

    _safe_publish_event(EventTypes.SISTEMA_INICIADO, event_data)


def publicar_error_critico(error: str, modulo: str, detalles: dict = None):
    """
    Publica evento de error crítico para monitoreo

    Uso:
        from core.signals import publicar_error_critico
        publicar_error_critico('DB Connection Failed', 'database', {'retry_count': 3})
    """
    from core.event_bus import EventTypes

    event_data = {"error": error, "modulo": modulo, "detalles": detalles or {}, "timestamp": timezone.now().isoformat()}

    _safe_publish_event(EventTypes.ERROR_CRITICO, event_data, persistent=True)
