import json

from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from app.models.product import Product
from app.models.purchase import Purchase
from app.models.supplier import Supplier
from app.models.user import User
from app.views.purchase_view import PurchaseView


class PurchaseController:
    @staticmethod
    def index(request):
        """Mostrar lista de compras"""
        if "user_id" not in request.session:
            return HttpResponseRedirect("/login/")

        user = User.get_by_id(request.session["user_id"])
        if not user:
            return HttpResponseRedirect("/login/")

        purchases = Purchase.get_all()
        from django.http import HttpResponse

        return HttpResponse(PurchaseView.index(user, purchases, request))

    @staticmethod
    @ensure_csrf_cookie
    def create(request):
        """Crear una nueva compra"""
        if "user_id" not in request.session:
            return HttpResponseRedirect("/login/")

        user = User.get_by_id(request.session["user_id"])
        if not user:
            return HttpResponseRedirect("/login/")

        if request.method == "POST":
            try:
                # ===== VERIFICAR SI VIENE CON FACTURA (MODO OCR) =====
                if 'receipt_file' in request.FILES and request.FILES['receipt_file']:
                    from app.utils.file_validators import validate_receipt_file
                    from app.utils.file_utils import save_receipt_file
                    from app.services.ocr_service import receipt_extractor
                    from django.utils import timezone
                    import tempfile
                    import os
                    
                    receipt_file = request.FILES['receipt_file']
                    
                    # Validar archivo
                    try:
                        validate_receipt_file(receipt_file)
                    except Exception as ve:
                        raise ValueError(f"Archivo de factura no válido: {str(ve)}")
                    
                    # Guardar archivo
                    receipt_path = save_receipt_file(receipt_file)
                    
                    # Extraer total con OCR si no viene manual
                    extracted_total = request.POST.get('total')
                    extraction_result = None
                    
                    if not extracted_total or extracted_total == '' or extracted_total == '0':
                        # Intentar extraer con OCR
                        with tempfile.NamedTemporaryFile(
                            delete=False, 
                            suffix=os.path.splitext(receipt_file.name)[1]
                        ) as tmp_file:
                            for chunk in receipt_file.chunks():
                                tmp_file.write(chunk)
                            tmp_path = tmp_file.name
                        
                        try:
                            extraction_result = receipt_extractor.extract_total(tmp_path)
                            if extraction_result['success']:
                                extracted_total = extraction_result['total']
                        finally:
                            try:
                                os.unlink(tmp_path)
                            except:
                                pass
                    
                    # Obtener datos de la compra
                    numero_factura = request.POST.get("numero_factura", "")
                    proveedor_id = request.POST.get("proveedor_id")
                    fecha = request.POST.get("fecha")
                    total = float(extracted_total or 0)
                    estado = request.POST.get("estado", "pendiente")
                    notas = request.POST.get("notas", "")
                    
                    if not proveedor_id or not fecha:
                        # Eliminar archivo si falta datos
                        from app.utils.file_utils import delete_receipt_file
                        delete_receipt_file(receipt_path)
                        raise ValueError("Faltan datos requeridos")
                    
                    # Crear la compra
                    purchase_data = {
                        "numero_factura": numero_factura,
                        "proveedor_id": int(proveedor_id),
                        "usuario_id": request.session["user_id"],
                        "fecha": fecha,
                        "total": total,
                        "estado": estado,
                        "notas": notas,
                    }
                    
                    purchase_id = Purchase.create(purchase_data, [])
                    
                    # Actualizar con datos de factura
                    purchase_obj = Purchase.objects.get(id=purchase_id)
                    purchase_obj.receipt_file = receipt_path
                    purchase_obj.receipt_type = 'pdf' if receipt_path.lower().endswith('.pdf') else 'image'
                    
                    if extraction_result:
                        purchase_obj.auto_extracted = extraction_result['success']
                        purchase_obj.extracted_total = extraction_result.get('total')
                        purchase_obj.extraction_confidence = extraction_result.get('confidence')
                        purchase_obj.extraction_log = str(extraction_result)
                    
                    purchase_obj.uploaded_at = timezone.now()
                    purchase_obj.save()
                    
                    return HttpResponseRedirect("/compras/")
                    
                else:
                    # ===== MODO MANUAL MEJORADO =====
                    from django.utils import timezone
                    
                    # Verificar si viene con factura adjunta (manual)
                    receipt_path = None
                    if 'receipt_file_manual' in request.FILES and request.FILES['receipt_file_manual']:
                        receipt_path = PurchaseController._validate_and_save_receipt(
                            request.FILES['receipt_file_manual']
                        )
                    
                    # Obtener datos básicos
                    numero_factura = request.POST.get("numero_factura", "")
                    proveedor_id = request.POST.get("proveedor_id")
                    fecha = request.POST.get("fecha")
                    estado = request.POST.get("estado", "pendiente")
                    notas = request.POST.get("notas", "")
                    
                    # Verificar modo sin productos
                    no_products_mode = request.POST.get("no_products_mode") == "on"
                    
                    if no_products_mode:
                        # Solo guardar total sin productos
                        manual_total = request.POST.get("manual_total")
                        if not manual_total:
                            raise ValueError("Debe ingresar un total")
                        
                        total = float(manual_total)
                        if total <= 0:
                            raise ValueError("El total debe ser mayor a cero")
                        
                        purchase_data = {
                            "numero_factura": numero_factura,
                            "proveedor_id": int(proveedor_id),
                            "usuario_id": request.session["user_id"],
                            "fecha": fecha or timezone.now(),
                            "total": total,
                            "estado": estado,
                            "notas": notas or "Compra sin detalles de productos"
                        }
                        purchase_id = Purchase.create(purchase_data, details=[])
                        
                        # Adjuntar factura si existe
                        if receipt_path and purchase_id:
                            purchase = Purchase.objects.get(id=purchase_id)
                            purchase.receipt_file = receipt_path
                            purchase.receipt_type = 'pdf' if receipt_path.lower().endswith('.pdf') else 'image'
                            purchase.auto_extracted = False
                            purchase.uploaded_at = timezone.now()
                            purchase.save()
                        
                        return HttpResponseRedirect(f"/compras/{purchase_id}/ver/")
                    
                    # Modo normal con productos
                    total = float(request.POST.get("total", 0))
                    details_json = request.POST.get("details", "[]")
                    details = json.loads(details_json)

                    if not proveedor_id or not fecha or not details:
                        raise ValueError("Faltan datos requeridos")

                    purchase_data = {
                        "numero_factura": numero_factura,
                        "proveedor_id": int(proveedor_id),
                        "usuario_id": request.session["user_id"],
                        "fecha": fecha,
                        "total": total,
                        "estado": estado,
                        "notas": notas,
                    }

                    purchase_id = Purchase.create(purchase_data, details)
                    
                    # Adjuntar factura si existe
                    if receipt_path and purchase_id:
                        purchase = Purchase.objects.get(id=purchase_id)
                        purchase.receipt_file = receipt_path
                        purchase.receipt_type = 'pdf' if receipt_path.lower().endswith('.pdf') else 'image'
                        purchase.auto_extracted = False
                        purchase.uploaded_at = timezone.now()
                        purchase.save()
                    
                    return HttpResponseRedirect("/compras/")


            except Exception as e:
                suppliers = Supplier.get_all()
                products = Product.get_all()
                error_message = f"Error al crear la compra: {str(e)}"
                from django.http import HttpResponse

                return HttpResponse(
                    PurchaseView.create(user, suppliers, products, request, error_message)
                )

        # GET request
        suppliers = Supplier.get_all()
        products = Product.get_all()
        from django.http import HttpResponse

        return HttpResponse(PurchaseView.create(user, suppliers, products, request))

    @staticmethod
    @ensure_csrf_cookie
    def edit(request, purchase_id):
        """Editar una compra existente"""
        if "user_id" not in request.session:
            return HttpResponseRedirect("/login/")

        user = User.get_by_id(request.session["user_id"])
        if not user:
            return HttpResponseRedirect("/login/")

        purchase = Purchase.get_by_id(purchase_id)
        if not purchase:
            return HttpResponseRedirect("/compras/")

        if request.method == "POST":
            try:
                # Obtener datos de la compra
                numero_factura = request.POST.get("numero_factura", "")
                proveedor_id = request.POST.get("proveedor_id")
                fecha = request.POST.get("fecha")
                total = float(request.POST.get("total", 0))
                estado = request.POST.get("estado", "pendiente")
                notas = request.POST.get("notas", "")

                # Obtener detalles de productos (JSON)
                details_json = request.POST.get("details", "[]")
                details = json.loads(details_json)

                if not proveedor_id or not fecha:
                    raise ValueError("Faltan datos requeridos")

                # Actualizar la compra
                purchase_data = {
                    "numero_factura": numero_factura,
                    "proveedor_id": int(proveedor_id),
                    "fecha": fecha,
                    "total": total,
                    "estado": estado,
                    "notas": notas,
                }

                Purchase.update(purchase_id, purchase_data)

                # Actualizar detalles
                if details:
                    Purchase.update_details(purchase_id, details)

                return HttpResponseRedirect("/compras/")

            except Exception as e:
                suppliers = Supplier.get_all()
                products = Product.get_all()
                details = Purchase.get_details(purchase_id)
                error_message = f"Error al actualizar la compra: {str(e)}"
                from django.http import HttpResponse

                return HttpResponse(
                    PurchaseView.edit(
                        user, purchase, suppliers, products, details, request, error_message
                    )
                )

        # GET request
        suppliers = Supplier.get_all()
        products = Product.get_all()
        details = Purchase.get_details(purchase_id)
        from django.http import HttpResponse

        return HttpResponse(
            PurchaseView.edit(user, purchase, suppliers, products, details, request)
        )

    @staticmethod
    def delete(request, purchase_id):
        """Eliminar una compra"""
        if "user_id" not in request.session:
            return HttpResponseRedirect("/login/")

        if request.method == "POST":
            try:
                Purchase.delete(purchase_id)
            except Exception as e:
                pass

        return HttpResponseRedirect("/compras/")

    @staticmethod
    def view(request, purchase_id):
        """Ver detalle de una compra"""
        if "user_id" not in request.session:
            return HttpResponseRedirect("/login/")

        user = User.get_by_id(request.session["user_id"])
        if not user:
            return HttpResponseRedirect("/login/")

        purchase = Purchase.get_by_id(purchase_id)
        if not purchase:
            return HttpResponseRedirect("/compras/")

        details = Purchase.get_details(purchase_id)
        from django.http import HttpResponse

        return HttpResponse(PurchaseView.view(user, purchase, details))
