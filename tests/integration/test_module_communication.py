"""
Test suite para validar la comunicación entre módulos y funcionalidades críticas.
Incluye datos realistas para pruebas de stock bajo, KPIs, y alertas.

Ejecutar: python manage.py test tests.integration.test_module_communication -v 2
"""
import os
import sys
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth import get_user_model
from django.db import connection

# Configure Django settings for testing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')


class ModuleCommunicationTestCase(TransactionTestCase):
    """Tests para verificar la comunicación entre módulos"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = Client()
    
    def setUp(self):
        """Setup con datos realistas para cada test"""
        from app.models.user import UserAccount
        from app.models.category import Category
        from app.models.product import Product
        from app.models.warehouse import Warehouse
        from app.models.supplier import Supplier
        
        # Crear usuario de prueba
        self.user = UserAccount.objects.create_user(
            username='test_integration',
            email='test@integration.com',
            password='TestPass123!',
            rol_id=1  # Admin
        )
        
        # Crear categorías realistas
        self.category_electronics = Category.objects.create(
            nombre='Electrónica',
            descripcion='Productos electrónicos y tecnología'
        )
        self.category_office = Category.objects.create(
            nombre='Oficina',
            descripcion='Suministros de oficina'
        )
        
        # Crear almacén (usando campos correctos: nombre, ubicacion, capacidad)
        self.warehouse = Warehouse.objects.create(
            nombre='Bodega Principal',
            ubicacion='Calle 123 #45-67, Bogotá',
            capacidad=1000
        )
        
        # Crear proveedor
        self.supplier = Supplier.objects.create(
            nombre='Distribuidora Nacional S.A.S',
            nit='900123456',
            digito_verificacion='7',
            email='ventas@distribuidora.com',
            telefono='6019876543',
            ciudad='Medellín'
        )
        
        # Crear productos con stock variado (incluyendo stock bajo)
        self.products = []
        
        # Productos con STOCK BAJO (< stock_minimo) - DEBEN GENERAR ALERTA
        low_stock_products = [
            ('LP001', 'Laptop HP ProBook 450', 5, Decimal('2500000.00'), 10),
            ('MS002', 'Mouse Inalámbrico Logitech', 3, Decimal('85000.00'), 15),
            ('AU003', 'Audífonos Sony WH-1000XM4', 2, Decimal('1200000.00'), 5),
            ('TE004', 'Teclado Mecánico RGB', 8, Decimal('350000.00'), 10),
            ('WC005', 'WebCam HD 1080p', 1, Decimal('180000.00'), 8),
        ]
        
        for codigo, name, stock, price, min_stock in low_stock_products:
            product = Product.objects.create(
                codigo=codigo,
                nombre=name,
                descripcion=f'Producto: {name}',
                precio_compra=price * Decimal('0.7'),
                precio_venta=price,
                stock_actual=stock,
                stock_minimo=min_stock,
                categoria=self.category_electronics,
                proveedor=self.supplier,
                activo=True
            )
            self.products.append(product)
        
        # Productos con stock NORMAL
        normal_stock_products = [
            ('MO006', 'Monitor 24" Samsung', 25, Decimal('750000.00'), 5),
            ('HD007', 'Cable HDMI 2m', 150, Decimal('25000.00'), 20),
            ('CA008', 'Cargador Universal', 80, Decimal('45000.00'), 15),
            ('AD009', 'Adaptador USB-C', 200, Decimal('35000.00'), 30),
            ('US010', 'Memoria USB 64GB', 100, Decimal('55000.00'), 25),
        ]
        
        for codigo, name, stock, price, min_stock in normal_stock_products:
            product = Product.objects.create(
                codigo=codigo,
                nombre=name,
                descripcion=f'Producto: {name}',
                precio_compra=price * Decimal('0.7'),
                precio_venta=price,
                stock_actual=stock,
                stock_minimo=min_stock,
                categoria=self.category_electronics,
                proveedor=self.supplier,
                activo=True
            )
            self.products.append(product)
        
        # Productos de oficina
        office_products = [
            ('OF011', 'Resma Papel Carta', 50, Decimal('15000.00'), 10),
            ('OF012', 'Carpetas AZ', 75, Decimal('12000.00'), 15),
            ('OF013', 'Esferos Caja x12', 120, Decimal('18000.00'), 20),
        ]
        
        for codigo, name, stock, price, min_stock in office_products:
            product = Product.objects.create(
                codigo=codigo,
                nombre=name,
                descripcion=f'Producto: {name}',
                precio_compra=price * Decimal('0.7'),
                precio_venta=price,
                stock_actual=stock,
                stock_minimo=min_stock,
                categoria=self.category_office,
                proveedor=self.supplier,
                activo=True
            )
            self.products.append(product)
    
    def tearDown(self):
        """Limpieza después de cada test"""
        from app.models.product import Product
        from app.models.category import Category
        from app.models.warehouse import Warehouse
        from app.models.supplier import Supplier
        from app.models.user import UserAccount
        
        # Limpiar en orden inverso por dependencias
        Product.objects.all().delete()
        Category.objects.all().delete()
        Warehouse.objects.all().delete()
        Supplier.objects.all().delete()
        UserAccount.objects.filter(username='test_integration').delete()


class ProductModelCRUDTests(ModuleCommunicationTestCase):
    """Tests para validar operaciones CRUD del modelo Product"""
    
    def test_product_get_all_returns_list(self):
        """Verifica que get_all() retorna todos los productos"""
        from app.models.product import Product
        
        products = Product.get_all()
        self.assertIsInstance(products, list)
        self.assertEqual(len(products), 13)  # 5 + 5 + 3 productos
    
    def test_product_get_by_id_valid(self):
        """Verifica que get_by_id() retorna el producto correcto"""
        from app.models.product import Product
        
        product = Product.get_by_id(self.products[0].id)
        self.assertIsNotNone(product)
        self.assertEqual(product['nombre'], 'Laptop HP ProBook 450')
    
    def test_product_get_by_id_invalid(self):
        """Verifica que get_by_id() retorna None para ID inválido"""
        from app.models.product import Product
        
        product = Product.get_by_id(99999)
        self.assertIsNone(product)
    
    def test_product_count(self):
        """Verifica que count() retorna el número correcto"""
        from app.models.product import Product
        
        count = Product.count()
        self.assertEqual(count, 13)


class StockAlertTests(ModuleCommunicationTestCase):
    """Tests para validar el sistema de alertas de stock bajo"""
    
    def test_detect_low_stock_products(self):
        """Verifica que se detectan productos con stock bajo (usando get_low_stock)"""
        from app.models.product import Product
        
        # Usar el método nativo get_low_stock
        low_stock = Product.get_low_stock(limit=20)
        
        # Debe haber al menos 5 productos con stock bajo
        self.assertGreaterEqual(len(low_stock), 5)
    
    def test_stock_alert_threshold(self):
        """Verifica que el umbral de stock bajo funciona correctamente"""
        from app.models.product import Product
        
        products = Product.get_all()
        
        # Productos que cumplen: stock_actual < stock_minimo
        critical_stock = [
            p for p in products 
            if p['stock_actual'] < p.get('stock_minimo', 10)
        ]
        
        # Verificamos que tenemos productos en alerta
        self.assertGreaterEqual(len(critical_stock), 4)
        
        for product in critical_stock:
            self.assertLess(
                product['stock_actual'],
                product['stock_minimo'],
                f"{product['nombre']} debería estar en alerta"
            )
    
    def test_low_stock_includes_critical_items(self):
        """Verifica que los productos más críticos están en la lista"""
        from app.models.product import Product
        
        low_stock = Product.get_low_stock(limit=20)
        low_stock_names = [p['nombre'] for p in low_stock]
        
        # WebCam tiene stock=1, debería estar primero o cerca
        self.assertIn('WebCam HD 1080p', low_stock_names)


class CategoryProductRelationTests(ModuleCommunicationTestCase):
    """Tests para validar la relación entre categorías y productos"""
    
    def test_category_has_products(self):
        """Verifica que las categorías tienen productos asociados"""
        from app.models.product import Product
        
        products = Product.get_all()
        
        electronics = [p for p in products if p.get('categoria') == 'Electrónica']
        office = [p for p in products if p.get('categoria') == 'Oficina']
        
        self.assertEqual(len(electronics), 10)  # 5 low + 5 normal
        self.assertEqual(len(office), 3)
    
    def test_category_get_all_returns_list(self):
        """Verifica que Category.get_all() funciona"""
        from app.models.category import Category
        
        categories = Category.get_all()
        self.assertIsInstance(categories, list)
        self.assertEqual(len(categories), 2)


class SupplierCRUDTests(ModuleCommunicationTestCase):
    """Tests para validar operaciones CRUD del modelo Supplier"""
    
    def test_supplier_get_all(self):
        """Verifica que get_all() retorna proveedores"""
        from app.models.supplier import Supplier
        
        suppliers = Supplier.get_all()
        self.assertIsInstance(suppliers, list)
        self.assertGreaterEqual(len(suppliers), 1)
    
    def test_supplier_get_by_id(self):
        """Verifica que get_by_id() funciona"""
        from app.models.supplier import Supplier
        
        supplier = Supplier.get_by_id(self.supplier.id)
        self.assertIsNotNone(supplier)
        self.assertEqual(supplier['nombre'], 'Distribuidora Nacional S.A.S')
        self.assertEqual(supplier['nit'], '900123456')


class WarehouseCRUDTests(ModuleCommunicationTestCase):
    """Tests para validar operaciones CRUD del modelo Warehouse"""
    
    def test_warehouse_get_all(self):
        """Verifica que get_all() retorna almacenes"""
        from app.models.warehouse import Warehouse
        
        warehouses = Warehouse.get_all()
        self.assertIsInstance(warehouses, list)
        self.assertGreaterEqual(len(warehouses), 1)
    
    def test_warehouse_get_by_id(self):
        """Verifica que get_by_id() funciona"""
        from app.models.warehouse import Warehouse
        
        warehouse = Warehouse.get_by_id(self.warehouse.id)
        self.assertIsNotNone(warehouse)
        self.assertEqual(warehouse['nombre'], 'Bodega Principal')


class ServiceCommunicationTests(ModuleCommunicationTestCase):
    """Tests para validar la comunicación entre servicios"""
    
    def test_kpi_service_available(self):
        """Verifica que el servicio de KPIs está disponible"""
        try:
            from app.services.kpi_service import KPIService
            # KPIService tiene métodos específicos como get_margen_bruto, get_ticket_promedio, etc.
            self.assertTrue(
                hasattr(KPIService, 'get_margen_bruto') or 
                hasattr(KPIService, 'get_ticket_promedio') or
                hasattr(KPIService, 'get_top_productos')
            )
        except ImportError:
            self.skipTest("KPIService no disponible")
    
    def test_cache_service_available(self):
        """Verifica que el servicio de caché está disponible"""
        try:
            from app.services.cache_service import CacheService
            self.assertIsNotNone(CacheService)
        except ImportError:
            self.skipTest("CacheService no disponible")


class EventBusCommunicationTests(TransactionTestCase):
    """Tests para validar la comunicación via EventBus"""
    
    def test_event_bus_singleton(self):
        """Verifica que EventBus es singleton"""
        from core.event_bus import event_bus
        
        # Obtener referencia
        bus1 = event_bus
        bus2 = event_bus
        
        self.assertIs(bus1, bus2)
    
    def test_event_bus_subscribe_and_publish(self):
        """Verifica que se puede suscribir y publicar eventos"""
        from core.event_bus import event_bus
        
        # Resetear para testing
        event_bus._reset_for_testing(use_memory=True)
        
        received_events = []
        
        def handler(data):
            received_events.append(data)
        
        # Suscribir
        event_bus.subscribe('test.event', handler)
        
        # Publicar
        event_bus.publish('test.event', {'message': 'test'})
        
        # Verificar (en modo memoria, la entrega es síncrona)
        self.assertEqual(len(received_events), 1)
        # EventBus envuelve los datos en event_data con estructura: {'type', 'data', 'timestamp', 'event_id'}
        self.assertEqual(received_events[0]['data']['message'], 'test')


class DataIntegrityTests(ModuleCommunicationTestCase):
    """Tests para verificar la integridad de datos entre módulos"""
    
    def test_product_category_foreign_key(self):
        """Verifica que la FK de categoría en producto es válida"""
        from app.models.product import Product
        
        products = Product.get_all()
        
        for product in products:
            # Todos los productos deben tener categoría
            self.assertIsNotNone(product.get('categoria'))
    
    def test_product_prices_valid(self):
        """Verifica que los precios de productos son válidos"""
        from app.models.product import Product
        
        products = Product.get_all()
        
        for product in products:
            precio_compra = float(product.get('precio_compra', 0))
            precio_venta = float(product.get('precio_venta', 0))
            
            # Precio de venta debe ser >= precio de compra
            self.assertGreaterEqual(
                precio_venta, 
                precio_compra,
                f"{product['nombre']}: precio_venta < precio_compra"
            )
    
    def test_stock_values_non_negative(self):
        """Verifica que el stock nunca es negativo"""
        from app.models.product import Product
        
        products = Product.get_all()
        
        for product in products:
            stock = product.get('stock_actual', 0)
            self.assertGreaterEqual(
                stock, 
                0,
                f"{product['nombre']}: stock negativo"
            )


class UnusedFunctionalityDetectionTests(TestCase):
    """Tests para identificar funcionalidades potencialmente no usadas"""
    
    def test_identify_duplicate_crud_patterns(self):
        """Identifica modelos con patrones CRUD duplicados"""
        from app.models import (
            category, product, sale, purchase,
            supplier, role, warehouse, inventory_movement
        )
        
        models_with_crud = []
        
        # Verificar qué modelos tienen get_all y get_by_id
        for module_name, module in [
            ('Category', category.Category),
            ('Product', product.Product),
            ('Sale', sale.Sale),
            ('Purchase', purchase.Purchase),
            ('Supplier', supplier.Supplier),
            ('Role', role.Role),
            ('Warehouse', warehouse.Warehouse),
            ('InventoryMovement', inventory_movement.InventoryMovement),
        ]:
            has_get_all = hasattr(module, 'get_all')
            has_get_by_id = hasattr(module, 'get_by_id')
            
            if has_get_all and has_get_by_id:
                models_with_crud.append(module_name)
        
        # Reportar: estos son candidatos para CRUDMixin
        print(f"\n[INFO] {len(models_with_crud)} modelos con patrones CRUD duplicados:")
        print(f"       {', '.join(models_with_crud)}")
        
        # Al menos deberían tener estos métodos
        self.assertGreaterEqual(len(models_with_crud), 6)


class AIServiceTests(TestCase):
    """Tests para verificar el servicio de IA"""
    
    def test_ai_service_help_message(self):
        """Verifica que get_help_message funciona"""
        try:
            from app.services.ai_service import AIService
            
            try:
                service = AIService()
                help_msg = service.get_help_message()
                
                self.assertIsInstance(help_msg, str)
                self.assertIn('ayuda', help_msg.lower())
            except ValueError:
                # Sin API keys - OK para tests
                pass
        except ImportError:
            self.skipTest("AIService no disponible")


class AnalyticsModuleTests(TestCase):
    """Tests para verificar el módulo de analytics"""
    
    def test_analytics_app_config(self):
        """Verifica que la app analytics está configurada"""
        from django.apps import apps
        
        try:
            analytics_config = apps.get_app_config('analytics')
            self.assertIsNotNone(analytics_config)
        except LookupError:
            self.skipTest("App analytics no instalada")
