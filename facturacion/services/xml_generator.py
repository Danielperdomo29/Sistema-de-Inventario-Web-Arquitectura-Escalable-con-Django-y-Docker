from lxml import etree
from datetime import datetime
import os
from django.conf import settings

class XMLGeneratorService:
    def __init__(self, invoice_data):
        self.data = invoice_data
        self.invoice_number = invoice_data['venta_info'].get('numero_factura') # Added to JSON or pass separate? 
        # Wait, TaxCalculatorService didn't include invoice_number in JSON explicitly in my memory, let me check. 
        # It has venta_info. But invoice_number is generated in Orchestrator.
        # I should pass invoice_number to TaxCalculator or Orchestrator should inject it.
        # Orchestrator generates number, then calls TaxCalculator.
        self.namespaces = {
            'cac': "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            'cbc': "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
            'ds': "http://www.w3.org/2000/09/xmldsig#",
            'ext': "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
            'sts': "dian:gov:co:facturaelectronica:Structures-2-1",
            'xades': "http://uri.etsi.org/01903/v1.3.2#",
            'xades141': "http://uri.etsi.org/01903/v1.4.1#",
            'xsi': "http://www.w3.org/2001/XMLSchema-instance"
        }

    def generate(self, invoice_number):
        """Genera el XML UBL 2.1"""
        # Elemento Raíz
        invoice = etree.Element("Invoice", nsmap=self.namespaces)
        invoice.set("xmlns", "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2")
        
        # UBLVersionID
        ubl_version = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}UBLVersionID")
        ubl_version.text = "UBL 2.1"
        
        # CustomizationID
        customization = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CustomizationID")
        customization.text = "10" 
        
        # ID Factura
        inv_id = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID")
        inv_id.text = invoice_number
        
        # Fecha Emisión
        issue_date = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueDate")
        issue_date.text = self.data['venta_info']['fecha']
        
        # Moneda
        doc_currency = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}DocumentCurrencyCode")
        doc_currency.text = "COP"
        
        # Emisor
        supplier_party = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingSupplierParty")
        party = etree.SubElement(supplier_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party")
        party_name_xml = etree.SubElement(party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyName")
        name = etree.SubElement(party_name_xml, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name")
        name.text = "MI EMPRESA S.A.S" 
        
        # Receptor (Cliente)
        customer_party = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingCustomerParty")
        cust_party = etree.SubElement(customer_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party")
        cust_party_tax = etree.SubElement(cust_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyTaxScheme")
        reg_name = etree.SubElement(cust_party_tax, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}RegistrationName")
        reg_name.text = self.data['cliente']['nombre']
        
        # Tax Totals (Global)
        for tax in self.data['totales_impuestos']:
            tax_total = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxTotal")
            tax_amount = etree.SubElement(tax_total, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxAmount")
            tax_amount.set("currencyID", "COP")
            tax_amount.text = str(tax['valor_total_impuesto'])
            
            tax_subtotal = etree.SubElement(tax_total, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxSubtotal")
            ts_amount = etree.SubElement(tax_subtotal, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxableAmount")
            ts_amount.set("currencyID", "COP")
            ts_amount.text = str(tax['base_imponible'])
            
            ts_tax_amount = etree.SubElement(tax_subtotal, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxAmount")
            ts_tax_amount.set("currencyID", "COP")
            ts_tax_amount.text = str(tax['valor_total_impuesto'])
            
            tax_category = etree.SubElement(tax_subtotal, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxCategory")
            percent = etree.SubElement(tax_category, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Percent")
            percent.text = str(tax['porcentaje'])
            
            tax_scheme = etree.SubElement(tax_category, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxScheme")
            scheme_id = etree.SubElement(tax_scheme, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID")
            scheme_id.text = tax['codigo_impuesto']
            scheme_name = etree.SubElement(tax_scheme, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name")
            scheme_name.text = tax['nombre']

        # Totales
        monetary_total = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}LegalMonetaryTotal")
        
        line_extension = etree.SubElement(monetary_total, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}LineExtensionAmount")
        line_extension.set("currencyID", "COP")
        line_extension.text = str(self.data['resumen_factura']['subtotal'])
        
        tax_exclusive = etree.SubElement(monetary_total, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxExclusiveAmount")
        tax_exclusive.set("currencyID", "COP")
        tax_exclusive.text = str(self.data['resumen_factura']['subtotal'])
        
        tax_inclusive = etree.SubElement(monetary_total, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxInclusiveAmount")
        tax_inclusive.set("currencyID", "COP")
        tax_inclusive.text = str(self.data['resumen_factura']['total_factura'])
        
        payable_amount = etree.SubElement(monetary_total, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PayableAmount")
        payable_amount.set("currencyID", "COP")
        payable_amount.text = str(self.data['resumen_factura']['total_factura'])
        
        # Líneas de factura
        for idx, item in enumerate(self.data['detalles_productos'], 1):
            line = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}InvoiceLine")
            line_id = etree.SubElement(line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID")
            line_id.text = str(idx)
            
            invoiced_qty = etree.SubElement(line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}InvoicedQuantity")
            invoiced_qty.set("unitCode", "94") 
            invoiced_qty.text = str(item['cantidad'])
            
            line_amount = etree.SubElement(line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}LineExtensionAmount")
            line_amount.set("currencyID", "COP")
            # LineExtensionAmount is Base Total (Price * Qty)
            base_total = item['valor_unitario'] * item['cantidad']
            line_amount.text = f"{base_total:.2f}"
            
            # Tax Info per line
            tax_total_line = etree.SubElement(line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxTotal")
            tax_amt_line = etree.SubElement(tax_total_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxAmount")
            tax_amt_line.set("currencyID", "COP")
            tax_amt_line.text = str(item['valor_iva'])
            
            tax_subtotal_line = etree.SubElement(tax_total_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxSubtotal")
            ts_amt_line = etree.SubElement(tax_subtotal_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxableAmount")
            ts_amt_line.set("currencyID", "COP")
            ts_amt_line.text = f"{base_total:.2f}"
            
            ts_tax_amt_line = etree.SubElement(tax_subtotal_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxAmount")
            ts_tax_amt_line.set("currencyID", "COP")
            ts_tax_amt_line.text = str(item['valor_iva'])
            
            tax_cat_line = etree.SubElement(tax_subtotal_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxCategory")
            per_line = etree.SubElement(tax_cat_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Percent")
            per_line.text = str(item['tasa_iva'])
            
            tax_sch_line = etree.SubElement(tax_cat_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxScheme")
            sch_id_line = etree.SubElement(tax_sch_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID")
            sch_id_line.text = item['tax_type_id']
            sch_name_line = etree.SubElement(tax_sch_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name")
            sch_name_line.text = "IVA" if item['tax_type_id'] == '01' else "INC"
            
            item_xml = etree.SubElement(line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Item")
            desc = etree.SubElement(item_xml, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Description")
            desc.text = item['descripcion']
            
            price = etree.SubElement(line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Price")
            price_amt = etree.SubElement(price, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PriceAmount")
            price_amt.set("currencyID", "COP")
            price_amt.text = str(item['valor_unitario'])

        xml_content = etree.tostring(invoice, pretty_print=True, xml_declaration=True, encoding='UTF-8')
        return xml_content
