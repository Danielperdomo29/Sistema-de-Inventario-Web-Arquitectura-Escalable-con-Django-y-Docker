"""
Validador de Límites por Usuario
Verifica límites de montos y tipos de asientos según rol del usuario
"""
from typing import Tuple, Dict, Any, Optional
from decimal import Decimal
from app.fiscal.validators.base_validator import ValidadorContable


class ValidadorLimitesUsuario(ValidadorContable):
    """
    Validador: Límites por Usuario/Rol
    
    Verifica límites según rol:
    - Vendedor: Solo asientos de venta, hasta $5M
    - Contador: Todos los tipos, hasta $50M
    - Auditor: Solo lectura (no puede crear)
    - Administrador: Sin límites
    """
    
    LIMITES_POR_ROL = {
        'vendedor': {
            'tipos_permitidos': ['VENTA'],
            'monto_maximo': Decimal('5000000'),  # $5M
        },
        'contador': {
            'tipos_permitidos': ['VENTA', 'COMPRA', 'AJUSTE', 'NOMINA', 'MANUAL'],
            'monto_maximo': Decimal('50000000'),  # $50M
        },
        'auditor': {
            'tipos_permitidos': [],  # Solo lectura
            'monto_maximo': Decimal('0'),
        },
        'administrador': {
            'tipos_permitidos': None,  # Todos
            'monto_maximo': None,  # Sin límite
        }
    }
    
    def validar(self, asiento_data: Dict[str, Any], contexto: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Valida límites del usuario
        """
        usuario = asiento_data.get('usuario')
        if not usuario:
            return True, ""  # Sin usuario, no validar (se validará en otro lado)
        
        # Obtener rol del usuario
        rol = self._obtener_rol_usuario(usuario)
        
        if rol not in self.LIMITES_POR_ROL:
            # Rol desconocido, aplicar restricciones de vendedor por seguridad
            rol = 'vendedor'
        
        limites = self.LIMITES_POR_ROL[rol]
        
        # Validar tipo de asiento
        tipo_asiento = asiento_data.get('tipo_asiento')
        tipos_permitidos = limites['tipos_permitidos']
        
        if tipos_permitidos is not None and tipo_asiento not in tipos_permitidos:
            return False, (
                f"El usuario con rol '{rol}' no puede crear asientos de tipo '{tipo_asiento}'. "
                f"Tipos permitidos: {', '.join(tipos_permitidos)}"
            )
        
        # Validar monto
        monto_maximo = limites['monto_maximo']
        if monto_maximo is not None:
            total_debito = Decimal(str(asiento_data.get('total_debito', 0)))
            total_credito = Decimal(str(asiento_data.get('total_credito', 0)))
            monto_asiento = max(total_debito, total_credito)
            
            if monto_asiento > monto_maximo:
                return False, (
                    f"El usuario con rol '{rol}' no puede crear asientos superiores a "
                    f"${monto_maximo:,.2f}. Monto del asiento: ${monto_asiento:,.2f}"
                )
        
        return True, ""
    
    def _obtener_rol_usuario(self, usuario) -> str:
        """
        Obtiene el rol del usuario
        Puede personalizarse según la estructura de roles del sistema
        """
        # Verificar si es superusuario
        if usuario.is_superuser:
            return 'administrador'
        
        # Verificar permisos específicos
        if usuario.has_perm('fiscal.cerrar_periodo'):
            return 'contador'
        
        if usuario.has_perm('fiscal.ver_logs_auditoria') and not usuario.has_perm('fiscal.add_asientocontable'):
            return 'auditor'
        
        # Por defecto, vendedor (más restrictivo)
        return 'vendedor'
    
    def obtener_severidad(self) -> str:
        return 'ERROR'
