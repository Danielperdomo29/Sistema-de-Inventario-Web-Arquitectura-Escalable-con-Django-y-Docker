"""
Servicio de KPIs para Dashboard
Calcula métricas críticas para contadores y administradores
"""
from django.db.models import Sum, Count, Avg, F
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache


class KPIService:
    """Servicio centralizado para cálculo de KPIs con caché"""
    
    # Timeouts de caché por criticidad
    CACHE_TIMEOUT_SHORT = 60 * 5      # 5 min - Datos críticos
    CACHE_TIMEOUT_MEDIUM = 60 * 30    # 30 min - Datos menos críticos
    CACHE_TIMEOUT_LONG = 60 * 60 * 2  # 2 horas - Datos históricos
    
    @staticmethod
    def get_margen_bruto_hoy():
        """
        Margen bruto del día vs ayer
        KPI #1 - Crítico para contadores
        
        Returns:
            dict: {
                'margen_hoy': float,
                'margen_ayer': float,
                'cambio_pct': float,
                'tendencia': 'up'|'down'
            }
        """
        cache_key = 'kpi:margen_bruto:today'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        from app.models.sale import Sale, SaleDetail
        
        hoy = timezone.now().date()
        ayer = hoy - timedelta(days=1)
        
        # Ventas de hoy
        ventas_hoy = Sale.objects.filter(fecha__date=hoy).aggregate(
            total=Sum('total')
        )['total'] or 0
        
        # Costo de ventas de hoy (desde SaleDetail)
        costo_hoy = SaleDetail.objects.filter(
            venta__fecha__date=hoy
        ).annotate(
            costo_total=F('cantidad') * F('producto__precio_compra')
        ).aggregate(
            total=Sum('costo_total')
        )['total'] or 0
        
        margen_hoy = float(ventas_hoy - costo_hoy)
        
        # Ayer (para comparación)
        ventas_ayer = Sale.objects.filter(fecha__date=ayer).aggregate(
            total=Sum('total')
        )['total'] or 0
        
        costo_ayer = SaleDetail.objects.filter(
            venta__fecha__date=ayer
        ).annotate(
            costo_total=F('cantidad') * F('producto__precio_compra')
        ).aggregate(
            total=Sum('costo_total')
        )['total'] or 0
        
        margen_ayer = float(ventas_ayer - costo_ayer)
        
        # % de cambio (robustez para división por cero)
        if margen_ayer > 0:
            cambio_pct = ((margen_hoy - margen_ayer) / margen_ayer) * 100
        elif margen_hoy > 0:
            cambio_pct = 100  # 100% de incremento si no había ventas ayer
        else:
            cambio_pct = 0
        
        result = {
            'margen_hoy': round(margen_hoy, 2),
            'margen_ayer': round(margen_ayer, 2),
            'cambio_pct': round(cambio_pct, 2),
            'tendencia': 'up' if cambio_pct > 0 else 'down'
        }
        
        cache.set(cache_key, result, KPIService.CACHE_TIMEOUT_SHORT)
        return result
    
    @staticmethod
    def get_ticket_promedio():
        """
        Ticket promedio del mes
        KPI #2 - Comportamiento del cliente
        
        Returns:
            dict: {
                'ticket_promedio': float,
                'cantidad_ventas': int
            }
        """
        cache_key = 'kpi:ticket_promedio:month'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        from app.models.sale import Sale
        
        mes_actual = timezone.now().month
        año_actual = timezone.now().year
        
        stats = Sale.objects.filter(
            fecha__year=año_actual,
            fecha__month=mes_actual
        ).aggregate(
            total=Sum('total'),
            count=Count('id')
        )
        
        # ROBUSTEZ: Evita división por cero
        ventas_count = stats['count'] or 0
        ventas_total = stats['total'] or 0
        ticket_promedio = (ventas_total / ventas_count) if ventas_count > 0 else 0.0
        
        result = {
            'ticket_promedio': round(float(ticket_promedio), 2),
            'cantidad_ventas': ventas_count
        }
        
        cache.set(cache_key, result, KPIService.CACHE_TIMEOUT_MEDIUM)
        return result
    
    @staticmethod
    def get_top_productos_semana(limit=3):
        """
        Top productos más vendidos de la semana
        KPI #3 - Productos estrella
        
        Args:
            limit: Cantidad de productos a retornar (default 3)
        
        Returns:
            list: [{
                'producto__nombre': str,
                'cantidad_total': int,
                'ingresos_total': float
            }]
        """
        cache_key = f'kpi:top_productos:week:{limit}'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        from app.models.sale import SaleDetail
        
        hace_7_dias = timezone.now() - timedelta(days=7)
        
        top_productos = SaleDetail.objects.filter(
            venta__fecha__gte=hace_7_dias
        ).values(
            'producto__nombre', 'producto__codigo'
        ).annotate(
            cantidad_total=Sum('cantidad'),
            ingresos_total=Sum(F('precio_unitario') * F('cantidad'))
        ).order_by('-cantidad_total')[:limit]
        
        result = []
        for p in top_productos:
            result.append({
                'nombre': p['producto__nombre'],
                'codigo': p['producto__codigo'],
                'cantidad': int(p['cantidad_total']),
                'ingresos': round(float(p['ingresos_total']), 2)
            })
        
        cache.set(cache_key, result, KPIService.CACHE_TIMEOUT_MEDIUM)
        return result
    
    @staticmethod
    def get_stock_bajo():
        """
        Productos con stock bajo
        KPI #4 - Alerta crítica para inventario
        
        Returns:
            dict: {
                'count': int,
                'productos': list
            }
        """
        cache_key = 'kpi:stock_bajo'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        from app.models.product import Product
        
        productos = Product.objects.filter(
            stock_actual__lte=F('stock_minimo'),
            activo=True
        ).values(
            'id', 'codigo', 'nombre', 'stock_actual', 'stock_minimo'
        ).annotate(
            deficit=F('stock_minimo') - F('stock_actual')
        ).order_by('-deficit')
        
        result = {
            'count': productos.count(),
            'productos': list(productos[:10])  # Top 10 más urgentes
        }
        
        cache.set(cache_key, result, KPIService.CACHE_TIMEOUT_SHORT)
        return result
    
    @staticmethod
    def get_ventas_mes_evolucion():
        """
        Evolución de ventas del mes día a día
        KPI #5 - Tendencia mensual
        
        Returns:
            dict: {
                'labels': list,
                'data': list,
                'total_mes': float
            }
        """
        cache_key = 'kpi:ventas_mes:evolucion'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        from app.models.sale import Sale
        from django.db.models.functions import TruncDate
        
        mes_actual = timezone.now().month
        año_actual = timezone.now().year
        
        # Group by date
        ventas_por_dia = Sale.objects.filter(
            fecha__year=año_actual,
            fecha__month=mes_actual
        ).annotate(
            dia=TruncDate('fecha')
        ).values('dia').annotate(
            total_dia=Sum('total')
        ).order_by('dia')
        
        labels = []
        data = []
        total_mes = 0
        
        for v in ventas_por_dia:
            labels.append(v['dia'].strftime('%d'))
            total_dia = float(v['total_dia'])
            data.append(total_dia)
            total_mes += total_dia
        
        result = {
            'labels': labels,
            'data': data,
            'total_mes': round(total_mes, 2)
        }
        
        cache.set(cache_key, result, KPIService.CACHE_TIMEOUT_MEDIUM)
        return result
    
    @staticmethod
    def get_flujo_caja_mensual(meses=6):
        """
        Flujo de caja mensual: Ingresos vs Egresos
        Fase 2.1 - Dashboard Profesional Avanzado
        
        Args:
            meses: Cantidad de meses a mostrar (default 6)
        
        Returns:
            dict: {
                'labels': ['Ene 2026', 'Feb 2026', ...],
                'ingresos': [120000.0, 135000.0, ...],
                'egresos': [80000.0, 95000.0, ...],
                'flujo_neto': [40000.0, 40000.0, ...],
                'total_ingresos': float,
                'total_egresos': float,
                'total_neto': float
            }
        """
        cache_key = f'kpi:flujo_caja:meses:{meses}'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        from app.models.sale import Sale
        from app.models.purchase import Purchase
        from django.db.models.functions import TruncMonth
        
        # Últimos N meses
        fecha_limite = timezone.now() - timedelta(days=30 * meses)
        
        # Ingresos por mes (Ventas)
        ingresos_por_mes = Sale.objects.filter(
            fecha__gte=fecha_limite
        ).annotate(
            mes=TruncMonth('fecha')
        ).values('mes').annotate(
            total=Sum('total')
        ).order_by('mes')
        
        # Egresos por mes (Compras)
        egresos_por_mes = Purchase.objects.filter(
            fecha__gte=fecha_limite
        ).annotate(
            mes=TruncMonth('fecha')
        ).values('mes').annotate(
            total=Sum('total')
        ).order_by('mes')
        
        # Crear diccionarios para lookup eficiente
        ingresos_dict = {i['mes']: float(i['total']) for i in ingresos_por_mes}
        egresos_dict = {e['mes']: float(e['total']) for e in egresos_por_mes}
        
        # Obtener todos los meses en el rango (union de ambos)
        all_months = set(ingresos_dict.keys()) | set(egresos_dict.keys())
        all_months = sorted(all_months)
        
        # Preparar datos para Chart.js
        labels = []
        ingresos = []
        egresos = []
        flujo_neto = []
        
        # Meses en español (seguro, sin user input)
        meses_es = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                    'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        
        for mes in all_months:
            # Label del mes (formato: "Ene 2026")
            labels.append(f"{meses_es[mes.month - 1]} {mes.year}")
            
            # Valores (0 si no hay datos en ese mes)
            ingreso = ingresos_dict.get(mes, 0)
            egreso = egresos_dict.get(mes, 0)
            neto = ingreso - egreso
            
            ingresos.append(round(ingreso, 2))
            egresos.append(round(egreso, 2))
            flujo_neto.append(round(neto, 2))
        
        result = {
            'labels': labels,
            'ingresos': ingresos,
            'egresos': egresos,
            'flujo_neto': flujo_neto,
            'total_ingresos': round(sum(ingresos), 2),
            'total_egresos': round(sum(egresos), 2),
            'total_neto': round(sum(flujo_neto), 2)
        }
        
        cache.set(cache_key, result, KPIService.CACHE_TIMEOUT_MEDIUM)
        return result
    
    @staticmethod
    def get_rotacion_inventario_por_categoria(top_n=10):
        """
        Rotación de inventario por categoría (Días de Inventario)
        Fase 2.2 - Dashboard Profesional Avanzado
        
        Fórmula: Días de Inventario = (Costo Inventario / Costo Ventas Mensual) * 30
        
        Args:
            top_n: Cantidad de categorías a mostrar (default 10)
        
        Returns:
            dict: {
                'labels': ['Categoría A', 'Categoría B', ...],
                'dias_inventario': [45, 60, 30, ...],
                'costo_inventario': [50000, 80000, ...],
                'rotacion_anual': [8, 6, 12, ...]  # veces que rota por año
            }
        """
        cache_key = f'kpi:rotacion_inventario:top:{top_n}'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        from app.models.product import Product
        from app.models.sale import SaleDetail
        from django.db.models import DecimalField
        from django.db.models import ExpressionWrapper
        
        # 1. Costo de Inventario Actual por Categoría
        # = SUM(stock_actual * precio_compra) por categoría
        inventario_por_categoria = Product.objects.filter(
            activo=True
        ).values(
            'categoria__nombre'
        ).annotate(
            costo_inventario=Sum(
                ExpressionWrapper(
                    F('stock_actual') * F('precio_compra'),
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                )
            )
        ).filter(
            costo_inventario__gt=0  # Solo categorías con inventario
        )
        
        # 2. Costo de Ventas (últimos 30 días) por Categoría
        # = SUM(cantidad_vendida * precio_compra_producto)
        fecha_limite = timezone.now() - timedelta(days=30)
        
        ventas_por_categoria = SaleDetail.objects.filter(
            venta__fecha__gte=fecha_limite
        ).values(
            'producto__categoria__nombre'
        ).annotate(
            costo_ventas=Sum(
                ExpressionWrapper(
                    F('cantidad') * F('producto__precio_compra'),
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                )
            )
        )
        
        # 3. Combinar datos y calcular Días de Inventario
        # Crear diccionarios para lookup
        inventario_dict = {
            item['categoria__nombre']: float(item['costo_inventario'] or 0)
            for item in inventario_por_categoria
        }
        
        ventas_dict = {
            item['producto__categoria__nombre']: float(item['costo_ventas'] or 0)
            for item in ventas_por_categoria
        }
        
        # Obtener todas las categorías con inventario
        categorias = inventario_dict.keys()
        
        # Calcular métricas por categoría
        resultados = []
        for categoria in categorias:
            costo_inv = inventario_dict.get(categoria, 0)
            costo_ven = ventas_dict.get(categoria, 0)
            
            # Días de Inventario = (Costo Inventario / Costo Ventas) * 30
            # Robustez: Si no hay ventas, días = infinito (usamos 999)
            if costo_ven > 0:
                dias_inventario = (costo_inv / costo_ven) * 30
                # Rotación Anual = 365 / días_inventario
                rotacion_anual = 365 / dias_inventario if dias_inventario > 0 else 0
            else:
                dias_inventario = 999  # Sin ventas = inventario estancado
                rotacion_anual = 0
            
            resultados.append({
                'categoria': categoria,
                'costo_inventario': round(costo_inv, 2),
                'costo_ventas': round(costo_ven, 2),
                'dias_inventario': round(dias_inventario, 1),
                'rotacion_anual': round(rotacion_anual, 2)
            })
        
        # Ordenar por días de inventario (mayor a menor = más crítico)
        resultados.sort(key=lambda x: x['dias_inventario'], reverse=True)
        
        # Tomar top N
        resultados = resultados[:top_n]
        
        # Preparar datos para Chart.js (barras horizontales)
        labels = [r['categoria'] for r in resultados]
        dias_inventario = [r['dias_inventario'] for r in resultados]
        costo_inventario = [r['costo_inventario'] for r in resultados]
        rotacion_anual = [r['rotacion_anual'] for r in resultados]
        
        result = {
            'labels': labels,
            'dias_inventario': dias_inventario,
            'costo_inventario': costo_inventario,
            'rotacion_anual': rotacion_anual,
            'categorias_count': len(labels)
        }
        
        cache.set(cache_key, result, KPIService.CACHE_TIMEOUT_MEDIUM)
        return result
    
    @staticmethod
    def clear_all_kpi_cache():
        """Invalida todos los cachés de KPIs (usar al finalizar día)"""
        cache_keys = [
            'kpi:margen_bruto:today',
            'kpi:ticket_promedio:month',
            'kpi:top_productos:week:3',
            'kpi:stock_bajo',
            'kpi:ventas_mes:evolucion',
            'kpi:flujo_caja:meses:6',  # Fase 2.1
            'kpi:rotacion_inventario:top:10'  # Fase 2.2
        ]
        
        for key in cache_keys:
            cache.delete(key)
