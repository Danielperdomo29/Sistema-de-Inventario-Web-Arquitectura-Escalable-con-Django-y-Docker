"""
Controlador para manejo de facturas y extracción OCR.
"""

import os
import tempfile
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.utils import timezone

from app.services.ocr_service import receipt_extractor
from app.utils.file_validators import validate_receipt_file
from app.utils.file_utils import save_receipt_file, generate_receipt_filename, delete_receipt_file

logger = logging.getLogger(__name__)


@ensure_csrf_cookie
@require_POST
def extract_total_from_receipt(request):
    """
    Endpoint para extraer total de factura usando OCR.
    
    URL: /api/purchases/extract-total/
    Método: POST
    Parámetro: receipt (archivo)
    
    Returns:
        JsonResponse con resultado de extracción.
    """
    print("\n" + "="*60)
    print("ENDPOINT: extract_total_from_receipt")
    print("="*60)
    
    try:
        # Verificar autenticación
        user_id = request.session.get("user_id")
        print(f"User ID: {user_id}")
        
        if not user_id:
            print("❌ Error: No autenticado")
            return JsonResponse({
                'success': False,
                'error': 'No autenticado'
            }, status=401)
        
        # Verificar que se envió archivo
        print(f"Archivos recibidos: {list(request.FILES.keys())}")
        
        if 'receipt' not in request.FILES:
            print("❌ Error: No se recibió archivo 'receipt'")
            return JsonResponse({
                'success': False,
                'error': 'No se recibió archivo'
            }, status=400)
        
        receipt_file = request.FILES['receipt']
        print(f"✓ Archivo recibido: {receipt_file.name}, tamaño: {receipt_file.size} bytes")
        
        # Validar archivo
        try:
            print("Validando archivo...")
            validate_receipt_file(receipt_file)
            print("✓ Archivo válido")
        except ValidationError as ve:
            print(f"❌ Validación falló: {ve}")
            return JsonResponse({
                'success': False,
                'error': str(ve)
            }, status=400)
        
        # Crear archivo temporal
        print("Creando archivo temporal...")
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=os.path.splitext(receipt_file.name)[1]
        ) as tmp_file:
            # Guardar contenido del archivo subido
            for chunk in receipt_file.chunks():
                tmp_file.write(chunk)
            tmp_path = tmp_file.name
        
        print(f"✓ Archivo temporal: {tmp_path}")
        print(f"¿Existe? {os.path.exists(tmp_path)}")
        
        try:
            print(f"Llamando a receipt_extractor.extract_all_fields()...")
            logger.info(f"Procesando archivo para OCR: {receipt_file.name}")
            
            # Extraer TODOS los campos usando OCR mejorado
            result = receipt_extractor.extract_all_fields(tmp_path)
            
            print(f"Resultado recibido: success={result.get('success')}")
            
            # Añadir información adicional
            result['filename_suggestion'] = generate_receipt_filename(receipt_file.name)
            result['original_filename'] = receipt_file.name
            result['file_size'] = receipt_file.size
            
            # Limpiar formato para respuesta
            if result['success']:
                print(f"✓ OCR exitoso: Total={result.get('total')}")
                response_data = {
                    'success': True,
                    'total': result['total'],
                    'invoice_number': result.get('invoice_number'),
                    'supplier_name': result.get('supplier_name'),
                    'date': result.get('date'),
                    'confidence': result['confidence'],
                    'extracted_text_preview': result['extracted_text'][:200],
                    'filename_suggestion': result['filename_suggestion']
                }
                logger.info(f"OCR exitoso: Total={result['total']}, Factura={result.get('invoice_number')}, Confianza={result['confidence']}")
            else:
                print(f"❌ OCR falló: {result.get('error')}")
                response_data = {
                    'success': False,
                    'error': result['error'] or 'No se pudo extraer el total',
                    'suggestions': [
                        'Verifica que la factura sea legible',
                        'Asegúrate de que incluya un total claramente visible',
                        'Intenta con una imagen de mejor calidad'
                    ]
                }
                logger.warning(f"OCR falló: {result['error']}")
            
            print("Retornando respuesta...")
            print("="*60 + "\n")
            return JsonResponse(response_data)
            
        finally:
            # Limpiar archivo temporal
            try:
                os.unlink(tmp_path)
                print(f"✓ Archivo temporal eliminado")
            except:
                pass
                
    except Exception as e:
        print(f"❌ EXCEPCIÓN: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"Error en extract_total_from_receipt: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@ensure_csrf_cookie
@require_POST
def save_purchase_with_receipt(request):
    """
    Endpoint para guardar compra con factura adjunta.
    
    URL: /api/purchases/save-with-receipt/
    Método: POST
    
    Parámetros esperados:
    - receipt_file (archivo): Archivo de la factura
    - total (opcional): Total de la compra (si no se extrae con OCR)
    - numero_factura, proveedor_id, fecha, notas, etc.
    """
    try:
        from app.models.purchase import Purchase
        from app.models.user import User
        
        # Verificar autenticación
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'No autenticado'
            }, status=401)
        
        # Inicializar variables
        receipt_path = None
        extraction_result = None
        
        # Manejar archivo de factura si existe
        if 'receipt_file' in request.FILES:
            receipt_file = request.FILES['receipt_file']
            
            # Validar archivo
            try:
                validate_receipt_file(receipt_file)
            except ValidationError as ve:
                return JsonResponse({
                    'success': False,
                    'error': f'Error en factura: {str(ve)}'
                }, status=400)
            
            # Guardar archivo
            receipt_path = save_receipt_file(receipt_file)
            logger.info(f"Factura guardada: {receipt_path}")
            
            # Extraer total si se solicita
            if request.POST.get('extract_total', 'false') == 'true':
                with tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix=os.path.splitext(receipt_file.name)[1]
                ) as tmp_file:
                    for chunk in receipt_file.chunks():
                        tmp_file.write(chunk)
                    tmp_path = tmp_file.name
                
                try:
                    extraction_result = receipt_extractor.extract_total(tmp_path)
                    logger.info(f"Extracción OCR resultado: {extraction_result['success']}")
                finally:
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
        
        # Determinar el total a usar
        # Prioridad: 1. Total manual, 2. Total extraído por OCR, 3. 0
        total = request.POST.get('total')
        if total:
            total = float(total)
        elif extraction_result and extraction_result['success']:
            total = extraction_result['total']
        else:
            total = 0.0
        
        # Preparar datos de compra
        purchase_data = {
            'numero_factura': request.POST.get('numero_factura', ''),
            'proveedor_id': request.POST.get('proveedor_id'),
            'usuario_id': user_id,
            'fecha': request.POST.get('fecha', timezone.now()),
            'total': total,
            'estado': request.POST.get('estado', 'pendiente'),
            'notas': request.POST.get('notas', '')
        }
        
        # Crear la compra
        try:
            from django.db import transaction
            
            with transaction.atomic():
                # Usar método create del modelo Purchase
                purchase_id = Purchase.create(
                    data=purchase_data,
                    details=[]  # Los detalles se añaden después si es necesario
                )
                
                if not purchase_id:
                    raise Exception("No se pudo crear la compra")
                
                # Obtener instancia para actualizar campos de factura
                purchase = Purchase.objects.get(id=purchase_id)
                
                # Asignar campos de factura si existe
                if receipt_path:
                    purchase.receipt_file = receipt_path
                    
                    # Determinar tipo de archivo
                    if receipt_path.lower().endswith('.pdf'):
                        purchase.receipt_type = 'pdf'
                    else:
                        purchase.receipt_type = 'image'
                    
                    # Guardar resultados de extracción
                    if extraction_result:
                        purchase.auto_extracted = extraction_result['success']
                        purchase.extracted_total = extraction_result.get('total')
                        purchase.extraction_confidence = extraction_result.get('confidence')
                        purchase.extraction_log = str(extraction_result)
                    
                    purchase.uploaded_at = timezone.now()
                    purchase.save()
                
                logger.info(f"Compra creada con ID: {purchase_id}, Factura: {bool(receipt_path)}")
                
                return JsonResponse({
                    'success': True,
                    'purchase_id': purchase_id,
                    'receipt_attached': bool(receipt_path),
                    'auto_extracted': purchase.auto_extracted if receipt_path else False,
                    'total': float(total)
                })
                
        except Exception as e:
            # Si hay error, eliminar archivo guardado si existe
            if receipt_path:
                delete_receipt_file(receipt_path)
            raise
        
    except Exception as e:
        logger.error(f"Error en save_purchase_with_receipt: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }, status=500)


@ensure_csrf_cookie
def view_receipt(request, purchase_id):
    """
    Vista para visualizar una factura adjunta.
    
    URL: /compras/<id>/factura/
    """
    try:
        from app.models.purchase import Purchase
        from django.http import FileResponse, Http404
        
        # Verificar autenticación
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'No autenticado'
            }, status=401)
        
        # Obtener compra
        purchase = Purchase.objects.filter(id=purchase_id).first()
        if not purchase or not purchase.receipt_file:
            raise Http404("Factura no encontrada")
        
        # Ruta completa del archivo
        file_path = os.path.join(settings.MEDIA_ROOT, purchase.receipt_file)
        
        if not os.path.exists(file_path):
            raise Http404("Archivo de factura no encontrado")
        
        # Retornar archivo
        return FileResponse(open(file_path, 'rb'))
        
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error en view_receipt: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
