from django.http import HttpResponse
from django.middleware.csrf import get_token

from app.views.layout import Layout


class CategoryView:
    """Vista de Categorías"""

    @staticmethod
    def index(user, categories, request=None):
        """Renderiza la página de listado de categorías"""
        csrf_token = get_token(request) if request else ""

        # Generar las filas de la tabla
        if categories:
            rows = ""
            for idx, category in enumerate(categories, 1):
                rows += f"""
                <tr>
                    <td>{idx}</td>
                    <td>{category['nombre']}</td>
                    <td>{category['descripcion'] or 'Sin descripción'}</td>
                    <td>
                        <a href="/categorias/{category['id']}/editar/" class="btn btn-warning btn-sm no-underline">
                            <i class="fas fa-edit"></i> Editar
                        </a>
                        <button type="button" class="btn btn-danger btn-sm no-underline" 
                                onclick="confirmDeleteAction('/categorias/{category['id']}/eliminar/', '{csrf_token}', '{category['nombre']}');">
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
                        <th>#</th>
                        <th>Nombre</th>
                        <th>Descripción</th>
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
                <div class="icon-4xl"><i class="fas fa-folder"></i></div>
                <h3>No hay categorías registradas</h3>
                <p>Comienza agregando tu primera categoría</p>
            </div>
            """

        content = f"""
        <div class="card">
            <div class="card-header">
                <span>Gestión de Categorías</span>
                <a href="/categorias/crear/" class="btn btn-primary"><i class="fas fa-plus"></i> Nueva Categoría</a>
            </div>
            {table_content}
        </div>
        """

        return HttpResponse(Layout.render("Categorías", user, "categorias", content))


    @staticmethod
    def create(user, request, error=None):
        """Vista del formulario de crear categoría"""

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

        content = f"""
        <div class="card">
            <div class="card-header">
                <span><i class="fas fa-folder-plus"></i> Crear Nueva Categoría</span>
                <a href="/categorias/" class="btn btn-secondary">← Volver</a>
            </div>
            <form method="POST" action="/categorias/crear/" class="p-20" data-validate>
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                
                <div class="mb-20">
                    <label class="form-label">Nombre *</label>
                    <input type="text" name="nombre" class="form-input"
                           data-rules="required|minLength:2"
                           data-label="Nombre"
                           placeholder="Nombre de la categoría">
                </div>
                
                <div class="mb-20">
                    <label class="form-label">Descripción</label>
                    <textarea name="descripcion" rows="4" class="form-textarea"
                              placeholder="Descripción opcional"></textarea>
                </div>
                
                <div class="form-actions">
                    <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Guardar Categoría</button>
                    <a href="/categorias/" class="btn btn-secondary no-underline"><i class="fas fa-times"></i> Cancelar</a>
                </div>
            </form>
        </div>
        {error_script}
        """

        return HttpResponse(Layout.render("Crear Categoría", user, "categorias", content))

    @staticmethod
    def edit(user, category, request, error=None):
        """Vista del formulario de editar categoría"""

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

        content = f"""
        <div class="card">
            <div class="card-header">
                <span><i class="fas fa-folder-open"></i> Editar Categoría</span>
                <a href="/categorias/" class="btn btn-secondary">← Volver</a>
            </div>
            <form method="POST" action="/categorias/{category['id']}/editar/" class="p-20" data-validate>
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                
                <div class="mb-20">
                    <label class="form-label">Nombre *</label>
                    <input type="text" name="nombre" value="{category['nombre']}" class="form-input"
                           data-rules="required|minLength:2"
                           data-label="Nombre">
                </div>
                
                <div class="mb-20">
                    <label class="form-label">Descripción</label>
                    <textarea name="descripcion" rows="4" class="form-textarea">{category.get('descripcion', '') or ''}</textarea>
                </div>
                
                <div class="form-actions">
                    <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Actualizar Categoría</button>
                    <a href="/categorias/" class="btn btn-secondary no-underline"><i class="fas fa-times"></i> Cancelar</a>
                </div>
            </form>
        </div>
        {error_script}
        """

        return HttpResponse(Layout.render("Editar Categoría", user, "categorias", content))
