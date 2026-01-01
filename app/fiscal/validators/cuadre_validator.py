"""
Validador de Cuadre Contable
Verifica que Débitos = Créditos (tolerancia ≤ 0.01)
"""
from decimal import Decimal
from typing import Tuple, Dict, Any, Optional
from app.fiscal.validators.base_validator import ValidadorCritico


class ValidadorCuadreContable(ValidadorCritico):
    """
    Validador CRÍTICO: Cuadre Contable
    
    Requisito DIAN: En todo asiento contable, la suma de débitos
    debe ser igual a la suma de créditos.
    
    Tolerancia: ≤ $0.01 (para manejar redondeos)
    """
    
    TOLERANCIA = Decimal('0.01')
    
    def validar(self, asiento_data: Dict[str, Any], contexto: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Valida que débitos = créditos
        
        Verifica:
        1. Suma de débitos de detalles
        2. Suma de créditos de detalles
        3. Diferencia absoluta ≤ tolerancia
        """
        detalles = asiento_data.get('detalles', [])
        
        if not detalles:
            return False, "El asiento debe tener al menos un detalle"
        
        # Calcular totales desde detalles
        total_debito_detalles = sum(
            Decimal(str(d.get('debito', 0)))
            for d in detalles
        )
        
        total_credito_detalles = sum(
            Decimal(str(d.get('credito', 0)))
            for d in detalles
        )
        
        # Calcular diferencia
        diferencia = abs(total_debito_detalles - total_credito_detalles)
        
        # Validar cuadre
        if diferencia > self.TOLERANCIA:
            mensaje = (
                f"Descuadre contable detectado: "
                f"Débitos=${total_debito_detalles:,.2f}, "
                f"Créditos=${total_credito_detalles:,.2f}, "
                f"Diferencia=${diferencia:,.2f} "
                f"(tolerancia máxima: ${self.TOLERANCIA})"
            )
            
            # Registrar fallo crítico
            self.registrar_fallo(asiento_data, mensaje, contexto)
            
            return False, mensaje
        
        # Validar que los totales del asiento coincidan con los detalles
        total_debito_asiento = Decimal(str(asiento_data.get('total_debito', 0)))
        total_credito_asiento = Decimal(str(asiento_data.get('total_credito', 0)))
        
        if abs(total_debito_asiento - total_debito_detalles) > self.TOLERANCIA:
            return False, (
                f"Total débito del asiento (${total_debito_asiento:,.2f}) "
                f"no coincide con suma de detalles (${total_debito_detalles:,.2f})"
            )
        
        if abs(total_credito_asiento - total_credito_detalles) > self.TOLERANCIA:
            return False, (
                f"Total crédito del asiento (${total_credito_asiento:,.2f}) "
                f"no coincide con suma de detalles (${total_credito_detalles:,.2f})"
            )
        
        return True, ""
