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
    def get_margen_bruto(dias=180):
        """
        Margen bruto del periodo vs periodo anterior
        KPI #1 - CR\u00cdTICO para contadores (Fase 1: Filtro din\u00e1mico)
        
        Args:
            dias: D\u00edas hacia atr\u00e1s para analizar (default 180)
        
        Returns:
            dict: {
                'margen_periodo': float,
                'margen_anterior': float,
                'cambio_pct': float,
                'tendencia': 'up'|'down'
            }
        """
        # Validar periodo
        if dias not in [7, 30, 90, 180, 365]:
            dias = 180
        
        cache_key = f'kpi:margen_bruto:dias:{dias}'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        from app.models.sale import Sale, SaleDetail
        
        fecha_limite = timezone.now() - timedelta(days=dias)
        fecha_anterior = fecha_limite - timedelta(days=dias)
        
        # Ventas del periodo actual
        ventas_periodo = Sale.objects.filter(fecha__gte=fecha_limite).aggregate(
            total=Sum('total')
        )['total'] or 0
        
        # Costo de ventas del periodo (desde SaleDetail)
        costo_periodo = SaleDetail.objects.filter(
            venta__fecha__gte=fecha_limite
        ).annotate(
            costo_total=F('cantidad') * F('producto__precio_compra')
        ).aggregate(
            total=Sum('costo_total')
        )['total'] or 0
        
        margen_periodo = float(ventas_periodo - costo_periodo)
        
        # Periodo anterior (para comparaci\u00f3n)
        ventas_anterior = Sale.objects.filter(
            fecha__gte=fecha_anterior,
            fecha__lt=fecha_limite
        ).aggregate(
            total=Sum('total')
        )['total'] or 0
        
        costo_anterior = SaleDetail.objects.filter(
            venta__fecha__gte=fecha_anterior,
            venta__fecha__lt=fecha_limite
        ).annotate(
            costo_total=F('cantidad') * F('producto__precio_compra')
        ).aggregate(
            total=Sum('costo_total')
        )['total'] or 0
        
        margen_anterior = float(ventas_anterior - costo_anterior)
        
        # % de cambio (robustez para divisi\u00f3n por cero)
        if margen_anterior > 0:
            cambio_pct = ((margen_periodo - margen_anterior) / margen_anterior) * 100
        elif margen_periodo > 0:
            cambio_pct = 100
        else:
            cambio_pct = 0
        
        result = {
            'margen_periodo': round(margen_periodo, 2),
            'margen_anterior': round(margen_anterior, 2),
            'cambio_pct': round(cambio_pct, 2),
            'tendencia': 'up' if cambio_pct > 0 else 'down'
        }
        
        cache.set(cache_key, result, KPIService.CACHE_TIMEOUT_SHORT)
        return result
    
    @staticmethod
    def get_ticket_promedio(dias=180):
        """
        Ticket promedio del periodo
        KPI #2 - Comportamiento del cliente (Fase 1: Filtro din\u00e1mico)
        
        Args:
            dias: D\u00edas hacia atr\u00e1s para analizar (default 180)
        
        Returns:
            dict: {
                'ticket_promedio': float,
                'cantidad_ventas': int
            }
        """
        # Validar periodo
        if dias not in [7, 30, 90, 180, 365]:
            dias = 180
        
        cache_key = f'kpi:ticket_promedio:dias:{dias}'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        from app.models.sale import Sale
        
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        stats = Sale.objects.filter(
            fecha__gte=fecha_limite
        ).aggregate(
            total=Sum('total'),
            count=Count('id')
        )
        
        # ROBUSTEZ: Evita divisi\u00f3n por cero
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
    def get_top_productos(dias=180, limit=3):
        """
        Top productos m\u00e1s vendidos del periodo
        KPI #3 - Productos estrella (Fase 1: Filtro din\u00e1mico)
        
        Args:
            dias: D\u00edas hacia atr\u00e1s para analizar (default 180)
            limit: Cantidad de productos a retornar (default 3)
        
        Returns:
            list: [{
                'nombre': str,
                'codigo': str,
                'cantidad': int,
                'ingresos': float
            }]
        """
        # Validar periodo
        if dias not in [7, 30, 90, 180, 365]:
            dias = 180
       
        cache_key = f'kpi:top_productos:dias:{dias}:limit:{limit}'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        from app.models.sale import SaleDetail
        
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        top_productos = SaleDetail.objects.filter(
            venta__fecha__gte=fecha_limite
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
    def get_ventas_evolucion(dias=180):
        """
        Evolución de ventas del periodo (día a día o agrupado)
        KPI #5 - Tendencia del periodo (Fase 1: Filtro dinámico)
        
        Args:
            dias: Días hacia atrás para analizar (default 180)
        
        Returns:
            dict: {
                'labels': list,
                'data': list,
                'total_periodo': float
            }
        """
        # Validar periodo
        if dias not in [7, 30, 90, 180, 365]:
            dias = 180
       
        cache_key = f'kpi:ventas_evolucion:dias:{dias}'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        from app.models.sale import Sale
        from django.db.models.functions import TruncDate, TruncWeek
        
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        # Agrupar por día si <= 30 días, por semana si > 30
        if dias <= 30:
            # Agrupación diaria
            ventas_agrupadas = Sale.objects.filter(
                fecha__gte=fecha_limite
            ).annotate(
                periodo=TruncDate('fecha')
            ).values('periodo').annotate(
                total_periodo=Sum('total')
            ).order_by('periodo')
            
            labels = [v['periodo'].strftime('%d/%m') for v in ventas_agrupadas]
        else:
            # Agrupación semanal
            ventas_agrupadas = Sale.objects.filter(
                fecha__gte=fecha_limite
            ).annotate(
                periodo=TruncWeek('fecha')
            ).values('periodo').annotate(
                total_periodo=Sum('total')
            ).order_by('periodo')
            
            labels = [f"Sem {v['periodo'].isocalendar()[1]}" for v in ventas_agrupadas]
        
        data = []
        total_general = 0
        
        for v in ventas_agrupadas:
            total = float(v['total_periodo'])
            data.append(round(total, 2))
            total_general += total
        
        result = {
            'labels': labels,
            'data': data,
            'total_periodo': round(total_general, 2)
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
    def get_concentracion_clientes(top_n=20, meses=6):
        """
        Análisis de Pareto: Concentración de Clientes
        Fase 2.3 - Dashboard Profesional Avanzado
        
        Identifica la regla 80/20: ¿El 80% de las ventas viene del 20% de los clientes?
        
        Args:
            top_n: Cantidad de clientes a analizar (default 20)
            meses: Meses hacia atrás para analizar (default 6)
        
        Returns:
            dict: {
                'labels': ['Cliente A', 'Cliente B', ...],
                'ventas': [50000, 40000, 30000, ...],
                'porcentaje_acumulado': [25, 45, 60, ...],  # % acumulado
                'total_ventas': float,
                'clientes_80': int,  # Cuántos clientes hacen 80% de ventas
                'concentracion_pct': float,  # % de clientes que hacen 80%
                'alerta': 'alta'|'media'|'baja'  # Nivel de concentración
            }
        """
        cache_key = f'kpi:concentracion_clientes:top:{top_n}:meses:{meses}'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        from app.models.sale import Sale
        from app.models.client import Client
        
        # Límite de fecha
        fecha_limite = timezone.now() - timedelta(days=30 * meses)
        
        # Ventas por cliente (últimos N meses)
        ventas_por_cliente = Sale.objects.filter(
            fecha__gte=fecha_limite
        ).values(
            'cliente__nombre', 'cliente__id'
        ).annotate(
            total_ventas=Sum('total')
        ).order_by('-total_ventas')[:top_n]
        
        if not ventas_por_cliente:
            # No hay datos
            return {
                'labels': [],
                'ventas': [],
                'porcentaje_acumulado': [],
                'total_ventas': 0,
                'clientes_80': 0,
                'concentracion_pct': 0,
                'alerta': 'baja'
            }
        
        # Calcular total de ventas (para %)
        total_ventas_global = sum([float(v['total_ventas'] or 0) for v in ventas_por_cliente])
        
        # Preparar datos con % acumulado
        labels = []
        ventas = []
        porcentaje_acumulado = []
        acumulado = 0
        clientes_80 = 0  # Cuántos clientes necesitas para llegar a 80%
        encontrado_80 = False
        
        for i, cliente in enumerate(ventas_por_cliente):
            nombre = cliente['cliente__nombre'] or f"Cliente #{cliente['cliente__id']}"
            venta = float(cliente['total_ventas'] or 0)
            
            # Calcular % de esta venta
            pct_venta = (venta / total_ventas_global) * 100 if total_ventas_global > 0 else 0
            acumulado += pct_venta
            
            # Identificar cuántos clientes hacen 80%
            if not encontrado_80 and acumulado >= 80:
                clientes_80 = i + 1
                encontrado_80 = True
            
            labels.append(nombre)
            ventas.append(round(venta, 2))
            porcentaje_acumulado.append(round(acumulado, 2))
        
        # Si nunca llegamos a 80% (pocos datos), clientes_80 = total
        if not encontrado_80:
            clientes_80 = len(ventas_por_cliente)
        
        # Calcular concentración (% de clientes que hacen 80% de ventas)
        total_clientes = Client.objects.filter(activo=True).count()
        concentracion_pct = (clientes_80 / total_clientes * 100) if total_clientes > 0 else 0
        
        # Alerta de concentración
        # Alta: <10% de clientes hacen 80% (muy riesgoso)
        # Media: 10-20% de clientes hacen 80%
        # Baja: >20% de clientes hacen 80% (diversificado)
        if concentracion_pct < 10:
            alerta = 'alta'
        elif concentracion_pct < 20:
            alerta = 'media'
        else:
            alerta = 'baja'
        
        result = {
            'labels': labels,
            'ventas': ventas,
            'porcentaje_acumulado': porcentaje_acumulado,
            'total_ventas': round(total_ventas_global, 2),
            'clientes_80': clientes_80,
            'concentracion_pct': round(concentracion_pct, 2),
            'alerta': alerta,
            'total_clientes': total_clientes
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
            'kpi:rotacion_inventario:top:10',  # Fase 2.2
            'kpi:concentracion_clientes:top:20:meses:6'  # Fase 2.3
        ]
        
        for key in cache_keys:
            cache.delete(key)
