from django.http import HttpResponse
from django.middleware.csrf import get_token

from app.views.layout import Layout


class PurchaseView:
    @staticmethod
    def index(user, purchases, request):
        """Vista de lista de compras"""

        from django.middleware.csrf import get_token

        csrf_token = f'<input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">'

        # Tabla de compras
        rows = ""
        if purchases:
            for idx, purchase in enumerate(purchases, 1):
                estado_badge = {
                    "pendiente": '<span class="badge badge-warning">Pendiente</span>',
                    "completada": '<span class="badge badge-success">Completada</span>',
                    "cancelada": '<span class="badge badge-cancelada">Cancelada</span>',
                }.get(purchase["estado"], purchase["estado"])

                # Columna de factura
                receipt_column = "-"
                try:
                    from app.models.purchase import Purchase as PurchaseModel

                    purchase_obj = PurchaseModel.objects.get(id=purchase["id"])
                    if purchase_obj.has_receipt():
                        icon_class = (
                            "fa-file-pdf text-danger" if purchase_obj.receipt_type == "pdf" else "fa-image text-primary"
                        )
                        receipt_url = f"/media/{purchase_obj.receipt_file}"
                        receipt_column = f'<a href="{receipt_url}" target="_blank" title="Ver factura"><i class="fas {icon_class} fa-lg"></i></a>'
                        if purchase_obj.auto_extracted:
                            receipt_column += ' <span class="badge badge-success" title="Extraído con OCR" style="font-size: 10px;"><i class="fas fa-robot"></i></span>'
                except:
                    pass

                rows += f"""
                <tr>
                    <td class="d-none d-md-table-cell">{idx}</td>
                    <td>{purchase.get('numero_factura', 'N/A')}</td>
                    <td>{purchase['proveedor_nombre']}</td>
                    <td class="d-none d-md-table-cell">{purchase['fecha']}</td>
                    <td>S/ {purchase['total']:.2f}</td>
                    <td>{estado_badge}</td>
                    <td class="d-none d-md-table-cell">{purchase['usuario_nombre']}</td>
                    <td class="text-center d-none d-md-table-cell">{receipt_column}</td>
                    <td>
                        <a href="/compras/{purchase['id']}/ver/" class="btn btn-info btn-sm">Ver</a>
                        <a href="/compras/{purchase['id']}/editar/" class="btn btn-warning">Editar</a>
                        <form method="POST" action="/compras/{purchase['id']}/eliminar/" class="d-inline">
                            {csrf_token}
                            <button type="submit" class="btn btn-danger"
                                    onclick="event.preventDefault(); var form = this.form; if(typeof Swal !== 'undefined') {{ Swal.fire({{ title: '¿Eliminar compra?', text: 'Esta acción no se puede deshacer', icon: 'warning', showCancelButton: true, confirmButtonColor: '#d33', cancelButtonColor: '#3085d6', confirmButtonText: 'Sí, eliminar', cancelButtonText: 'Cancelar' }}).then(function(result) {{ if (result.isConfirmed) {{ form.submit(); }} }}); }} else if (confirm('¿Estás seguro de eliminar esta compra?')) {{ form.submit(); }} return false;">
                                Eliminar
                            </button>
                        </form>
                    </td>
                </tr>
                """

            table_content = f"""
            <div class="table-container">
                <table>
                <thead>
                    <tr>
                        <th class="d-none d-md-table-cell">#</th>
                        <th>N° Factura</th>
                        <th>Proveedor</th>
                        <th class="d-none d-md-table-cell">Fecha</th>
                        <th>Total</th>
                        <th>Estado</th>
                        <th class="d-none d-md-table-cell">Usuario</th>
                        <th width="80" class="d-none d-md-table-cell">Factura</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
                </table>
            </div>
            """
        else:
            table_content = """
            <div class="empty-state">
                <div class="icon-4xl"><i class="fas fa-shopping-cart"></i></div>
                <h3>No hay compras registradas</h3>
                <p>Comienza agregando tu primera compra</p>
            </div>
            """

        content = f"""
        <div class="card">
            <div class="card-header">
                <span>Gestión de Compras</span>
                <a href="/compras/crear/" class="btn btn-primary">+ Nueva Compra</a>
            </div>
            {table_content}
        </div>
        """

        return Layout.render("Compras", user, "compras", content)

    @staticmethod
    def create(user, suppliers, products, request, error=None):
        """Vista de formulario para crear compra"""

        from django.middleware.csrf import get_token

        csrf_token = f'<input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">'

        error_html = ""
        if error:
            error_html = f"""
            <div class="alert-error">
                {error}
            </div>
            """

        # Select de proveedores - incluir proveedor general para OCR
        from app.models.supplier import Supplier

        default_supplier, _ = Supplier.objects.get_or_create(
            nombre="Proveedor General (OCR)", defaults={"activo": True, "tax_identification_type": "NIT"}
        )
        suppliers_options = '<option value="">Seleccione un proveedor</option>'
        suppliers_options += (
            f'<option value="{default_supplier.id}" data-default="true">Proveedor General (OCR)</option>'
        )
        for supplier in suppliers:
            if supplier["id"] != default_supplier.id:
                suppliers_options += f'<option value="{supplier["id"]}">{supplier["nombre"]}</option>'

        # Select de productos
        products_options = '<option value="">Seleccione un producto</option>'
        for product in products:
            products_options += f'<option value="{product["id"]}" data-price="{product["precio_venta"]}">{product["nombre"]} - S/ {product["precio_venta"]:.2f}</option>'

        # JavaScript para OCR
        receipt_js = """
<script src="/static/js/purchase_receipt.js"></script>
"""

        content = f"""
        <div class="card">
            <div class="card-header">
                <span>Nueva Compra</span>
                <a href="/compras/" class="btn btn-secondary">← Volver</a>
            </div>
            {error_html}

            <!-- SELECTOR DE MODO -->
            <div class="p-20 bg-light">
                <h5 class="mb-3"><i class="fas fa-cog"></i> Modo de Entrada</h5>
                <div class="btn-group w-100" role="group">
                    <input type="radio" class="btn-check" name="entry_mode" id="mode_manual" value="manual" checked>
                    <label class="btn btn-outline-primary" for="mode_manual" style="width: 50%; padding: 15px;">
                        <i class="fas fa-keyboard fa-2x d-block mb-2"></i>
                        <strong>Modo Manual</strong><br>
                        <small>Ingreso producto por producto</small>
                    </label>

                    <input type="radio" class="btn-check" name="entry_mode" id="mode_auto" value="auto">
                    <label class="btn btn-outline-success" for="mode_auto" style="width: 50%; padding: 15px;">
                        <i class="fas fa-robot fa-2x d-block mb-2"></i>
                        <strong>Modo OCR Automático</strong><br>
                        <small>Subir factura y extraer total</small>
                    </label>
                </div>
            </div>

            <!-- PANEL MANUAL -->
            <div id="panel_manual" class="mode-panel">
                <form method="POST" action="/compras/crear/" id="purchaseForm" class="p-20" enctype="multipart/form-data">
                    {csrf_token}
                    <input type="hidden" name="details" id="detailsInput" value="[]">

                <div class="form-grid">
                    <div>
                        <label class="form-label">N° Factura</label>
                        <input type="text" name="numero_factura" placeholder="Opcional" class="form-input">
                    </div>

                    <div>
                        <label class="form-label">Proveedor *</label>
                        <select name="proveedor_id" id="supplierSelect" class="form-select">
                            {suppliers_options}
                        </select>
                    </div>


                    <div>
                        <label class="form-label">Fecha *</label>
                        <input type="date" name="fecha" required class="form-input" value="{__import__('datetime').date.today().isoformat()}">
                    </div>


                    <div>
                        <label class="form-label">Estado</label>
                        <select name="estado" class="form-select">
                            <option value="pendiente">Pendiente</option>
                            <option value="completada">Completada</option>
                            <option value="cancelada">Cancelada</option>
                        </select>
                    </div>
                </div>

                <div class="mt-20">
                    <label class="form-label">Notas</label>
                    <textarea name="notas" rows="2" class="form-textarea"></textarea>
                </div>

                <!-- NUEVA SECCIÓN: Adjuntar Factura -->
                <div class="mt-3 p-3" style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px;">
                    <h6 class="mb-3"><i class="fas fa-paperclip"></i> Adjuntar Factura (Opcional)</h6>
                    <div>
                        <input type="file" name="receipt_file_manual" id="receipt_file_manual" class="form-input"
                               accept=".pdf,.jpg,.jpeg,.png,.gif,.bmp">
                        <small class="form-text text-muted">PDF o imagen (máx. 5MB) - Se guardará con la compra</small>
                    </div>

                    <!-- Previsualización de la factura -->
                    <div id="receipt_preview_manual" style="display: none; margin-top: 15px; border: 1px solid #ddd; border-radius: 4px; padding: 10px; background: white;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <strong><i class="fas fa-eye"></i> Previsualización</strong>
                            <button type="button" onclick="clearManualReceiptPreview()" class="btn btn-sm btn-secondary">
                                <i class="fas fa-times"></i> Quitar
                            </button>
                        </div>
                        <div id="receipt_preview_content_manual" style="max-height: 400px; overflow: auto; text-align: center;">
                            <!-- Aquí se mostrará la imagen o PDF -->
                        </div>
                    </div>
                </div>

                <!-- NUEVA SECCIÓN: Modo sin productos -->
                <div class="mt-3 p-3" style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 4px;">
                    <div class="form-check mb-2">
                        <input type="checkbox" class="form-check-input" id="no_products_mode" name="no_products_mode">
                        <label class="form-check-label" for="no_products_mode">
                            <strong><i class="fas fa-exclamation-triangle text-warning"></i> Compra sin detalles de productos</strong>
                        </label>
                        <small class="d-block text-muted mt-1">Marcar si los productos no están registrados en el sistema. Solo se guardará el total de la compra.</small>
                    </div>
                    <div id="manual_total_input" style="display: none; margin-top: 15px;">
                        <label class="form-label"><strong>Total de la Compra *</strong></label>
                        <div style="display: flex; align-items: center;">
                            <span style="padding: 10px 15px; background: #e9ecef; border: 1px solid #ced4da; border-radius: 4px 0 0 4px; font-weight: bold;">S/</span>
                            <input type="number" name="manual_total" id="manual_total" step="0.01" min="0" class="form-input"
                                   style="border-radius: 0 4px 4px 0; flex: 1; font-size: 1.1em;" placeholder="0.00" disabled>
                        </div>
                        <small class="form-text text-muted">Ingrese el total de la factura</small>
                    </div>
                </div>

                <div id="products_section_wrapper">
                    <hr class="form-divider">

                    <h3 class="mb-20">Productos</h3>

                <div class="purchase-product-grid">
                    <div>
                        <label class="form-label">Producto</label>
                        <select id="productSelect" class="form-select">
                            {products_options}
                        </select>
                    </div>
                    <div>
                        <label class="form-label">Cantidad</label>
                        <input type="number" id="quantityInput" min="1" value="1" class="form-input">
                    </div>
                    <div>
                        <label class="form-label">Precio Unitario</label>
                        <input type="number" id="priceInput" min="0" step="0.01" value="0" class="form-input">
                    </div>
                    <div>
                        <button type="button" class="btn btn-success" id="addProductBtn">+ Agregar</button>
                    </div>
                </div>

                <div class="table-container">
                <table class="mt-20">
                    <thead>
                        <tr>
                            <th>Producto</th>
                            <th class="col-w-100">Cantidad</th>
                            <th class="col-w-120">P. Unitario</th>
                            <th class="col-w-120">Subtotal</th>
                            <th class="col-w-80">Acción</th>
                        </tr>
                    </thead>
                    <tbody id="productsTableBody">
                        <tr id="emptyRow">
                            <td colspan="5" class="empty-message-cell">
                                No hay productos agregados
                            </td>
                        </tr>
                    </tbody>
                    <tfoot>
                        <tr>
                            <td colspan="3" class="text-right">TOTAL:</td>
                            <td id="totalAmount">S/ 0.00</td>
                            <td></td>
                        </tr>
                    </tfoot>
                </table>
                </div>

                <input type="hidden" name="total" id="totalInput" value="0">
                </div> <!-- Cierre de products_section_wrapper -->

                    <div class="form-actions-end mt-30">
                        <a href="/compras/" class="btn btn-secondary">Cancelar</a>
                        <button type="submit" class="btn btn-primary">Guardar Compra</button>
                    </div>
                </form>
            </div>

            <!-- PANEL AUTOMATICO (OCR) -->
            <div id="panel_auto" class="mode-panel" style="display: none;">
                <form method="POST" action="/compras/crear/" id="ocrPurchaseForm" class="p-20" enctype="multipart/form-data">
                    {csrf_token}

                    <div class="ocr-info-banner">
                        <i class="fas fa-robot"></i>
                        <div>
                            <strong>Modo OCR Inteligente</strong><br>
                            <small>Sube tu factura y extraeremos autom&aacute;ticamente: total, proveedor, N&deg; factura y fecha. Puedes editar cualquier campo antes de guardar.</small>
                        </div>
                    </div>

                    <!-- Step 1: Upload -->
                    <div class="ocr-step">
                        <div class="ocr-step-header">
                            <span class="ocr-step-num">1</span>
                            <strong>Subir Factura</strong>
                        </div>
                        <div class="ocr-upload-area" id="ocr_upload_area">
                            <input type="file" class="form-input" id="receipt_file" name="receipt_file"
                                   accept=".pdf,.jpg,.jpeg,.png,.gif,.bmp" required style="display:none;">
                            <div id="upload_placeholder" style="text-align:center; cursor:pointer;" onclick="document.getElementById('receipt_file').click()">
                                <i class="fas fa-cloud-upload-alt" style="font-size:2.5em; color:#6c63ff; margin-bottom:10px;"></i>
                                <p style="margin:0; font-weight:600; color:#333;">Arrastra o haz clic para subir</p>
                                <small style="color:#888;">PDF, JPG, PNG (m&aacute;x. 5MB)</small>
                            </div>
                            <div id="upload_file_info" style="display:none;"></div>
                        </div>
                        <div class="mt-2 text-center">
                            <button type="button" class="btn btn-primary btn-lg" id="btn_extract" disabled style="min-width: 280px;">
                                <i class="fas fa-search"></i> Extraer Datos con OCR
                            </button>
                        </div>
                    </div>

                    <!-- Step 2: Preview (hidden until extraction) -->
                    <div id="extraction_result" style="display: none;">
                        <div class="ocr-step">
                            <div class="ocr-step-header">
                                <span class="ocr-step-num">2</span>
                                <strong>Vista Previa - Datos Extra&iacute;dos</strong>
                                <div id="confidence_badge" style="margin-left:auto;"></div>
                            </div>

                            <div class="ocr-preview-grid">
                                <!-- Columna izquierda: imagen -->
                                <div class="ocr-preview-image">
                                    <div id="receipt_image_preview" class="receipt-thumb">
                                        <i class="fas fa-file-invoice" style="font-size:3em; color:#ccc;"></i>
                                        <small style="color:#999;">Vista previa</small>
                                    </div>
                                    <!-- Confidence -->
                                    <div style="margin-top:12px;">
                                        <label class="form-label" style="font-size:0.85em; margin-bottom:4px;">Confianza OCR</label>
                                        <div style="background: #e9ecef; border-radius: 6px; height: 24px; overflow: hidden;">
                                            <div id="confidence_bar" style="height: 100%; width: 0%; background: linear-gradient(90deg, #28a745, #20c997); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 0.75em; transition: width 0.5s ease;"></div>
                                        </div>
                                    </div>
                                </div>

                                <!-- Columna derecha: campos editables -->
                                <div class="ocr-preview-fields">
                                    <div class="ocr-field-row">
                                        <div class="ocr-field">
                                            <label class="form-label">
                                                <i class="fas fa-dollar-sign text-success"></i> Total Factura
                                                <span class="ocr-badge" id="badge_total" style="display:none;">OCR</span>
                                            </label>
                                            <div style="display: flex;">
                                                <span class="ocr-currency-prefix">$</span>
                                                <input type="number" class="form-input ocr-editable" id="extracted_total" name="total"
                                                       step="0.01" placeholder="0.00" style="border-radius: 0 6px 6px 0; flex: 1; font-size: 1.15em; font-weight: 600;">
                                            </div>
                                        </div>
                                        <div class="ocr-field">
                                            <label class="form-label">
                                                <i class="fas fa-building text-primary"></i> Proveedor
                                                <span class="ocr-badge" id="badge_supplier" style="display:none;">OCR</span>
                                            </label>
                                            <div id="ocr_supplier_display" style="display:none; margin-bottom:6px;">
                                                <small class="text-muted"><i class="fas fa-robot"></i> Detectado: <span id="ocr_supplier_text"></span></small>
                                            </div>
                                            <select name="proveedor_id" id="ocr_proveedor_select" required class="form-select ocr-editable">
                                                {suppliers_options}
                                            </select>
                                            <div id="ocr_supplier_actions" style="display:none; margin-top:4px;">
                                                <small>
                                                    <a href="/proveedores/crear/" target="_blank" id="ocr_create_supplier_link" style="color:#6c63ff; text-decoration:none;">
                                                        <i class="fas fa-plus-circle"></i> Crear nuevo proveedor
                                                    </a>
                                                    <span style="color:#888; margin-left:8px;" id="ocr_supplier_hint"></span>
                                                </small>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="ocr-field-row">
                                        <div class="ocr-field">
                                            <label class="form-label">
                                                <i class="fas fa-hashtag text-info"></i> N&deg; Factura
                                                <span class="ocr-badge" id="badge_invoice" style="display:none;">OCR</span>
                                            </label>
                                            <input type="text" name="numero_factura" id="ocr_numero_factura" class="form-input ocr-editable" placeholder="Opcional">
                                        </div>
                                        <div class="ocr-field">
                                            <label class="form-label">
                                                <i class="fas fa-calendar text-warning"></i> Fecha
                                                <span class="ocr-badge" id="badge_date" style="display:none;">OCR</span>
                                            </label>
                                            <input type="date" name="fecha" id="ocr_fecha" required class="form-input ocr-editable" value="{__import__('datetime').date.today().isoformat()}">
                                        </div>
                                    </div>
                                    <div class="ocr-field-row">
                                        <div class="ocr-field">
                                            <label class="form-label"><i class="fas fa-flag"></i> Estado</label>
                                            <select name="estado" class="form-select">
                                                <option value="pendiente">Pendiente</option>
                                                <option value="completada">Completada</option>
                                                <option value="cancelada">Cancelada</option>
                                            </select>
                                        </div>
                                        <div class="ocr-field">
                                            <label class="form-label"><i class="fas fa-sticky-note"></i> Notas</label>
                                            <input type="text" name="notas" class="form-input" placeholder="Notas adicionales...">
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Texto extraido colapsable -->
                            <details class="ocr-extracted-text" style="margin-top:12px;">
                                <summary style="cursor:pointer; color:#6c757d; font-size:0.85em;">
                                    <i class="fas fa-file-alt"></i> Ver texto completo extra&iacute;do por OCR
                                </summary>
                                <pre id="ocr_raw_text" style="max-height:200px; overflow:auto; background:#f8f9fa; padding:10px; border-radius:4px; font-size:0.8em; margin-top:8px; white-space:pre-wrap; word-break:break-word;"></pre>
                            </details>
                        </div>
                    </div>

                    <input type="hidden" name="mode" value="ocr">
                    <input type="hidden" name="details" value="[]">

                    <div class="form-actions-end mt-4">
                        <button type="button" class="btn btn-secondary" id="btnSwitchToManual">
                            <i class="fas fa-exchange-alt"></i> Cambiar a Manual
                        </button>
                        <button type="submit" class="btn btn-success btn-lg" id="btnSaveOcr">
                            <i class="fas fa-save"></i> Guardar Compra
                        </button>
                    </div>
                </form>
            </div>
        </div>

        {receipt_js}

        <style>
        .mode-panel {{ padding: 0; }}
        .btn-check:checked + label {{ background-color: #007bff !important; color: white !important; }}
        .btn-check:checked + label.btn-outline-success {{ background-color: #28a745 !important; }}
        .alert-info {{ padding: 15px; margin-bottom: 20px; background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 4px; }}

        /* OCR Panel Styles */
        .ocr-info-banner {{
            display: flex; align-items: center; gap: 14px;
            padding: 16px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border-radius: 8px; margin-bottom: 20px;
        }}
        .ocr-info-banner i {{ font-size: 2em; opacity: 0.9; }}
        .ocr-step {{
            background: #fff; border: 1px solid #e0e0e0; border-radius: 8px;
            padding: 20px; margin-bottom: 16px;
        }}
        .ocr-step-header {{
            display: flex; align-items: center; gap: 10px; margin-bottom: 16px;
        }}
        .ocr-step-num {{
            width: 28px; height: 28px; border-radius: 50%; background: #6c63ff;
            color: white; font-weight: bold; font-size: 0.85em;
            display: flex; align-items: center; justify-content: center;
        }}
        .ocr-upload-area {{
            border: 2px dashed #d0d0d0; border-radius: 8px; padding: 30px;
            transition: border-color 0.3s, background 0.3s; margin-bottom: 12px;
        }}
        .ocr-upload-area.drag-over {{ border-color: #6c63ff; background: #f0eeff; }}
        .ocr-upload-area.has-file {{ border-style: solid; border-color: #28a745; background: #f6fff6; }}
        .ocr-preview-grid {{
            display: grid; grid-template-columns: 240px 1fr; gap: 20px;
        }}
        @media (max-width: 768px) {{
            .ocr-preview-grid {{ grid-template-columns: 1fr; }}
        }}
        .ocr-preview-image {{
            display: flex; flex-direction: column; align-items: center;
        }}
        .receipt-thumb {{
            width: 100%; min-height: 200px; max-height: 320px; overflow: hidden;
            border: 1px solid #e0e0e0; border-radius: 6px; background: #fafafa;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
        }}
        .receipt-thumb img {{ width: 100%; height: auto; object-fit: contain; border-radius: 6px; }}
        .ocr-preview-fields {{ display: flex; flex-direction: column; gap: 12px; }}
        .ocr-field-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
        @media (max-width: 600px) {{
            .ocr-field-row {{ grid-template-columns: 1fr; }}
        }}
        .ocr-field label {{ font-size: 0.85em; margin-bottom: 4px; }}
        .ocr-badge {{
            display: inline-block; font-size: 0.65em; padding: 2px 6px;
            background: #ffc107; color: #333; border-radius: 3px; font-weight: 700;
            margin-left: 6px; vertical-align: middle;
        }}
        .ocr-editable.ocr-filled {{
            border-color: #28a745 !important; background: #f0fff4 !important;
            box-shadow: 0 0 0 2px rgba(40, 167, 69, 0.15);
        }}
        .ocr-currency-prefix {{
            padding: 8px 14px; background: #e9ecef; border: 1px solid #ced4da;
            border-radius: 6px 0 0 6px; font-weight: bold; color: #495057;
            display: flex; align-items: center;
        }}
        </style>

        <script>
        document.getElementById('btnSwitchToManual')?.addEventListener('click', function() {{
            document.getElementById('mode_manual').checked = true;
            document.getElementById('panel_manual').style.display = 'block';
            document.getElementById('panel_auto').style.display = 'none';
        }});
        </script>

        <script src="/static/js/purchase-manager.js?v=2.0"></script>
        <script src="/static/js/purchase_manual_mode.js?v=2.0"></script>
        """

        return Layout.render("Nueva Compra", user, "compras", content)

    @staticmethod
    def edit(user, purchase, suppliers, products, details, request, error=None):
        """Vista de formulario para editar compra"""

        from django.middleware.csrf import get_token

        csrf_token = f'<input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">'

        error_html = ""
        if error:
            error_html = f"""
            <div class="alert-error">
                {error}
            </div>
            """

        # Select de proveedores
        suppliers_options = '<option value="">-- Seleccione un proveedor --</option>'
        for supplier in suppliers:
            selected = "selected" if supplier["id"] == purchase["proveedor_id"] else ""
            suppliers_options += f'<option value="{supplier["id"]}" {selected}>{supplier["nombre"]}</option>'

        # Select de productos
        products_options = '<option value="">Seleccione un producto</option>'
        for product in products:
            products_options += f'<option value="{product["id"]}" data-price="{product["precio_venta"]}">{product["nombre"]} - S/ {product["precio_venta"]:.2f}</option>'

        # Estados
        estados = ["pendiente", "completada", "cancelada"]
        estado_options = ""
        for estado in estados:
            selected = "selected" if estado == purchase["estado"] else ""
            estado_options += f'<option value="{estado}" {selected}>{estado.capitalize()}</option>'

        # Detalles iniciales en JavaScript
        details_json = "[]"
        if details:
            import json

            details_data = []
            for detail in details:
                details_data.append(
                    {
                        "producto_id": detail["producto_id"],
                        "producto_nombre": detail["producto_nombre"],
                        "cantidad": detail["cantidad"],
                        "precio_unitario": float(detail["precio_unitario"]),
                        "subtotal": float(detail["subtotal"]),
                    }
                )
            details_json = json.dumps(details_data)

        content = f"""
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1 class="h3 mb-0">Editar Compra #{purchase['id']}</h1>
            <a href="/compras/" class="btn btn-secondary">
                <i class="fas fa-arrow-left"></i> Volver
            </a>
        </div>

        {error_html}

        <div class="card shadow-sm">
            <div class="card-body">
                <form method="POST" id="purchaseForm">
                    {csrf_token}
                    <input type="hidden" name="details" id="detailsInput" value="">

                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label">N° Factura</label>
                            <input type="text" class="form-control" name="numero_factura" value="{purchase.get('numero_factura', '')}">
                        </div>

                        <div class="col-md-6 mb-3">
                            <label class="form-label">Proveedor <span class="text-danger">*</span></label>
                            <select class="form-select" name="proveedor_id" required>
                                {suppliers_options}
                            </select>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Fecha <span class="text-danger">*</span></label>
                            <input type="date" class="form-control" name="fecha" value="{str(purchase['fecha']).split()[0] if purchase['fecha'] else ''}" required>
                        </div>

                        <div class="col-md-6 mb-3">
                            <label class="form-label">Estado</label>
                            <select class="form-select" name="estado">
                                {estado_options}
                            </select>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">Notas</label>
                        <textarea class="form-control" name="notas" rows="2">{purchase.get('notas', '')}</textarea>
                    </div>

                    <hr class="my-4">

                    <h5 class="mb-3">Productos</h5>

                    <div class="row mb-3">
                        <div class="col-md-5">
                            <label class="form-label">Producto</label>
                            <select class="form-select" id="productSelect">
                                {products_options}
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Cantidad</label>
                            <input type="number" class="form-control" id="quantityInput" min="1" value="1">
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Precio Unitario</label>
                            <input type="number" class="form-control" id="priceInput" min="0" step="0.01" value="0">
                        </div>
                        <div class="col-md-1 d-flex align-items-end">
                            <button type="button" class="btn btn-success w-100" id="addProductBtn">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                    </div>

                    <div class="table-responsive">
                        <table class="table table-bordered" id="productsTable">
                            <thead class="table-light">
                                <tr>
                                    <th>Producto</th>
                                    <th width="100">Cantidad</th>
                                    <th width="120">P. Unitario</th>
                                    <th width="120">Subtotal</th>
                                    <th width="80">Acción</th>
                                </tr>
                            </thead>
                            <tbody id="productsTableBody">
                                <tr id="emptyRow">
                                    <td colspan="5" class="text-center text-muted">
                                        No hay productos agregados
                                    </td>
                                </tr>
                            </tbody>
                            <tfoot>
                                <tr class="table-light fw-bold">
                                    <td colspan="3" class="text-end">TOTAL:</td>
                                    <td id="totalAmount">S/ 0.00</td>
                                    <td></td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>

                    <input type="hidden" name="total" id="totalInput" value="0">

                    <div class="d-flex justify-content-end gap-2 mt-4">
                        <a href="/compras/" class="btn btn-secondary">Cancelar</a>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save"></i> Actualizar Compra
                        </button>
                    </div>
                </form>
            </div>
        </div>

        <script src="/static/js/purchase-manager.js"></script>
        <script>
        // Cargar detalles existentes
        const existingDetails = {details_json};
        document.addEventListener('DOMContentLoaded', function() {{
            loadExistingDetails(existingDetails);
        }});
        </script>
        """

        return Layout.render("Editar Compra", user, "compras", content)

    @staticmethod
    def view(user, purchase, details):
        """Vista de detalle de una compra"""

        estado_class = {"pendiente": "warning", "completada": "success", "cancelada": "danger"}.get(
            purchase["estado"], "secondary"
        )

        # Detalles de productos
        details_rows = ""
        if details:
            for idx, detail in enumerate(details, 1):
                details_rows += f"""
                <tr>
                    <td>{idx}</td>
                    <td>{detail['producto_nombre']}</td>
                    <td>{detail['cantidad']}</td>
                    <td>S/ {detail['precio_unitario']:.2f}</td>
                    <td>S/ {detail['subtotal']:.2f}</td>
                </tr>
                """
        else:
            details_rows = '<tr><td colspan="5" class="text-center text-muted">Sin productos</td></tr>'

        content = f"""
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1 class="h3 mb-0">Detalle de Compra #{purchase['id']}</h1>
            <div>
                <a href="/compras/{purchase['id']}/editar/" class="btn btn-warning">
                    <i class="fas fa-edit"></i> Editar
                </a>
                <a href="/compras/" class="btn btn-secondary">
                    <i class="fas fa-arrow-left"></i> Volver
                </a>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6 mb-4">
                <div class="card shadow-sm">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0">Información de la Compra</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-2">
                            <strong>N° Factura:</strong> {purchase.get('numero_factura', 'N/A')}
                        </div>
                        <div class="mb-2">
                            <strong>Proveedor:</strong> {purchase['proveedor_nombre']}
                        </div>
                        <div class="mb-2">
                            <strong>Fecha:</strong> {purchase['fecha']}
                        </div>
                        <div class="mb-2">
                            <strong>Estado:</strong>
                            <span class="badge bg-{estado_class}">{purchase['estado']}</span>
                        </div>
                        <div class="mb-2">
                            <strong>Usuario:</strong> {purchase['usuario_nombre']}
                        </div>
                        <div class="mb-2">
                            <strong>Notas:</strong> {purchase.get('notas', 'Sin notas')}
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-md-6 mb-4">
                <div class="card shadow-sm">
                    <div class="card-header bg-success text-white">
                        <h5 class="mb-0">Totales</h5>
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                            <span class="h4 mb-0">Total:</span>
                            <span class="h3 mb-0 text-success">S/ {purchase['total']:.2f}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="card shadow-sm">
            <div class="card-header bg-light">
                <h5 class="mb-0">Productos</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-bordered">
                        <thead class="table-light">
                            <tr>
                                <th width="50">#</th>
                                <th>Producto</th>
                                <th width="100">Cantidad</th>
                                <th width="120">P. Unitario</th>
                                <th width="120">Subtotal</th>
                            </tr>
                        </thead>
                        <tbody>
                            {details_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        """

        # ===== SECCIÓN DE FACTURA ADJUNTA =====
        receipt_section = ""
        try:
            from app.models.purchase import Purchase as PurchaseModel

            purchase_obj = PurchaseModel.objects.get(id=purchase["id"])

            if purchase_obj.has_receipt():
                # Badge de OCR
                ocr_badge = ""
                if purchase_obj.auto_extracted:
                    ocr_badge = '<span class="badge bg-success ms-2" style="font-size: 14px;"><i class="fas fa-robot"></i> Extraído con OCR</span>'

                # Info de extracción OCR
                ocr_info = ""
                if purchase_obj.auto_extracted:
                    confidence_pct = purchase_obj.get_confidence_percentage()
                    confidence_class = (
                        "success" if confidence_pct >= 80 else "warning" if confidence_pct >= 50 else "danger"
                    )

                    ocr_info = f"""
                    <div class="alert alert-{confidence_class} mb-4">
                        <div class="row">
                            <div class="col-md-6">
                                <strong><i class="fas fa-robot"></i> Total Extraído Automáticamente</strong>
                                <h3 class="mt-2">S/ {purchase_obj.extracted_total:.2f}</h3>
                            </div>
                            <div class="col-md-6">
                                <strong>Confianza de Extracción:</strong>
                                <div style="background: #f0f0f0; border-radius: 4px; height: 30px; margin-top: 10px; overflow: hidden;">
                                    <div class="bg-{confidence_class}" style="height: 100%; width: {confidence_pct}%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                                        {confidence_pct:.0f}%
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """

                # Preview según tipo
                preview_content = ""
                receipt_url = f"/media/{purchase_obj.receipt_file}"

                if purchase_obj.receipt_type == "pdf":
                    preview_content = f"""
                    <div class="text-center mb-3" style="background: #f5f5f5; padding: 20px; border-radius: 8px;">
                        <iframe src="{receipt_url}" width="100%" height="600" style="border: 2px solid #ddd; border-radius: 4px;">
                            Tu navegador no soporta la visualización de PDF.
                        </iframe>
                    </div>
                    """
                else:
                    preview_content = f"""
                    <div class="text-center mb-3" style="background: #f5f5f5; padding: 20px; border-radius: 8px;">
                        <img src="{receipt_url}" class="img-fluid" style="max-height: 600px; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" alt="Factura">
                    </div>
                    """

                # Construir sección completa
                receipt_section = f"""
                <div class="card shadow-sm mt-4">
                    <div class="card-header bg-light">
                        <h5 class="mb-0">
                            <i class="fas fa-file-invoice"></i> Factura Adjunta
                            {ocr_badge}
                        </h5>
                    </div>
                    <div class="card-body">
                        {ocr_info}
                        {preview_content}
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <i class="fas fa-info-circle text-muted"></i>
                                <small class="text-muted">Archivo: {purchase_obj.receipt_file.split('/')[-1]}</small>
                            </div>
                            <div>
                                <a href="{receipt_url}" class="btn btn-primary" download>
                                    <i class="fas fa-download"></i> Descargar
                                </a>
                                <a href="{receipt_url}" class="btn btn-secondary" target="_blank">
                                    <i class="fas fa-external-link-alt"></i> Abrir
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
                """
        except Exception as e:
            receipt_section = ""

        content += receipt_section

        return Layout.render("Detalle de Compra", user, "compras", content)
