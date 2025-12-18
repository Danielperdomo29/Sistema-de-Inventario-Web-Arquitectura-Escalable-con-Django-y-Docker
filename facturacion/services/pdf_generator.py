from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from io import BytesIO
import os

class PDFGeneratorService:
    def __init__(self, invoice_data):
        self.data = invoice_data

    def generate(self, invoice_number):
        """Genera el PDF de la factura"""
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Header
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1 * inch, height - 1 * inch, "FACTURA ELECTRÓNICA DE VENTA")
        
        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, height - 1.3 * inch, "MI EMPRESA S.A.S")
        c.drawString(1 * inch, height - 1.45 * inch, "NIT: 900.123.456-7")
        
        # Invoice Info
        c.setFont("Helvetica-Bold", 12)
        c.drawString(4.5 * inch, height - 1 * inch, f"N° {invoice_number}")
        c.setFont("Helvetica", 10)
        c.drawString(4.5 * inch, height - 1.3 * inch, f"Fecha: {self.data['venta_info']['fecha']}")
        
        # Client Info
        c.line(1 * inch, height - 1.6 * inch, 7.5 * inch, height - 1.6 * inch)
        c.drawString(1 * inch, height - 1.9 * inch, f"Cliente: {self.data['cliente']['nombre']}")
        c.drawString(1 * inch, height - 2.1 * inch, f"NIT/CC: {self.data['cliente']['identificacion']}")
        
        # Table Header
        y = height - 2.5 * inch
        c.line(1 * inch, y, 7.5 * inch, y)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(1 * inch, y - 10, "Producto")
        c.drawString(3.5 * inch, y - 10, "Cant")
        c.drawString(4.0 * inch, y - 10, "Precio Base")
        c.drawString(5.0 * inch, y - 10, "IVA %")
        c.drawString(5.5 * inch, y - 10, "Impuesto")
        c.drawString(6.5 * inch, y - 10, "Total")
        c.line(1 * inch, y - 15, 7.5 * inch, y - 15)
        
        # Items
        y -= 30
        c.setFont("Helvetica", 9)
        for item in self.data['detalles_productos']:
            # Truncate text
            name = item['descripcion'][:30]
            c.drawString(1 * inch, y, name)
            c.drawString(3.5 * inch, y, f"{item['cantidad']}")
            c.drawString(4.0 * inch, y, f"${item['valor_unitario']:,.0f}")
            c.drawString(5.0 * inch, y, f"{item['tasa_iva']}%")
            c.drawString(5.5 * inch, y, f"${item['valor_iva']:,.0f}")
            # Use total_item here or value unitario * qty? The prompt asked for "Total por Item" which is in JSON.
            # But visually usually we show Line Total.
            # Let's show item['total_item'] which is Base + Tax * Qty.
            c.drawString(6.5 * inch, y, f"${item['total_item']:,.0f}")
            y -= 15
            
        # Summary & Taxes
        y -= 20
        c.line(1 * inch, y, 7.5 * inch, y)
        
        # Tax Breakdown Table (Left Side)
        tax_y = y - 20
        c.setFont("Helvetica-Bold", 8)
        c.drawString(1 * inch, tax_y, "Desglose de Impuestos")
        tax_y -= 15
        c.drawString(1 * inch, tax_y, "Impuesto")
        c.drawString(2 * inch, tax_y, "Base")
        c.drawString(3 * inch, tax_y, "Valor")
        tax_y -= 5
        c.line(1 * inch, tax_y, 3.5 * inch, tax_y)
        tax_y -= 10
        
        c.setFont("Helvetica", 8)
        for tax in self.data['totales_impuestos']:
            c.drawString(1 * inch, tax_y, f"{tax['nombre']} {tax['porcentaje']}%")
            c.drawString(2 * inch, tax_y, f"${tax['base_imponible']:,.0f}")
            c.drawString(3 * inch, tax_y, f"${tax['valor_total_impuesto']:,.0f}")
            tax_y -= 10
        
        # Totals (Right Side)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(5.5 * inch, y - 20, "Subtotal:")
        c.drawString(6.5 * inch, y - 20, f"${self.data['resumen_factura']['subtotal']:,.0f}")
        
        c.drawString(5.5 * inch, y - 35, "Impuestos:")
        c.drawString(6.5 * inch, y - 35, f"${self.data['resumen_factura']['total_impuestos']:,.0f}")
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(5.5 * inch, y - 55, "TOTAL:")
        c.drawString(6.5 * inch, y - 55, f"${self.data['resumen_factura']['total_factura']:,.0f}")

        # CUFE & QR Placeholders
        c.setFont("Helvetica", 6)
        c.drawString(1 * inch, 100, "CUFE: (Espacio reservado para CUFE)")
        c.rect(6.5 * inch, 80, 0.8 * inch, 0.8 * inch)
        c.drawString(6.6 * inch, 65, "QR Code")

        # Footer
        c.setFont("Helvetica-Oblique", 8)
        c.centering = 1
        c.drawString(width/2, 30, "Representación gráfica de factura electrónica - Generado por Sistema Django")
        
        c.showPage()
        c.save()
        
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
