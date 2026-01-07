"""
Servicio para extracción de texto de facturas usando OCR.
Implementa patrón Strategy para diferentes tipos de archivos.
"""

import pytesseract
import fitz  # PyMuPDF
from PIL import Image
import re
import os
import logging
from abc import ABC, abstractmethod
import magic
from django.conf import settings

# Configurar ruta de Tesseract desde settings
if hasattr(settings, 'TESSERACT_CMD'):
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

logger = logging.getLogger(__name__)

# Last updated: 2026-01-06 09:24 - Added multi-field extraction


class OCRStrategy(ABC):
    """Interfaz para estrategias de extracción OCR"""
    
    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        pass
    
    @abstractmethod
    def get_type(self) -> str:
        pass


class PDFExtractionStrategy(OCRStrategy):
    """Estrategia para extracción de PDFs"""
    
    def extract_text(self, file_path: str) -> str:
        """Extrae texto de archivo PDF"""
        try:
            text = ""
            doc = fitz.open(file_path)
            
            for page_num, page in enumerate(doc):
                # Extraer texto de la página
                page_text = page.get_text()
                text += f"\n--- Página {page_num + 1} ---\n{page_text}"
            
            doc.close()
            logger.info(f"Texto extraído de PDF: {len(text)} caracteres")
            return text
            
        except Exception as e:
            logger.error(f"Error extrayendo texto de PDF: {str(e)}")
            raise
    
    def get_type(self) -> str:
        return "pdf"


