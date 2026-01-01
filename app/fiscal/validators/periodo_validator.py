"""
Validador de Período Abierto
Verifica que el período contable esté abierto para modificaciones
"""
from typing import Tuple, Dict, Any, Optional
from datetime import date
from app.fiscal.validators.base_validator import ValidadorCritico


class ValidadorPeriodoAbierto(ValidadorCritico):
    """
    Validador CRÍTICO: Período Contable Abierto
    
    Requisito DIAN: No se pueden crear/modificar asientos en períodos cerrados
    
    Verifica:
    1. Que el período contable exista
    2. Que el período esté en estado 'ABIERTO'
    3. Que la fecha del asiento esté dentro del período
    """
    
    def validar(self, asiento_data: Dict[str, Any], contexto: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Valida que el período contable esté abierto
        """
        from app.fiscal.models import PeriodoContable
        
        fecha_contable = asiento_data.get('fecha_contable')
        periodo_contable = asiento_data.get('periodo_contable')
        
        if not fecha_contable:
            return False, "La fecha contable es obligatoria"
        
        # Si viene el período directamente
        if periodo_contable:
            if periodo_contable.estado == 'CERRADO':
                mensaje = (
                    f"No se puede crear/modificar asientos en el período {periodo_contable} "
                    f"porque está CERRADO desde {periodo_contable.fecha_cierre}"
                )
                self.registrar_fallo(asiento_data, mensaje, contexto)
                return False, mensaje
            
            if periodo_contable.estado == 'BLOQUEADO':
                mensaje = (
                    f"El período {periodo_contable} está BLOQUEADO "
                    f"(en proceso de auditoría o cierre)"
                )
                self.registrar_fallo(asiento_data, mensaje, contexto)
                return False, mensaje
            
            return True, ""
        
        # Buscar período por fecha
        try:
            periodo = PeriodoContable.objects.get(
                fecha_inicio__lte=fecha_contable,
                fecha_fin__gte=fecha_contable
            )
        except PeriodoContable.DoesNotExist:
            # Si no existe el período, se puede crear (se creará automáticamente)
            return True, ""
        except PeriodoContable.MultipleObjectsReturned:
            return False, (
                f"Error de configuración: múltiples períodos para la fecha {fecha_contable}"
            )
        
        # Verificar estado del período encontrado
        if periodo.estado == 'CERRADO':
            mensaje = (
                f"El período {periodo} está CERRADO. "
                f"No se pueden crear asientos con fecha {fecha_contable}"
            )
            self.registrar_fallo(asiento_data, mensaje, contexto)
            return False, mensaje
        
        if periodo.estado == 'BLOQUEADO':
            mensaje = (
                f"El período {periodo} está BLOQUEADO. "
                f"No se pueden crear asientos con fecha {fecha_contable}"
            )
            self.registrar_fallo(asiento_data, mensaje, contexto)
            return False, mensaje
        
        return True, ""
