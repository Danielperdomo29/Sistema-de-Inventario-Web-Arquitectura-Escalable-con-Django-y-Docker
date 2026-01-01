"""
Validador de Secuencia Numérica
Verifica numeración consecutiva de asientos por año
"""
from typing import Tuple, Dict, Any, Optional
from app.fiscal.validators.base_validator import ValidadorCritico


class ValidadorSecuenciaNumerica(ValidadorCritico):
    """
    Validador CRÍTICO: Secuencia Numérica Consecutiva
    
    Requisito DIAN: Los asientos deben tener numeración consecutiva
    sin saltos ni duplicados
    """
    
    def validar(self, asiento_data: Dict[str, Any], contexto: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Valida que el número de asiento sea consecutivo
        """
        from app.fiscal.models import AsientoContable
        from django.db.models import Max
        
        numero_asiento = asiento_data.get('numero_asiento')
        fecha_contable = asiento_data.get('fecha_contable')
        modo = contexto.get('modo', 'creacion') if contexto else 'creacion'
        
        if not numero_asiento:
            return False, "El número de asiento es obligatorio"
        
        # En modo modificación, permitir el mismo número
        if modo == 'modificacion':
            asiento_id = asiento_data.get('id')
            if asiento_id:
                asiento_existente = AsientoContable.objects.filter(
                    id=asiento_id,
                    numero_asiento=numero_asiento
                ).exists()
                if asiento_existente:
                    return True, ""  # Es el mismo asiento
        
        # Verificar que no exista el número
        if AsientoContable.objects.filter(numero_asiento=numero_asiento).exists():
            return False, f"El número de asiento {numero_asiento} ya existe"
        
        # Obtener el último número del año
        año = fecha_contable.year if fecha_contable else None
        if año:
            ultimo_numero = AsientoContable.objects.filter(
                fecha_contable__year=año
            ).aggregate(Max('numero_asiento'))['numero_asiento__max']
        else:
            ultimo_numero = AsientoContable.objects.aggregate(
                Max('numero_asiento')
            )['numero_asiento__max']
        
        if ultimo_numero is None:
            # Primer asiento
            if numero_asiento != 1:
                return False, f"El primer asiento debe ser número 1, no {numero_asiento}"
        else:
            # Debe ser consecutivo
            numero_esperado = ultimo_numero + 1
            if numero_asiento != numero_esperado:
                return False, (
                    f"Número de asiento debe ser {numero_esperado} "
                    f"(consecutivo al último: {ultimo_numero})"
                )
        
        return True, ""
