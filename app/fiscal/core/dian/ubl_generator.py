from lxml import etree
from datetime import datetime
from typing import Dict, Any
from decimal import Decimal

class UBLGeneratorService:
    """
    Generador de Facturas Electrónicas en formato UBL 2.1 (DIAN Colombia).
    Construye el XML completo desde datos de factura y configuración fiscal.
    """
    
    # Namespaces UBL 2.1 estándar DIAN
    NAMESPACES = {
        None: "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        "ccts": "urn:un:unece:uncefact:documentation:2",
        "ds": "http://www.w3.org/2000/09/xmldsig#",
        "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
        "qdt": "urn:oasis:names:specification:ubl:schema:xsd:QualifiedDatatypes-2",
        "udt": "urn:un:unece:uncefact:data:specification:UnqualifiedDataTypesSchemaModule:2",
        "sts": "dian:gov:co:facturaelectronica:Structures-2-1",
    }

    def __init__(self, fiscal_config):
        """
        Args:
            fiscal_config: Instancia de FiscalConfig con datos del emisor y resolución.
        """
        self.config = fiscal_config

    def _to_decimal(self, val):
        """Helper para asegurar Decimal desde string o número"""
        from decimal import Decimal
        if not val: return Decimal('0.00')
        if isinstance(val, (int, float, Decimal)): return val
        try:
            return Decimal(str(val).replace(',', ''))
        except:
            return Decimal('0.00')

    def generar_xml(self, factura_data: Dict[str, Any]) -> str:
        """
        Genera el XML UBL 2.1 completo de una factura.
        
        Args:
            factura_data (dict): Diccionario con datos de la factura:
                - numero_factura (str)
                - fecha_emision (date/str)
                - hora_emision (time/str)
                - cliente (dict): {nit, razon_social, direccion, ciudad, email, tipo_persona}
                - items (list): [{descripcion, cantidad, precio_unitario, valor_total, impuestos}]
                - subtotal (Decimal)
                - total_iva (Decimal)
                - total_factura (Decimal)
                - cufe (str) - Generado previamente por FiscalCryptoManager
                
        Returns:
            str: XML formateado como string.
        """
        # Crear elemento raíz Invoice
        nsmap = self.NAMESPACES.copy()
        root = etree.Element(
            "Invoice",
            nsmap=nsmap,
            attrib={
                "{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}UBLExtensions": ""
            }
        )
        
        # Remover atributo temporal
        del root.attrib["{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}UBLExtensions"]
        
        # UBLExtensions (placeholder para firma digital)
        self._add_ubl_extensions(root)
        
        # Metadatos básicos
        self._add_element(root, "cbc:UBLVersionID", "UBL 2.1")
        self._add_element(root, "cbc:CustomizationID", "10")
        self._add_element(root, "cbc:ProfileID", "DIAN 2.1")
        self._add_element(root, "cbc:ProfileExecutionID", str(self.config.ambiente))
        self._add_element(root, "cbc:ID", factura_data['numero_factura'])
        self._add_element(root, "cbc:UUID", factura_data['cufe'], attrib={"schemeName": "CUFE-SHA384"})
        
        # Fechas
        fecha = factura_data['fecha_emision']
        if isinstance(fecha, str):
            fecha_str = fecha
        else:
            fecha_str = fecha.strftime('%Y-%m-%d')
        
        self._add_element(root, "cbc:IssueDate", fecha_str)
        self._add_element(root, "cbc:IssueTime", str(factura_data.get('hora_emision', '12:00:00-05:00')))
        
        # Tipo de documento (01 = Factura de Venta)
        self._add_element(root, "cbc:InvoiceTypeCode", "01")
        
        # Moneda
        self._add_element(root, "cbc:DocumentCurrencyCode", "COP", attrib={"listID": "ISO 4217 Alpha"})
        
        # Resolución de facturación
        self._add_invoice_control(root)
        
        # Partes (Supplier, Customer)
        self._add_accounting_supplier_party(root)
        self._add_accounting_customer_party(root, factura_data['cliente'])
        
        # Totales de impuestos
        self._add_tax_total(root, factura_data)
        
        # Totales monetarios
        self._add_legal_monetary_total(root, factura_data)
        
        # Líneas de factura (items)
        for idx, item in enumerate(factura_data['items'], start=1):
            self._add_invoice_line(root, idx, item)
        
        # Convertir a string con formato
        xml_string = etree.tostring(
            root,
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8'
        ).decode('utf-8')
        
        return xml_string

    def _add_ubl_extensions(self, root):
        """Agrega UBLExtensions (estructura para firma digital)"""
        ext_elem = etree.SubElement(root, "{%s}UBLExtensions" % self.NAMESPACES['ext'])
        ubl_ext = etree.SubElement(ext_elem, "{%s}UBLExtension" % self.NAMESPACES['ext'])
        ext_content = etree.SubElement(ubl_ext, "{%s}ExtensionContent" % self.NAMESPACES['ext'])
        
        # Placeholder para DianExtensions (Software, Proveedor, etc.)
        sts_ext = etree.SubElement(ext_content, "{%s}DianExtensions" % self.NAMESPACES['sts'])
        
        # SoftwareProvider
        soft_prov = etree.SubElement(sts_ext, "{%s}SoftwareProvider" % self.NAMESPACES['sts'])
        self._add_element(soft_prov, "sts:ProviderID", self.config.nit_emisor, attrib={"schemeID": self.config.dv_emisor})
        self._add_element(soft_prov, "sts:SoftwareID", self.config.software_id)
        
        # SoftwareSecurityCode (calculado con PIN + SoftwareID + PrefixNumero)
        # Por ahora placeholder
        soft_sec = etree.SubElement(sts_ext, "{%s}SoftwareSecurityCode" % self.NAMESPACES['sts'])
        soft_sec.text = "placeholder_security_code"

    def _add_invoice_control(self, root):
        """Agrega InvoiceControl con datos de la resolución"""
        inv_ctrl = etree.SubElement(root, "InvoiceControl")
        self._add_element(inv_ctrl, "cbc:InvoiceAuthorization", self.config.numero_resolucion)
        
        # Período de autorización
        auth_period = etree.SubElement(inv_ctrl, "{%s}AuthorizationPeriod" % self.NAMESPACES['cac'])
        if self.config.fecha_resolucion:
            fecha_res = self.config.fecha_resolucion.strftime('%Y-%m-%d')
            self._add_element(auth_period, "cbc:StartDate", fecha_res)
        
        # Rango autorizado
        auth_range = etree.SubElement(inv_ctrl, "{%s}AuthorizedInvoices" % self.NAMESPACES['cac'])
        self._add_element(auth_range, "cbc:Prefix", self.config.prefijo)
        self._add_element(auth_range, "cbc:From", str(self.config.rango_desde))
        self._add_element(auth_range, "cbc:To", str(self.config.rango_hasta))

    def _add_accounting_supplier_party(self, root):
        """Agrega AccountingSupplierParty (Emisor)"""
        supplier = etree.SubElement(root, "{%s}AccountingSupplierParty" % self.NAMESPACES['cac'])
        party = etree.SubElement(supplier, "{%s}Party" % self.NAMESPACES['cac'])
        
        # Identificación
        party_id_elem = etree.SubElement(party, "{%s}PartyIdentification" % self.NAMESPACES['cac'])
        self._add_element(party_id_elem, "cbc:ID", self.config.nit_emisor, attrib={
            "schemeID": self.config.dv_emisor,
            "schemeName": "31"  # 31 = NIT
        })
        
        # Nombre
        party_name = etree.SubElement(party, "{%s}PartyName" % self.NAMESPACES['cac'])
        self._add_element(party_name, "cbc:Name", self.config.razon_social)

    def _add_accounting_customer_party(self, root, cliente_data):
        """Agrega AccountingCustomerParty (Cliente/Adquirente)"""
        customer = etree.SubElement(root, "{%s}AccountingCustomerParty" % self.NAMESPACES['cac'])
        party = etree.SubElement(customer, "{%s}Party" % self.NAMESPACES['cac'])
        
        # Identificación
        party_id_elem = etree.SubElement(party, "{%s}PartyIdentification" % self.NAMESPACES['cac'])
        self._add_element(party_id_elem, "cbc:ID", cliente_data.get('nit', '222222222222'), attrib={
            "schemeID": "1",
            "schemeName": "31"
        })
        
        # Nombre
        party_name = etree.SubElement(party, "{%s}PartyName" % self.NAMESPACES['cac'])
        self._add_element(party_name, "cbc:Name", cliente_data.get('razon_social', 'Cliente Final'))

    def _add_tax_total(self, root, factura_data):
        """Agrega TaxTotal con desglose de IVA"""
        tax_total = etree.SubElement(root, "{%s}TaxTotal" % self.NAMESPACES['cac'])
        
        total_iva = self._to_decimal(factura_data.get('total_iva', 0))
        subtotal = self._to_decimal(factura_data.get('subtotal', 0))

        self._add_element(tax_total, "cbc:TaxAmount", f"{total_iva:.2f}", attrib={"currencyID": "COP"})
        
        # TaxSubtotal (IVA 19%)
        tax_subtotal = etree.SubElement(tax_total, "{%s}TaxSubtotal" % self.NAMESPACES['cac'])
        self._add_element(tax_subtotal, "cbc:TaxableAmount", f"{subtotal:.2f}", attrib={"currencyID": "COP"})
        self._add_element(tax_subtotal, "cbc:TaxAmount", f"{total_iva:.2f}", attrib={"currencyID": "COP"})
        
        tax_category = etree.SubElement(tax_subtotal, "{%s}TaxCategory" % self.NAMESPACES['cac'])
        self._add_element(tax_category, "cbc:Percent", "19.00")
        
        tax_scheme = etree.SubElement(tax_category, "{%s}TaxScheme" % self.NAMESPACES['cac'])
        self._add_element(tax_scheme, "cbc:ID", "01")
        self._add_element(tax_scheme, "cbc:Name", "IVA")

    def _add_legal_monetary_total(self, root, factura_data):
        """Agrega LegalMonetaryTotal con los totales"""
        monetary_total = etree.SubElement(root, "{%s}LegalMonetaryTotal" % self.NAMESPACES['cac'])
        
        subtotal = self._to_decimal(factura_data.get('subtotal', 0))
        total = self._to_decimal(factura_data.get('total_factura', 0))
        
        self._add_element(monetary_total, "cbc:LineExtensionAmount", f"{subtotal:.2f}", attrib={"currencyID": "COP"})
        self._add_element(monetary_total, "cbc:TaxExclusiveAmount", f"{subtotal:.2f}", attrib={"currencyID": "COP"})
        self._add_element(monetary_total, "cbc:TaxInclusiveAmount", f"{total:.2f}", attrib={"currencyID": "COP"})
        self._add_element(monetary_total, "cbc:PayableAmount", f"{total:.2f}", attrib={"currencyID": "COP"})

    def _add_invoice_line(self, parent, line_id, item_data):
        """Agrega una línea de factura"""
        inv_line = etree.SubElement(parent, "{%s}InvoiceLine" % self.NAMESPACES['cac'])
        self._add_element(inv_line, "cbc:ID", str(line_id))
        self._add_element(inv_line, "cbc:InvoicedQuantity", str(item_data.get('cantidad', 1)), attrib={"unitCode": "EA"})
        
        # Usar valores pre-formateados del mapper (ya son strings)
        total_linea = item_data.get('total_linea', item_data.get('subtotal_linea', '0.00'))
        precio_unitario = item_data.get('precio_unitario', '0.00')
        
        self._add_element(inv_line, "cbc:LineExtensionAmount", total_linea, attrib={"currencyID": "COP"})
        
        # Item (descripción del producto)
        item_elem = etree.SubElement(inv_line, "{%s}Item" % self.NAMESPACES['cac'])
        self._add_element(item_elem, "cbc:Description", item_data.get('descripcion', 'Producto'))
        
        # Precio
        price_elem = etree.SubElement(inv_line, "{%s}Price" % self.NAMESPACES['cac'])
        self._add_element(price_elem, "cbc:PriceAmount", precio_unitario, attrib={"currencyID": "COP"})

    def _add_element(self, parent, tag, text=None, attrib=None):
        """Helper para agregar elementos con namespace"""
        if ':' in tag:
            ns_prefix, local_name = tag.split(':', 1)
            ns_uri = self.NAMESPACES.get(ns_prefix)
            elem = etree.SubElement(parent, "{%s}%s" % (ns_uri, local_name), attrib=attrib or {})
        else:
            elem = etree.SubElement(parent, tag, attrib=attrib or {})
        
        if text is not None:
            elem.text = str(text)
        
        return elem
