"""
Controlador para generación de facturas electrónicas DIAN.
"""
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect
import logging

from app.models.user import User
from app.models.sale import Sale
from app.fiscal.services.invoice_service import InvoiceGenerationService

logger = logging.getLogger(__name__)


class DianInvoiceController:
    """
    Controlador para generar facturas electrónicas DIAN desde ventas.
    """
    
    @staticmethod
    def generate_invoice(request, sale_id):
        """
        Genera una factura electrónica DIAN para una venta.
        
        Args:
            request: HttpRequest
            sale_id: ID de la venta
            
        Returns:
            JSON con resultado o redirección
        """
        # Verificar autenticación
        user_id = request.session.get("user_id")
        if not user_id:
            return HttpResponseRedirect("/login/")
        
        user = User.get_by_id(user_id)
        if not user:
            request.session.flush()
            return HttpResponseRedirect("/login/")
        
        try:
            # Obtener la venta
            sale = Sale.objects.get(id=sale_id)
            
            # Verificar si ya tiene factura VÁLIDA
            tiene_factura_valida = False
            numero_factura_existente = None
            
            if hasattr(sale, 'factura_electronica') and sale.factura_electronica:
                factura_existente = sale.factura_electronica
                
                # Solo consideramos válida si tiene número de factura y CUFE
                if factura_existente.numero_factura and factura_existente.cufe:
                    tiene_factura_valida = True
                    numero_factura_existente = factura_existente.numero_factura
                else:
                    # Factura incompleta - eliminar para regenerar
                    logger.warning(f"Eliminando factura incompleta para venta {sale_id}")
                    factura_existente.delete()
            
            if tiene_factura_valida:
                logger.info(f"Retornando factura existente para venta {sale_id}")
                response_data = {
                    'success': True,
                    'message': 'Factura electrónica ya existente',
                    'numero_factura': numero_factura_existente,
                    'cufe': factura_existente.cufe[:32] + '...' if factura_existente.cufe else None,
                    'pdf_url': factura_existente.archivo_pdf.url if factura_existente.archivo_pdf else None,
                    'xml_url': factura_existente.archivo_xml.url if factura_existente.archivo_xml else None,
                }
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse(response_data)
                
                # Si no es AJAX y tenemos PDF, redirigir al PDF
                if factura_existente.archivo_pdf:
                    return HttpResponseRedirect(factura_existente.archivo_pdf.url)
                    
                return HttpResponseRedirect('/ventas/')
            
            # Generar factura electrónica
            logger.info(f"Generando factura electrónica para venta {sale_id}")
            factura, xml_string = InvoiceGenerationService.generar_factura_electronica(sale)
            
            # Respuesta exitosa
            response_data = {
                'success': True,
                'message': 'Factura electrónica generada exitosamente',
                'numero_factura': factura.numero_factura,
                'cufe': factura.cufe[:32] + '...',  # CUFE abreviado
                'pdf_url': factura.archivo_pdf.url if factura.archivo_pdf else None,
                'xml_url': factura.archivo_xml.url if factura.archivo_xml else None,
            }
            
            logger.info(f"Factura {factura.numero_factura} generada exitosamente")
            
            # Si es AJAX, retornar JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(response_data)
            
            # Si no es AJAX, redirigir a ventas
            return HttpResponseRedirect('/ventas/')
            
        except Sale.DoesNotExist:
            error_msg = f'No se encontró la venta con ID {sale_id}'
            logger.error(error_msg)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg}, status=404)
            return HttpResponseRedirect('/ventas/')
            
        except Exception as e:
            error_msg = f'Error al generar factura: {str(e)}'
            logger.error(error_msg, exc_info=True)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg}, status=500)
            return HttpResponseRedirect('/ventas/')
    
    @staticmethod
    def download_pdf(request, sale_id):
        """
        Descarga el PDF de una factura electrónica.
        
        Args:
            request: HttpRequest
            sale_id: ID de la venta
            
        Returns:
            PDF file response
        """
        # Verificar autenticación
        user_id = request.session.get("user_id")
        if not user_id:
            return HttpResponseRedirect("/login/")
        
        try:
            sale = Sale.objects.get(id=sale_id)
            
            if not hasattr(sale, 'factura_electronica') or not sale.factura_electronica:
                return HttpResponse("Esta venta no tiene factura electrónica", status=404)
            
            factura = sale.factura_electronica
            
            if not factura.archivo_pdf:
                return HttpResponse("El PDF de la factura no está disponible", status=404)
            
            # Redirigir al archivo PDF
            return HttpResponseRedirect(factura.archivo_pdf.url)
            
        except Sale.DoesNotExist:
            return HttpResponse("Venta no encontrada", status=404)
        except Exception as e:
            logger.error(f"Error al descargar PDF: {e}", exc_info=True)
            return HttpResponse(f"Error al descargar PDF: {str(e)}", status=500)
    
    @staticmethod
    def download_xml(request, sale_id):
        """
        Descarga el XML de una factura electrónica.
        
        Args:
            request: HttpRequest
            sale_id: ID de la venta
            
        Returns:
            XML file response
        """
        # Verificar autenticación
        user_id = request.session.get("user_id")
        if not user_id:
            return HttpResponseRedirect("/login/")
        
        try:
            sale = Sale.objects.get(id=sale_id)
            
            if not hasattr(sale, 'factura_electronica') or not sale.factura_electronica:
                return HttpResponse("Esta venta no tiene factura electrónica", status=404)
            
            factura = sale.factura_electronica
            
            if not factura.archivo_xml:
                return HttpResponse("El XML de la factura no está disponible", status=404)
            
            # Redirigir al archivo XML
            return HttpResponseRedirect(factura.archivo_xml.url)
            
        except Sale.DoesNotExist:
            return HttpResponse("Venta no encontrada", status=404)
        except Exception as e:
            logger.error(f"Error al descargar XML: {e}", exc_info=True)
            return HttpResponse(f"Error al descargar XML: {str(e)}", status=500)
