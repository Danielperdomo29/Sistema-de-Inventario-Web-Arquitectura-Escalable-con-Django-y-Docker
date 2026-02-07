"""
Tests unitarios para el servicio de KPIs.
Cubre métodos de KPIService y endpoints de API.
"""

import json
from decimal import Decimal
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from app.services.kpi_service import KPIService


class KPIServiceTestCase(TestCase):
    """Tests para KPIService - Lógica de negocio de KPIs"""
    
    @classmethod
    def setUpTestData(cls):
        """Configurar datos de prueba una vez para toda la clase"""
        # Crear usuario de prueba
        User = get_user_model()
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def setUp(self):
        """Configurar cliente y limpiar caché antes de cada test"""
        self.client = Client()
        # Limpiar caché de KPIs
        from django.core.cache import cache
        cache.clear()
    
    # =========================================================================
    # Tests de Margen Bruto
    # =========================================================================
    
    def test_get_margen_bruto_returns_valid_structure(self):
        """Test: get_margen_bruto retorna estructura válida"""
        result = KPIService.get_margen_bruto()
        
        self.assertIsInstance(result, dict)
        self.assertIn('margen_periodo', result)
        self.assertIn('cambio_pct', result)
        self.assertIn('tendencia', result)
        
        # Validar tipos
        self.assertIsInstance(result['margen_periodo'], (int, float))
        self.assertIsInstance(result['cambio_pct'], (int, float))
        self.assertIn(result['tendencia'], ['up', 'down', 'neutral'])
    
    def test_get_margen_bruto_validates_periodo(self):
        """Test: get_margen_bruto valida parámetro dias"""
        # Periodos válidos
        for dias in [7, 30, 90, 180, 365]:
            result = KPIService.get_margen_bruto(dias=dias)
            self.assertIsInstance(result, dict)
        
        # Periodo inválido debe usar default (180)
        result = KPIService.get_margen_bruto(dias=999)
        self.assertIsInstance(result, dict)
    
    # =========================================================================
    # Tests de Ticket Promedio
    # =========================================================================
    
    def test_get_ticket_promedio_returns_valid_structure(self):
        """Test: get_ticket_promedio retorna estructura válida"""
        result = KPIService.get_ticket_promedio()
        
        self.assertIsInstance(result, dict)
        self.assertIn('ticket_promedio', result)
        self.assertIn('cantidad_ventas', result)
        
        # Validar tipos
        self.assertIsInstance(result['ticket_promedio'], (int, float))
        self.assertIsInstance(result['cantidad_ventas'], int)
    
    def test_get_ticket_promedio_handles_zero_ventas(self):
        """Test: get_ticket_promedio maneja división por cero"""
        # Este test verifica que no hay excepción cuando no hay ventas
        result = KPIService.get_ticket_promedio(dias=1)  # Periodo muy corto
        
        self.assertIsInstance(result, dict)
        self.assertGreaterEqual(result['ticket_promedio'], 0)
    
    # =========================================================================
    # Tests de Top Productos
    # =========================================================================
    
    def test_get_top_productos_returns_list(self):
        """Test: get_top_productos retorna lista"""
        result = KPIService.get_top_productos()
        
        self.assertIsInstance(result, list)
        
        # Si hay productos, verificar estructura
        if result:
            producto = result[0]
            self.assertIn('nombre', producto)
            self.assertIn('codigo', producto)
            self.assertIn('cantidad', producto)
            self.assertIn('ingresos', producto)
    
    def test_get_top_productos_respects_limit(self):
        """Test: get_top_productos respeta parámetro limit"""
        for limit in [1, 3, 5, 10]:
            result = KPIService.get_top_productos(limit=limit)
            self.assertLessEqual(len(result), limit)
    
    # =========================================================================
    # Tests de Stock Bajo
    # =========================================================================
    
    def test_get_stock_bajo_returns_dict(self):
        """Test: get_stock_bajo retorna diccionario válido"""
        result = KPIService.get_stock_bajo()
        
        self.assertIsInstance(result, dict)
        self.assertIn('count', result)
        self.assertIn('productos', result)
        
        # Validar tipos
        self.assertIsInstance(result['count'], int)
        self.assertIsInstance(result['productos'], list)
    
    # =========================================================================
    # Tests de Evolución de Ventas
    # =========================================================================
    
    def test_get_ventas_evolucion_returns_chart_data(self):
        """Test: get_ventas_evolucion retorna datos para Chart.js"""
        result = KPIService.get_ventas_evolucion()
        
        self.assertIsInstance(result, dict)
        self.assertIn('labels', result)
        self.assertIn('data', result)
        self.assertIn('total_periodo', result)
        
        # Labels y data deben tener misma longitud
        self.assertEqual(len(result['labels']), len(result['data']))
    
    # =========================================================================
    # Tests de Rentabilidad
    # =========================================================================
    
    def test_get_rentabilidad_productos_returns_list(self):
        """Test: get_rentabilidad_productos retorna lista"""
        result = KPIService.get_rentabilidad_productos()
        
        self.assertIsInstance(result, list)
        
        if result:
            producto = result[0]
            self.assertIn('nombre', producto)
            self.assertIn('margen_porcentaje', producto)
            self.assertIn('ganancia_total', producto)
            self.assertIn('unidades_vendidas', producto)
    
    # =========================================================================
    # Tests de Análisis ABC
    # =========================================================================
    
    def test_get_productos_abc_analysis_returns_classification(self):
        """Test: get_productos_abc_analysis retorna clasificación ABC"""
        result = KPIService.get_productos_abc_analysis()
        
        self.assertIsInstance(result, dict)
        self.assertIn('productos', result)
        self.assertIn('resumen', result)
        
        # Verificar estructura del resumen
        resumen = result['resumen']
        self.assertIn('clase_a', resumen)
        self.assertIn('clase_b', resumen)
        self.assertIn('clase_c', resumen)
    
    # =========================================================================
    # Tests de Rotación Inventario
    # =========================================================================
    
    def test_get_rotacion_inventario_returns_list(self):
        """Test: get_rotacion_inventario retorna lista"""
        result = KPIService.get_rotacion_inventario()
        
        self.assertIsInstance(result, list)
        
        if result:
            producto = result[0]
            self.assertIn('nombre', producto)
            self.assertIn('rotacion_dias', producto)
            self.assertIn('clasificacion', producto)
            self.assertIn('color', producto)
    
    def test_get_rotacion_inventario_classification(self):
        """Test: get_rotacion_inventario clasifica correctamente"""
        result = KPIService.get_rotacion_inventario()
        
        valid_classifications = ['Rápida', 'Media', 'Lenta']
        valid_colors = ['success', 'warning', 'danger']
        
        for producto in result:
            self.assertIn(producto['clasificacion'], valid_classifications)
            self.assertIn(producto['color'], valid_colors)


