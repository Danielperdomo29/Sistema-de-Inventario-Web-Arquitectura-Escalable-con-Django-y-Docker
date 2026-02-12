from django.http import HttpResponse
from django.middleware.csrf import get_token

from app.views.layout import Layout


class WarehouseView:
    """Vista de Almacenes"""

    @staticmethod
    def index(user, warehouses, request=None):
        """Renderiza la página de listado de almacenes"""
        csrf_token = get_token(request) if request else ""

        # Generar las filas de la tabla
        if warehouses:
            rows = ""
            for idx, warehouse in enumerate(warehouses, 1):
                rows += f"""
                <tr>
                    <td>{idx}</td>
                    <td>{warehouse['nombre']}</td>
                    <td>{warehouse.get('ubicacion', 'N/A') or 'N/A'}</td>
                    <td>{warehouse.get('capacidad', 0):,}</td>
                    <td>
                        <a href="/almacenes/{warehouse['id']}/editar/" class="btn btn-warning btn-sm no-underline">
                            <i class="fas fa-edit"></i> Editar
                        </a>
                        <button type="button" class="btn btn-danger btn-sm no-underline"
                                onclick="confirmDeleteAction('/almacenes/{warehouse['id']}/eliminar/',
                                                           '{csrf_token}',
                                                           '{warehouse['nombre']}');">
                            <i class="fas fa-trash"></i> Eliminar
                        </button>
                    </td>
                </tr>
                """

            table_content = f"""
            <div class="table-container">
                <table class="table-warehouses">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Nombre</th>
                        <th>Ubicación</th>
                        <th>Capacidad</th>
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
                <i class="fas fa-warehouse icon-4xl"></i>
                <h3>No hay almacenes registrados</h3>
                <p>Comienza agregando tu primer almacén</p>
            </div>
            """

        content = f"""
        <div class="card">
            <div class="card-header">
                <span>Gestión de Almacenes</span>
                <a href="/almacenes/crear/" class="btn btn-primary"><i class="fas fa-plus"></i> Nuevo Almacén</a>
            </div>
            {table_content}
        </div>
        """

        return HttpResponse(Layout.render("Almacenes", user, "almacenes", content))

    @staticmethod
    def create(user, request, error=None):
        """Vista del formulario de crear almacén"""

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
                <span><i class="fas fa-warehouse"></i> Crear Nuevo Almacén</span>
                <a href="/almacenes/" class="btn btn-secondary">← Volver</a>
            </div>
            <form method="POST" action="/almacenes/crear/" class="p-20" data-validate>
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">

                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Nombre *</label>
                        <input type="text" name="nombre" class="form-input"
                               data-rules="required|minLength:2"
                               data-label="Nombre"
                               placeholder="Nombre del almacén">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Ubicación</label>
                        <input type="text" name="ubicacion" class="form-input"
                               data-label="Ubicación"
                               placeholder="Ej: Bodega Principal">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Capacidad</label>
                        <input type="number" name="capacidad" value="0" min="0" class="form-input"
                               data-rules="numeric|min:0"
                               data-label="Capacidad">
                    </div>
                </div>

                <div class="form-actions mt-30">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save"></i> Guardar Almacén
                    </button>
                    <a href="/almacenes/" class="btn btn-secondary no-underline">
                        <i class="fas fa-times"></i> Cancelar
                    </a>
                </div>
            </form>
        </div>
        {error_script}
        """

        return HttpResponse(Layout.render("Crear Almacén", user, "almacenes", content))

    @staticmethod
    def edit(user, warehouse, request, error=None):
        """Vista del formulario de editar almacén"""

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
                <span><i class="fas fa-warehouse"></i> Editar Almacén</span>
                <a href="/almacenes/" class="btn btn-secondary">← Volver</a>
            </div>
            <form method="POST" action="/almacenes/{warehouse['id']}/editar/" class="p-20" data-validate>
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">

                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Nombre *</label>
                        <input type="text" name="nombre" value="{warehouse['nombre']}" class="form-input"
                               data-rules="required|minLength:2"
                               data-label="Nombre">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Ubicación</label>
                        <input type="text" name="ubicacion" value="{warehouse.get('ubicacion', '') or ''}"
                               class="form-input"
                               data-label="Ubicación">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Capacidad</label>
                        <input type="number" name="capacidad" value="{warehouse.get('capacidad', 0)}"
                               min="0" class="form-input"
                               data-rules="numeric|min:0"
                               data-label="Capacidad">
                    </div>
                </div>

                <div class="form-actions mt-30">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save"></i> Actualizar Almacén
                    </button>
                    <a href="/almacenes/" class="btn btn-secondary no-underline">
                        <i class="fas fa-times"></i> Cancelar
                    </a>
                </div>
            </form>
        </div>
        {error_script}
        """

        return HttpResponse(Layout.render("Editar Almacén", user, "almacenes", content))
