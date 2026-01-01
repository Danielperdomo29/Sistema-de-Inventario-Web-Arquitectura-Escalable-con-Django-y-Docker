from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Any
from django.db.models import Sum, Q
from ..models import AsientoContable, CuentaContable, PeriodoContable

class ReporteFiscalService:
    """Servicio centralizado para generación de reportes fiscales"""
    
    @staticmethod
    def generar_libro_diario(fecha_inicio: date, fecha_fin: date) -> Dict[str, List]:
        """
        Genera libro diario agrupando asientos por fecha
        
        Args:
            fecha_inicio: Fecha inicial del período
            fecha_fin: Fecha final del período
            
        Returns:
            Dict con asientos agrupados por fecha
        """
        asientos = AsientoContable.objects.filter(
            fecha_contable__range=[fecha_inicio, fecha_fin],
            estado='ACTIVO'  # Antes es_activo=True
        ).select_related('periodo_contable').prefetch_related('detalles').order_by('fecha_contable', 'id')
        
        libro = {}
        for asiento in asientos:
            fecha_str = asiento.fecha_contable.strftime('%Y-%m-%d')
            if fecha_str not in libro:
                libro[fecha_str] = []
            
            detalles_formateados = []
            for detalle in asiento.detalles.all():
                detalles_formateados.append({
                    'cuenta': detalle.cuenta_contable.codigo,
                    'nombre_cuenta': detalle.cuenta_contable.nombre,
                    'debito': detalle.debito,
                    'credito': detalle.credito,
                    'descripcion': detalle.descripcion_detalle
                })
            
            libro[fecha_str].append({
                'id': asiento.id,
                'descripcion': asiento.descripcion,
                'referencia': asiento.documento_origen_numero, # Antes referencia
                'detalles': detalles_formateados,
                'total_debito': sum(d['debito'] for d in detalles_formateados),
                'total_credito': sum(d['credito'] for d in detalles_formateados)
            })
        
        return libro
    
    @staticmethod
    def generar_balance_prueba(fecha_corte: date) -> Dict[str, Any]:
        """
        Genera balance de prueba (sumas iguales)
        
        Args:
            fecha_corte: Fecha de corte para el balance
            
        Returns:
            Dict con cuentas y sus saldos
        """
        # Obtener todas las cuentas con movimientos hasta la fecha
        cuentas = CuentaContable.objects.filter(
            movimientos__asiento__fecha_contable__lte=fecha_corte,
            movimientos__asiento__estado='ACTIVO'
        ).distinct()
        
        balance = []
        total_debito = Decimal('0.00')
        total_credito = Decimal('0.00')
        
        for cuenta in cuentas:
            movimientos = cuenta.movimientos.filter(
                asiento__fecha_contable__lte=fecha_corte,
                asiento__estado='ACTIVO'
            )
            
            # Sumar débitos
            sum_debito = movimientos.filter(debito__gt=0).aggregate(
                total=Sum('debito')
            )['total'] or Decimal('0.00')
            
            # Sumar créditos
            sum_credito = movimientos.filter(credito__gt=0).aggregate(
                total=Sum('credito')
            )['total'] or Decimal('0.00')
            
            saldo = sum_debito - sum_credito
            
            balance.append({
                'codigo': cuenta.codigo,
                'nombre': cuenta.nombre,
                'tipo': cuenta.get_tipo_display(),
                'debito': sum_debito,
                'credito': sum_credito,
                'saldo_deudor': saldo if saldo > 0 else Decimal('0.00'),
                'saldo_acreedor': abs(saldo) if saldo < 0 else Decimal('0.00')
            })
            
            total_debito += sum_debito
            total_credito += sum_credito
        
        return {
            'fecha_corte': fecha_corte,
            'cuentas': balance,
            'totales': {
                'total_debito': total_debito,
                'total_credito': total_credito,
                'diferencia': total_debito - total_credito
            }
        }
    
    @staticmethod
    def generar_libro_mayor(anio: int, mes: int = None) -> Dict[str, Any]:
        """
        Genera libro mayor con saldos mensuales
        
        Args:
            anio: Año del reporte
            mes: Mes específico (opcional)
            
        Returns:
            Dict con saldos mensuales por cuenta
        """
        cuentas = CuentaContable.objects.all()
        libro_mayor = {}
        
        for cuenta in cuentas:
            saldos_mensuales = []
            
            for mes_num in range(1, 13):
                if mes and mes_num != mes:
                    continue
                    
                fecha_inicio = date(anio, mes_num, 1)
                if mes_num == 12:
                    fecha_fin = date(anio, 12, 31)
                else:
                    fecha_fin = date(anio, mes_num + 1, 1) - timedelta(days=1)
                
                movimientos = cuenta.movimientos.filter(
                    asiento__fecha_contable__range=[fecha_inicio, fecha_fin],
                    asiento__estado='ACTIVO'
                )
                
                saldo_debito = movimientos.filter(debito__gt=0).aggregate(
                    total=Sum('debito')
                )['total'] or Decimal('0.00')
                
                saldo_credito = movimientos.filter(credito__gt=0).aggregate(
                    total=Sum('credito')
                )['total'] or Decimal('0.00')
                
                saldo_mes = saldo_debito - saldo_credito
                
                saldos_mensuales.append({
                    'mes': mes_num,
                    'mes_nombre': fecha_inicio.strftime('%B'),
                    'debito': saldo_debito,
                    'credito': saldo_credito,
                    'saldo': saldo_mes
                })
            
            if any(m['saldo'] != 0 for m in saldos_mensuales):
                 libro_mayor[cuenta.codigo] = {
                    'cuenta': cuenta.nombre,
                    'saldos_mensuales': saldos_mensuales
                }
        
        return {
            'anio': anio,
            'mes': mes,
            'libro_mayor': libro_mayor
        }
    
    @staticmethod
    def generar_estado_resultados(fecha_inicio: date, fecha_fin: date) -> Dict[str, Any]:
        """
        Genera estado de resultados (Pérdidas y Ganancias)
        """
        # Cuentas de ingresos (clase 4)
        ingresos = CuentaContable.objects.filter(codigo__startswith='4')
        total_ingresos = Decimal('0.00')
        
        for cuenta in ingresos:
            movimientos = cuenta.movimientos.filter(
                asiento__fecha_contable__range=[fecha_inicio, fecha_fin],
                asiento__estado='ACTIVO',
                credito__gt=0  # Ingresos aumentan con crédito
            )
            total_ingresos += movimientos.aggregate(total=Sum('credito'))['total'] or Decimal('0.00')
        
        # Cuentas de costos (clase 6)
        costos = CuentaContable.objects.filter(codigo__startswith='6')
        total_costos = Decimal('0.00')
        
        for cuenta in costos:
            movimientos = cuenta.movimientos.filter(
                asiento__fecha_contable__range=[fecha_inicio, fecha_fin],
                asiento__estado='ACTIVO',
                debito__gt=0  # Costos aumentan con débito
            )
            total_costos += movimientos.aggregate(total=Sum('debito'))['total'] or Decimal('0.00')
        
        # Cuentas de gastos (clase 5)
        gastos = CuentaContable.objects.filter(codigo__startswith='5')
        total_gastos = Decimal('0.00')
        
        for cuenta in gastos:
            movimientos = cuenta.movimientos.filter(
                asiento__fecha_contable__range=[fecha_inicio, fecha_fin],
                asiento__estado='ACTIVO',
                debito__gt=0  # Gastos aumentan con débito
            )
            total_gastos += movimientos.aggregate(total=Sum('debito'))['total'] or Decimal('0.00')
        
        utilidad_bruta = total_ingresos - total_costos
        utilidad_neta = utilidad_bruta - total_gastos
        
        return {
            'periodo': f"{fecha_inicio} - {fecha_fin}",
            'ingresos': total_ingresos,
            'costos': total_costos,
            'utilidad_bruta': utilidad_bruta,
            'gastos': total_gastos,
            'utilidad_neta': utilidad_neta
        }
