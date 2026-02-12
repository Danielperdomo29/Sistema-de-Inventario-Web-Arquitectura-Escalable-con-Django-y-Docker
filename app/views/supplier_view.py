from django.http import HttpResponse
from django.middleware.csrf import get_token

from app.views.layout import Layout


class SupplierView:
    @staticmethod
    def index(user, suppliers, total, request):
        """Vista de lista de proveedores"""

        csrf_token = get_token(request)

        rows = ""
        if suppliers:
            for idx, supplier in enumerate(suppliers, 1):
                # Formatear NIT completo
                nit_display = "N/A"
                if supplier.get("nit"):
                    dv = supplier.get("digito_verificacion", "?")
                    nit_display = f"{supplier['nit']}-{dv}"

                rows += f"""
                <tr>
                    <td>{idx}</td>
                    <td>{supplier['nombre']}</td>
                    <td>{nit_display}</td>
                    <td>{supplier.get('rut', 'N/A') or 'N/A'}</td>
                    <td>{supplier.get('telefono', 'N/A') or 'N/A'}</td>
                    <td>{supplier.get('email', 'N/A') or 'N/A'}</td>
                    <td>{supplier.get('ciudad', 'N/A') or 'N/A'}</td>
                    <td>
                        <a href="/proveedores/{supplier['id']}/editar/" class="btn btn-warning btn-sm">
                            <i class="fas fa-edit"></i> Editar
                        </a>
                        <button type="button" class="btn btn-danger btn-sm btn-delete-supplier"
                                data-id="{supplier['id']}"
                                data-name="{supplier['nombre']}"
                                data-csrf="{csrf_token}">
                            <i class="fas fa-trash"></i> Eliminar
                        </button>
                    </td>
                </tr>
                """

            table_content = f"""
            <div class="table-container">
                <table class="table-suppliers">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Nombre/Razón Social</th>
                        <th>NIT</th>
                        <th>RUT</th>
                        <th>Teléfono</th>
                        <th>Email</th>
                        <th>Ciudad</th>
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
                <i class="fas fa-truck icon-4xl"></i>
                <h3>No hay proveedores registrados</h3>
                <p>Comienza agregando tu primer proveedor</p>
            </div>
            """

        # SweetAlert2 script for delete confirmation
        delete_script = """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('.btn-delete-supplier').forEach(function(btn) {
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    const supplierId = this.getAttribute('data-id');
                    const supplierName = this.getAttribute('data-name');
                    const csrfToken = this.getAttribute('data-csrf');

                    Swal.fire({
                        title: '¿Estás seguro?',
                        html: `¿Deseas eliminar el proveedor <strong>${supplierName}</strong>?<br><small class="text-muted">Esta acción no se puede revertir.</small>`,
                        icon: 'warning',
                        showCancelButton: true,
                        confirmButtonColor: '#e11d48',
                        cancelButtonColor: '#4b5563',
                        confirmButtonText: '<i class="fas fa-trash"></i> Sí, eliminar',
                        cancelButtonText: '<i class="fas fa-times"></i> Cancelar',
                        reverseButtons: true
                    }).then((result) => {
                        if (result.isConfirmed) {
                            // Create and submit form
                            const form = document.createElement('form');
                            form.method = 'POST';
                            form.action = `/proveedores/${supplierId}/eliminar/`;

                            const csrfInput = document.createElement('input');
                            csrfInput.type = 'hidden';
                            csrfInput.name = 'csrfmiddlewaretoken';
                            csrfInput.value = csrfToken;

                            form.appendChild(csrfInput);
                            document.body.appendChild(form);
                            form.submit();
                        }
                    });
                });
            });
        });
        </script>
        """

        content = f"""
        <div class="card">
            <div class="card-header">
                <span>Gestión de Proveedores</span>
                <a href="/proveedores/crear/" class="btn btn-primary"><i class="fas fa-plus"></i> Nuevo Proveedor</a>
            </div>
            {table_content}
        </div>
        {delete_script}
        """

        return HttpResponse(Layout.render("Proveedores", user, "proveedores", content))

    @staticmethod
    def create(user, request, error=None):
        """Vista de formulario para crear proveedor"""

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
                <span><i class="fas fa-truck"></i> Crear Nuevo Proveedor</span>
                <a href="/proveedores/" class="btn btn-secondary">← Volver</a>
            </div>
            <form method="POST" action="/proveedores/crear/" class="p-20" id="supplierForm">
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">

                <h4 class="form-section-title"><i class="fas fa-building"></i> Información General</h4>
                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Nombre/Razón Social *</label>
                        <input type="text" name="nombre" id="nombre" class="form-input"
                               placeholder="Ej: Distribuidora Nacional S.A.S">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Ciudad</label>
                        <input type="text" name="ciudad" maxlength="100" class="form-input"
                               placeholder="Ej: Bogotá">
                    </div>
                </div>

                <h4 class="form-section-title mt-20"><i class="fas fa-id-card"></i> Identificación Tributaria</h4>
                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">NIT</label>
                        <div style="display: flex; gap: 10px;">
                            <input type="text" name="nit" id="nit" maxlength="15"
                                   class="form-input" style="flex: 3;"
                                   placeholder="Ej: 900123456">
                            <span style="align-self: center; font-weight: bold;">-</span>
                            <input type="text" name="digito_verificacion" id="dv" maxlength="1"
                                   class="form-input" style="flex: 1; max-width: 60px; text-align: center;"
                                   placeholder="DV" title="Dígito de Verificación">
                        </div>
                        <small class="form-help-text">Número de Identificación Tributaria con dígito de verificación</small>
                    </div>

                    <div class="form-group">
                        <label class="form-label">RUT</label>
                        <input type="text" name="rut" maxlength="50" class="form-input"
                               placeholder="Registro Único Tributario">
                    </div>
                </div>

                <h4 class="form-section-title mt-20"><i class="fas fa-address-book"></i> Información de Contacto</h4>
                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Teléfono</label>
                        <input type="text" name="telefono" maxlength="20" class="form-input"
                               placeholder="Ej: 601 1234567">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Email</label>
                        <input type="email" name="email" id="email" maxlength="100" class="form-input"
                               placeholder="correo@empresa.com">
                    </div>
                </div>

                <div class="mt-20">
                    <label class="form-label">Dirección</label>
                    <textarea name="direccion" rows="3" class="form-textarea"
                              placeholder="Dirección completa del proveedor"></textarea>
                </div>

                <div class="form-actions-end mt-30">
                    <a href="/proveedores/" class="btn btn-secondary"><i class="fas fa-times"></i> Cancelar</a>
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save"></i> Guardar Proveedor
                    </button>
                </div>
            </form>
        </div>

        {error_script}

        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const form = document.getElementById('supplierForm');

            form.addEventListener('submit', function(e) {{
                const nombre = document.getElementById('nombre').value.trim();
                const email = document.getElementById('email').value.trim();
                const nit = document.getElementById('nit').value.trim();
                const dv = document.getElementById('dv').value.trim();

                let errors = [];

                // Validación nombre requerido
                if (!nombre) {{
                    errors.push('El Nombre/Razón Social es requerido');
                }}

                // Validación email formato
                if (email && !isValidEmail(email)) {{
                    errors.push('El formato del email no es válido');
                }}

                // Validación NIT solo números
                if (nit && !/^[0-9]+$/.test(nit)) {{
                    errors.push('El NIT debe contener solo números');
                }}

                // Validación DV solo un dígito
                if (dv && !/^[0-9]$/.test(dv)) {{
                    errors.push('El dígito de verificación debe ser un solo número');
                }}

                // Si hay NIT pero no DV, advertir
                if (nit && !dv) {{
                    errors.push('Si ingresa NIT, también debe ingresar el dígito de verificación');
                }}

                if (errors.length > 0) {{
                    e.preventDefault();
                    Swal.fire({{
                        icon: 'warning',
                        title: 'Campos Inválidos',
                        html: '<ul style="text-align:left;">' +
                              errors.map(err => '<li>' + err + '</li>').join('') +
                              '</ul>',
                        confirmButtonColor: '#3085d6',
                        confirmButtonText: 'Corregir'
                    }});
                    return false;
                }}
            }});

            function isValidEmail(email) {{
                return /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email);
            }}
        }});
        </script>

        <style>
            .form-section-title {{
                font-size: 1rem;
                color: #374151;
                margin-bottom: 15px;
                padding-bottom: 8px;
                border-bottom: 2px solid #e5e7eb;
            }}
            .form-help-text {{
                color: #6b7280;
                font-size: 0.75rem;
                margin-top: 4px;
            }}
        </style>
        """

        return HttpResponse(Layout.render("Nuevo Proveedor", user, "proveedores", content))

    @staticmethod
    def edit(user, supplier, request, error=None):
        """Vista de formulario para editar proveedor"""

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
                <span><i class="fas fa-edit"></i> Editar Proveedor</span>
                <a href="/proveedores/" class="btn btn-secondary">← Volver</a>
            </div>
            <form method="POST" action="/proveedores/{supplier['id']}/editar/" class="p-20" id="supplierForm">
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">

                <h4 class="form-section-title"><i class="fas fa-building"></i> Información General</h4>
                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Nombre/Razón Social *</label>
                        <input type="text" name="nombre" id="nombre" value="{supplier['nombre']}" class="form-input">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Ciudad</label>
                        <input type="text" name="ciudad" value="{supplier.get('ciudad', '') or ''}"
                               maxlength="100" class="form-input">
                    </div>
                </div>

                <h4 class="form-section-title mt-20"><i class="fas fa-id-card"></i> Identificación Tributaria</h4>
                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">NIT</label>
                        <div style="display: flex; gap: 10px;">
                            <input type="text" name="nit" id="nit" value="{supplier.get('nit', '') or ''}"
                                   maxlength="15" class="form-input" style="flex: 3;">
                            <span style="align-self: center; font-weight: bold;">-</span>
                            <input type="text" name="digito_verificacion" id="dv"
                                   value="{supplier.get('digito_verificacion', '') or ''}" maxlength="1"
                                   class="form-input" style="flex: 1; max-width: 60px; text-align: center;">
                        </div>
                        <small class="form-help-text">Número de Identificación Tributaria con dígito de verificación</small>
                    </div>

                    <div class="form-group">
                        <label class="form-label">RUT</label>
                        <input type="text" name="rut" value="{supplier.get('rut', '') or ''}"
                               maxlength="50" class="form-input">
                    </div>
                </div>

                <h4 class="form-section-title mt-20"><i class="fas fa-address-book"></i> Información de Contacto</h4>
                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Teléfono</label>
                        <input type="text" name="telefono" value="{supplier.get('telefono', '') or ''}"
                               maxlength="20" class="form-input">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Email</label>
                        <input type="email" name="email" id="email" value="{supplier.get('email', '') or ''}"
                               maxlength="100" class="form-input">
                    </div>
                </div>

                <div class="mt-20">
                    <label class="form-label">Dirección</label>
                    <textarea name="direccion" rows="3" class="form-textarea">{supplier.get('direccion', '') or ''}</textarea>
                </div>

                <div class="form-actions-end mt-30">
                    <a href="/proveedores/" class="btn btn-secondary"><i class="fas fa-times"></i> Cancelar</a>
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save"></i> Actualizar Proveedor
                    </button>
                </div>
            </form>
        </div>

        {error_script}

        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const form = document.getElementById('supplierForm');

            form.addEventListener('submit', function(e) {{
                const nombre = document.getElementById('nombre').value.trim();
                const email = document.getElementById('email').value.trim();
                const nit = document.getElementById('nit').value.trim();
                const dv = document.getElementById('dv').value.trim();

                let errors = [];

                // Validación nombre requerido
                if (!nombre) {{
                    errors.push('El Nombre/Razón Social es requerido');
                }}

                // Validación email formato
                if (email && !isValidEmail(email)) {{
                    errors.push('El formato del email no es válido');
                }}

                // Validación NIT solo números
                if (nit && !/^[0-9]+$/.test(nit)) {{
                    errors.push('El NIT debe contener solo números');
                }}

                // Validación DV solo un dígito
                if (dv && !/^[0-9]$/.test(dv)) {{
                    errors.push('El dígito de verificación debe ser un solo número');
                }}

                // Si hay NIT pero no DV, advertir
                if (nit && !dv) {{
                    errors.push('Si ingresa NIT, también debe ingresar el dígito de verificación');
                }}

                if (errors.length > 0) {{
                    e.preventDefault();
                    Swal.fire({{
                        icon: 'warning',
                        title: 'Campos Inválidos',
                        html: '<ul style="text-align:left;">' +
                              errors.map(err => '<li>' + err + '</li>').join('') +
                              '</ul>',
                        confirmButtonColor: '#3085d6',
                        confirmButtonText: 'Corregir'
                    }});
                    return false;
                }}
            }});

            function isValidEmail(email) {{
                return /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email);
            }}
        }});
        </script>

        <style>
            .form-section-title {{
                font-size: 1rem;
                color: #374151;
                margin-bottom: 15px;
                padding-bottom: 8px;
                border-bottom: 2px solid #e5e7eb;
            }}
            .form-help-text {{
                color: #6b7280;
                font-size: 0.75rem;
                margin-top: 4px;
            }}
        </style>
        """

        return HttpResponse(Layout.render("Editar Proveedor", user, "proveedores", content))
