from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any
from django.db import transaction
from django.db.models import Sum, Q
from ..models import (
    AsientoContable, CuentaContable, PeriodoContable, 
    DetalleAsiento, LogAuditoriaContable
)
from ..services.hash_manager import HashManager
from django.utils import timezone

class CierreContableService:
    """Servicio para ejecutar el cierre contable periódico"""
    
    def __init__(self, periodo_id: int):
        self.periodo = PeriodoContable.objects.get(id=periodo_id)
        self.hash_manager = HashManager()
        
    def validar_cuadre_periodo(self) -> bool:
        """
        Verifica que suma Debitos = suma Creditos en el período
        
        Returns:
            True si está cuadrado, False en caso contrario
        """
        total_debito = DetalleAsiento.objects.filter(
            asiento__periodo_contable=self.periodo,
            asiento__estado='ACTIVO'
        ).aggregate(
            total=Sum('debito')
        )['total'] or Decimal('0.00')
        
        total_credito = DetalleAsiento.objects.filter(
            asiento__periodo_contable=self.periodo,
            asiento__estado='ACTIVO'
        ).aggregate(
            total=Sum('credito')
        )['total'] or Decimal('0.00')
        
        return abs(total_debito - total_credito) < Decimal('0.01')  # Tolerancia para decimales
    
    def calcular_resultado(self) -> Dict[str, Decimal]:
        """
        Calcula el resultado del período (Ingresos - Gastos - Costos)
        
        Returns:
            Dict con totales por clase de cuenta
        """
        # Cuentas de Ingreso (clase 4)
        cuentas_ingreso = CuentaContable.objects.filter(codigo__startswith='4')
        total_ingresos = Decimal('0.00')
        
        for cuenta in cuentas_ingreso:
            # Ingresos son Crédito, Saldo positivo es crédito
            # Si obtner_saldo_periodo devuelve debito - credito, para ingresos será negativo
            # Ajustaremos según la implementación de CuentaContable o recalculamos aquí
            # Asumamos que CuentaContable.obtener_saldo_periodo devuelve el saldo natural
            # Pero para estar seguros recalculamos con campos debito/credito
            
            movimientos = DetalleAsiento.objects.filter(
               asiento__periodo_contable=self.periodo,
               asiento__estado='ACTIVO',
               cuenta_contable=cuenta
            )
            
            creditos = movimientos.aggregate(sum=Sum('credito'))['sum'] or Decimal('0.00')
            debitos = movimientos.aggregate(sum=Sum('debito'))['sum'] or Decimal('0.00')
            
            saldo_cuenta = creditos - debitos
            total_ingresos += saldo_cuenta
        
        # Cuentas de Costo (clases 6 y 7)
        cuentas_costo = CuentaContable.objects.filter(
            Q(codigo__startswith='6') | Q(codigo__startswith='7')
        )
        total_costos = Decimal('0.00')
        
        for cuenta in cuentas_costo:
            movimientos = DetalleAsiento.objects.filter(
               asiento__periodo_contable=self.periodo,
               asiento__estado='ACTIVO',
               cuenta_contable=cuenta
            )
            debitos = movimientos.aggregate(sum=Sum('debito'))['sum'] or Decimal('0.00')
            creditos = movimientos.aggregate(sum=Sum('credito'))['sum'] or Decimal('0.00')
            
            saldo_cuenta = debitos - creditos
            total_costos += saldo_cuenta
        
        # Cuentas de Gasto (clase 5)
        cuentas_gasto = CuentaContable.objects.filter(codigo__startswith='5')
        total_gastos = Decimal('0.00')
        
        for cuenta in cuentas_gasto:
            movimientos = DetalleAsiento.objects.filter(
               asiento__periodo_contable=self.periodo,
               asiento__estado='ACTIVO',
               cuenta_contable=cuenta
            )
            debitos = movimientos.aggregate(sum=Sum('debito'))['sum'] or Decimal('0.00')
            creditos = movimientos.aggregate(sum=Sum('credito'))['sum'] or Decimal('0.00')
            
            saldo_cuenta = debitos - creditos
            total_gastos += saldo_cuenta
        
        utilidad_bruta = total_ingresos - total_costos
        utilidad_neta = utilidad_bruta - total_gastos
        
        return {
            'total_ingresos': total_ingresos,
            'total_costos': total_costos,
            'total_gastos': total_gastos,
            'utilidad_bruta': utilidad_bruta,
            'utilidad_neta': utilidad_neta
        }
    
    @transaction.atomic
    def generar_asiento_cierre(self, usuario) -> AsientoContable:
        """
        Genera el asiento de cierre contable
        
        Args:
            usuario: Usuario que genera el cierre
            
        Returns:
            AsientoContable creado
        """
        # Validar que el período esté cuadrado
        if not self.validar_cuadre_periodo():
            raise ValueError("El período no está cuadrado. No se puede realizar el cierre.")
        
        # Calcular resultado
        resultado = self.calcular_resultado()
        utilidad_neta = resultado['utilidad_neta']
        
        # Calcular siguiente número de asiento
        from django.db.models import Max
        ultimo_numero = AsientoContable.objects.aggregate(Max('numero_asiento'))['numero_asiento__max'] or 0
        siguiente_numero = ultimo_numero + 1

        # Crear asiento de cierre
        asiento_cierre = AsientoContable.objects.create(
            descripcion=f"Cierre contable período {str(self.periodo)}",
            fecha_contable=self.periodo.fecha_fin,
            periodo_contable=self.periodo,
            tipo_asiento='CIERRE',
            estado='ACTIVO',
            numero_asiento=siguiente_numero,
            usuario_creacion=usuario
        )
        
        # 1. Cerrar cuentas de Ingreso (4xxx) -> Debitar saldo crédito
        cuentas_ingreso = CuentaContable.objects.filter(codigo__startswith='4')
        for cuenta in cuentas_ingreso:
            movimientos = DetalleAsiento.objects.filter(
               asiento__periodo_contable=self.periodo,
               asiento__estado='ACTIVO',
               cuenta_contable=cuenta
            )
            creditos = movimientos.aggregate(sum=Sum('credito'))['sum'] or Decimal('0.00')
            debitos = movimientos.aggregate(sum=Sum('debito'))['sum'] or Decimal('0.00')
            saldo = creditos - debitos
            
            if saldo > 0:
                DetalleAsiento.objects.create(
                    asiento=asiento_cierre,
                    cuenta_contable=cuenta,
                    debito=saldo,
                    credito=0,
                    descripcion_detalle=f"Cierre de {cuenta.nombre}",
                    orden=1
                )
        
        # 2. Cerrar cuentas de Gasto (5xxx) -> Acreditar saldo débito
        cuentas_gasto = CuentaContable.objects.filter(codigo__startswith='5')
        for cuenta in cuentas_gasto:
            movimientos = DetalleAsiento.objects.filter(
               asiento__periodo_contable=self.periodo,
               asiento__estado='ACTIVO',
               cuenta_contable=cuenta
            )
            debitos = movimientos.aggregate(sum=Sum('debito'))['sum'] or Decimal('0.00')
            creditos = movimientos.aggregate(sum=Sum('credito'))['sum'] or Decimal('0.00')
            saldo = debitos - creditos # Naturaleza débito
            
            if saldo > 0:
                DetalleAsiento.objects.create(
                    asiento=asiento_cierre,
                    cuenta_contable=cuenta,
                    debito=0,
                    credito=saldo,
                    descripcion_detalle=f"Cierre de {cuenta.nombre}",
                    orden=2
                )
        
        # 3. Cerrar cuentas de Costo (6xxx, 7xxx) -> Acreditar saldo débito
        cuentas_costo = CuentaContable.objects.filter(
            Q(codigo__startswith='6') | Q(codigo__startswith='7')
        )
        for cuenta in cuentas_costo:
            movimientos = DetalleAsiento.objects.filter(
               asiento__periodo_contable=self.periodo,
               asiento__estado='ACTIVO',
               cuenta_contable=cuenta
            )
            debitos = movimientos.aggregate(sum=Sum('debito'))['sum'] or Decimal('0.00')
            creditos = movimientos.aggregate(sum=Sum('credito'))['sum'] or Decimal('0.00')
            saldo = debitos - creditos # Naturaleza débito
            
            if saldo > 0:
                DetalleAsiento.objects.create(
                    asiento=asiento_cierre,
                    cuenta_contable=cuenta,
                    debito=0,
                    credito=saldo,
                    descripcion_detalle=f"Cierre de {cuenta.nombre}",
                    orden=3
                )
        
        # 4. Registrar la utilidad/pérdida en cuenta patrimonial
        try:
            cuenta_utilidad = CuentaContable.objects.get(codigo='3605')  # Utilidad del ejercicio
        except CuentaContable.DoesNotExist:
             # Fallback si no existe la cta exacta, buscar una generica de patrimonio
             cuenta_utilidad = CuentaContable.objects.filter(codigo__startswith='3').first()
             if not cuenta_utilidad:
                 raise ValueError("No existe cuenta patrimonial (3xxx) para cierre")

        if utilidad_neta > 0:
            # Utilidad: naturaleza CRÉDITO en patrimonio
            DetalleAsiento.objects.create(
                asiento=asiento_cierre,
                cuenta_contable=cuenta_utilidad,
                debito=0,
                credito=utilidad_neta,
                descripcion_detalle=f"Utilidad del período {str(self.periodo)}",
                orden=4
            )
        else:
            # Pérdida: naturaleza DÉBITO en patrimonio (reduce patrimonio)
            DetalleAsiento.objects.create(
                asiento=asiento_cierre,
                cuenta_contable=cuenta_utilidad,
                debito=abs(utilidad_neta),
                credito=0,
                descripcion_detalle=f"Pérdida del período {str(self.periodo)}",
                orden=4
            )
        
        # Recalcular totales del asiento antes de hash y save final
        total_deb = sum(d.debito for d in asiento_cierre.detalles.all())
        total_cred = sum(d.credito for d in asiento_cierre.detalles.all())
        asiento_cierre.total_debito = total_deb
        asiento_cierre.total_credito = total_cred
        
        # Calcular y guardar hash de integridad
        # Usamos el metodo del modelo si existe, o el manager
        if hasattr(asiento_cierre, 'calcular_hash'):
             asiento_cierre.hash_integridad = asiento_cierre.calcular_hash()
        else:
             asiento_cierre.hash_integridad = self.hash_manager.generar_hash_asiento(asiento_cierre._to_dict())
             
        asiento_cierre.save()
        
        # Registrar log de auditoría
        LogAuditoriaContable.registrar(
            usuario=usuario,
            tipo_evento='CIERRE_CONTABLE',
            asiento=asiento_cierre,
            detalles={'mensaje': f"Asiento de cierre {asiento_cierre.id} generado para período {str(self.periodo)}"}
        )
        
        return asiento_cierre
    
    @transaction.atomic
    def cerrar_periodo(self, usuario) -> Dict[str, Any]:
        """
        Ejecuta el cierre completo del período
        
        Args:
            usuario: Usuario que ejecuta el cierre
            
        Returns:
            Dict con información del cierre
        """
        # Verificar que el período no esté ya cerrado
        if self.periodo.estado == 'CERRADO':
            raise ValueError("El período ya está cerrado.")
        
        # Generar asiento de cierre
        asiento_cierre = self.generar_asiento_cierre(usuario)
        
        # Bloquear asientos del período (esto dependeria de la logica de bloqueo, 
        # aqui asumimos que el validador de periodo bloqueo por fecha_cierre del periodo)
        
        # Actualizar estado del período
        self.periodo.estado = 'CERRADO'
        self.periodo.fecha_cierre = datetime.now() # O timezone.now()
        self.periodo.save()
        
        # Registrar log de cierre
        # El log auditoria contable suele pedir un asiento, si aqui es evento de modelo periodo, 
        # quizas necesitemos otro log o forzarlo.
        # Usaremos print/logging normal si LogAuditoriaContable requiere asiento obligatorio
        # O creamos un log vinculado al asiento de cierre
        
        return {
            'periodo': str(self.periodo),
            'estado': self.periodo.estado,
            'asiento_cierre_id': asiento_cierre.id,
            'fecha_cierre': self.periodo.fecha_cierre,
            'mensaje': 'Cierre contable ejecutado exitosamente'
        }
    
    def validar_cierre_periodo_anterior(self) -> bool:
        """
        Valida que el período anterior esté cerrado antes de operar en el actual
        
        Returns:
            True si puede operar, False en caso contrario
        """
        # Asumiendo que PeridoContable tiene metodos para esto, si no mock simple
        if hasattr(self.periodo, 'es_primer_periodo') and self.periodo.es_primer_periodo():
             return True
             
        if hasattr(self.periodo, 'obtener_periodo_anterior'):
            periodo_anterior = self.periodo.obtener_periodo_anterior()
            if periodo_anterior and periodo_anterior.estado != 'CERRADO':
                return False
        
        # Si no hay metodos, implementacion simple buscando por fecha
        anterior = PeriodoContable.objects.filter(fecha_fin__lt=self.periodo.fecha_inicio).order_by('-fecha_fin').first()
        if anterior and anterior.estado != 'CERRADO':
             return False
             
        return True
