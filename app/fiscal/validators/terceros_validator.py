"""
Validador de Terceros DIAN
Verifica que los NITs sean válidos y estén activos
"""
from typing import Tuple, Dict, Any, Optional
from app.fiscal.validators.base_validator import ValidadorAdvertencia


class ValidadorTercerosDIAN(ValidadorAdvertencia):
    """
    Validador ADVERTENCIA: Terceros y NITs
    
    Verifica:
    1. Formato válido de NIT
    2. Dígito de verificación correcto
    3. Tercero existe en PerfilFiscal (si aplica)
    """
    
    def validar(self, asiento_data: Dict[str, Any], contexto: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Valida terceros y NITs
        """
        from app.fiscal.validators.nit_validator import NITValidator
        
        tercero_nit = asiento_data.get('tercero_nit', '').strip()
        
        # Si no hay tercero, es válido (no todos los asientos requieren tercero)
        if not tercero_nit:
            return True, ""
        
        # Validar formato de NIT
        nit_validator = NITValidator()
        
        try:
            nit_limpio = nit_validator.limpiar_nit(tercero_nit)
            nit_validator.validar_nit(nit_limpio)
        except Exception as e:
            # Es advertencia, no bloquea pero registra
            mensaje = f"NIT '{tercero_nit}' tiene formato inválido: {str(e)}"
            self.registrar_fallo(asiento_data, mensaje, contexto)
            return False, mensaje
        
        # Verificar si existe en PerfilFiscal
        from app.fiscal.models import PerfilFiscal
        
        try:
            perfil = PerfilFiscal.objects.get(nit=nit_limpio)
            
            # Verificar que esté activo
            if not perfil.activo:
                mensaje = (
                    f"El tercero con NIT {tercero_nit} ({perfil.razon_social}) "
                    f"está inactivo en el sistema"
                )
                self.registrar_fallo(asiento_data, mensaje, contexto)
                return False, mensaje
            
        except PerfilFiscal.DoesNotExist:
            # No existe, es advertencia pero no bloquea
            # (puede ser un tercero nuevo que se creará después)
            pass
        
        return True, ""
    
    def obtener_severidad(self) -> str:
        return 'ADVERTENCIA'