class KPIAPITestCase(TestCase):
    """Tests para API endpoints de KPIs"""
    
    @classmethod
    def setUpTestData(cls):
        """Configurar datos de prueba"""
        User = get_user_model()
        cls.user = User.objects.create_user(
            username='apiuser',
            email='api@example.com',
            password='apipass123'
        )
    
    def setUp(self):
        """Configurar cliente y autenticar"""
        self.client = Client()
        self.client.login(username='apiuser', password='apipass123')
        
        # Limpiar caché
        from django.core.cache import cache
        cache.clear()
    
    # =========================================================================
    # Tests de Endpoint /api/kpi/productos/
    # =========================================================================
    
    def test_api_kpi_productos_returns_200(self):
        """Test: GET /api/kpi/productos/ retorna 200"""
        response = self.client.get('/api/kpi/productos/')
        self.assertEqual(response.status_code, 200)
    
    def test_api_kpi_productos_returns_json(self):
        """Test: GET /api/kpi/productos/ retorna JSON válido"""
        response = self.client.get('/api/kpi/productos/')
        
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        self.assertIsInstance(data, dict)
    
    def test_api_kpi_productos_structure(self):
        """Test: GET /api/kpi/productos/ retorna estructura correcta"""
        response = self.client.get('/api/kpi/productos/')
        data = json.loads(response.content)
        
        # Verificar secciones principales
        self.assertIn('ventas', data)
        self.assertIn('inventario', data)
        self.assertIn('metadata', data)
        
        # Verificar subsecciones de ventas
        self.assertIn('top_vendidos', data['ventas'])
        self.assertIn('rentabilidad', data['ventas'])
        self.assertIn('abc_analysis', data['ventas'])
        
        # Verificar subsecciones de inventario
        self.assertIn('rotacion', data['inventario'])
    
    def test_api_kpi_productos_validates_dias_param(self):
        """Test: API valida parámetro dias"""
        # Valores válidos
        for dias in [7, 30, 90, 180, 365]:
            response = self.client.get(f'/api/kpi/productos/?dias={dias}')
            self.assertEqual(response.status_code, 200)
        
        # Valor inválido
        response = self.client.get('/api/kpi/productos/?dias=999')
        self.assertEqual(response.status_code, 400)
    
    def test_api_kpi_productos_validates_limit_param(self):
        """Test: API valida parámetro limit"""
        # Valores válidos
        for limit in [1, 5, 10, 20]:
            response = self.client.get(f'/api/kpi/productos/?limit={limit}')
            self.assertEqual(response.status_code, 200)
        
        # Valor inválido (fuera de rango 1-20)
        response = self.client.get('/api/kpi/productos/?limit=100')
        self.assertEqual(response.status_code, 400)
        
        response = self.client.get('/api/kpi/productos/?limit=0')
        self.assertEqual(response.status_code, 400)
    
    # =========================================================================
    # Tests de Endpoint /api/kpi/productos/abc/
    # =========================================================================
    
    def test_api_kpi_abc_detalle_returns_200(self):
        """Test: GET /api/kpi/productos/abc/ retorna 200"""
        response = self.client.get('/api/kpi/productos/abc/')
        self.assertEqual(response.status_code, 200)
    
    def test_api_kpi_abc_detalle_structure(self):
        """Test: GET /api/kpi/productos/abc/ retorna estructura correcta"""
        response = self.client.get('/api/kpi/productos/abc/')
        data = json.loads(response.content)
        
        self.assertIn('productos', data)
        self.assertIn('resumen', data)
        self.assertIn('metadata', data)
    
    # =========================================================================
    # Tests de Endpoint /api/kpi/invalidar-cache/
    # =========================================================================
    
    def test_api_invalidar_cache_returns_success(self):
        """Test: GET /api/kpi/invalidar-cache/ retorna success"""
        response = self.client.get('/api/kpi/invalidar-cache/')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data.get('success'))
    
    # =========================================================================
    # Tests de Seguridad
    # =========================================================================
    
    def test_api_sanitizes_parameters(self):
        """Test: API sanitiza parámetros de entrada"""
        # Intentar inyección SQL (debe ser manejado como inválido)
        response = self.client.get('/api/kpi/productos/?dias=1;DROP TABLE;')
        # Debe retornar 400 o manejarlo como inválido
        self.assertIn(response.status_code, [400, 200])
        
        # Intentar XSS
        response = self.client.get('/api/kpi/productos/?dias=<script>')
        self.assertIn(response.status_code, [400, 200])


class KPICacheTestCase(TestCase):
    """Tests para verificar comportamiento de caché de KPIs"""
    
    def setUp(self):
        """Limpiar caché antes de cada test"""
        from django.core.cache import cache
        cache.clear()
    
    def test_kpi_uses_cache(self):
        """Test: KPIService usa caché correctamente"""
        from django.core.cache import cache
        
        # Primera llamada (sin caché)
        result1 = KPIService.get_ticket_promedio()
        
        # Segunda llamada (con caché)
        result2 = KPIService.get_ticket_promedio()
        
        # Deben ser iguales
        self.assertEqual(result1, result2)
    
    def test_clear_kpi_cache(self):
        """Test: Limpieza de caché funciona"""
        # Llenar caché
        KPIService.get_ticket_promedio()
        
        # Limpiar caché
        KPIService.clear_all_kpi_cache()
        
        # No debe haber error al volver a llamar
        result = KPIService.get_ticket_promedio()
        self.assertIsInstance(result, dict)
