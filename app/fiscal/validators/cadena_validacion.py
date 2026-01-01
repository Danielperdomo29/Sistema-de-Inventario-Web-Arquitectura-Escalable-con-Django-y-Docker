"""
Cadena de Validación - Chain of Responsibility
Orquesta todos los validadores DIAN en secuencia
"""
from typing import List, Tuple, Dict, Any, Optional
from app.fiscal.validators.base_validator import ValidadorContable
from app.fiscal.validators.cuadre_validator import ValidadorCuadreContable
from app.fiscal.validators.periodo_validator import ValidadorPeriodoAbierto
from app.fiscal.validators.secuencia_validator import ValidadorSecuenciaNumerica
from app.fiscal.validators.cuentas_validator import ValidadorCuentasPUC
from app.fiscal.validators.limites_validator import ValidadorLimitesUsuario
from app.fiscal.validators.terceros_validator import ValidadorTercerosDIAN
from app.fiscal.validators.montos_validator import ValidadorMontosPositivos


class CadenaValidacionContable:
    """
    Cadena de Validación para Asientos Contables
    
    Implementa el patrón Chain of Responsibility para ejecutar
    todos los validadores DIAN en secuencia.
    
    Orden de validación (de más crítico a menos):
    1. ValidadorMontosPositivos - Formato y valores básicos
    2. ValidadorCuadreContable - Débitos = Créditos
    3. ValidadorCuentasPUC - Cuentas válidas
    4. ValidadorPeriodoAbierto - Período no cerrado
    5. ValidadorSecuenciaNumerica - Numeración consecutiva
    6. ValidadorLimitesUsuario - Límites por rol
    7. ValidadorTercerosDIAN - NITs válidos (advertencia)
    """
    
    def __init__(self):
        """
        Inicializa la cadena de validadores
        """
        # Crear validadores en orden de criticidad
        self.validadores: List[ValidadorContable] = [
            ValidadorMontosPositivos(),
            ValidadorCuadreContable(),
            ValidadorCuentasPUC(),
            ValidadorPeriodoAbierto(),
            ValidadorSecuenciaNumerica(),
            ValidadorLimitesUsuario(),
            ValidadorTercerosDIAN(),
        ]
        
        # Encadenar validadores
        for i in range(len(self.validadores) - 1):
            self.validadores[i].establecer_siguiente(self.validadores[i + 1])
    
    def validar(self, asiento_data: Dict[str, Any], contexto: Optional[Dict] = None) -> Tuple[bool, List[dict]]:
        """
        Ejecuta la cadena completa de validación
        
        Args:
            asiento_data: Dict con datos del asiento a validar
            contexto: Dict opcional con contexto (request, ip, etc.)
        
        Returns:
            Tuple[bool, List[dict]]: (es_valido, lista_errores)
                lista_errores: [
                    {
                        'validador': str,
                        'mensaje': str,
                        'severidad': 'CRITICO' | 'ERROR' | 'ADVERTENCIA'
                    }
                ]
        """
        if not self.validadores:
            return True, []
        
        # Ejecutar cadena desde el primer validador
        es_valido, errores = self.validadores[0].validar_cadena(asiento_data, contexto)
        
        return es_valido, errores
    
    def validar_criticos_solo(self, asiento_data: Dict[str, Any], contexto: Optional[Dict] = None) -> Tuple[bool, List[dict]]:
        """
        Ejecuta solo validadores críticos (más rápido)
        
        Útil para validaciones previas o en tiempo real
        """
        validadores_criticos = [
            ValidadorMontosPositivos(),
            ValidadorCuadreContable(),
            ValidadorCuentasPUC(),
            ValidadorPeriodoAbierto(),
        ]
        
        # Encadenar
        for i in range(len(validadores_criticos) - 1):
            validadores_criticos[i].establecer_siguiente(validadores_criticos[i + 1])
        
        # Ejecutar
        es_valido, errores = validadores_criticos[0].validar_cadena(asiento_data, contexto)
        
        return es_valido, errores
    
    def obtener_validadores(self) -> List[ValidadorContable]:
        """
        Retorna la lista de validadores configurados
        """
        return self.validadores
    
    def agregar_validador(self, validador: ValidadorContable, posicion: Optional[int] = None):
        """
        Agrega un validador personalizado a la cadena
        
        Args:
            validador: Instancia de ValidadorContable
            posicion: Posición en la cadena (None = al final)
        """
        if posicion is None:
            # Agregar al final
            if self.validadores:
                self.validadores[-1].establecer_siguiente(validador)
            self.validadores.append(validador)
        else:
            # Insertar en posición específica
            self.validadores.insert(posicion, validador)
            # Reencadenar
            for i in range(len(self.validadores) - 1):
                self.validadores[i].establecer_siguiente(self.validadores[i + 1])
    
    def generar_reporte_validacion(self, errores: List[dict]) -> str:
        """
        Genera un reporte legible de errores de validación
        
        Args:
            errores: Lista de errores retornada por validar()
        
        Returns:
            str: Reporte formateado
        """
        if not errores:
            return "✅ Todas las validaciones pasaron correctamente"
        
        # Agrupar por severidad
        criticos = [e for e in errores if e['severidad'] == 'CRITICO']
        errores_normales = [e for e in errores if e['severidad'] == 'ERROR']
        advertencias = [e for e in errores if e['severidad'] == 'ADVERTENCIA']
        
        reporte = []
        
        if criticos:
            reporte.append("🔴 ERRORES CRÍTICOS:")
            for error in criticos:
                reporte.append(f"  • [{error['validador']}] {error['mensaje']}")
        
        if errores_normales:
            reporte.append("\n⚠️ ERRORES:")
            for error in errores_normales:
                reporte.append(f"  • [{error['validador']}] {error['mensaje']}")
        
        if advertencias:
            reporte.append("\n⚡ ADVERTENCIAS:")
            for advertencia in advertencias:
                reporte.append(f"  • [{advertencia['validador']}] {advertencia['mensaje']}")
        
        return "\n".join(reporte)


# Instancia global para uso directo
cadena_validacion_global = CadenaValidacionContable()


def validar_asiento(asiento_data: Dict[str, Any], contexto: Optional[Dict] = None) -> Tuple[bool, List[dict]]:
    """
    Función de utilidad para validar un asiento usando la cadena global
    
    Uso:
        es_valido, errores = validar_asiento(asiento_data, contexto)
        if not es_valido:
            print(CadenaValidacionContable().generar_reporte_validacion(errores))
    """
    return cadena_validacion_global.validar(asiento_data, contexto)
