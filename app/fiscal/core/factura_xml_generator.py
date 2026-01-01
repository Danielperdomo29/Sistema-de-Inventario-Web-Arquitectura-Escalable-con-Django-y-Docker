import logging
import uuid
from decimal import Decimal
from datetime import datetime
from django.conf import settings
from lxml import etree
from app.fiscal.models import FacturaElectronica

logger = logging.getLogger(__name__)

class GeneradorXMLDIAN:
    """
    Generador de XML Factura Electrónica UBL 2.1 (DIAN Colombia)
    """

    def __init__(self):
        self.namespaces = {
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
            'ds': 'http://www.w3.org/2000/09/xmldsig#',
            'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
            'sts': 'dian:gov:co:facturaelectronica:Structures-2-1',
            'xades': 'http://uri.etsi.org/01903/v1.3.2#',
            'xades141': 'http://uri.etsi.org/01903/v1.4.1#',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        }
        
    def generar_xml_factura(self, factura: FacturaElectronica) -> str:
        """
        Genera el XML UBL 2.1 para una factura electrónica
        
        Args:
            factura: Instancia de FacturaElectronica vinculada a una Venta
            
        Returns:
            str: Contenido XML generado
        """
        venta = factura.venta
        
        # --- Obtener Datos faltantes en Modelo Sale ---
        # 1. Empresa (Emisor) - Mock/Config
        empresa = {
            'nit': '900123456',
            'dv': '1',
            'nombre': 'MI EMPRESA S.A.S',
            'direccion': 'Calle 1 # 2-3',
            'telefono': '3000000000',
            'email': 'facturacion@miempresa.com',
            'municipio': '11001',
            'departamento': '11'
        }
        
        # 2. Resolución - Mock/Config
        resolucion = '18760000001'
        
        # 3. Calcular Subtotal/Impuestos (Ya que Sale solo tiene total)
        # Asumiendo que Sale.total es Inc. IVA. O calculando desde detalles.
        # Mejor calcular desde detalles para precisión.
        detalles = list(venta.detalles.all())
        subtotal_venta = sum(d.subtotal for d in detalles)
        # Si los detalles ya tienen IVA, habría que desglosar.
        # Para este MVP, asumiremos que detalle.subtotal es BASE, y Sale.total es Final.
        # O si detalle.subtotal es final, entonces base = subtotal / 1.19
        
        # Vamos a usar Sale.total como PayablenAmount.
        # Y recalcular bases asumiendo un impuesto simple o tomando subtotal = total (regimen simplificado)
        # Ajuste: Usar subtotal calculado de detalles
        
        total_pagar = venta.total
        
        # Lógica de fallback si no hay detalles (que no deberia pasar en completada)
        if not detalles and subtotal_venta == 0:
             subtotal_venta = total_pagar

        # --- Fin Datos faltantes ---

        cliente = venta.cliente
        
        # 1. Crear elemento raíz Invoice
        invoice = etree.Element(
            '{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice', 
            nsmap={None: 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2', **self.namespaces}
        )
        
        # 2. UBLExtensions (Contenedor para firma y datos adicionales)
        exts = etree.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}UBLExtensions')
        
        # Extension DIAN
        uce = etree.SubElement(exts, '{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}UBLExtension')
        ext_content = etree.SubElement(uce, '{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}ExtensionContent')
        dian_ext = etree.SubElement(ext_content, '{dian:gov:co:facturaelectronica:Structures-2-1}DianExtensions')
        etree.SubElement(dian_ext, '{dian:gov:co:facturaelectronica:Structures-2-1}InvoiceControl').append(
            etree.Element('{dian:gov:co:facturaelectronica:Structures-2-1}InvoiceAuthorization', text=resolucion) 
        )
        
        # Extension Firma (Placeholder)
        uce_sig = etree.SubElement(exts, '{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}UBLExtension')
        etree.SubElement(uce_sig, '{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}ExtensionContent') # La firma irá aquí después
        
        # 3. Datos Generales
        etree.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}UBLVersionID').text = 'UBL 2.1'
        etree.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CustomizationID').text = '10' # 10 = Factura Electrónica
        etree.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ProfileID').text = 'DIAN 2.1'
        etree.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID').text = venta.numero_factura
        etree.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}UUID', schemeID='CUFE', schemeName='CUFE-SHA384').text = factura.cufe or ''
        # venta.fecha es DateTime, convertir
        etree.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueDate').text = venta.fecha.strftime('%Y-%m-%d')
        etree.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueTime').text = venta.fecha.strftime('%H:%M:%S-05:00')
        etree.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}InvoiceTypeCode').text = '01' # 01 = Factura de Venta
        
        # 4. Moneda
        etree.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}DocumentCurrencyCode').text = 'COP'
        
        # 5. Emisor (AccountingSupplierParty)
        supplier = etree.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingSupplierParty')
        party = etree.SubElement(supplier, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party')
        # ... Mapeo detallado de Emisor ... (Simplificado - Hardcoded por ahora)
        party_tax_scheme = etree.SubElement(party, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyTaxScheme')
        etree.SubElement(party_tax_scheme, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}RegistrationName').text = empresa['nombre']
        etree.SubElement(party_tax_scheme, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CompanyID', schemeID=empresa['dv'], schemeName='31').text = empresa['nit']
        
        # 6. Receptor (AccountingCustomerParty)
        customer = etree.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingCustomerParty')
        party_cust = etree.SubElement(customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party')
        # ... Mapeo detallado de Receptor ... (Usando datos reales de cliente)
        party_tax_scheme_c = etree.SubElement(party_cust, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyTaxScheme')
        etree.SubElement(party_tax_scheme_c, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}RegistrationName').text = cliente.nombre
        etree.SubElement(party_tax_scheme_c, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CompanyID', schemeName='13').text = cliente.documento if cliente.documento else '222222222222'
        
        # 7. Totales (LegalMonetaryTotal)
        monetary = etree.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}LegalMonetaryTotal')
        etree.SubElement(monetary, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}LineExtensionAmount', currencyID='COP').text = f"{subtotal_venta:.2f}"
        etree.SubElement(monetary, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxExclusiveAmount', currencyID='COP').text = f"{subtotal_venta:.2f}" # Base imponible
        etree.SubElement(monetary, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxInclusiveAmount', currencyID='COP').text = f"{total_pagar:.2f}"
        etree.SubElement(monetary, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PayableAmount', currencyID='COP').text = f"{total_pagar:.2f}"
        
        # 8. Líneas de Factura (InvoiceLine)
        for idx, detalle in enumerate(detalles, 1):
            line = etree.SubElement(invoice, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}InvoiceLine')
            etree.SubElement(line, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID').text = str(idx)
            etree.SubElement(line, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}InvoicedQuantity', unitCode='EA').text = f"{detalle.cantidad:.6f}"
            etree.SubElement(line, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}LineExtensionAmount', currencyID='COP').text = f"{detalle.subtotal:.2f}"
            
            # Item
            item = etree.SubElement(line, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Item')
            etree.SubElement(item, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Description').text = detalle.producto.nombre
            
            # Precio
            price = etree.SubElement(line, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Price')
            etree.SubElement(price, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PriceAmount', currencyID='COP').text = f"{detalle.precio_unitario:.2f}"

        # Retornar XML como string
        return etree.tostring(invoice, pretty_print=True, xml_declaration=True, encoding='UTF-8').decode('utf-8')
