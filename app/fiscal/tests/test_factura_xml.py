from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from app.models.user_account import UserAccount
from app.models.client import Client
from app.models.sale import Sale, SaleDetail
from app.models.product import Product
from app.fiscal.models import FacturaElectronica
from app.fiscal.core.factura_xml_generator import GeneradorXMLDIAN

class FacturaXMLTest(TestCase):
    def setUp(self):
        # 1. Crear Usuario
        self.user = UserAccount.objects.create(
            username='xml_tester',
            email='xml@test.com',
            first_name='XML',
            last_name='Tester'
        )
        
        # 2. Crear Cliente
        self.cliente = Client.objects.create(
            nombre='Cliente XML',
            documento='999999999',
            email='clientexml@test.com'
        )
        
        # 3. Crear Producto
        self.producto = Product.objects.create(
            nombre='Producto XML Test',
            precio=Decimal('10000.00'),
            stock=100
        )
        
        # 4. Crear Venta
        self.venta = Sale.objects.create(
            numero_factura='SETT-100',
            fecha=timezone.now(),
            total=Decimal('11900.00'), # 10k + IVA?
            usuario=self.user,
            estado='completada',
            cliente=self.cliente
        )
        
        # 5. Detalle
        SaleDetail.objects.create(
            venta=self.venta,
            producto=self.producto,
            cantidad=1,
            precio_unitario=Decimal('10000.00'),
            subtotal=Decimal('10000.00'),
            total=Decimal('10000.00') # MVP assumption
        )
        
        # 6. Factura Electronica
        self.factura_el, _ = FacturaElectronica.objects.get_or_create(
            venta=self.venta,
            defaults={'cufe': 'test-cufe-12345'}
        )
        
    def test_generar_xml_estructura_basica(self):
        """Prueba que el XML se genere con los tags UBL principales"""
        generador = GeneradorXMLDIAN()
        xml = generador.generar_xml_factura(self.factura_el)
        
        # Verificaciones básicas
        self.assertTrue(xml.startswith('<'), "El output debe empezar como XML")
        self.assertIn('urn:oasis:names:specification:ubl:schema:xsd:Invoice-2', xml)
        self.assertIn('<cbc:ID>SETT-100</cbc:ID>', xml)
        self.assertIn('<cbc:IssueDate>', xml)
        self.assertIn(f'<cbc:RegistrationName>{self.cliente.nombre}</cbc:RegistrationName>', xml)
        
    def test_xml_contiene_items(self):
        """Prueba que el XML contenga las líneas de detalle"""
        generador = GeneradorXMLDIAN()
        xml = generador.generar_xml_factura(self.factura_el)
        
        self.assertIn('<cac:InvoiceLine>', xml)
        self.assertIn(f'<cbc:Description>{self.producto.nombre}</cbc:Description>', xml)
        
    def test_namespace_dian_presente(self):
        """Prueba que las extensiones DIAN estén presentes"""
        generador = GeneradorXMLDIAN()
        xml = generador.generar_xml_factura(self.factura_el)
        
        self.assertIn('dian:gov:co:facturaelectronica:Structures-2-1', xml)
        self.assertIn('InvoiceAuthorization', xml)
