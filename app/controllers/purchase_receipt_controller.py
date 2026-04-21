"""
Controlador para manejo de facturas y extracción OCR.
"""

import logging
import os
import tempfile

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from app.services.ocr_service import receipt_extractor
from app.utils.file_utils import delete_receipt_file, generate_receipt_filename, save_receipt_file
from app.utils.file_validators import validate_receipt_file

logger = logging.getLogger(__name__)


def _find_matching_supplier(extracted_name: str):
    """
    Busca el proveedor que mejor coincida con el nombre extraido por OCR.
    Returns: (supplier_id, supplier_nombre) o (None, None)
    """
    import re

    from django.db.models import Q

    from app.models.supplier import Supplier

    if not extracted_name:
        return None, None

    extracted_clean = extracted_name.strip()

    # 1. Buscar por NIT si el texto contiene uno
    nit_match = re.search(r"(\d{9,10})", extracted_clean)
    if nit_match:
        nit_value = nit_match.group(1)
        supplier = Supplier.objects.filter(nit=nit_value, activo=True).first()
        if supplier:
            return supplier.id, supplier.nombre

    # 2. Buscar coincidencia exacta (case-insensitive) en nombre
    supplier = Supplier.objects.filter(nombre__iexact=extracted_clean, activo=True).first()
    if supplier:
        return supplier.id, supplier.nombre

    # 3. Buscar coincidencia parcial (el nombre extraido contiene el del proveedor o viceversa)
    extracted_lower = extracted_clean.lower()
    suppliers = Supplier.objects.filter(activo=True).values_list("id", "nombre")

    best_match = None
    best_score = 0

    for sup_id, sup_nombre in suppliers:
        sup_lower = sup_nombre.lower()

        # Coincidencia directa de substrings
        if sup_lower in extracted_lower or extracted_lower in sup_lower:
            score = len(sup_lower) / max(len(extracted_lower), 1)
            if score > best_score:
                best_score = score
                best_match = (sup_id, sup_nombre)
            continue

        # Token matching: contar palabras en comun
        extract_tokens = set(re.findall(r"\b\w{3,}\b", extracted_lower))
        sup_tokens = set(re.findall(r"\b\w{3,}\b", sup_lower))
        # Quitar palabras genericas
        stopwords = {"sas", "ltda", "sa", "nit", "the", "de", "del", "los", "las", "y", "and"}
        extract_tokens -= stopwords
        sup_tokens -= stopwords

        if extract_tokens and sup_tokens:
            overlap = extract_tokens & sup_tokens
            if overlap:
                score = len(overlap) / max(len(sup_tokens), 1)
                if score > best_score and score >= 0.4:
                    best_score = score
                    best_match = (sup_id, sup_nombre)

    return best_match if best_match else (None, None)


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
    print("\n" + "=" * 60)
    print("ENDPOINT: extract_total_from_receipt")
    print("=" * 60)

    try:
        # Verificar autenticación
        user_id = request.session.get("user_id")
        print(f"User ID: {user_id}")

        if not user_id:
            print("❌ Error: No autenticado")
            return JsonResponse({"success": False, "error": "No autenticado"}, status=401)

        # Verificar que se envió archivo
        print(f"Archivos recibidos: {list(request.FILES.keys())}")

        if "receipt" not in request.FILES:
            print("❌ Error: No se recibió archivo 'receipt'")
            return JsonResponse({"success": False, "error": "No se recibió archivo"}, status=400)

        receipt_file = request.FILES["receipt"]
        print(f"✓ Archivo recibido: {receipt_file.name}, tamaño: {receipt_file.size} bytes")

        # Validar archivo
        try:
            print("Validando archivo...")
            validate_receipt_file(receipt_file)
            print("✓ Archivo válido")
        except ValidationError as ve:
            print(f"❌ Validación falló: {ve}")
            return JsonResponse({"success": False, "error": str(ve)}, status=400)

        # Crear archivo temporal
        print("Creando archivo temporal...")
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(receipt_file.name)[1]) as tmp_file:
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
            result["filename_suggestion"] = generate_receipt_filename(receipt_file.name)
            result["original_filename"] = receipt_file.name
            result["file_size"] = receipt_file.size

            # Limpiar formato para respuesta
            if result["success"]:
                print(f"✓ OCR exitoso: Total={result.get('total')}")

                # --- Fuzzy match del proveedor ---
                supplier_match_id = None
                supplier_match_name = None
                if result.get("supplier_name"):
                    supplier_match_id, supplier_match_name = _find_matching_supplier(result["supplier_name"])

                response_data = {
                    "success": True,
                    "total": result["total"],
                    "invoice_number": result.get("invoice_number"),
                    "supplier_name": result.get("supplier_name"),
                    "supplier_match_id": supplier_match_id,
                    "supplier_match_name": supplier_match_name,
                    "date": result.get("date"),
                    "confidence": result["confidence"],
                    "extracted_text_preview": result["extracted_text"][:500],
                    "filename_suggestion": result["filename_suggestion"],
                }
                logger.info(
                    f"OCR exitoso: Total={result['total']}, Factura={result.get('invoice_number')}, Confianza={result['confidence']}"
                )
            else:
                print(f"❌ OCR falló: {result.get('error')}")
                response_data = {
                    "success": False,
                    "error": result["error"] or "No se pudo extraer el total",
                    "suggestions": [
                        "Verifica que la factura sea legible",
                        "Asegúrate de que incluya un total claramente visible",
                        "Intenta con una imagen de mejor calidad",
                    ],
                }
                logger.warning(f"OCR falló: {result['error']}")

            print("Retornando respuesta...")
            print("=" * 60 + "\n")
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
        return JsonResponse({"success": False, "error": f"Error interno del servidor: {str(e)}"}, status=500)


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
            return JsonResponse({"success": False, "error": "No autenticado"}, status=401)

        # Inicializar variables
        receipt_path = None
        extraction_result = None

        # Manejar archivo de factura si existe
        if "receipt_file" in request.FILES:
            receipt_file = request.FILES["receipt_file"]

            # Validar archivo
            try:
                validate_receipt_file(receipt_file)
            except ValidationError as ve:
                return JsonResponse({"success": False, "error": f"Error en factura: {str(ve)}"}, status=400)

            # Guardar archivo
            receipt_path = save_receipt_file(receipt_file)
            logger.info(f"Factura guardada: {receipt_path}")

            # Extraer total si se solicita
            if request.POST.get("extract_total", "false") == "true":
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=os.path.splitext(receipt_file.name)[1]
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
        total = request.POST.get("total")
        if total:
            total = float(total)
        elif extraction_result and extraction_result["success"]:
            total = extraction_result["total"]
        else:
            total = 0.0

        # Preparar datos de compra
        purchase_data = {
            "numero_factura": request.POST.get("numero_factura", ""),
            "proveedor_id": request.POST.get("proveedor_id"),
            "usuario_id": user_id,
            "fecha": request.POST.get("fecha", timezone.now()),
            "total": total,
            "estado": request.POST.get("estado", "pendiente"),
            "notas": request.POST.get("notas", ""),
        }

        # Crear la compra
        try:
            from django.db import transaction

            with transaction.atomic():
                # Usar método create del modelo Purchase
                purchase_id = Purchase.create(
                    data=purchase_data, details=[]  # Los detalles se añaden después si es necesario
                )

                if not purchase_id:
                    raise Exception("No se pudo crear la compra")

                # Obtener instancia para actualizar campos de factura
                purchase = Purchase.objects.get(id=purchase_id)

                # Asignar campos de factura si existe
                if receipt_path:
                    purchase.receipt_file = receipt_path

                    # Determinar tipo de archivo
                    if receipt_path.lower().endswith(".pdf"):
                        purchase.receipt_type = "pdf"
                    else:
                        purchase.receipt_type = "image"

                    # Guardar resultados de extracción
                    if extraction_result:
                        purchase.auto_extracted = extraction_result["success"]
                        purchase.extracted_total = extraction_result.get("total")
                        purchase.extraction_confidence = extraction_result.get("confidence")
                        purchase.extraction_log = str(extraction_result)

                    purchase.uploaded_at = timezone.now()
                    purchase.save()

                logger.info(f"Compra creada con ID: {purchase_id}, Factura: {bool(receipt_path)}")

                return JsonResponse(
                    {
                        "success": True,
                        "purchase_id": purchase_id,
                        "receipt_attached": bool(receipt_path),
                        "auto_extracted": purchase.auto_extracted if receipt_path else False,
                        "total": float(total),
                    }
                )

        except Exception as e:
            # Si hay error, eliminar archivo guardado si existe
            if receipt_path:
                delete_receipt_file(receipt_path)
            raise

    except Exception as e:
        logger.error(f"Error en save_purchase_with_receipt: {str(e)}", exc_info=True)

        return JsonResponse({"success": False, "error": f"Error interno: {str(e)}"}, status=500)


@ensure_csrf_cookie
def view_receipt(request, purchase_id):
    """
    Vista para visualizar una factura adjunta.

    URL: /compras/<id>/factura/
    """
    try:
        from django.http import FileResponse, Http404

        from app.models.purchase import Purchase

        # Verificar autenticación
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"success": False, "error": "No autenticado"}, status=401)

        # Obtener compra
        purchase = Purchase.objects.filter(id=purchase_id).first()
        if not purchase or not purchase.receipt_file:
            raise Http404("Factura no encontrada")

        # Ruta completa del archivo
        file_path = os.path.join(settings.MEDIA_ROOT, purchase.receipt_file)

        if not os.path.exists(file_path):
            raise Http404("Archivo de factura no encontrado")

        # Retornar archivo
        return FileResponse(open(file_path, "rb"))

    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error en view_receipt: {str(e)}", exc_info=True)
        return JsonResponse({"success": False, "error": str(e)}, status=500)