class ImageExtractionStrategy(OCRStrategy):
    """Estrategia para extracción de imágenes"""
    
    def __init__(self, language='spa+eng'):
        self.language = language
    
    
    def extract_text(self, file_path: str) -> str:
        """Extrae texto de imagen con preprocesamiento mejorado"""
        print(f"\n{'='*60}")
        print(f"INICIANDO EXTRACCION DE IMAGEN")
        print(f"Archivo: {file_path}")
        print(f"{'='*60}\n")
        
        logger.info(f"🔍 Iniciando extracción de imagen: {file_path}")
        
        # Intentar con OpenCV primero
        try:
            import cv2
            import numpy as np
            
            print("✓ OpenCV importado correctamente")
            logger.info("✅ OpenCV importado correctamente")
            
            # Leer imagen
            image = Image.open(file_path)
            print(f"✓ Imagen abierta: {image.size}, modo: {image.mode}")
            logger.info(f"📐 Imagen abierta: {image.size}, modo: {image.mode}")
            
            img_array = np.array(image)
            print(f"✓ Array shape: {img_array.shape}")
            
            # Convertir a escala de grises
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                print("✓ Convertido a escala de grises")
            else:
                gray = img_array
                print("✓ Ya en escala de grises")
            
            # Redimensionar si es muy pequeña
            height, width = gray.shape
            print(f"✓ Dimensiones: {width}x{height}")
            
            if width < 1000:
                scale = 1500 / width  # Menos agresivo: 1500 en vez de 2000
                new_width = int(width * scale)
                new_height = int(height * scale)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                print(f"✓ Redimensionado a: {new_width}x{new_height}")
            
            # Denoise MUY SUAVE para no distorsionar texto
            print("✓ Aplicando denoise suave...")
            denoised = cv2.fastNlMeansDenoising(gray, None, h=5, templateWindowSize=7, searchWindowSize=21)
            
            # Contraste moderado
            print("✓ Mejorando contraste...")
            clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # Usar umbral simple en lugar de adaptativo (menos distorsión)
            print("✓ Aplicando umbral...")
            _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            processed_image = Image.fromarray(binary)
            print("✓ Imagen procesada con OpenCV")
            
            print("✓ Ejecutando Tesseract...")
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(processed_image, lang='spa+eng', config=custom_config)
            
            print(f"✓ Texto extraído: {len(text)} caracteres")
            print(f"Preview: {text[:200]}...")
            print(f"\n{'='*60}\n")
            
            logger.info(f"✅ Texto extraído con OpenCV ({len(text)} caracteres)")
            return text
            
        except ImportError as ie:
            print(f"⚠ OpenCV no disponible: {ie}")
            logger.warning(f"⚠️ OpenCV no disponible: {str(ie)}")
        except Exception as e:
            print(f"✗ Error con OpenCV: {type(e).__name__}: {e}")
            logger.error(f"❌ Error con OpenCV: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # FALLBACK: Método básico
        try:
            print("\nUsando método básico (sin OpenCV)...")
            image = Image.open(file_path)
            print(f"✓ Imagen: {image.size}, modo: {image.mode}")
            
            if image.mode != 'L':
                image = image.convert('L')
                print("✓ Convertido a escala de grises")
            
            print("✓ Ejecutando Tesseract...")
            text = pytesseract.image_to_string(image, lang='spa+eng', config='--oem 3 --psm 6')
            
            print(f"✓ Texto extraído: {len(text)} caracteres")
            print(f"Preview: {text[:200]}...")
            print(f"\n{'='*60}\n")
            
            logger.info(f"✅ Texto extraído con método básico ({len(text)} caracteres)")
            return text
            
        except Exception as e:
            print(f"✗ ERROR FATAL: {type(e).__name__}: {e}")
            logger.error(f"❌ Error fatal: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    
    def get_type(self) -> str:
        return "image"


class ReceiptOCRExtractor:
    """Extractor principal para facturas con soporte múltiple"""
    
    # Patrones para buscar totales (en español) - MEJORADOS v2
    TOTAL_PATTERNS = [
        # Patrones específicos que capturan números completos con múltiples separadores
        # Ejemplos: 1.499.070, 119,000.00, 1,234,567.89
        r'(?i)total\s*a\s*pagar\s*[:\.\s]*[\$COP\s]*\s*([0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]{1,3})?)',
        r'(?i)total\s*[:\.\s]*[\$COP\s]*\s*([0-9]{1,3}(?:[.,][0-9]{3})+(?:[.,][0-9]{1,3})?)',
        r'(?i)importe\s*total\s*[:\.\s]*[\$COP\s]*\s*([0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]{1,3})?)',
        r'(?i)valor\s*total\s*[:\.\s]*[\$COP\s]*\s*([0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]{1,3})?)',
        r'(?i)gran\s*total\s*[:\.\s]*[\$COP\s]*\s*([0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]{1,3})?)',
        r'(?i)subtotal\s*[:\.\s]*[\$COP\s]*\s*([0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]{1,3})?)',
        
        # Patrón "TOTAL:" con formato flexible
        r'(?i)TOTAL[:\s]+[\$COP\s]*([0-9]{1,3}(?:[.,][0-9]{3})+(?:[.,][0-9]{1,3})?)',
        
        # Patrón genérico - captura cualquier número con separadores
        r'[\$]\s*([0-9]{1,3}(?:[.,][0-9]{3})+(?:[.,][0-9]{1,3})?)',
        
        # Fallback: números con al menos un separador (más permisivo)
        r'(?i)total\s*[:\.\s]*[\$COP\s]*\s*((?:[0-9]+[.,])+[0-9]+)',
    ]
    
    def __init__(self):
        self.strategies = {
            'pdf': PDFExtractionStrategy(),
            'image': ImageExtractionStrategy()
        }
    
    def detect_file_type(self, file_path: str) -> str:
        """Detecta el tipo de archivo usando magic"""
        try:
            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(file_path)
            
            if mime_type == 'application/pdf':
                return 'pdf'
            elif mime_type.startswith('image/'):
                return 'image'
            else:
                raise ValueError(f"Tipo de archivo no soportado: {mime_type}")
        except Exception as e:
            # Fallback: detectar por extensión
            logger.warning(f"Error detectando MIME type: {e}, usando extensión")
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.pdf':
                return 'pdf'
            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                return 'image'
            else:
                raise ValueError(f"Extensión no soportada: {ext}")
    
    def extract_total(self, file_path: str) -> dict:
        """
        Extrae el total de una factura
        
        Returns:
            dict: {
                'success': bool,
                'total': float or None,
                'confidence': float,
                'extracted_text': str,
                'found_pattern': str or None,
                'error': str or None
            }
        """
        try:
            # Detectar tipo de archivo
            file_type = self.detect_file_type(file_path)
            logger.info(f"Procesando archivo tipo: {file_type}")
            
            # Seleccionar estrategia
            strategy = self.strategies.get(file_type)
            if not strategy:
                return {
                    'success': False,
                    'total': None,
                    'confidence': 0.0,
                    'extracted_text': '',
                    'found_pattern': None,
                    'error': f'Tipo de archivo no soportado: {file_type}'
                }
            
            # Extraer texto
            text = strategy.extract_text(file_path)
            
            # Buscar totales
            total, confidence, pattern = self._find_total_in_text(text)
            
            return {
                'success': total is not None,
                'total': total,
                'confidence': confidence,
                'extracted_text': text[:500] + '...' if len(text) > 500 else text,
                'found_pattern': pattern,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error en extracción OCR: {str(e)}")
            return {
                'success': False,
                'total': None,
                'confidence': 0.0,
                'extracted_text': '',
                'found_pattern': None,
                'error': str(e)
            }
    
    def extract_all_fields(self, file_path: str) -> dict:
        """
        Extrae todos los campos relevantes de una factura de forma segura
        
        Returns:
            dict: {
                'success': bool,
                'total': float or None,
                'invoice_number': str or None,
                'supplier_name': str or None,
                'date': str or None,
                'confidence': float,
                'extracted_text': str,
                'error': str or None
            }
        """
        try:
            # Detectar tipo de archivo
            file_type = self.detect_file_type(file_path)
            logger.info(f"Extrayendo todos los campos de archivo tipo: {file_type}")
            
            # Seleccionar estrategia
            strategy = self.strategies.get(file_type)
            if not strategy:
                return self._empty_result('Tipo de archivo no soportado')
            
            # Extraer texto
            text = strategy.extract_text(file_path)
            
            # Extraer campos individuales
            total, total_confidence, total_pattern = self._find_total_in_text(text)
            invoice_number = self._extract_invoice_number(text)
            supplier_name = self._extract_supplier_name(text)
            date = self._extract_date(text)
            
            # Calcular confianza general
            overall_confidence = total_confidence if total is not None else 0.0
            
            return {
                'success': total is not None,
                'total': total,
                'invoice_number': invoice_number,
                'supplier_name': supplier_name,
                'date': date,
                'confidence': overall_confidence,
                'extracted_text': text[:1000] + '...' if len(text) > 1000 else text,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error en extracción completa de OCR: {str(e)}")
            return self._empty_result(str(e))
    
    def _empty_result(self, error_msg: str) -> dict:
        """Retorna resultado vacío con error"""
        return {
            'success': False,
            'total': None,
            'invoice_number': None,
            'supplier_name': None,
            'date': None,
            'confidence': 0.0,
            'extracted_text': '',
            'error': error_msg
        }
    
    def _extract_invoice_number(self, text: str) -> str:
        """
        Extrae número de factura de forma segura
        Busca patrones como: Factura N°, Invoice #, N° Factura, etc.
        """
        import html
        
        patterns = [
            r'(?i)(?:factura|invoice)\s*n[°º#]?\s*[:\-]?\s*([A-Z0-9\-]+)',
            r'(?i)n[°º#]\s*(?:factura|invoice)\s*[:\-]?\s*([A-Z0-9\-]+)',
            r'(?i)(?:no|num|number)\s*[:\.\-]?\s*([A-Z0-9\-]{3,})',
            r'(?i)pedido\s*no[:\.\s]*([A-Z0-9\-]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Sanitizar (solo alfanuméricos y guiones)
                invoice_num = matches[0].strip()
                invoice_num = re.sub(r'[^A-Z0-9\-]', '', invoice_num.upper())
                if len(invoice_num) >= 3:  # Mínimo 3 caracteres
                    return html.escape(invoice_num[:50])  # Máximo 50 caracteres, escape HTML
        
        return None
    
    def _extract_supplier_name(self, text: str) -> str:
        """
        Extrae nombre de proveedor de forma segura
        Busca en las primeras líneas del documento
        """
        import html
        
        # Tomar solo las primeras 500 caracteres (encabezado)
        header = text[:500]
        lines = header.split('\n')
        
        # Buscar líneas con nombre de empresa (generalmente primeras 5 líneas)
        for i, line in enumerate(lines[:5]):
            line = line.strip()
            # Filtrar líneas que parecen nombres de empresa
            if len(line) > 3 and not re.match(r'^[\d\s\.\-]+$', line):
                # Sanitizar
                supplier = re.sub(r'\s+', ' ', line)  # Normalizar espacios
                supplier = supplier[:100]  # Máximo 100 caracteres
                return html.escape(supplier)
        
        return None
    
    def _extract_date(self, text: str) -> str:
        """
        Extrae fecha de forma segura
        Busca formatos: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, etc.
        """
        import html
        from datetime import datetime
        
        patterns = [
            r'(?i)fecha\s*[:\-]?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            r'(?i)(?:date|fec)\s*[:\-]?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',  # DD/MM/YYYY o DD-MM-YYYY
            r'(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})',  # YYYY-MM-DD
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                date_str = matches[0].strip()
                # Validar que es una fecha válida
                try:
                    # Intentar parsear la fecha
                    for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y', '%d-%m-%y']:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt)
                            # Retornar en formato estándar YYYY-MM-DD
                            return html.escape(parsed_date.strftime('%Y-%m-%d'))
                        except ValueError:
                            continue
                except:
                    pass
        
        return None
    def _find_total_in_text(self, text: str) -> tuple:
        """
        Busca el total en el texto extraído
        
        Returns:
            tuple: (total, confidence, pattern_used)
        """
        best_total = None
        best_confidence = 0.0
        best_pattern = None
        
        for pattern in self.TOTAL_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            if matches:
                # Tomar el último match (a menudo el total final)
                amount_str = matches[-1].strip()
                
                try:
                    # Normalizar formato numérico de manera inteligente
                    total = self._normalize_amount(amount_str)
                    
                    # Calcular confianza
                    confidence = self._calculate_confidence(pattern, total, text)
                    
                    if confidence > best_confidence:
                        best_total = total
                        best_confidence = confidence
                        best_pattern = pattern
                        
                except ValueError:
                    continue
        
        return best_total, best_confidence, best_pattern
    
    def _normalize_amount(self, amount_str: str) -> float:
        """
        Normaliza formatos de números de diferentes países
        Ejemplos:
        - "1.499.070" (Colombia) -> 1499070.0
        - "119,000.00" (USA) -> 119000.0
        - "1,499.99" (USA) -> 1499.99
        - "1.234,56" (Europa) -> 1234.56
        """
        # Limpiar espacios y símbolos de moneda
        amount_str = amount_str.replace(' ', '').replace('$', '').replace('COP', '')
        
        # Contar puntos y comas
        dot_count = amount_str.count('.')
        comma_count = amount_str.count(',')
        
        # Determinar el formato
        if dot_count > 0 and comma_count > 0:
            # Ambos presentes: determinar cuál es el decimal
            last_dot_pos = amount_str.rfind('.')
            last_comma_pos = amount_str.rfind(',')
            
            if last_dot_pos > last_comma_pos:
                # Formato: 1,499.99 (punto es decimal)
                amount_str = amount_str.replace(',', '')
            else:
                # Formato: 1.499,99 (coma es decimal)
                amount_str = amount_str.replace('.', '').replace(',', '.')
                
        elif dot_count > 1 and comma_count == 0:
            # Formato: 1.499.070 (puntos son separadores de miles)
            amount_str = amount_str.replace('.', '')
            
        elif comma_count > 1 and dot_count == 0:
            # Formato: 1,499,070 (comas son separadores de miles)
            amount_str = amount_str.replace(',', '')
            
        elif dot_count == 1 and comma_count == 0:
            # Un solo punto: podría ser miles o decimal
            parts = amount_str.split('.')
            if len(parts[1]) == 3 and len(parts[0]) <= 3:
                # Formato: 119.000 (punto es separador de miles)
                amount_str = amount_str.replace('.', '')
            # Sino, asumir que es decimal (formato: 123.45)
            
        elif comma_count == 1 and dot_count == 0:
            # Una sola coma: probablemente decimal europeo
            amount_str = amount_str.replace(',', '.')
        
        return float(amount_str)
    
    def _calculate_confidence(self, pattern: str, total: float, text: str) -> float:
        """Calcula confianza de la extracción"""
        confidence = 0.5  # Base
        
        # Aumentar confianza si el total es razonable (entre 1 y 1,000,000)
        if 1 <= total <= 1000000:
            confidence += 0.2
        
        # Aumentar si el patrón es específico
        if 'pagar' in pattern.lower() or 'importe' in pattern.lower():
            confidence += 0.1
        
        # Aumentar si aparece cerca del final del texto (último 30%)
        pattern_pos = text.lower().find('total')
        if pattern_pos > len(text) * 0.7:
            confidence += 0.2
        
        return min(confidence, 1.0)  # Máximo 1.0


# Instancia global para reutilización
receipt_extractor = ReceiptOCRExtractor()
