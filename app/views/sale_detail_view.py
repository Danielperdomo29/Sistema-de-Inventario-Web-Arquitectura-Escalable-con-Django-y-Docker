import html as html_module
from django.http import HttpResponse
from django.middleware.csrf import get_token

from app.views.layout import Layout


class SaleDetailView:
    @staticmethod
    def index(user, details, request, context=None):
        """Vista de lista de detalles de ventas con búsqueda, paginación y badges"""

        csrf_token = get_token(request)
        ctx = context or {}
        q = html_module.escape(ctx.get('q', ''))
        ordering = ctx.get('ordering', '-fecha')
        total_count = ctx.get('total_count', len(details))
        total_subtotal = ctx.get('total_subtotal', 0)
        page_obj = ctx.get('page_obj', None)

        # --- Helper: sort arrow ---
        def sort_link(field, label, extra_classes=''):
            current = ordering
            if current == field:
                new_order = f'-{field}'
                arrow = ' <i class="fas fa-sort-up"></i>'
            elif current == f'-{field}':
                new_order = field
                arrow = ' <i class="fas fa-sort-down"></i>'
            else:
                new_order = field
                arrow = ' <i class="fas fa-sort text-muted" style="opacity:0.4;"></i>'
            q_param = f'&q={q}' if q else ''
            return f'<th class="{extra_classes}"><a href="?order={new_order}{q_param}" style="color:inherit;text-decoration:none;">{label}{arrow}</a></th>'

        # --- Stats Banner ---
        stats_html = f"""
        <div style="display:flex; gap:20px; flex-wrap:wrap; margin-bottom:16px;">
            <div style="background:linear-gradient(135deg,#667eea,#764ba2); color:#fff; padding:14px 20px; border-radius:10px; flex:1; min-width:160px;">
                <div style="font-size:0.8em; opacity:0.9;">Total Items</div>
                <div style="font-size:1.5em; font-weight:700;">{total_count}</div>
            </div>
            <div style="background:linear-gradient(135deg,#11998e,#38ef7d); color:#fff; padding:14px 20px; border-radius:10px; flex:1; min-width:160px;">
                <div style="font-size:0.8em; opacity:0.9;">Suma Subtotales</div>
                <div style="font-size:1.5em; font-weight:700;">$ {total_subtotal:,.2f}</div>
            </div>
        </div>
        """

        # --- Search Bar + Export ---
        export_q = f'?q={q}' if q else ''
        search_html = f"""
        <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-bottom:16px;">
            <form method="GET" action="/items-venta/" style="display:flex; flex:1; min-width:200px; gap:8px;">
                <div style="position:relative; flex:1;">
                    <i class="fas fa-search" style="position:absolute; left:12px; top:50%; transform:translateY(-50%); color:#888;"></i>
                    <input type="text" name="q" value="{q}"
                           placeholder="Buscar por producto, cliente o factura..."
                           style="width:100%; padding:10px 12px 10px 38px; border:1px solid #ddd; border-radius:8px; font-size:0.95em; background:#f8f9fa; transition:border .2s;"
                           onfocus="this.style.borderColor='#667eea'; this.style.background='#fff';"
                           onblur="this.style.borderColor='#ddd'; this.style.background='#f8f9fa';">
                </div>
                <button type="submit" class="btn btn-primary" style="white-space:nowrap;">
                    <i class="fas fa-search"></i> Buscar
                </button>
                {'<a href="/items-venta/" class="btn btn-secondary" style="white-space:nowrap;"><i class="fas fa-times"></i> Limpiar</a>' if q else ''}
            </form>
            <a href="/items-venta/exportar/{export_q}" class="btn btn-success" style="white-space:nowrap;">
                <i class="fas fa-file-csv"></i> Exportar CSV
            </a>
        </div>
        """

        # --- Estado badge helper ---
        def get_estado_badge(estado):
            estado_low = (estado or 'completada').lower()
            badges = {
                'completada': '<span style="background:#d4edda;color:#155724;padding:3px 10px;border-radius:12px;font-size:0.8em;font-weight:600;"><i class="fas fa-check-circle"></i> Completada</span>',
                'pendiente': '<span style="background:#fff3cd;color:#856404;padding:3px 10px;border-radius:12px;font-size:0.8em;font-weight:600;"><i class="fas fa-clock"></i> Pendiente</span>',
                'cancelada': '<span style="background:#f8d7da;color:#721c24;padding:3px 10px;border-radius:12px;font-size:0.8em;font-weight:600;"><i class="fas fa-ban"></i> Cancelada</span>',
                'anulada': '<span style="background:#f8d7da;color:#721c24;padding:3px 10px;border-radius:12px;font-size:0.8em;font-weight:600;"><i class="fas fa-times-circle"></i> Anulada</span>',
            }
            return badges.get(estado_low, f'<span style="background:#e2e3e5;color:#383d41;padding:3px 10px;border-radius:12px;font-size:0.8em;">{estado}</span>')

        # --- Table Rows ---
        rows = ""
        if details:
            start_idx = 1
            if page_obj:
                start_idx = (page_obj.number - 1) * 20 + 1

            for idx, detail in enumerate(details, start_idx):
                estado_badge = get_estado_badge(detail.get('venta_estado', 'completada'))
                fecha = detail.get('fecha_venta', '')
                if hasattr(fecha, 'strftime'):
                    fecha = fecha.strftime('%d/%m/%Y')

                rows += f"""
                <tr>
                    <td class="d-none d-md-table-cell" style="color:#888;font-size:0.85em;">{idx}</td>
                    <td class="d-none d-md-table-cell"><strong>{detail.get('numero_factura', 'N/A')}</strong></td>
                    <td class="d-none d-md-table-cell">{detail['cliente_nombre']}</td>
                    <td class="d-none d-md-table-cell" style="font-size:0.9em;">{fecha}</td>
                    <td><strong>{detail['producto_nombre']}</strong></td>
                    <td style="text-align:center;">{detail['cantidad']}</td>
                    <td>$ {detail['precio_unitario']:,.2f}</td>
                    <td><strong>$ {detail['subtotal']:,.2f}</strong></td>
                    <td class="d-none d-md-table-cell">{estado_badge}</td>
                    <td>
                        <div style="display:flex; gap:4px; flex-wrap:nowrap;">
                            <a href="/items-venta/{detail['id']}/ver/" class="btn btn-info btn-sm" title="Ver factura">
                                <i class="fas fa-eye"></i>
                            </a>
                            <a href="/items-venta/{detail['id']}/editar/" class="btn btn-warning btn-sm" title="Editar">
                                <i class="fas fa-edit"></i>
                            </a>
                            <button type="button" class="btn btn-danger btn-sm" title="Eliminar"
                                    onclick="confirmDeleteAction('/items-venta/{detail['id']}/eliminar/', '{csrf_token}', 'Detalle #{detail['id']}');">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
                """

            table_content = f"""
            <div class="table-container">
                <table>
                <thead>
                    <tr>
                        <th class="d-none d-md-table-cell" style="width:40px;">#</th>
                        {sort_link('factura', 'N° Factura', 'd-none d-md-table-cell')}
                        {sort_link('cliente', 'Cliente', 'd-none d-md-table-cell')}
                        {sort_link('fecha', 'Fecha', 'd-none d-md-table-cell')}
                        {sort_link('producto', 'Producto')}
                        <th>Cant.</th>
                        <th>Precio Unit.</th>
                        {sort_link('subtotal', 'Subtotal')}
                        <th class="d-none d-md-table-cell">Estado</th>
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
            empty_msg = 'No se encontraron resultados para tu búsqueda.' if q else 'No hay detalles de ventas registrados.'
            empty_sub = f'<p>Intenta con otro término o <a href="/items-venta/">ver todos</a></p>' if q else '<p>Comienza agregando el primer detalle</p>'
            table_content = f"""
            <div class="empty-state">
                <i class="fas fa-{'search' if q else 'file-invoice'} icon-4xl"></i>
                <h3>{empty_msg}</h3>
                {empty_sub}
            </div>
            """

        # --- Pagination ---
        pagination_html = ""
        if page_obj and page_obj.paginator.num_pages > 1:
            q_param = f'&q={q}' if q else ''
            order_param = f'&order={ordering}' if ordering != '-fecha' else ''
            pages = []

            # Previous
            if page_obj.has_previous():
                pages.append(f'<a href="?page={page_obj.previous_page_number()}{q_param}{order_param}" style="padding:6px 12px;border:1px solid #ddd;border-radius:6px;text-decoration:none;color:#667eea;">← Anterior</a>')

            # Page numbers
            total_pages = page_obj.paginator.num_pages
            current = page_obj.number
            for p in range(1, total_pages + 1):
                if p == current:
                    pages.append(f'<span style="padding:6px 12px;background:#667eea;color:#fff;border-radius:6px;font-weight:600;">{p}</span>')
                elif abs(p - current) <= 2 or p == 1 or p == total_pages:
                    pages.append(f'<a href="?page={p}{q_param}{order_param}" style="padding:6px 12px;border:1px solid #ddd;border-radius:6px;text-decoration:none;color:#333;">{p}</a>')
                elif abs(p - current) == 3:
                    pages.append('<span style="padding:6px 4px;color:#888;">...</span>')

            # Next
            if page_obj.has_next():
                pages.append(f'<a href="?page={page_obj.next_page_number()}{q_param}{order_param}" style="padding:6px 12px;border:1px solid #ddd;border-radius:6px;text-decoration:none;color:#667eea;">Siguiente →</a>')

            pagination_html = f"""
            <div style="display:flex; justify-content:center; align-items:center; gap:6px; padding:16px 0; flex-wrap:wrap;">
                {''.join(pages)}
            </div>
            <div style="text-align:center; color:#888; font-size:0.85em; margin-bottom:10px;">
                Página {page_obj.number} de {page_obj.paginator.num_pages}
            </div>
            """

        # --- Filtered indicator ---
        filter_indicator = ''
        if q:
            filter_indicator = f"""
            <div style="background:#e8f0fe; border-left:4px solid #667eea; padding:10px 16px; border-radius:6px; margin-bottom:12px; display:flex; align-items:center; gap:8px;">
                <i class="fas fa-filter" style="color:#667eea;"></i>
                <span>Mostrando resultados para: <strong>"{q}"</strong> ({total_count} resultados)</span>
            </div>
            """

        content = f"""
        <div class="card">
            <div class="card-header">
                <span><i class="fas fa-file-invoice"></i> Gestión de Detalles de Ventas</span>
                <a href="/items-venta/crear/" class="btn btn-primary"><i class="fas fa-plus"></i> Nuevo Detalle</a>
            </div>
            <div class="p-20">
                {stats_html}
                {search_html}
                {filter_indicator}
                {table_content}
                {pagination_html}
            </div>
        </div>
        """

        return Layout.render("Detalles de Ventas", user, "items-venta", content)

    @staticmethod
    def create(user, sales, products, request, error=None):
        """Vista de formulario para crear detalle de venta"""

        csrf_token = get_token(request)

        # SweetAlert2 for server-side errors
        error_script = ""
        if error:
            error_script = f"""
            <script>
            document.addEventListener('DOMContentLoaded', function() {{
                Swal.fire({{
                    icon: 'error',
                    title: 'Error de Validación',
                    text: '{error}',
                    confirmButtonColor: '#3085d6'
                }});
            }});
            </script>
            """

        # Select de ventas
        sale_options = '<option value="">Seleccione una venta</option>'
        for sale in sales:
            sale_options += f'<option value="{sale["id"]}">{sale.get("numero_factura", "Sin factura")} - {sale["cliente_nombre"]} ({sale["fecha"]})</option>'

        # Select de productos
        product_options = '<option value="">Seleccione un producto</option>'
        for product in products:
            product_options += f'<option value="{product["id"]}" data-price="{product["precio_venta"]}">{product["nombre"]} - $ {product["precio_venta"]:.2f}</option>'

        content = f"""
        <div class="card">
            <div class="card-header">
                <span><i class="fas fa-file-invoice"></i> Crear Nuevo Detalle de Venta</span>
                <a href="/items-venta/" class="btn btn-secondary">← Volver</a>
            </div>
            <form method="POST" action="/items-venta/crear/" class="p-20" id="detailForm" data-validate>
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Venta *</label>
                        <select name="venta_id" class="form-select"
                                data-rules="required"
                                data-label="Venta">
                            {sale_options}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Producto *</label>
                        <select name="producto_id" id="producto" class="form-select"
                                data-rules="required"
                                data-label="Producto">
                            {product_options}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Cantidad *</label>
                        <input type="number" name="cantidad" id="cantidad" value="1" min="1" class="form-input"
                               data-rules="required|numeric|min:1"
                               data-label="Cantidad">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Precio Unitario *</label>
                        <input type="number" name="precio_unitario" id="precio_unitario" step="0.01" min="0" class="form-input"
                               data-rules="required|min:0"
                               data-label="Precio Unitario">
                    </div>
                </div>
                
                <div class="total-summary">
                    <p>
                        Subtotal: $ <span id="subtotal">0.00</span>
                    </p>
                </div>
                
                <div class="form-actions-end mt-30">
                    <a href="/items-venta/" class="btn btn-secondary"><i class="fas fa-times"></i> Cancelar</a>
                    <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Guardar Detalle</button>
                </div>
            </form>
        </div>
        
        <script src="/static/js/detail-calculator.js"></script>
        {error_script}
        """

        return Layout.render("Nuevo Detalle de Venta", user, "items-venta", content)

    @staticmethod
    def edit(user, detail, products, request, error=None):
        """Vista de formulario para editar detalle de venta"""

        csrf_token = get_token(request)

        # SweetAlert2 for server-side errors
        error_script = ""
        if error:
            error_script = f"""
            <script>
            document.addEventListener('DOMContentLoaded', function() {{
                Swal.fire({{
                    icon: 'error',
                    title: 'Error de Validación',
                    text: '{error}',
                    confirmButtonColor: '#3085d6'
                }});
            }});
            </script>
            """

        # Select de productos
        product_options = ""
        for product in products:
            selected = "selected" if product["id"] == detail["producto_id"] else ""
            product_options += f'<option value="{product["id"]}" data-price="{product["precio_venta"]}" {selected}>{product["nombre"]} - $ {product["precio_venta"]:.2f}</option>'

        content = f"""
        <div class="card">
            <div class="card-header">
                <span><i class="fas fa-edit"></i> Editar Detalle de Venta</span>
                <a href="/items-venta/" class="btn btn-secondary">← Volver</a>
            </div>
            <form method="POST" action="/items-venta/{detail['id']}/editar/" class="p-20" id="detailForm" data-validate>
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Venta</label>
                        <input type="text" value="{detail.get('numero_factura', 'Sin factura')}" disabled
                               class="form-input-disabled">
                        <small class="form-hint">La venta no se puede cambiar</small>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Producto *</label>
                        <select name="producto_id" id="producto" class="form-select"
                                data-rules="required"
                                data-label="Producto">
                            {product_options}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Cantidad *</label>
                        <input type="number" name="cantidad" id="cantidad" value="{detail['cantidad']}" min="1" class="form-input"
                               data-rules="required|numeric|min:1"
                               data-label="Cantidad">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Precio Unitario *</label>
                        <input type="number" name="precio_unitario" id="precio_unitario" value="{detail['precio_unitario']}" step="0.01" min="0" class="form-input"
                               data-rules="required|min:0"
                               data-label="Precio Unitario">
                    </div>
                </div>
                
                <div class="total-summary">
                    <p>
                        Subtotal: $ <span id="subtotal">{detail['subtotal']:.2f}</span>
                    </p>
                </div>
                
                <div class="form-actions-end mt-30">
                    <a href="/items-venta/" class="btn btn-secondary"><i class="fas fa-times"></i> Cancelar</a>
                    <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Actualizar Detalle</button>
                </div>
            </form>
        </div>
        
        <script src="/static/js/detail-calculator.js"></script>
        {error_script}
        """

        return Layout.render("Editar Detalle de Venta", user, "items-venta", content)

    @staticmethod
    def view(user, detail):
        """Vista de detalle con vista previa de factura"""

        estado_map = {
            "pendiente": ('<i class="fas fa-clock"></i> Pendiente', '#fff3cd', '#856404'),
            "completada": ('<i class="fas fa-check-circle"></i> Completada', '#d4edda', '#155724'),
            "cancelada": ('<i class="fas fa-ban"></i> Cancelada', '#f8d7da', '#721c24'),
            "anulada": ('<i class="fas fa-times-circle"></i> Anulada', '#f8d7da', '#721c24'),
        }
        estado_key = (detail.get("venta_estado", "completada") or "completada").lower()
        badge_text, badge_bg, badge_color = estado_map.get(
            estado_key, (estado_key.capitalize(), '#e2e3e5', '#383d41')
        )
        estado_badge = f'<span style="background:{badge_bg};color:{badge_color};padding:4px 12px;border-radius:12px;font-weight:600;font-size:0.85em;">{badge_text}</span>'

        fecha = detail.get('fecha_venta', '')
        if hasattr(fecha, 'strftime'):
            fecha_display = fecha.strftime('%d/%m/%Y %H:%M')
            fecha_short = fecha.strftime('%d/%m/%Y')
        else:
            fecha_display = str(fecha)
            fecha_short = str(fecha)

        # --- Invoice Items Table ---
        invoice_items = detail.get('venta_items', [])
        invoice_rows = ""
        for i, item in enumerate(invoice_items, 1):
            highlight = ' style="background:#f0f7ff;"' if item['producto_nombre'] == detail['producto_nombre'] else ''
            invoice_rows += f"""
            <tr{highlight}>
                <td style="padding:8px 12px; border-bottom:1px solid #eee;">{i}</td>
                <td style="padding:8px 12px; border-bottom:1px solid #eee;">{item['producto_nombre']}</td>
                <td style="padding:8px 12px; border-bottom:1px solid #eee; text-align:center;">{item['cantidad']}</td>
                <td style="padding:8px 12px; border-bottom:1px solid #eee; text-align:right;">$ {item['precio_unitario']:,.2f}</td>
                <td style="padding:8px 12px; border-bottom:1px solid #eee; text-align:right; font-weight:600;">$ {item['subtotal']:,.2f}</td>
            </tr>
            """

        venta_subtotal = detail.get('venta_subtotal', 0)
        venta_iva = detail.get('venta_iva', 0)
        venta_total = detail.get('venta_total', 0)

        content = f"""
        <div class="card">
            <div class="card-header">
                <span><i class="fas fa-file-invoice"></i> Detalle de Venta #{detail['id']}</span>
                <a href="/items-venta/" class="btn btn-secondary">← Volver</a>
            </div>
            
            <div class="p-20">
                <!-- Sale Info Cards -->
                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:16px; margin-bottom:24px;">
                    <div style="background:#f8f9fa; border-radius:10px; padding:16px; border-left:4px solid #667eea;">
                        <div style="font-size:0.8em; color:#888; margin-bottom:4px;">N° Factura</div>
                        <div style="font-size:1.1em; font-weight:700; color:#333;">{detail.get('numero_factura', 'Sin factura')}</div>
                    </div>
                    <div style="background:#f8f9fa; border-radius:10px; padding:16px; border-left:4px solid #11998e;">
                        <div style="font-size:0.8em; color:#888; margin-bottom:4px;">Cliente</div>
                        <div style="font-size:1.1em; font-weight:700; color:#333;">{detail['cliente_nombre']}</div>
                        <div style="font-size:0.8em; color:#888;">{detail.get('cliente_documento', '')}</div>
                    </div>
                    <div style="background:#f8f9fa; border-radius:10px; padding:16px; border-left:4px solid #f093fb;">
                        <div style="font-size:0.8em; color:#888; margin-bottom:4px;">Fecha</div>
                        <div style="font-size:1.1em; font-weight:700; color:#333;">{fecha_display}</div>
                    </div>
                    <div style="background:#f8f9fa; border-radius:10px; padding:16px; border-left:4px solid #fd7e14;">
                        <div style="font-size:0.8em; color:#888; margin-bottom:4px;">Estado</div>
                        <div style="margin-top:4px;">{estado_badge}</div>
                    </div>
                </div>

                <!-- Invoice Preview Card -->
                <div style="border:2px solid #e0e0e0; border-radius:12px; overflow:hidden; margin-bottom:24px;" id="invoice_preview">
                    <!-- Invoice Header -->
                    <div style="background:linear-gradient(135deg,#1a1a2e,#16213e); color:#fff; padding:24px 30px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                            <div>
                                <h2 style="margin:0; font-size:1.4em;">FACTURA DE VENTA</h2>
                                <div style="opacity:0.7; margin-top:4px;">{detail.get('numero_factura', 'Sin numero')}</div>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-size:0.85em; opacity:0.8;">Fecha de emisión</div>
                                <div style="font-size:1.1em; font-weight:600;">{fecha_short}</div>
                            </div>
                        </div>
                    </div>

                    <!-- Client Info -->
                    <div style="padding:20px 30px; background:#f8f9fa; border-bottom:1px solid #e0e0e0;">
                        <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:16px;">
                            <div>
                                <div style="font-size:0.8em; color:#888; text-transform:uppercase; letter-spacing:1px;">Cliente</div>
                                <div style="font-size:1.1em; font-weight:600; color:#333;">{detail['cliente_nombre']}</div>
                                <div style="font-size:0.9em; color:#666;">{detail.get('cliente_documento', 'Sin documento')}</div>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-size:0.8em; color:#888; text-transform:uppercase; letter-spacing:1px;">Pago</div>
                                <div style="font-size:1em; font-weight:600; color:#333;">{detail.get('tipo_pago', 'N/A').capitalize()}</div>
                            </div>
                        </div>
                    </div>

                    <!-- Items Table -->
                    <div style="padding:0;">
                        <table style="width:100%; border-collapse:collapse;">
                            <thead>
                                <tr style="background:#eef1f6;">
                                    <th style="padding:10px 12px; text-align:left; font-size:0.85em; color:#555; font-weight:600;">#</th>
                                    <th style="padding:10px 12px; text-align:left; font-size:0.85em; color:#555; font-weight:600;">Producto</th>
                                    <th style="padding:10px 12px; text-align:center; font-size:0.85em; color:#555; font-weight:600;">Cant.</th>
                                    <th style="padding:10px 12px; text-align:right; font-size:0.85em; color:#555; font-weight:600;">Precio Unit.</th>
                                    <th style="padding:10px 12px; text-align:right; font-size:0.85em; color:#555; font-weight:600;">Subtotal</th>
                                </tr>
                            </thead>
                            <tbody>
                                {invoice_rows}
                            </tbody>
                        </table>
                    </div>

                    <!-- Totals -->
                    <div style="padding:20px 30px; background:#f8f9fa; border-top:2px solid #e0e0e0;">
                        <div style="display:flex; justify-content:flex-end;">
                            <div style="min-width:250px;">
                                <div style="display:flex; justify-content:space-between; padding:6px 0; color:#666;">
                                    <span>Subtotal sin IVA:</span>
                                    <span>$ {venta_subtotal:,.2f}</span>
                                </div>
                                <div style="display:flex; justify-content:space-between; padding:6px 0; color:#666;">
                                    <span>IVA:</span>
                                    <span>$ {venta_iva:,.2f}</span>
                                </div>
                                <div style="display:flex; justify-content:space-between; padding:10px 0; border-top:2px solid #333; font-size:1.2em; font-weight:700; color:#155724;">
                                    <span>TOTAL:</span>
                                    <span>$ {venta_total:,.2f}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Notes -->
                    {'<div style="padding:16px 30px; border-top:1px solid #e0e0e0; color:#666; font-size:0.9em;"><strong>Notas:</strong> ' + detail.get("venta_notas", "") + '</div>' if detail.get("venta_notas") else ''}
                </div>

                <!-- Actions -->
                <div style="display:flex; gap:10px; flex-wrap:wrap;">
                    <button onclick="window.print();" class="btn btn-primary">
                        <i class="fas fa-print"></i> Imprimir Factura
                    </button>
                    <a href="/items-venta/{detail['id']}/editar/" class="btn btn-warning">
                        <i class="fas fa-edit"></i> Editar Detalle
                    </a>
                    <a href="/items-venta/" class="btn btn-secondary">
                        <i class="fas fa-arrow-left"></i> Volver al Listado
                    </a>
                </div>
            </div>
        </div>

        <style>
            @media print {{
                .sidebar, .navbar, .card-header .btn, .btn {{ display: none !important; }}
                #invoice_preview {{ border: none !important; }}
            }}
        </style>
        """

        return Layout.render("Ver Detalle de Venta", user, "items-venta", content)
