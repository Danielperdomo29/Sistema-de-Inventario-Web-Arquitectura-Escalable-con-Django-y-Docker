"""
Validador de Cuentas PUC
Verifica que las cuentas contables existan y sean válidas
"""
from typing import Tuple, Dict, Any, Optional
from app.fiscal.validators.base_validator import ValidadorCritico


class ValidadorCuentasPUC(ValidadorCritico):
    """
    Validador CRÍTICO: Cuentas del PUC
    
    Verifica:
    1. Que las cuentas existan en el PUC
    2. Que las cuentas permitan movimiento (no sean agrupadoras)
    3. Que las cuentas estén activas
    """
    
    def validar(self, asiento_data: Dict[str, Any], contexto: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Valida que todas las cuentas sean válidas
        """
        from app.fiscal.models import CuentaContable
        
        detalles = asiento_data.get('detalles', [])
        
        if not detalles:
            return False, "El asiento debe tener al menos un detalle"
        
        errores = []
        
        for idx, detalle in enumerate(detalles, 1):
            cuenta_id = detalle.get('cuenta_contable_id') or detalle.get('cuenta_id')
            cuenta_codigo = detalle.get('cuenta_codigo')
            
            # Buscar cuenta
            try:
                if cuenta_id:
                    cuenta = CuentaContable.objects.get(id=cuenta_id)
                elif cuenta_codigo:
                    cuenta = CuentaContable.objects.get(codigo=cuenta_codigo)
                else:
                    errores.append(f"Línea {idx}: Debe especificar cuenta_id o cuenta_codigo")
                    continue
            except CuentaContable.DoesNotExist:
                ref = cuenta_id or cuenta_codigo
                errores.append(f"Línea {idx}: Cuenta '{ref}' no existe en el PUC")
                continue
            
            # Verificar que permita movimiento
            if not cuenta.acepta_movimiento:
                errores.append(
                    f"Línea {idx}: Cuenta {cuenta.codigo} - {cuenta.nombre} "
                    f"no permite movimiento (es agrupadora)"
                )
            
            # Verificar que esté activa
            if not cuenta.activa:
                errores.append(
                    f"Línea {idx}: Cuenta {cuenta.codigo} - {cuenta.nombre} "
                    f"está inactiva"
                )
        
        if errores:
            mensaje = "Errores en cuentas PUC:\n" + "\n".join(errores)
            self.registrar_fallo(asiento_data, mensaje, contexto)
            return False, mensaje
        
        return True, ""
