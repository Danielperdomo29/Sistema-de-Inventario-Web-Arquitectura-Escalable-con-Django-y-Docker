from django.http import HttpResponse
from django.middleware.csrf import get_token

from app.views.layout import Layout


class ClientView:
    """Vista de Clientes"""

    @staticmethod
    def index(user, clients):
        """Renderiza la página de listado de clientes"""
        from django.middleware.csrf import get_token

        # Generar las filas de la tabla
        if clients:
            rows = ""
            for idx, client in enumerate(clients, 1):
                rows += f"""
                <tr>
                    <td>{idx}</td>
                    <td>{client['nombre']}</td>
                    <td>{client.get('documento', 'N/A') or 'N/A'}</td>
                    <td>{client.get('telefono', 'N/A') or 'N/A'}</td>
                    <td>{client.get('email', 'N/A') or 'N/A'}</td>
                    <td>
                        <a href="/clientes/{client['id']}/editar/" class="btn btn-warning btn-sm no-underline">
                            <i class="fas fa-edit"></i> Editar
                        </a>
                        <a href="/clientes/{client['id']}/eliminar/" class="btn btn-danger btn-sm no-underline" 
                           onclick="event.preventDefault(); confirmDeleteAction('/clientes/{client['id']}/eliminar/', window.csrfToken, '{client['nombre']}');">
                            <i class="fas fa-trash"></i> Eliminar
                        </a>
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
                        <th>Documento</th>
                        <th>Teléfono</th>
                        <th>Email</th>
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
                <div class="icon-4xl"><i class="fas fa-users"></i></div>
                <h3>No hay clientes registrados</h3>
                <p>Comienza agregando tu primer cliente</p>
            </div>
            """

        content = f"""
        <div class="card">
            <div class="card-header">
                <span>Gestión de Clientes</span>
                <a href="/clientes/crear/" class="btn btn-primary"><i class="fas fa-plus"></i> Nuevo Cliente</a>
            </div>
            {table_content}
        </div>
        """

        return HttpResponse(Layout.render("Clientes", user, "clientes", content))

    @staticmethod
    def create(user, request, error=None):
        """Vista del formulario de crear cliente"""

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
                <span><i class="fas fa-user-plus"></i> Crear Nuevo Cliente</span>
                <a href="/clientes/" class="btn btn-secondary">← Volver</a>
            </div>
            <form method="POST" action="/clientes/crear/" class="p-20" data-validate>
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                
                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Nombre Completo *</label>
                        <input type="text" name="nombre" class="form-input"
                               data-rules="required|minLength:3"
                               data-label="Nombre Completo"
                               placeholder="Nombre del cliente">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Documento (NIT/C.C)</label>
                        <input type="text" name="documento" class="form-input"
                               data-label="Documento"
                               placeholder="Ej: 123456789">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Teléfono</label>
                        <input type="text" name="telefono" class="form-input"
                               data-rules="phone"
                               data-label="Teléfono"
                               placeholder="Ej: 3001234567">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Email</label>
                        <input type="email" name="email" class="form-input"
                               data-rules="email"
                               data-label="Email"
                               placeholder="correo@ejemplo.com">
                    </div>
                </div>
                
                <div class="mt-20">
                    <label class="form-label">Dirección</label>
                    <textarea name="direccion" rows="3" class="form-textarea"
                              placeholder="Dirección completa"></textarea>
                </div>
                
                <div class="form-actions mt-30">
                    <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Guardar Cliente</button>
                    <a href="/clientes/" class="btn btn-secondary no-underline"><i class="fas fa-times"></i> Cancelar</a>
                </div>
            </form>
        </div>
        {error_script}
        """

        return HttpResponse(Layout.render("Crear Cliente", user, "clientes", content))

    @staticmethod
    def edit(user, client, request, error=None):
        """Vista del formulario de editar cliente"""

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
                <span><i class="fas fa-user-edit"></i> Editar Cliente</span>
                <a href="/clientes/" class="btn btn-secondary">← Volver</a>
            </div>
            <form method="POST" action="/clientes/{client['id']}/editar/" class="p-20" data-validate>
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                
                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Nombre Completo *</label>
                        <input type="text" name="nombre" value="{client['nombre']}" class="form-input"
                               data-rules="required|minLength:3"
                               data-label="Nombre Completo">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Documento (NIT/C.C)</label>
                        <input type="text" name="documento" value="{client.get('documento', '') or ''}" class="form-input"
                               data-label="Documento">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Teléfono</label>
                        <input type="text" name="telefono" value="{client.get('telefono', '') or ''}" class="form-input"
                               data-rules="phone"
                               data-label="Teléfono">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Email</label>
                        <input type="email" name="email" value="{client.get('email', '') or ''}" class="form-input"
                               data-rules="email"
                               data-label="Email">
                    </div>
                </div>
                
                <div class="mt-20">
                    <label class="form-label">Dirección</label>
                    <textarea name="direccion" rows="3" class="form-textarea">{client.get('direccion', '') or ''}</textarea>
                </div>
                
                <div class="form-actions mt-30">
                    <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Actualizar Cliente</button>
                    <a href="/clientes/" class="btn btn-secondary no-underline"><i class="fas fa-times"></i> Cancelar</a>
                </div>
            </form>
        </div>
        {error_script}
        """

        return HttpResponse(Layout.render("Editar Cliente", user, "clientes", content))

