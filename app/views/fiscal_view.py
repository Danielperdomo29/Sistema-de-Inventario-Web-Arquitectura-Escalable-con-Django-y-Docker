"""
Vistas HTML para el Módulo Fiscal - Fase A.

Genera el HTML para las diferentes secciones del módulo fiscal.
"""
from django.http import HttpResponse
from app.views.layout import Layout


class FiscalView:
    """Vista del Módulo Fiscal"""

    @staticmethod
    def index(user, request_path, stats, ultimos_perfiles):
        """Dashboard del módulo fiscal"""

        # Tarjetas de estadísticas
        stats_cards = f"""
        <div class="stats-primary-grid">
            <div class="stat-card-primary bg-gradient-indigo">
                <div class="stat-card-content">
                    <div class="stat-card-info">
                        <p>Perfiles Fiscales</p>
                        <h2>{stats['total_perfiles']}</h2>
                        <small>{stats['perfiles_activos']} activos</small>
                    </div>
                    <div class="stat-card-icon"><i class="fas fa-file-invoice"></i></div>
                </div>
            </div>
            
            <div class="stat-card-primary bg-gradient-teal">
                <div class="stat-card-content">
                    <div class="stat-card-info">
                        <p>Cuentas PUC</p>
                        <h2>{stats['total_cuentas_puc']}</h2>
                        <small>{stats['cuentas_activas']} activas</small>
                    </div>
                    <div class="stat-card-icon"><i class="fas fa-list-alt"></i></div>
                </div>
            </div>
            
            <div class="stat-card-primary bg-gradient-orange">
                <div class="stat-card-content">
                    <div class="stat-card-info">
                        <p>Impuestos</p>
                        <h2>{stats['total_impuestos']}</h2>
                        <small>{stats['impuestos_activos']} activos</small>
                    </div>
                    <div class="stat-card-icon"><i class="fas fa-percent"></i></div>
                </div>
            </div>
        </div>
        """

        # Accesos rápidos
        quick_access = """
        <div class="stats-secondary-grid">
            <div class="stat-card-secondary border-indigo">
                <p>Perfiles Fiscales</p>
                <a href="/fiscal/perfiles/" class="btn btn-primary">Ver Todos</a>
            </div>
            
            <div class="stat-card-secondary border-teal">
                <p>Cuentas PUC</p>
                <a href="/fiscal/cuentas-puc/" class="btn btn-primary">Ver Árbol</a>
            </div>
            
            <div class="stat-card-secondary border-orange">
                <p>Impuestos</p>
                <a href="/fiscal/impuestos/" class="btn btn-primary">Ver Configuración</a>
            </div>
            
            <div class="stat-card-secondary border-purple">
                <p>Django Admin</p>
                <a href="/admin/fiscal/" class="btn btn-secondary">Administrar</a>
            </div>
        </div>
        """

        # Últimos perfiles creados
        perfiles_rows = ""
        if ultimos_perfiles:
            for perfil in ultimos_perfiles:
                perfiles_rows += f"""
                <tr>
                    <td>{perfil['nombre']}</td>
                    <td>{perfil['tipo_documento']}</td>
                    <td>{perfil['numero_documento']}-{perfil['dv']}</td>
                    <td>{perfil['regimen']}</td>
                    <td>{perfil['fecha_creacion']}</td>
                    <td>
                        <a href="/fiscal/perfiles/{perfil['id']}/editar/" class="btn btn-info btn-sm">
                            Ver
                        </a>
                    </td>
                </tr>
                """
        else:
            perfiles_rows = '<tr><td colspan="6" class="empty-message"><i class="fas fa-info-circle"></i> No hay perfiles fiscales registrados</td></tr>'

        ultimos_perfiles_section = f"""
        <div class="card">
            <div class="card-header">
                <span><i class="fas fa-file-invoice"></i> Últimos Perfiles Fiscales</span>
                <a href="/fiscal/perfiles/" class="btn btn-primary">Ver Todos</a>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Nombre</th>
                            <th>Tipo Documento</th>
                            <th>Número</th>
                            <th>Régimen</th>
                            <th>Fecha Creación</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {perfiles_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

        # Banner de bienvenida
        welcome_banner = """
        <div class="welcome-banner">
            <h1><i class="fas fa-file-invoice-dollar"></i> Módulo Fiscal - Fase A</h1>
            <p>Gestión de perfiles fiscales, cuentas PUC e impuestos conforme a normativa DIAN</p>
        </div>
        """

        content = (
            welcome_banner
            + stats_cards
            + quick_access
            + ultimos_perfiles_section
        )

        return HttpResponse(Layout.render("Módulo Fiscal", user, "fiscal", content))

    @staticmethod
    def perfiles_list(user, request_path, perfiles):
        """Listado de perfiles fiscales"""

        # Tabla de perfiles
        perfiles_rows = ""
        if perfiles:
            for perfil in perfiles:
                estado_badge = '<span class="badge badge-success">Activo</span>' if perfil['activo'] else '<span class="badge badge-danger">Inactivo</span>'
                perfiles_rows += f"""
                <tr>
                    <td>{perfil['nombre']}</td>
                    <td>{perfil['tipo_documento']}</td>
                    <td>{perfil['numero_documento']}-{perfil['dv']}</td>
                    <td>{perfil['tipo_persona']}</td>
                    <td>{perfil['regimen']}</td>
                    <td>{perfil['email']}</td>
                    <td>{estado_badge}</td>
                    <td>
                        <a href="/fiscal/perfiles/{perfil['id']}/editar/" class="btn btn-info btn-sm">
                            <i class="fas fa-edit"></i> Editar
                        </a>
                    </td>
                </tr>
                """
        else:
            perfiles_rows = '<tr><td colspan="8" class="empty-message"><i class="fas fa-info-circle"></i> No hay perfiles fiscales registrados</td></tr>'

        perfiles_table = f"""
        <div class="card">
            <div class="card-header">
                <span><i class="fas fa-file-invoice"></i> Perfiles Fiscales</span>
                <a href="/fiscal/perfiles/crear/" class="btn btn-success">
                    <i class="fas fa-plus"></i> Nuevo Perfil
                </a>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Nombre</th>
                            <th>Tipo Doc.</th>
                            <th>Número</th>
                            <th>Tipo Persona</th>
                            <th>Régimen</th>
                            <th>Email</th>
                            <th>Estado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {perfiles_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

        # Breadcrumb
        breadcrumb = """
        <div class="breadcrumb">
            <a href="/fiscal/">Módulo Fiscal</a> / <span>Perfiles Fiscales</span>
        </div>
        """

        content = breadcrumb + perfiles_table

        return HttpResponse(Layout.render("Perfiles Fiscales", user, "fiscal", content))

    @staticmethod
    def perfil_form(user, request_path, perfil_data):
        """Formulario para crear/editar perfil fiscal"""

        # Determinar si es creación o edición
        is_edit = perfil_data is not None
        title = "Editar Perfil Fiscal" if is_edit else "Nuevo Perfil Fiscal"
        action_url = f"/fiscal/perfiles/{perfil_data['id']}/editar/" if is_edit else "/fiscal/perfiles/crear/"

        # Valores por defecto
        if not perfil_data:
            perfil_data = {
                'nombre': '',
                'tipo_documento': '31',
                'numero_documento': '',
                'tipo_persona': 'J',
                'regimen': '48',
                'nombre_comercial': '',
                'email_facturacion': '',
                'telefono': '',
                'direccion': '',
                'departamento_codigo': '',
                'municipio_codigo': '',
            }

        form_html = f"""
        <div class="card">
            <div class="card-header">
                <span><i class="fas fa-file-invoice"></i> {title}</span>
            </div>
            <div class="card-body">
                <form method="POST" action="{action_url}">
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i>
                        <strong>Nota:</strong> La funcionalidad de crear/editar perfiles fiscales estará disponible en una próxima actualización.
                        Por ahora, utiliza el <a href="/admin/fiscal/perfilfiscal/" target="_blank">Django Admin</a> para gestionar perfiles.
                    </div>
                    
                    <div class="form-actions">
                        <a href="/fiscal/perfiles/" class="btn btn-secondary">
                            <i class="fas fa-arrow-left"></i> Volver
                        </a>
                        <a href="/admin/fiscal/perfilfiscal/add/" class="btn btn-primary" target="_blank">
                            <i class="fas fa-external-link-alt"></i> Crear en Admin
                        </a>
                    </div>
                </form>
            </div>
        </div>
        """

        # Breadcrumb
        breadcrumb = f"""
        <div class="breadcrumb">
            <a href="/fiscal/">Módulo Fiscal</a> / 
            <a href="/fiscal/perfiles/">Perfiles Fiscales</a> / 
            <span>{title}</span>
        </div>
        """

        content = breadcrumb + form_html

        return HttpResponse(Layout.render(title, user, "fiscal", content))

    @staticmethod
    def cuentas_puc_list(user, request_path, cuentas_tree):
        """Listado jerárquico de cuentas PUC"""

        # Construir árbol HTML
        tree_html = ""
        for cuenta_clase in cuentas_tree:
            naturaleza_badge = '<span class="badge badge-success">Débito</span>' if cuenta_clase['naturaleza'] == 'D' else '<span class="badge badge-info">Crédito</span>'
            estado_badge = '<span class="badge badge-success">Activa</span>' if cuenta_clase['activa'] else '<span class="badge badge-secondary">Inactiva</span>'

            tree_html += f"""
            <div class="puc-nivel-1">
                <div class="puc-cuenta">
                    <strong>{cuenta_clase['codigo']}</strong> - {cuenta_clase['nombre']}
                    {naturaleza_badge} {estado_badge}
                </div>
            """

            # Nivel 2
            for cuenta_nivel_2 in cuenta_clase['subcuentas']:
                naturaleza_badge_2 = '<span class="badge badge-success">Débito</span>' if cuenta_nivel_2['naturaleza'] == 'D' else '<span class="badge badge-info">Crédito</span>'
                estado_badge_2 = '<span class="badge badge-success">Activa</span>' if cuenta_nivel_2['activa'] else '<span class="badge badge-secondary">Inactiva</span>'

                tree_html += f"""
                <div class="puc-nivel-2">
                    <div class="puc-cuenta">
                        <strong>{cuenta_nivel_2['codigo']}</strong> - {cuenta_nivel_2['nombre']}
                        {naturaleza_badge_2} {estado_badge_2}
                    </div>
                """

                # Nivel 3
                for cuenta_nivel_3 in cuenta_nivel_2['subcuentas']:
                    naturaleza_badge_3 = '<span class="badge badge-success">Débito</span>' if cuenta_nivel_3['naturaleza'] == 'D' else '<span class="badge badge-info">Crédito</span>'
                    estado_badge_3 = '<span class="badge badge-success">Activa</span>' if cuenta_nivel_3['activa'] else '<span class="badge badge-secondary">Inactiva</span>'

                    tree_html += f"""
                    <div class="puc-nivel-3">
                        <div class="puc-cuenta">
                            <strong>{cuenta_nivel_3['codigo']}</strong> - {cuenta_nivel_3['nombre']}
                            {naturaleza_badge_3} {estado_badge_3}
                        </div>
                    </div>
                    """

                tree_html += "</div>"  # Cerrar nivel 2

            tree_html += "</div>"  # Cerrar nivel 1

        puc_card = f"""
        <div class="card">
            <div class="card-header">
                <span><i class="fas fa-list-alt"></i> Plan Único de Cuentas (PUC)</span>
                <a href="/admin/fiscal/cuentacontable/" class="btn btn-secondary" target="_blank">
                    <i class="fas fa-cog"></i> Administrar
                </a>
            </div>
            <div class="card-body">
                <div class="puc-tree">
                    {tree_html}
                </div>
            </div>
        </div>

        <style>
            .puc-tree {{
                font-family: monospace;
                font-size: 14px;
            }}
            .puc-nivel-1 {{
                margin-bottom: 20px;
                border-left: 3px solid #6366f1;
                padding-left: 15px;
            }}
            .puc-nivel-2 {{
                margin-left: 20px;
                margin-top: 10px;
                border-left: 2px solid #14b8a6;
                padding-left: 15px;
            }}
            .puc-nivel-3 {{
                margin-left: 20px;
                margin-top: 5px;
                padding-left: 15px;
                border-left: 1px solid #f59e0b;
            }}
            .puc-cuenta {{
                padding: 8px;
                background: #f8f9fa;
                border-radius: 4px;
                margin-bottom: 5px;
            }}
            .puc-cuenta strong {{
                color: #1e293b;
            }}
            .puc-cuenta .badge {{
                margin-left: 10px;
                font-size: 11px;
            }}
        </style>
        """

        # Breadcrumb
        breadcrumb = """
        <div class="breadcrumb">
            <a href="/fiscal/">Módulo Fiscal</a> / <span>Cuentas PUC</span>
        </div>
        """

        content = breadcrumb + puc_card

        return HttpResponse(Layout.render("Cuentas PUC", user, "fiscal", content))

    @staticmethod
    def impuestos_list(user, request_path, impuestos):
        """Listado de impuestos configurados"""

        # Tabla de impuestos
        impuestos_rows = ""
        if impuestos:
            for impuesto in impuestos:
                estado_badge = '<span class="badge badge-success">Activo</span>' if impuesto['activo'] else '<span class="badge badge-danger">Inactivo</span>'
                aplica_ventas = '<i class="fas fa-check text-success"></i>' if impuesto['aplica_ventas'] else '<i class="fas fa-times text-danger"></i>'
                aplica_compras = '<i class="fas fa-check text-success"></i>' if impuesto['aplica_compras'] else '<i class="fas fa-times text-danger"></i>'
                base_minima = f"${impuesto['base_minima']:,.2f}" if impuesto['base_minima'] else "N/A"

                impuestos_rows += f"""
                <tr>
                    <td><strong>{impuesto['codigo']}</strong></td>
                    <td>{impuesto['nombre']}</td>
                    <td>{impuesto['tipo']}</td>
                    <td class="text-right"><strong>{impuesto['porcentaje']}%</strong></td>
                    <td class="text-right">{base_minima}</td>
                    <td>{impuesto['cuenta_por_pagar']}</td>
                    <td class="text-center">{aplica_ventas}</td>
                    <td class="text-center">{aplica_compras}</td>
                    <td>{estado_badge}</td>
                </tr>
                """
        else:
            impuestos_rows = '<tr><td colspan="9" class="empty-message"><i class="fas fa-info-circle"></i> No hay impuestos configurados</td></tr>'

        impuestos_table = f"""
        <div class="card">
            <div class="card-header">
                <span><i class="fas fa-percent"></i> Impuestos Configurados</span>
                <a href="/admin/fiscal/impuesto/" class="btn btn-secondary" target="_blank">
                    <i class="fas fa-cog"></i> Administrar
                </a>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Código</th>
                            <th>Nombre</th>
                            <th>Tipo</th>
                            <th class="text-right">Porcentaje</th>
                            <th class="text-right">Base Mínima</th>
                            <th>Cuenta por Pagar</th>
                            <th class="text-center">Ventas</th>
                            <th class="text-center">Compras</th>
                            <th>Estado</th>
                        </tr>
                    </thead>
                    <tbody>
                        {impuestos_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

        # Breadcrumb
        breadcrumb = """
        <div class="breadcrumb">
            <a href="/fiscal/">Módulo Fiscal</a> / <span>Impuestos</span>
        </div>
        """

        content = breadcrumb + impuestos_table

        return HttpResponse(Layout.render("Impuestos", user, "fiscal", content))
