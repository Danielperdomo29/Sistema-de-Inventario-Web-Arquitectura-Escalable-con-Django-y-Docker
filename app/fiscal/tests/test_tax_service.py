from django.test import TestCase
from datetime import datetime, timedelta
from decimal import Decimal
from app.fiscal.services.tax_service import TaxCalculatorService
from app.models import Product, Sale, SaleDetail, Purchase, PurchaseDetail, Client, Supplier, UserAccount
import unittest
from django.utils import timezone

class TaxServiceTestCase(TestCase):
    def setUp(self):
        # Create user for FK
        self.user = UserAccount.objects.create(
            username='testfiscal',
            email='test@fiscal.com',
            first_name='Test',
            last_name='Fiscal'
        )

        # Crear productos con diferentes configuraciones de impuesto
        self.product_19 = Product.objects.create(
            nombre="Producto 19%",
            descripcion="Producto con IVA 19% no incluido",
            precio_venta=100.00,
            tax_percentage=Decimal('19.00'),
            is_tax_included=False,
            precio_compra=50.00,
            stock_actual=100,
            stock_minimo=10,
            codigo="P19"
        )
        
        self.product_5 = Product.objects.create(
            nombre="Producto 5%",
            descripcion="Producto con IVA 5% no incluido",
            precio_venta=50.00,
            tax_percentage=Decimal('5.00'),
            is_tax_included=False,
            precio_compra=25.00,
            stock_actual=100,
            stock_minimo=10,
            codigo="P5"
        )
        
        self.product_0 = Product.objects.create(
            nombre="Producto 0%",
            descripcion="Producto exento de IVA",
            precio_venta=30.00,
            tax_percentage=Decimal('0.00'),
            is_tax_included=False,
            precio_compra=15.00,
            stock_actual=100,
            stock_minimo=10,
            codigo="P0"
        )
        
        self.product_19_included = Product.objects.create(
            nombre="Producto 19% Incluido",
            descripcion="Producto con IVA 19% incluido en precio",
            precio_venta=119.00,  # Precio con IVA incluido
            tax_percentage=Decimal('19.00'),
            is_tax_included=True,
            precio_compra=60.00,
            stock_actual=100,
            stock_minimo=10,
            codigo="P19INC"
        )
        
        # Crear cliente y proveedor
        self.client = Client.objects.create(
            nombre="Cliente de Prueba",
            email="cliente@prueba.com",
            telefono="123456789",
            documento="123456789"
        )
        
        self.supplier = Supplier.objects.create(
            nombre="Proveedor de Prueba",
            email="proveedor@prueba.com",
            telefono="987654321"
        )
        
        # Fechas para pruebas
        self.start_date = timezone.now().date() - timedelta(days=60)
        self.end_date = timezone.now().date()
    
    def test_calculate_tax_on_sale_not_included(self):
        """Test cálculo de impuesto en venta con IVA no incluido"""
        sale_detail = type('obj', (object,), {
            'producto': self.product_19,
            'subtotal': Decimal('200.00'),
        })
        
        result = TaxCalculatorService.calculate_tax_on_sale(sale_detail)
        
        # Base: 200, IVA: 200 * 19% = 38
        self.assertEqual(result['base'], Decimal('200.00'))
        self.assertEqual(result['tax'], Decimal('38.00'))
        self.assertEqual(result['rate'], Decimal('19.00'))
    
    def test_calculate_tax_on_sale_included(self):
        """Test cálculo de impuesto en venta con IVA incluido"""
        sale_detail = type('obj', (object,), {
            'producto': self.product_19_included,
            'subtotal': Decimal('119.00'),
        })
        
        result = TaxCalculatorService.calculate_tax_on_sale(sale_detail)
        
        # Precio con IVA incluido: 119
        # Base: 119 / 1.19 = 100
        # IVA: 119 - 100 = 19
        self.assertEqual(result['base'], Decimal('100.00'))
        self.assertEqual(result['tax'], Decimal('19.00'))
        self.assertEqual(result['rate'], Decimal('19.00'))
    
    def test_get_iva_generado(self):
        """Test cálculo completo de IVA generado"""
        # Crear ventas de prueba
        sale = Sale.objects.create(
            cliente=self.client,
            usuario=self.user,
            fecha=timezone.now(),  # datetime
            estado='completada',
            total=500.00,
            numero_factura=f"TEST-{datetime.now().timestamp()}"
        )
        
        SaleDetail.objects.create(
            venta=sale,
            producto=self.product_19,
            cantidad=2,
            precio_unitario=100.00,
            subtotal=200.00
        )
        
        SaleDetail.objects.create(
            venta=sale,
            producto=self.product_5,
            cantidad=1,
            precio_unitario=50.00,
            subtotal=50.00
        )
        
        SaleDetail.objects.create(
            venta=sale,
            producto=self.product_19_included,
            cantidad=1,
            precio_unitario=119.00,
            subtotal=119.00
        )
        
        result = TaxCalculatorService.get_iva_generado(self.start_date, self.end_date)
        
        # Verificar estructura
        self.assertIn('tarifas', result)
        self.assertIn('total_base', result)
        self.assertIn('total_tax', result)
        self.assertIn('ventas_detalle', result)
        
        # Verificar tarifas
        self.assertIn('19', result['tarifas'])
        self.assertIn('5', result['tarifas'])
        
        # Verificar totales (aproximados por decimales)
        self.assertTrue(result['total_tax'] > Decimal('0.00'))
    
    def test_get_iva_descontable(self):
        """Test cálculo completo de IVA descontable"""
        # Crear compras de prueba
        purchase = Purchase.objects.create(
            proveedor=self.supplier,
            usuario=self.user,
            fecha=timezone.now(),
            estado='completada',
            total=238.00,
            numero_factura=f"TEST-BUY-{datetime.now().timestamp()}"
        )
        
        PurchaseDetail.objects.create(
            compra=purchase,
            producto=self.product_19,
            cantidad=2,
            precio_unitario=100.00,
            subtotal=200.00
        )
        
        result = TaxCalculatorService.get_iva_descontable(self.start_date, self.end_date)
        
        # Verificar estructura
        self.assertIn('tarifas', result)
        self.assertIn('total_base', result)
        self.assertIn('total_tax', result)
        self.assertIn('compras_detalle', result)
        
        # Verificar tarifas
        self.assertIn('19', result['tarifas'])
        
        # IVA descontable: 200 * 19% = 38
        self.assertEqual(result['tarifas']['19']['tax'], Decimal('38.00'))
    
    def test_get_period_dates_bimestral(self):
        """Test cálculo de fechas para período bimestral"""
        start_date, end_date = TaxCalculatorService.get_period_dates(2024, 'bimestral', 1)
        
        # Bimestre 1: Enero 1 - Febrero 29 (2024 es bisiesto)
        self.assertEqual(start_date, datetime(2024, 1, 1).date())
        self.assertEqual(end_date, datetime(2024, 2, 29).date())
        
        # Bimestre 6: Noviembre 1 - Diciembre 31
        start_date, end_date = TaxCalculatorService.get_period_dates(2024, 'bimestral', 6)
        self.assertEqual(start_date, datetime(2024, 11, 1).date())
        self.assertEqual(end_date, datetime(2024, 12, 31).date())
    
    def test_get_period_dates_cuatrimestral(self):
        """Test cálculo de fechas para período cuatrimestral"""
        start_date, end_date = TaxCalculatorService.get_period_dates(2024, 'cuatrimestral', 1)
        
        # Cuatrimestre 1: Enero 1 - Abril 30
        self.assertEqual(start_date, datetime(2024, 1, 1).date())
        self.assertEqual(end_date, datetime(2024, 4, 30).date())
        
        # Cuatrimestre 3: Septiembre 1 - Diciembre 31
        start_date, end_date = TaxCalculatorService.get_period_dates(2024, 'cuatrimestral', 3)
        self.assertEqual(start_date, datetime(2024, 9, 1).date())
        self.assertEqual(end_date, datetime(2024, 12, 31).date())
    
    def test_get_declaracion_iva(self):
        """Test generación completa de declaración de IVA"""
        # Crear ventas y compras para el período
        sale = Sale.objects.create(
            cliente=self.client,
            usuario=self.user,
            fecha=timezone.now(),
            estado='completada',
            total=238.00,
            numero_factura=f"TEST-DEC-{datetime.now().timestamp()}"
        )
        
        SaleDetail.objects.create(
            venta=sale,
            producto=self.product_19,
            cantidad=2,
            precio_unitario=100.00,
            subtotal=200.00
        )
        
        purchase = Purchase.objects.create(
            proveedor=self.supplier,
            usuario=self.user,
            fecha=timezone.now(),
            estado='completada',
            total=119.00,
            numero_factura=f"TEST-BUY-DEC-{datetime.now().timestamp()}"
        )
        
        PurchaseDetail.objects.create(
            compra=purchase,
            producto=self.product_19_included,
            cantidad=1,
            precio_unitario=119.00,
            subtotal=119.00
        )
        
        # Obtener declaración
        # Usamos el año actual y bimestre actual para asegurar que coincida con timezone.now()
        now = datetime.now()
        bimestre = ((now.month - 1) // 2) + 1
        
        declaracion = TaxCalculatorService.get_declaracion_iva(
            year=now.year,
            period_type='bimestral',
            period_number=bimestre
        )
        
        # Verificar estructura
        self.assertIn('periodo', declaracion)
        self.assertIn('iva_generado', declaracion)
        self.assertIn('iva_descontable', declaracion)
        self.assertIn('resumen', declaracion)
        self.assertIn('metadata', declaracion)
        
        # Verificar cálculos
        # IVA generado: 200 * 19% = 38
        # IVA descontable: 119 / 1.19 = 100 * 19% = 19
        # IVA neto: 38 - 19 = 19
        self.assertEqual(declaracion['iva_generado']['tarifas']['19']['tax'], Decimal('38.00'))
        self.assertEqual(declaracion['iva_descontable']['tarifas']['19']['tax'], Decimal('19.00'))
        self.assertEqual(declaracion['resumen']['iva_neto_a_pagar'], Decimal('19.00'))
    
    def test_empty_period(self):
        """Test para período sin transacciones"""
        result = TaxCalculatorService.get_iva_generado(
            datetime(2023, 1, 1).date(),
            datetime(2023, 1, 31).date()
        )
        
        self.assertEqual(result['total_base'], Decimal('0.00'))
        self.assertEqual(result['total_tax'], Decimal('0.00'))
        self.assertEqual(len(result['ventas_detalle']), 0)
    
    def test_invalid_period_number(self):
        """Test para número de período inválido"""
        with self.assertRaises(ValueError):
            TaxCalculatorService.get_period_dates(2024, 'bimestral', 7)
        
        with self.assertRaises(ValueError):
            TaxCalculatorService.get_period_dates(2024, 'cuatrimestral', 4)
    
    def test_invalid_period_type(self):
        """Test para tipo de período inválido"""
        with self.assertRaises(ValueError):
            TaxCalculatorService.get_period_dates(2024, 'mensual', 1)
