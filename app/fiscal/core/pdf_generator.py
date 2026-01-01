from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus.flowables import KeepTogether
from reportlab.pdfgen import canvas
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import Dict
from django.conf import settings

class PDFGenerator:
    """Wrapper sobre ReportLab para generación de reportes financieros"""
    
    def __init__(self, titulo: str, empresa_nombre: str, empresa_nit: str):
        self.titulo = titulo
        self.empresa_nombre = empresa_nombre
        self.empresa_nit = empresa_nit
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Configura estilos personalizados"""
        self.titulo_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Centrado
        )
        
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.grey
        )
        
        self.table_header_style = ParagraphStyle(
            'TableHeader',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.white,
            alignment=1
        )
        
        self.table_cell_style = ParagraphStyle(
            'TableCell',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=1
        )
    
    def _add_header_footer(self, canvas, doc):
        """Agrega encabezado y pie de página a cada página"""
        canvas.saveState()
        
        # Encabezado
        canvas.setFont('Helvetica-Bold', 12)
        canvas.drawString(inch, doc.pagesize[1] - inch, self.empresa_nombre)
        
        canvas.setFont('Helvetica', 10)
        canvas.drawString(inch, doc.pagesize[1] - inch - 15, f"NIT: {self.empresa_nit}")
        
        canvas.setFont('Helvetica-Bold', 14)
        canvas.drawCentredString(doc.pagesize[0]/2, doc.pagesize[1] - inch, self.titulo)
        
        # Línea separadora
        canvas.line(inch, doc.pagesize[1] - inch - 25, 
                   doc.pagesize[0] - inch, doc.pagesize[1] - inch - 25)
        
        # Pie de página
        canvas.setFont('Helvetica', 8)
        page_num = canvas.getPageNumber()
        fecha_gen = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        canvas.drawString(inch, 0.75 * inch, 
                         f"Generado: {fecha_gen} | Página {page_num}")
        
        canvas.restoreState()
    
    def generar_libro_diario_pdf(self, libro_diario: Dict, fecha_inicio: str, fecha_fin: str) -> BytesIO:
        """Genera PDF del libro diario"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=inch,
            leftMargin=inch,
            topMargin=1.5*inch,
            bottomMargin=inch
        )
        
        elements = []
        
        # Título y período
        elements.append(Paragraph("LIBRO DIARIO", self.titulo_style))
        elements.append(Paragraph(f"Período: {fecha_inicio} al {fecha_fin}", self.header_style))
        elements.append(Spacer(1, 20))
        
        # Tabla de asientos
        for fecha, asientos in libro_diario.items():
            # Encabezado de fecha
            elements.append(Paragraph(f"Fecha: {fecha}", self.styles['Heading3']))
            elements.append(Spacer(1, 10))
            
            for asiento in asientos:
                # Tabla de detalles del asiento
                data = [
                    ['Cuenta', 'Nombre Cuenta', 'Débito', 'Crédito', 'Descripción']
                ]
                
                for detalle in asiento['detalles']:
                    data.append([
                        detalle['cuenta'],
                        detalle['nombre_cuenta'],
                        f"${detalle['debito']:,.2f}",
                        f"${detalle['credito']:,.2f}",
                        detalle['descripcion'][:50]  # Limitar longitud
                    ])
                
                # Agregar totales
                data.append([
                    'TOTAL',
                    '',
                    f"${asiento['total_debito']:,.2f}",
                    f"${asiento['total_credito']:,.2f}",
                    asiento['descripcion']
                ])
                
                # Ajuste de anchos para A4 Landscape (aprox 28cm ancho total - margenes)
                table = Table(data, colWidths=[2.5*cm, 5.5*cm, 3.5*cm, 3.5*cm, 8*cm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Nombre cuenta y descripción alineados a izq
                    ('ALIGN', (4, 1), (4, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#f8f9fa')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e9ecef')), # Fila total
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ]))
                
                elements.append(KeepTogether([table])) # Mantener asiento unido
                elements.append(Spacer(1, 15))
            
            elements.append(Spacer(1, 20))
        
        # Construir PDF
        doc.build(elements, onFirstPage=self._add_header_footer, 
                 onLaterPages=self._add_header_footer)
        
        buffer.seek(0)
        return buffer
    
    def generar_balance_prueba_pdf(self, balance_data: Dict) -> BytesIO:
        """Genera PDF del balance de prueba"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=inch,
            leftMargin=inch,
            topMargin=1.5*inch,
            bottomMargin=inch
        )
        
        elements = []
        
        # Título y período
        elements.append(Paragraph("BALANCE DE PRUEBA", self.titulo_style))
        elements.append(Paragraph(f"Fecha de corte: {balance_data['fecha_corte']}", self.header_style))
        elements.append(Spacer(1, 20))
        
        # Tabla de cuentas
        data = [
            ['Cuenta', 'Nombre', 'Débito', 'Crédito', 'Saldo Deudor', 'Saldo Acreedor']
        ]
        
        for cuenta in balance_data['cuentas']:
            data.append([
                cuenta['codigo'],
                cuenta['nombre'],
                f"${cuenta['debito']:,.2f}",
                f"${cuenta['credito']:,.2f}",
                f"${cuenta['saldo_deudor']:,.2f}",
                f"${cuenta['saldo_acreedor']:,.2f}"
            ])
        
        # Totales
        data.append([
            'TOTALES',
            '',
            f"${balance_data['totales']['total_debito']:,.2f}",
            f"${balance_data['totales']['total_credito']:,.2f}",
            '',
            ''
        ])
        
        table = Table(data, colWidths=[2.5*cm, 7.5*cm, 3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -2), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e9ecef')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Resumen de cuadre
        elements.append(Paragraph("RESUMEN DE CUADRE", self.styles['Heading3']))
        elements.append(Spacer(1, 10))
        
        cuadre_data = [
            ['Total Débitos', f"${balance_data['totales']['total_debito']:,.2f}"],
            ['Total Créditos', f"${balance_data['totales']['total_credito']:,.2f}"],
            ['Diferencia', f"${balance_data['totales']['diferencia']:,.2f}"]
        ]
        
        cuadre_table = Table(cuadre_data, colWidths=[6*cm, 3*cm])
        cuadre_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        elements.append(cuadre_table)
        
        doc.build(elements, onFirstPage=self._add_header_footer, 
                 onLaterPages=self._add_header_footer)
        
        buffer.seek(0)
        return buffer
    
    def generar_estado_resultados_pdf(self, estado_resultados: Dict) -> BytesIO:
        """Genera PDF del estado de resultados"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4, # Vertical para Estado de Resultados
            rightMargin=inch,
            leftMargin=inch,
            topMargin=1.5*inch,
            bottomMargin=inch
        )
        
        elements = []
        
        elements.append(Paragraph("ESTADO DE RESULTADOS", self.titulo_style))
        elements.append(Paragraph(f"Período: {estado_resultados['periodo']}", self.header_style))
        elements.append(Spacer(1, 30))
        
        # Ingresos
        elements.append(Paragraph("INGRESOS", self.styles['Heading2']))
        ingresos_data = [
            ['Ventas', f"${estado_resultados['ingresos']:,.2f}"]
        ]
        ingresos_table = Table(ingresos_data, colWidths=[12*cm, 3*cm])
        ingresos_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        elements.append(ingresos_table)
        
        elements.append(Spacer(1, 20))
        
        # Costos
        elements.append(Paragraph("COSTOS", self.styles['Heading2']))
        costos_data = [
            ['Costos de ventas', f"${estado_resultados['costos']:,.2f}"]
        ]
        costos_table = Table(costos_data, colWidths=[12*cm, 3*cm])
        costos_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        elements.append(costos_table)
        
        elements.append(Spacer(1, 10))
        
        # Utilidad Bruta
        utilidad_bruta_data = [
            ['UTILIDAD BRUTA', f"${estado_resultados['utilidad_bruta']:,.2f}"]
        ]
        utilidad_table = Table(utilidad_bruta_data, colWidths=[12*cm, 3*cm])
        utilidad_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
        ]))
        elements.append(utilidad_table)
        
        elements.append(Spacer(1, 20))
        
        # Gastos
        elements.append(Paragraph("GASTOS OPERACIONALES", self.styles['Heading2']))
        gastos_data = [
            ['Gastos administrativos', f"${estado_resultados['gastos']:,.2f}"]
        ]
        gastos_table = Table(gastos_data, colWidths=[12*cm, 3*cm])
        gastos_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        elements.append(gastos_table)
        
        elements.append(Spacer(1, 10))
        
        # Utilidad Neta
        utilidad_neta_data = [
            ['UTILIDAD NETA DEL EJERCICIO', f"${estado_resultados['utilidad_neta']:,.2f}"]
        ]
        utilidad_neta_table = Table(utilidad_neta_data, colWidths=[12*cm, 3*cm])
        utilidad_neta_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.black),
            ('TEXTCOLOR', (0, 0), (-1, -1), 
             colors.green if estado_resultados['utilidad_neta'] > 0 else colors.red),
        ]))
        elements.append(utilidad_neta_table)
        
        doc.build(elements, onFirstPage=self._add_header_footer, 
                 onLaterPages=self._add_header_footer)
        
        buffer.seek(0)
        return buffer
