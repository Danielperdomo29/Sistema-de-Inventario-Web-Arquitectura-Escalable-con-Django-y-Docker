"""
Validador de Montos Positivos
Verifica que los montos sean positivos y tengan formato correcto
"""
from typing import Tuple, Dict, Any, Optional
from decimal import Decimal, InvalidOperation
from app.fiscal.validators.base_validator import ValidadorCritico


class ValidadorMontosPositivos(ValidadorCritico):
    """
    Validador CRÍTICO: Montos Positivos
    
    Verifica:
    1. Montos no negativos
    2. Formato decimal correcto (2 decimales)
    3. Cada línea tiene débito O crédito (no ambos)
    4. Al menos una línea con monto > 0
    """
    
    def validar(self, asiento_data: Dict[str, Any], contexto: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Valida montos de detalles
        """
        detalles = asiento_data.get('detalles', [])
        
        if not detalles:
            return False, "El asiento debe tener al menos un detalle"
        
        errores = []
        tiene_movimiento = False
        
        for idx, detalle in enumerate(detalles, 1):
            try:
                debito = Decimal(str(detalle.get('debito', 0)))
                credito = Decimal(str(detalle.get('credito', 0)))
            except (InvalidOperation, ValueError) as e:
                errores.append(f"Línea {idx}: Formato de monto inválido - {str(e)}")
                continue
            
            # Validar no negativos
            if debito < 0:
                errores.append(f"Línea {idx}: Débito no puede ser negativo (${debito})")
            
            if credito < 0:
                errores.append(f"Línea {idx}: Crédito no puede ser negativo (${credito})")
            
            # Validar que tenga débito O crédito (no ambos)
            if debito > 0 and credito > 0:
                errores.append(
                    f"Línea {idx}: No puede tener débito Y crédito simultáneamente "
                    f"(D:${debito}, C:${credito})"
                )
            
            # Validar que tenga al menos uno
            if debito == 0 and credito == 0:
                errores.append(f"Línea {idx}: Debe tener débito o crédito mayor a cero")
            
            # Verificar que haya al menos un movimiento
            if debito > 0 or credito > 0:
                tiene_movimiento = True
            
            # Validar decimales (máximo 2)
            if debito > 0:
                decimales_debito = abs(debito.as_tuple().exponent)
                if decimales_debito > 2:
                    errores.append(
                        f"Línea {idx}: Débito tiene más de 2 decimales (${debito})"
                    )
            
            if credito > 0:
                decimales_credito = abs(credito.as_tuple().exponent)
                if decimales_credito > 2:
                    errores.append(
                        f"Línea {idx}: Crédito tiene más de 2 decimales (${credito})"
                    )
        
        if not tiene_movimiento:
            errores.append("El asiento debe tener al menos una línea con monto mayor a cero")
        
        if errores:
            mensaje = "Errores en montos:\n" + "\n".join(errores)
            self.registrar_fallo(asiento_data, mensaje, contexto)
            return False, mensaje
        
        return True, ""
