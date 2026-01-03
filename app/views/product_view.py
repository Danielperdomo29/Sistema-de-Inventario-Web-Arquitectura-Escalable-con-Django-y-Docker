from django.http import HttpResponse
from django.middleware.csrf import get_token

from app.views.layout import Layout


class ProductView:
    """Vista de Productos"""

    @staticmethod
    def index(user, request, products):
        """Vista de lista de productos"""
        csrf_token = get_token(request)

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
                    <td>{product['stock_actual']}</td>
                    <td>
                        <a href="/productos/{product['id']}/editar/" class="btn btn-warning btn-sm no-underline">
                            <i class="fas fa-edit"></i> Editar
                        </a>
                        <button type="button" class="btn btn-danger btn-sm no-underline" 
                                onclick="confirmDeleteAction('/productos/{product['id']}/eliminar/', '{csrf_token}', '{product['nombre']}');">
                            <i class="fas fa-trash"></i> Eliminar
                        </button>
                    </td>
                </tr>
                """

            table_content = f"""
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Nombre</th>
                            <th>Categoría</th>
                            <th>Precio</th>
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
        <div class="card">
            <div class="card-header">
                <span>Productos</span>
                <a href="/productos/crear/" class="btn btn-primary"><i class="fas fa-plus"></i> Nuevo Producto</a>
            </div>
            {table_content}
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
            category_options += (
                f'<option value="{category["id"]}" {selected}>{category["nombre"]}</option>'
            )

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
                        <input type="number" name="precio_compra" value="{product['precio_compra']}" step="0.01" class="form-input"
                               data-rules="required|min:0"
                               data-label="Precio Compra">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Precio Venta *</label>
                        <input type="number" name="precio_venta" value="{product['precio_venta']}" step="0.01" class="form-input"
                               data-rules="required|min:0"
                               data-label="Precio Venta">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Stock Actual</label>
                        <input type="number" name="stock_actual" value="{product['stock_actual']}" class="form-input"
                               data-rules="numeric|min:0"
                               data-label="Stock Actual">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Stock Mínimo</label>
                        <input type="number" name="stock_minimo" value="{product.get('stock_minimo', 10)}" class="form-input"
                               data-rules="numeric|min:0"
                               data-label="Stock Mínimo">
                    </div>
                </div>
                
                <div class="mt-20">
                    <label class="form-label">Descripción</label>
                    <textarea name="descripcion" rows="4" class="form-textarea">{product.get('descripcion', '') or ''}</textarea>
                </div>
                
                <div class="form-actions mt-30">
                    <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Actualizar Producto</button>
                    <a href="/productos/" class="btn btn-secondary no-underline"><i class="fas fa-times"></i> Cancelar</a>
                </div>
            </form>
        </div>
        {error_script}
        """

        return HttpResponse(Layout.render("Editar Producto", user, "productos", content))
