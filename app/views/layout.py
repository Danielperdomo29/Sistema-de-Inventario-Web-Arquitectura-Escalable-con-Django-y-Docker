class Layout:
    """Layouts y componentes compartidos"""

    @staticmethod
    def get_styles():
        """Carga los estilos CSS desde archivo externo"""
        return """
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link rel="stylesheet" href="/static/css/main.css">
        <link rel="stylesheet" href="/static/css/forms.css">
        <link rel="stylesheet" href="/static/css/dashboard.css">
        <link rel="stylesheet" href="/static/css/swal.css">
        <link rel="stylesheet" href="/static/css/chatbot.css">
        <link rel="stylesheet" href="/static/css/theme-corporate-neutral.css?v=6.0">
        <script src='https://cdn.jsdelivr.net/npm/sweetalert2@11'></script>
        """

    @staticmethod
    def navbar(user):
        """Componente de Navbar"""
        return f"""
        <div class="navbar">
            <div class="navbar-content">
                <button class="hamburger-menu" id="hamburger-menu" aria-label="Toggle menu">
                    <i class="fas fa-bars"></i>
                </button>
                <h1>Sistema de Inventario</h1>
                <div class="navbar-menu">
                    <span>Hola, {user.username}</span>
                    <a href="/logout/">Cerrar Sesión</a>
                </div>
            </div>
        </div>
        """

    @staticmethod
    def sidebar(active_page=""):
        """Componente de Sidebar con secciones colapsables"""
        
        # Categorización de items del menú
        inventario_items = [
            {"url": "/", "label": '<i class="fas fa-home"></i> Dashboard', "key": "dashboard"},
            {"url": "/productos/", "label": '<i class="fas fa-box"></i> Productos', "key": "productos"},
            {"url": "/categorias/", "label": '<i class="fas fa-tags"></i> Categorías', "key": "categorias"},
            {"url": "/almacenes/", "label": '<i class="fas fa-warehouse"></i> Almacenes', "key": "almacenes"},
            {"url": "/movimientos-inventario/", "label": '<i class="fas fa-exchange-alt"></i> Movimientos Inventario', "key": "movimientos-inventario"},
            {"url": "/proveedores/", "label": '<i class="fas fa-truck"></i> Proveedores', "key": "proveedores"},
            {"url": "/reportes/", "label": '<i class="fas fa-chart-bar"></i> Reportes', "key": "reportes"},
        ]
        
        facturacion_items = [
            {"url": "/clientes/", "label": '<i class="fas fa-users"></i> Clientes', "key": "clientes"},
            {"url": "/ventas/", "label": '<i class="fas fa-shopping-cart"></i> Ventas', "key": "ventas"},
            {"url": "/detalle-ventas/", "label": '<i class="fas fa-receipt"></i> Detalle Ventas', "key": "detalle-ventas"},
            {"url": "/compras/", "label": '<i class="fas fa-shopping-bag"></i> Compras', "key": "compras"},
            {"url": "/detalle-compras/", "label": '<i class="fas fa-file-invoice"></i> Detalle Compras', "key": "detalle-compras"},
            {"url": "/fiscal/", "label": '<i class="fas fa-file-invoice-dollar"></i> Módulo Fiscal', "key": "fiscal"},
        ]
        
        sistema_items = [
            {"url": "/roles/", "label": '<i class="fas fa-user-tag"></i> Roles', "key": "roles"},
            {"url": "/chatbot/", "label": '<i class="fas fa-robot"></i> Chatbot IA', "key": "chatbot"},
            {"url": "/configuracion/", "label": '<i class="fas fa-cog"></i> Configuración', "key": "configuracion"},
            {"url": "/documentacion/", "label": '<i class="fas fa-book"></i> Documentación', "key": "documentacion"},
        ]
        
        def generate_menu_html(items):
            """Genera el HTML para un grupo de items del menú"""
            menu_html = ""
            for item in items:
                active_class = 'class="active"' if item["key"] == active_page else ""
                label_text = item["label"].split('</i>')[-1].strip() if '</i>' in item["label"] else item["label"]
                menu_html += f'<li><a href="{item["url"]}" {active_class} data-tooltip="{label_text}">{item["label"]}</a></li>\n'
            return menu_html
        
        inventario_html = generate_menu_html(inventario_items)
        facturacion_html = generate_menu_html(facturacion_items)
        sistema_html = generate_menu_html(sistema_items)
        
        return f"""
        <div class="sidebar-overlay" id="sidebar-overlay"></div>
        <div class="sidebar" id="sidebar">
            <!-- Sección Inventario -->
            <div class="sidebar-section" data-section="inventario">
                <div class="sidebar-section-header">
                    <div class="section-title">
                        <i class="fas fa-boxes"></i>
                        <span>Inventario</span>
                    </div>
                    <button class="section-toggle" data-section="inventario" aria-label="Toggle Inventario">
                        <i class="fas fa-chevron-down"></i>
                    </button>
                </div>
                <ul class="sidebar-menu" data-section="inventario">
                    {inventario_html}
                </ul>
            </div>

            <!-- Sección Facturación -->
            <div class="sidebar-section" data-section="facturacion">
                <div class="sidebar-section-header">
                    <div class="section-title">
                        <i class="fas fa-file-invoice-dollar"></i>
                        <span>Facturación</span>
                    </div>
                    <button class="section-toggle" data-section="facturacion" aria-label="Toggle Facturación">
                        <i class="fas fa-chevron-down"></i>
                    </button>
                </div>
                <ul class="sidebar-menu" data-section="facturacion">
                    {facturacion_html}
                </ul>
            </div>

            <!-- Sección Sistema -->
            <div class="sidebar-section" data-section="sistema">
                <div class="sidebar-section-header">
                    <div class="section-title">
                        <i class="fas fa-cog"></i>
                        <span>Sistema</span>
                    </div>
                    <button class="section-toggle" data-section="sistema" aria-label="Toggle Sistema">
                        <i class="fas fa-chevron-down"></i>
                    </button>
                </div>
                <ul class="sidebar-menu" data-section="sistema">
                    {sistema_html}
                </ul>
            </div>
        </div>
        """

    @staticmethod
    def render(title, user, active_page, content):
        """Renderiza el layout completo"""
        styles = Layout.get_styles()
        navbar = Layout.navbar(user)
        sidebar = Layout.sidebar(active_page)

        chatbot_script = ""
        if active_page == "chatbot":
            chatbot_script = '<script src="/static/js/chatbot.js"></script>'
        return f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title} - Sistema de Inventario</title>
            {styles}
        </head>
        <body>
            {navbar}
            <div class="layout">
                {sidebar}
                <div class="main-content">
                    {content}
                </div>
            </div>
            <script src="/static/js/main.js"></script>
            <script src="/static/js/sidebar.js"></script>
            <script src="/static/js/sidebar-sections.js"></script>
            <script>
                // Pasar estado del usuario al JavaScript
                // activo=1 → true (puede modificar), activo=0 → false (no puede modificar)
                window.userActive = {('true' if user.is_active else 'false')};
            </script>
            <script src="/static/js/protection.js"></script>
            {chatbot_script}
        </body>
        </html>
        """
