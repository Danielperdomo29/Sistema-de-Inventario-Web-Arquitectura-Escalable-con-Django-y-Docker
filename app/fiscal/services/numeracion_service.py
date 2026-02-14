"""
Servicio de gestión de numeración de facturas electrónicas.
Maneja la asignación de consecutivos dentro de rangos autorizados por la DIAN.
"""

import logging
from decimal import Decimal
from typing import Optional, Tuple

from django.core.exceptions import ValidationError
from django.core.mail import mail_admins
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from app.fiscal.models import RangoNumeracion

logger = logging.getLogger(__name__)


class NumeracionService:
    """
    Servicio para gestión de numeración de facturas electrónicas.

    Maneja:
    - Asignación de consecutivos
    - Validación de disponibilidad
    - Alertas de agotamiento
    - Concurrencia (transacciones)
    """

    @staticmethod
    @transaction.atomic
    def obtener_siguiente_numero(fiscal_config_id: int, prefijo: Optional[str] = None) -> Tuple[str, RangoNumeracion]:
        """
        Obtiene y reserva el próximo número de factura disponible.

        Args:
            fiscal_config_id: ID de la configuración fiscal
            prefijo: Prefijo específico. Si es None, usa el rango por defecto

        Returns:
            Tuple (numero_formateado, rango_utilizado)

        Raises:
            ValidationError: Si no hay rangos disponibles

        Thread-safe mediante select_for_update()
        """
        # Construir query base
        query = RangoNumeracion.objects.filter(fiscal_config_id=fiscal_config_id, estado="activo").select_for_update()

        # Filtrar por prefijo o usar el por defecto
        if prefijo:
            query = query.filter(prefijo=prefijo)
        else:
            query = query.filter(is_default=True)

        # Ordenar por fecha de inicio (usar el más reciente primero)
        query = query.order_by("-fecha_inicio_vigencia")

        # Obtener rango disponible
        rango = query.first()

        if not rango:
            error_msg = f"No hay rangos activos disponibles"
            if prefijo:
                error_msg += f" para el prefijo '{prefijo}'"
            logger.error(f"NumeracionService: {error_msg}")
            raise ValidationError(_(error_msg))

        # Validar que el rango puede asignar
        if not rango.puede_asignar():
            logger.error(
                f"Rango {rango.id} no puede asignar números. "
                f"Estado: {rango.estado}, Vigente: {rango.esta_vigente()}"
            )
            raise ValidationError(_("El rango seleccionado no puede asignar números actualmente"))

        # Obtener número actual
        numero = rango.consecutivo_actual

        # Formatear número con prefijo
        numero_formateado = rango.formato_numero(numero)

        # Incrementar consecutivo
        rango.consecutivo_actual += 1

        # Actualizar estado automáticamente (si se agotó)
        rango._actualizar_estado()

        # Guardar cambios
        rango.save()

        logger.info(
            f"Asignado número {numero_formateado} del rango {rango.id}. "
            f"Consecutivo actual: {rango.consecutivo_actual}"
        )

        # Verificar si requiere alerta
        if rango.requiere_alerta:
            NumeracionService._enviar_alerta_agotamiento(rango)

        return numero_formateado, rango

    @staticmethod
    def validar_disponibilidad(fiscal_config_id: int, prefijo: Optional[str] = None) -> dict:
        """
        Valida la disponibilidad de números en los rangos.

        Args:
            fiscal_config_id: ID de la configuración fiscal
            prefijo: Prefijo específico. Si es None, revisa todos

        Returns:
            Dict con información de disponibilidad:
            {
                'disponible': bool,
                'numeros_restantes': int,
                'porcentaje_uso': Decimal,
                'rango_activo': RangoNumeracion or None,
                'mensaje': str
            }
        """
        query = RangoNumeracion.objects.filter(fiscal_config_id=fiscal_config_id, estado="activo")

        if prefijo:
            query = query.filter(prefijo=prefijo)
        else:
            query = query.filter(is_default=True)

        rango = query.order_by("-fecha_inicio_vigencia").first()

        if not rango:
            return {
                "disponible": False,
                "numeros_restantes": 0,
                "porcentaje_uso": Decimal("0"),
                "rango_activo": None,
                "mensaje": "No hay rangos activos disponibles",
            }

        disponibles = rango.numeros_disponibles
        porcentaje = rango.porcentaje_uso

        # Determinar mensaje
        if disponibles == 0:
            mensaje = "Rango agotado"
        elif porcentaje >= 90:
            mensaje = f"Quedan solo {disponibles} números disponibles (crítico)"
        elif porcentaje >= 70:
            mensaje = f"Quedan {disponibles} números disponibles (atención)"
        else:
            mensaje = f"{disponibles} números disponibles"

        return {
            "disponible": rango.puede_asignar(),
            "numeros_restantes": disponibles,
            "porcentaje_uso": porcentaje,
            "rango_activo": rango,
            "mensaje": mensaje,
        }

    @staticmethod
    def _enviar_alerta_agotamiento(rango: RangoNumeracion):
        """
        Envía alerta a administradores sobre agotamiento de rango.

        Args:
            rango: Instancia de RangoNumeracion
        """
        if rango.alerta_enviada:
            return

        porcentaje = rango.porcentaje_uso
        disponibles = rango.numeros_disponibles

        subject = f"⚠️ Alerta: Rango de Numeración DIAN próximo a agotarse"

        message = f"""
        El rango de numeración está próximo a agotarse:
        
        Detalles:
        - Prefijo: {rango.prefijo}
        - Resolución: {rango.numero_resolucion}
        - Rango: {rango.rango_desde} - {rango.rango_hasta}
        - Consecutivo Actual: {rango.consecutivo_actual}
        - Números Disponibles: {disponibles}
        - Porcentaje de Uso: {porcentaje:.2f}%
        - Fecha Fin Vigencia: {rango.fecha_fin_vigencia}
        
        ACCIÓN REQUERIDA:
        Solicite un nuevo rango de numeración a la DIAN antes de que se agote el actual.
        """

        try:
            mail_admins(subject=subject, message=message, fail_silently=True)

            # Marcar alerta como enviada
            rango.alerta_enviada = True
            rango.save(update_fields=["alerta_enviada"])

            logger.warning(
                f"Alerta de agotamiento enviada para rango {rango.id}. "
                f"Disponibles: {disponibles} ({porcentaje:.2f}% usado)"
            )

        except Exception as e:
            logger.error(f"Error al enviar alerta de agotamiento: {e}")

    @staticmethod
    def obtener_rango_activo(fiscal_config_id: int, prefijo: Optional[str] = None) -> Optional[RangoNumeracion]:
        """
        Obtiene el rango activo actual sin modificarlo.

        Args:
            fiscal_config_id: ID de la configuración fiscal
            prefijo: Prefijo específico

        Returns:
            RangoNumeracion o None
        """
        query = RangoNumeracion.objects.filter(fiscal_config_id=fiscal_config_id, estado="activo")

        if prefijo:
            query = query.filter(prefijo=prefijo)
        else:
            query = query.filter(is_default=True)

        return query.order_by("-fecha_inicio_vigencia").first()

    @staticmethod
    def validar_numero_en_rango(numero: int, rango_id: int) -> bool:
        """
        Valida si un número está dentro de un rango específico.

        Args:
            numero: Número a validar
            rango_id: ID del rango

        Returns:
            True si el número está en el rango
        """
        try:
            rango = RangoNumeracion.objects.get(id=rango_id)
            return rango.rango_desde <= numero <= rango.rango_hasta
        except RangoNumeracion.DoesNotExist:
            return False

    @staticmethod
    def estadisticas_uso() -> dict:
        """
        Obtiene estadísticas de uso de todos los rangos activos.

        Returns:
            Dict con estadísticas generales
        """
        rangos_activos = RangoNumeracion.objects.filter(estado="activo")

        total_rangos = rangos_activos.count()
        total_disponibles = sum(r.numeros_disponibles for r in rangos_activos)

        criticos = rangos_activos.filter(consecutivo_actual__gte=models.F("rango_hasta") * 0.9).count()

        return {
            "rangos_activos": total_rangos,
            "numeros_disponibles_total": total_disponibles,
            "rangos_criticos": criticos,
            "rangos": [
                {
                    "prefijo": r.prefijo,
                    "disponibles": r.numeros_disponibles,
                    "porcentaje_uso": float(r.porcentaje_uso),
                    "vigente_hasta": r.fecha_fin_vigencia,
                }
                for r in rangos_activos
            ],
        }
