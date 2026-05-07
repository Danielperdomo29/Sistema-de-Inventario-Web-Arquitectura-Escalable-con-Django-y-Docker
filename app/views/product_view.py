from django.http import HttpResponse
from django.middleware.csrf import get_token

from app.views.layout import Layout


class ProductView:
    """Vista de Productos"""

    @staticmethod
    def index(user, request, products, categories):
        """Vista de lista de productos"""
        csrf_token = get_token(request)

        # Filtros Estilo iOS (FASE 4)
        q = request.GET.get("q", "")
        cat_selected = request.GET.get("categoria", "")

        cat_options = '<option value="">Todas las Categorías</option>'
        for cat in categories:
            selected = "selected" if str(cat["id"]) == cat_selected else ""
            cat_options += f'<option value="{cat["id"]}" {selected}>{cat["nombre"]}</option>'

        filter_bar = f"""
        <style>
            .sales-filter-bar {{
                display: flex;
                flex-wrap: nowrap;
                align-items: center;
                gap: 12px;
                padding: 12px 20px;
                background: rgba(255, 255, 255, 0.8);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border-radius: 40px;
                border: 1px solid rgba(255, 255, 255, 0.3);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
                margin-bottom: 24px;
                overflow-x: auto;
                scrollbar-width: none;
            }}
            .sales-filter-bar::-webkit-scrollbar {{ display: none; }}
            .filter-item {{
                display: flex;
                align-items: center;
                background: rgba(242, 242, 247, 0.8);
                border-radius: 20px;
                padding: 0 15px;
                height: 40px;
                min-width: 180px;
            }}
            .filter-input {{
                border: none;
                background: transparent;
                font-size: 14px;
                width: 100%;
                outline: none;
                color: #1c1c1e;
            }}
            .filter-btn-primary {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                background: #007AFF;
                color: white;
                border-radius: 40px;
                padding: 0 24px;
                height: 44px;
                border: none;
                font-weight: 500;
                font-size: 16px;
                transition: all 0.2s ease;
                white-space: nowrap;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0, 122, 255, 0.2);
            }}
            .filter-btn-primary:hover {{
                background: #005BBF;
                transform: translateY(-1px);
                box-shadow: 0 6px 16px rgba(0, 122, 255, 0.3);
            }}
            .filter-btn-primary:active {{ transform: translateY(0); }}

            .filter-btn-clear {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                height: 44px;
                padding: 0 24px;
                border-radius: 40px;
                font-size: 16px;
                font-weight: 500;
                border: 1px solid #E5E5EA;
                background: #FFFFFF;
                color: #8E8E93;
                cursor: pointer;
                transition: all 0.2s ease;
                white-space: nowrap;
                text-decoration: none;
            }}
            .filter-btn-clear:hover {{
                background: #F2F2F7;
                color: #1C1C1E;
                border-color: #D1D1D6;
            }}
        </style>
        <form id="product-filter-form" method="GET" action="/productos/" class="sales-filter-bar">
            <div class="filter-item">
                <i class="fas fa-search mr-2 text-muted"></i>
                <input type="text" id="filter-q" name="q" placeholder="Nombre o código..." class="filter-input" value="{q}">
            </div>
            <div class="filter-item">
                <i class="fas fa-layer-group mr-2 text-muted"></i>
                <select id="filter-cat" name="categoria" class="filter-input">
                    {cat_options}
                </select>
            </div>
            <button type="submit" class="filter-btn-primary">
                <i class="fas fa-search"></i>
                <span>Filtrar</span>
            </button>
            <a href="/productos/" class="filter-btn-clear">
                <i class="fas fa-times"></i>
                <span>Limpiar</span>
            </a>
        </form>

        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const filterForm = document.getElementById('product-filter-form');

            filterForm.addEventListener('submit', function(e) {{
                const q = document.getElementById('filter-q').value.trim();
                const cat = document.getElementById('filter-cat').value;

                if (!q && !cat) {{
                    e.preventDefault();
                    if (typeof Swal !== 'undefined') {{
                        Swal.fire({{
                            icon: 'info',
                            title: 'Búsqueda Vacía',
                            text: 'Por favor, ingresa un nombre, código o selecciona una categoría para filtrar.',
                            confirmButtonColor: '#007AFF',
                            confirmButtonText: 'Entendido',
                            customClass: {{
                                popup: 'rounded-2xl shadow-xl border-0'
                            }}
                        }});
                    }} else {{
                        alert('Por favor ingresa un criterio para filtrar.');
                    }}
                }}
            }});
        }});
        </script>
        """

        # Generar filas de la tabla
        if products:
            rows = ""
            for product in products:
                rows += f"""
                <tr>
                    <td>{product['id']}</td>
                    <td>{product['nombre']}</td>
                    <td>{product.get('categoria', 'Sin categoría')}</td>
                    <td>${product['precio_venta']:,.2f}</td>
                    <td>
                        <span class="badge { 'bg-success' if product['iva_tipo'] == 'GRAVADO' else 'bg-secondary' }">
                            {product['iva_porcentaje']}%
                        </span>
                    </td>
                    <td>{product.get('descuento', 0)}%</td>
                    <td>{product['stock_actual']}</td>
                    <td>
                        <a href="/productos/{product['id']}/editar/" class="btn btn-warning btn-sm no-underline">
                            <i class="fas fa-edit"></i> Editar
                        </a>
                        <button type="button" class="btn btn-danger btn-sm no-underline"
                                onclick="confirmDeleteAction('/productos/{product['id']}/eliminar/',
                                                           '{csrf_token}',
                                                           '{product['nombre']}');">
                            <i class="fas fa-trash"></i> Eliminar
                        </button>
                    </td>
                </tr>
                """

            table_content = f"""
            <div class="table-container">
                <table class="table-products">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Nombre</th>
                            <th>Categoría</th>
                            <th>Precio</th>
                            <th>IVA</th>
                            <th>Desc</th>
                            <th>Stock</th>
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
                <div class="icon-4xl"><i class="fas fa-box"></i></div>
                <h3>No hay productos registrados</h3>
                <p>Comienza agregando tu primer producto</p>
            </div>
            """

        content = f"""
        <div class="mb-4">
            <h1 class="h3 mb-0 text-gray-800">Inventario de Productos</h1>
        </div>

        {filter_bar}

        <div class="card shadow-sm border-0" style="border-radius: 16px; overflow: hidden;">
            <div class="card-header bg-white border-bottom-0 py-3 d-flex justify-content-between align-items-center">
                <h6 class="m-0 font-weight-bold text-primary">Catálogo Maestro</h6>
                <a href="/productos/crear/" class="btn btn-primary btn-sm rounded-pill no-underline">
                    <i class="fas fa-plus mr-1"></i> Nuevo Producto
                </a>
            </div>
            <div class="card-body p-0">
                {table_content}
            </div>
        </div>
        """

        return HttpResponse(Layout.render("Productos", user, "productos", content))

    @staticmethod
    def create(user, categories, request, error=None):
        """Vista del formulario de crear producto"""

        csrf_token = get_token(request)

        # Generar opciones de categorías
        category_options = ""
        for category in categories:
            category_options += f'<option value="{category["id"]}">{category["nombre"]}</option>'

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

        content = f"""
        <div class="card">
            <div class="card-header">
                <span><i class="fas fa-box"></i> Crear Nuevo Producto</span>
                <a href="/productos/" class="btn btn-secondary">← Volver</a>
            </div>
            <form method="POST" action="/productos/crear/" class="p-20" data-validate>
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Código *</label>
                        <input type="text" name="codigo" class="form-input"
                               data-rules="required|minLength:2"
                               data-label="Código"
                               placeholder="Ej: PROD001">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Nombre *</label>
                        <input type="text" name="nombre" class="form-input"
                               data-rules="required|minLength:2"
                               data-label="Nombre"
                               placeholder="Nombre del producto">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Categoría *</label>
                        <select name="categoria_id" class="form-select"
                                data-rules="required"
                                data-label="Categoría">
                            <option value="">Seleccione una categoría</option>
                            {category_options}
                        </select>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Precio Compra *</label>
                        <input type="number" name="precio_compra" step="0.01" class="form-input"
                               data-rules="required|min:0"
                               data-label="Precio Compra"
                               placeholder="0.00">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Precio Venta *</label>
                        <input type="number" name="precio_venta" step="0.01" class="form-input"
                               data-rules="required|min:0"
                               data-label="Precio Venta"
                               placeholder="0.00">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Descuento Base (%)</label>
                        <input type="number" name="descuento" step="0.01" value="0.00" class="form-input"
                               data-label="Descuento">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Stock Actual</label>
                        <input type="number" name="stock_actual" value="0" class="form-input"
                               data-rules="numeric|min:0"
                               data-label="Stock Actual">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Stock Mínimo</label>
                        <input type="number" name="stock_minimo" value="10" class="form-input"
                               data-rules="numeric|min:0"
                               data-label="Stock Mínimo">
                    </div>
                </div>

                <div class="mt-20">
                    <label class="form-label">Descripción</label>
                    <textarea name="descripcion" rows="4" class="form-textarea"
                              placeholder="Descripción del producto"></textarea>
                </div>

                <div class="card shadow-sm border-left-primary mt-4">
                    <div class="card-header bg-white py-3">
                        <h6 class="m-0 font-weight-bold text-primary">
                            <i class="fas fa-file-invoice-dollar mr-2"></i> Configuración Tributaria (DIAN)
                        </h6>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6 form-group">
                                <label class="form-label font-weight-bold">Código DIAN (UNSPSC) *</label>
                                <input type="text" name="codigo_dian" class="form-input"
                                       placeholder="Ej: 43211503" data-rules="required|min:8" maxlength="20">
                                <small class="text-muted">Código de 8 dígitos obligatorio para factura electrónica.</small>
                            </div>
                            <div class="col-md-6 form-group">
                                <label class="form-label font-weight-bold">Unidad de Medida</label>
                                <select name="unidad_medida" class="form-select">
                                    <option value="94" selected>94 - Unidad</option>
                                    <option value="E48">E48 - Unidad de servicio</option>
                                    <option value="KGM">KGM - Kilogramo</option>
                                    <option value="MTR">MTR - Metro</option>
                                </select>
                            </div>
                        </div>
                        <div class="row mt-3">
                            <div class="col-md-4 form-group">
                                <label class="form-label font-weight-bold">Tipo de IVA</label>
                                <select name="iva_tipo" id="iva_tipo_select" class="form-select" onchange="toggleIvaFields()">
                                    <option value="GRAVADO" selected>Gravado</option>
                                    <option value="EXENTO">Exento</option>
                                    <option value="EXCLUIDO">Excluido</option>
                                </select>
                            </div>
                            <div class="col-md-4 form-group">
                                <label class="form-label font-weight-bold">Tarifa IVA (%)</label>
                                <select name="iva_porcentaje" id="iva_porcentaje_input" class="form-select">
                                    <option value="19.00" selected>19% (General)</option>
                                    <option value="5.00">5% (Reducida)</option>
                                    <option value="0.00">0% (Exento/Excluido)</option>
                                </select>
                            </div>
                            <div class="col-md-4 form-group">
                                <label class="form-label font-weight-bold">Impoconsumo (%)</label>
                                <input type="number" name="impoconsumo" class="form-input" step="0.01" value="0.00">
                            </div>
                        </div>
                    </div>
                </div>

                <script>
                function toggleIvaFields() {{
                    const type = document.getElementById('iva_tipo_select').value;
                    const percentage = document.getElementById('iva_porcentaje_input');
                    if (type === 'EXENTO' || type === 'EXCLUIDO') {{
                        percentage.value = "0.00";
                        percentage.disabled = true;
                    }} else {{
                        percentage.disabled = false;
                        if (percentage.value === "0.00") percentage.value = "19.00";
                    }}
                }}
                </script>

                <div class="form-actions mt-30">
                    <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Guardar Producto</button>
                    <a href="/productos/" class="btn btn-secondary no-underline"><i class="fas fa-times"></i> Cancelar</a>
                </div>
            </form>
        </div>
        {error_script}
        """

        return HttpResponse(Layout.render("Crear Producto", user, "productos", content))

    @staticmethod
    def edit(user, product, categories, request, error=None):
        """Vista del formulario de editar producto"""

        csrf_token = get_token(request)

        # Generar opciones de categorías
        category_options = ""
        for category in categories:
            selected = "selected" if category["id"] == product.get("categoria_id") else ""
            category_options += f'<option value="{category["id"]}" {selected}>{category["nombre"]}</option>'

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

        content = f"""
        <div class="card">
            <div class="card-header">
                <span><i class="fas fa-box"></i> Editar Producto</span>
                <a href="/productos/" class="btn btn-secondary">← Volver</a>
            </div>
            <form method="POST" action="/productos/{product['id']}/editar/" class="p-20" data-validate>
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Código *</label>
                        <input type="text" name="codigo" value="{product['codigo']}" class="form-input"
                               data-rules="required|minLength:2"
                               data-label="Código">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Nombre *</label>
                        <input type="text" name="nombre" value="{product['nombre']}" class="form-input"
                               data-rules="required|minLength:2"
                               data-label="Nombre">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Categoría *</label>
                        <select name="categoria_id" class="form-select"
                                data-rules="required"
                                data-label="Categoría">
                            <option value="">Seleccione una categoría</option>
                            {category_options}
                        </select>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Precio Compra *</label>
                        <input type="number" name="precio_compra" value="{product['precio_compra']}"
                               step="0.01" class="form-input"
                               data-rules="required|min:0"
                               data-label="Precio Compra">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Precio Venta *</label>
                        <input type="number" name="precio_venta" value="{product['precio_venta']}"
                               step="0.01" class="form-input"
                               data-rules="required|min:0"
                               data-label="Precio Venta">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Descuento Base (%)</label>
                        <input type="number" name="descuento" value="{product.get('descuento', 0.00)}"
                               step="0.01" class="form-input"
                               data-label="Descuento">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Stock Actual</label>
                        <input type="number" name="stock_actual" value="{product['stock_actual']}"
                               class="form-input"
                               data-rules="numeric|min:0"
                               data-label="Stock Actual">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Stock Mínimo</label>
                        <input type="number" name="stock_minimo" value="{product.get('stock_minimo', 10)}"
                               class="form-input"
                               data-rules="numeric|min:0"
                               data-label="Stock Mínimo">
                    </div>
                </div>

                <div class="mt-20">
                    <label class="form-label">Descripción</label>
                    <textarea name="descripcion" rows="4" class="form-textarea">{product.get('descripcion', '') or ''}</textarea>
                </div>

                <div class="card shadow-sm border-left-primary mt-4">
                    <div class="card-header bg-white py-3">
                        <h6 class="m-0 font-weight-bold text-primary">
                            <i class="fas fa-file-invoice-dollar mr-2"></i> Configuración Tributaria (DIAN)
                        </h6>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6 form-group">
                                <label class="form-label font-weight-bold">Código DIAN (UNSPSC) *</label>
                                <input type="text" name="codigo_dian" class="form-input"
                                       placeholder="Ej: 43211503" value="{product.get('codigo_dian', '')}"
                                       data-rules="required|min:8" maxlength="20">
                                <small class="text-muted">Código de 8 dígitos obligatorio para factura electrónica.</small>
                            </div>
                            <div class="col-md-6 form-group">
                                <label class="form-label font-weight-bold">Unidad de Medida</label>
                                <select name="unidad_medida" class="form-select">
                                    <option value="94" { 'selected' if product.get('unidad_medida') == '94' else '' }>94 - Unidad</option>
                                    <option value="E48" { 'selected' if product.get('unidad_medida') == 'E48' else '' }>E48 - Unidad de servicio</option>
                                    <option value="KGM" { 'selected' if product.get('unidad_medida') == 'KGM' else '' }>KGM - Kilogramo</option>
                                    <option value="MTR" { 'selected' if product.get('unidad_medida') == 'MTR' else '' }>MTR - Metro</option>
                                </select>
                            </div>
                        </div>
                        <div class="row mt-3">
                            <div class="col-md-4 form-group">
                                <label class="form-label font-weight-bold">Tipo de IVA</label>
                                <select name="iva_tipo" id="iva_tipo_select_edit" class="form-select" onchange="toggleIvaFieldsEdit()">
                                    <option value="GRAVADO" { 'selected' if product.get('iva_tipo') == 'GRAVADO' else '' }>Gravado</option>
                                    <option value="EXENTO" { 'selected' if product.get('iva_tipo') == 'EXENTO' else '' }>Exento</option>
                                    <option value="EXCLUIDO" { 'selected' if product.get('iva_tipo') == 'EXCLUIDO' else '' }>Excluido</option>
                                </select>
                            </div>
                            <div class="col-md-4 form-group">
                                <label class="form-label font-weight-bold">Tarifa IVA (%)</label>
                                <select name="iva_porcentaje" id="iva_porcentaje_input_edit" class="form-select">
                                    <option value="19.00" { 'selected' if float(product.get('iva_porcentaje', 0)) == 19.00 else '' }>19% (General)</option>
                                    <option value="5.00" { 'selected' if float(product.get('iva_porcentaje', 0)) == 5.00 else '' }>5% (Reducida)</option>
                                    <option value="0.00" { 'selected' if float(product.get('iva_porcentaje', 0)) == 0.00 else '' }>0% (Exento/Excluido)</option>
                                </select>
                            </div>
                            <div class="col-md-4 form-group">
                                <label class="form-label font-weight-bold">Impoconsumo (%)</label>
                                <input type="number" name="impoconsumo" class="form-input" step="0.01" value="{product.get('impoconsumo', 0.00)}">
                            </div>
                        </div>
                    </div>
                </div>

                <script>
                function toggleIvaFieldsEdit() {{
                    const type = document.getElementById('iva_tipo_select_edit').value;
                    const percentage = document.getElementById('iva_porcentaje_input_edit');
                    if (type === 'EXENTO' || type === 'EXCLUIDO') {{
                        percentage.value = "0.00";
                        percentage.disabled = true;
                    }} else {{
                        percentage.disabled = false;
                    }}
                }}
                // Initialize on load
                document.addEventListener('DOMContentLoaded', toggleIvaFieldsEdit);
                </script>

                <div class="form-actions mt-30">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save"></i> Actualizar Producto
                    </button>
                    <a href="/productos/" class="btn btn-secondary no-underline">
                        <i class="fas fa-times"></i> Cancelar
                    </a>
                </div>
            </form>
        </div>
        {error_script}
        """

        return HttpResponse(Layout.render("Editar Producto", user, "productos", content))
