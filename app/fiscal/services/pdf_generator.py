"""
Generador de PDF para facturas electrónicas DIAN.
Crea representación gráfica profesional similar a tickets térmicos.
"""
from io import BytesIO
from decimal import Decimal
from datetime import datetime
import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.platypus import PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

from django.conf import settings
from app.fiscal.models import FiscalConfig


class InvoicePDFGenerator:
    """
    Generador de PDF para facturas electrónicas DIAN.
    Formato compatible con impresoras de 80mm y carta.
    """
    
    def __init__(self, factura_data: dict, fiscal_config: FiscalConfig):
        """
        Inicializa el generador de PDF.
        
        Args:
            factura_data: Datos de la factura (del UBLMapper)
            fiscal_config: Configuración fiscal de la empresa
        """
        self.factura_data = factura_data
        self.fiscal_config = fiscal_config
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configura estilos personalizados para el PDF."""
        # Estilo para encabezado de empresa
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading1'],
            fontSize=14,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=6
        ))
        
        # Estilo para información de empresa
        self.styles.add(ParagraphStyle(
            name='CompanyInfo',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=3
        ))
        
        # Estilo para secciones
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=10,
            textColor=colors.black,
            spaceBefore=10,
            spaceAfter=6,
            alignment=TA_LEFT
        ))
        
        # Estilo para datos pequeños
        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontSize=7,
            textColor=colors.black,
            alignment=TA_LEFT
        ))
        
        # Estilo para totales
        self.styles.add(ParagraphStyle(
            name='TotalText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_RIGHT,
            fontName='Helvetica-Bold'
        ))
    
    def generar_pdf(self, output_path: str = None) -> BytesIO:
        """
        Genera el PDF de la factura.
        
        Args:
            output_path: Ruta donde guardar el PDF (opcional)
            
        Returns:
            BytesIO con el contenido del PDF
        """
        buffer = BytesIO()
        
        # Configurar documento (80mm width ≈ 226 points)
        # Usar ancho de ticket térmico
        page_width = 80 * mm
        page_height = 297 * mm  # Alto variable
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=(page_width, page_height),
            rightMargin=5*mm,
            leftMargin=5*mm,
            topMargin=5*mm,
            bottomMargin=5*mm
        )
        
        # Construir elementos del PDF
        story = []
        
        # 1. Encabezado de empresa
        story.extend(self._build_header())
        
        # 2. Código de barras del número de factura
        # TEMPORALMENTE DESHABILITADO - TODO: Arreglar código de barras
        # story.append(self._build_barcode())
        # story.append(Spacer(1, 3*mm))
        
        # 3. Información de la factura
        story.extend(self._build_invoice_info())
        
        # 4. Información del cliente
        story.extend(self._build_customer_info())
        
        # 5. Forma de pago
        story.extend(self._build_payment_info())
        
        # 6. Línea separadora
        story.append(Spacer(1, 3*mm))
        
        # 7. Tabla de productos
        story.append(self._build_items_table())
        
        # 8. Totales
        story.extend(self._build_totals())
        
        # 9. Información de resolución DIAN
        story.extend(self._build_resolution_info())
        
        # 10. Código QR
        story.append(Spacer(1, 5*mm))
        story.append(self._build_qr_code())
        
        # 11. CUFE
        story.extend(self._build_cufe())
        
        # 12. Mensaje de agradecimiento
        story.extend(self._build_footer())
        
        # Generar PDF
        doc.build(story)
        
        # Guardar si se especifica ruta
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
        
        buffer.seek(0)
        return buffer
    
    def _build_header(self) -> list:
        """Construye el encabezado con información de la empresa."""
        elements = []
        
        # Nombre de la empresa
        company_name = Paragraph(
            f"<b>Perdomo Industries S.A.S</b>",
            self.styles['CompanyName']
        )
        elements.append(company_name)

        # Subtítulos
        elements.append(Paragraph("Facturación Electrónica", self.styles['CompanyInfo']))
        elements.append(Paragraph("Sistema de Inventario y Facturación", self.styles['CompanyInfo']))
        elements.append(Spacer(1, 2*mm))
        
        # NIT
        nit_text = f"NIT: {self.fiscal_config.nit_emisor}-{self.fiscal_config.dv_emisor}"
        elements.append(Paragraph(nit_text, self.styles['CompanyInfo']))
        
        # Dirección (si está disponible en factura_data)
        if 'supplier' in self.factura_data and 'address' in self.factura_data['supplier']:
            address = self.factura_data['supplier']['address']
            elements.append(Paragraph(address, self.styles['CompanyInfo']))
        
        # Teléfono y email (si están disponibles)
        if 'supplier' in self.factura_data:
            supplier = self.factura_data['supplier']
            if 'phone' in supplier:
                elements.append(Paragraph(f"Tel: {supplier['phone']}", self.styles['CompanyInfo']))
            if 'email' in supplier:
                elements.append(Paragraph(supplier['email'], self.styles['CompanyInfo']))
        
        elements.append(Spacer(1, 5*mm))
        
        return elements
    
    def _build_barcode(self):
        """Genera código de barras del número de factura."""
        from reportlab.graphics import renderPDF
        from reportlab.platypus.flowables import Flowable
        
        numero_factura = self.factura_data.get('numero_factura', 'N/A')
        
        # Crear código de barras Code128
        barcode = code128.Code128(
            numero_factura,
            barHeight=10*mm,
            barWidth=0.5*mm
        )
        
        # Crear Drawing y agregar el barcode
        drawing = Drawing(70*mm, 12*mm)
        drawing.add(barcode)
        
        return drawing
    
    def _build_invoice_info(self) -> list:
        """Construye información básica de la factura."""
        elements = []
        
        numero_factura = self.factura_data.get('numero_factura', 'N/A')
        fecha_emision = self.factura_data.get('fecha_emision', 'N/A')
        hora_emision = self.factura_data.get('hora_emision', 'N/A')
        
        elements.append(Paragraph(
            f"<b>Factura Electrónica de Venta: {numero_factura}</b>",
            self.styles['SmallText']
        ))
        elements.append(Paragraph(
            f"Fecha: {fecha_emision} Hora: {hora_emision}",
            self.styles['SmallText']
        ))
        elements.append(Spacer(1, 3*mm))
        
        return elements
    
    def _build_customer_info(self) -> list:
        """Construye información del cliente."""
        elements = []
        
        if 'customer' in self.factura_data:
            customer = self.factura_data['customer']
            
            elements.append(Paragraph("<b>Cliente:</b>", self.styles['SmallText']))
            elements.append(Paragraph(
                customer.get('name', 'CONSUMIDOR FINAL'),
                self.styles['SmallText']
            ))
            
            if 'nit' in customer:
                elements.append(Paragraph(
                    f"NIT: {customer['nit']}",
                    self.styles['SmallText']
                ))
            
            if 'address' in customer:
                elements.append(Paragraph(
                    f"Direc: {customer['address']}",
                    self.styles['SmallText']
                ))
            
            elements.append(Spacer(1, 3*mm))
        
        return elements
    
    def _build_payment_info(self) -> list:
        """Construye información de forma de pago."""
        elements = []
        
        payment_mean = self.factura_data.get('payment_means', 'CONTADO')
        
        elements.append(Paragraph(
            f"<b>Forma de Pago:</b> {payment_mean}",
            self.styles['SmallText']
        ))
        elements.append(Spacer(1, 3*mm))
        
        return elements
    
    def _build_items_table(self):
        """Construye tabla de productos."""
        items = self.factura_data.get('items', [])
        
        # Datos de la tabla
        # Datos de la tabla
        data = [
            ['Cant', 'Desc', 'VrUnit', 'Total']
        ]
        
        for item in items:
            # Helper robusto para números
            def get_f(key, default=0.0):
                val = item.get(key, default)
                if isinstance(val, (int, float, Decimal)): return float(val)
                try:
                    return float(str(val).replace(',', '').replace('$', ''))
                except (ValueError, TypeError):
                    return float(default)

            cantidad = int(get_f('cantidad', 0))
            precio = get_f('precio_unitario', 0)
            total_linea = cantidad * precio # Recalcular para asegurar consistencia

            data.append([
                str(cantidad),
                item.get('descripcion', '')[:25],
                f"${precio:,.0f}",
                f"${total_linea:,.0f}"
            ])
        
        # Crear tabla (anchos ajustados para 80mm: 10, 35, 15, 15 => 75mm total)
        table = Table(data, colWidths=[10*mm, 35*mm, 15*mm, 15*mm])
        

        
        # Estilo de la tabla
        table.setStyle(TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Contenido
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 6),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Cantidad centrada
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),  # Precios alineados a derecha
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        return table
    
    def _build_totals(self) -> list:
        """Construye sección de totales."""
        elements = []
        
        totals = self.factura_data.get('totales', {}) # Corregido: UBLMapper usa 'totales'
        tax_totals = self.factura_data.get('impuestos', {})
        
        elements.append(Spacer(1, 3*mm))
        
        # Subtotal
        # Helper robusto para totales
        def get_f(val):
            if isinstance(val, (int, float, Decimal)): return float(val)
            try:
                return float(str(val).replace(',', '').replace('$', ''))
            except:
                return 0.0

        totals = self.factura_data.get('totales', {}) # Corregido: UBLMapper usa 'totales'
        tax_totals = self.factura_data.get('impuestos', {}) # Corregido: llave 'impuestos' viene de UBLMapper
        
        # Extracción segura de valores
        subtotal = get_f(totals.get('subtotal', 0))
        # Total impuestos (IVA) - UBLMapper usa 'total_iva'
        iva_total = get_f(totals.get('total_iva', 0)) 
        if iva_total == 0:
             # Intentar buscar en impuestos si no está en totals
             iva_total = get_f(tax_totals.get('iva', {}).get('total', 0))
             
        total = get_f(totals.get('total', 0))
        
        elements.append(Spacer(1, 3*mm))
        
        elements.append(Paragraph(
            f"Subtotal: ${subtotal:,.2f}",
            self.styles['SmallText']
        ))
        
        elements.append(Paragraph(
            f"IVA (19%): ${iva_total:,.2f}",
            self.styles['SmallText']
        ))
        
        elements.append(Paragraph(
            f"<b>TOTAL: ${total:,.2f}</b>",
            self.styles['TotalText']
        ))
        
        elements.append(Spacer(1, 5*mm))
        
        return elements
    
    def _build_resolution_info(self) -> list:
        """Construye información de resolución DIAN."""
        elements = []
        
        elements.append(Paragraph(
            f"<b>Resolución DIAN No. {self.fiscal_config.numero_resolucion}</b>",
            self.styles['SmallText']
        ))
        res_date = self.fiscal_config.fecha_resolucion
        res_date_str = str(res_date) if res_date else "N/A"
        
        elements.append(Paragraph(
            f"Fecha: {res_date_str}",
            self.styles['SmallText']
        ))
        elements.append(Paragraph(
            f"Prefijo: {self.fiscal_config.prefijo}",
            self.styles['SmallText']
        ))
        elements.append(Paragraph(
            f"Numeración autorizada del {self.fiscal_config.rango_desde} al {self.fiscal_config.rango_hasta}",
            self.styles['SmallText']
        ))
        
        return elements
    
    def _build_qr_code(self):
        """Genera código QR con datos de validación."""
        # Datos para QR según DIAN
        cufe = self.factura_data.get('cufe', '')
        numero_factura = self.factura_data.get('numero_factura', '')
        fecha = self.factura_data.get('fecha_emision', '')
        nit_emisor = f"{self.fiscal_config.nit_emisor}-{self.fiscal_config.dv_emisor}"
        
        customer = self.factura_data.get('customer', {})
        nit_cliente = customer.get('nit', '222222222222')
        
        total = self.factura_data.get('totals', {}).get('total', 0)
        
        # Formato QR DIAN
        qr_data = f"NumFac: {numero_factura}\n"
        qr_data += f"FecFac: {fecha}\n"
        qr_data += f"NitFac: {nit_emisor}\n"
        qr_data += f"DocAdq: {nit_cliente}\n"
        qr_data += f"ValFac: {total:.2f}\n"
        qr_data += f"CUFE: {cufe}"
        
        # Generar QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=3,
            border=1,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Convertir a imagen
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Guardar en buffer
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Crear elemento Image para ReportLab
        qr_image = Image(img_buffer, width=50*mm, height=50*mm)
        qr_image.hAlign = 'CENTER'
        
        return qr_image
    
    def _build_cufe(self) -> list:
        """Construye sección del CUFE."""
        elements = []
        
        cufe = self.factura_data.get('cufe', 'N/A')
        
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph("<b>CUFE:</b>", self.styles['SmallText']))
        
        # Dividir CUFE en líneas para mejor legibilidad
        cufe_lineas = [cufe[i:i+40] for i in range(0, len(cufe), 40)]
        for linea in cufe_lineas:
            elements.append(Paragraph(linea, self.styles['SmallText']))
        
        return elements
    
    def _build_footer(self) -> list:
        """Construye pie de página."""
        elements = []
        
        elements.append(Spacer(1, 5*mm))
        elements.append(Paragraph(
            "<b>***GRACIAS POR SU COMPRA***</b>",
            self.styles['CompanyInfo']
        ))
        elements.append(Paragraph(
            "Verifique su factura en www.dian.gov.co",
            self.styles['SmallText']
        ))
        
        return elements
