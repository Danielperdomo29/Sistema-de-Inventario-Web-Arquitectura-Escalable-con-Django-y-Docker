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
                    <a href="/configuracion/" style="margin-right: 15px;"><i class="fas fa-user-cog"></i> Mi Perfil</a>
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
            {"url": "/", "label": "Dashboard", "icon": "fas fa-home", "key": "dashboard"},
            {"url": "/productos/", "label": "Productos", "icon": "fas fa-box", "key": "productos"},
            {"url": "/categorias/", "label": "Categorías", "icon": "fas fa-tags", "key": "categorias"},
            {"url": "/almacenes/", "label": "Almacenes", "icon": "fas fa-warehouse", "key": "almacenes"},
            {"url": "/movimientos-inventario/", "label": "Movimientos Inventario", "icon": "fas fa-exchange-alt", "key": "movimientos-inventario"},
            {"url": "/proveedores/", "label": "Proveedores", "icon": "fas fa-truck", "key": "proveedores"},
            {"url": "/reportes/", "label": "Reportes", "icon": "fas fa-chart-bar", "key": "reportes"},
        ]
        
        facturacion_items = [
            {"url": "/clientes/", "label": "Clientes", "icon": "fas fa-users", "key": "clientes"},
            {"url": "/ventas/", "label": "Ventas", "icon": "fas fa-shopping-cart", "key": "ventas"},
            {"url": "/items-venta/", "label": "Detalles de Venta", "icon": "fas fa-receipt", "key": "items-venta"},
            {"url": "/compras/", "label": "Compras", "icon": "fas fa-shopping-bag", "key": "compras"},
            {"url": "/detalle-compras/", "label": "Detalle Compras", "icon": "fas fa-file-invoice", "key": "detalle-compras"},
        ]
        
        fiscal_items = [
            {"url": "/fiscal/reportes/declaracion-iva/", "label": "Declaración IVA (300)", "icon": "fas fa-file-invoice-dollar", "key": "declaracion_iva"},
            {"url": "/fiscal/reportes/declaracion-retefuente/", "label": "Retención Fte (350)", "icon": "fas fa-hand-holding-usd", "key": "declaracion_retefuente"},
            {"url": "/fiscal/reportes/libro-diario/", "label": "Libro Diario", "icon": "fas fa-book", "key": "libro_diario"},
            {"url": "/fiscal/reportes/balance-prueba/", "label": "Balance de Prueba", "icon": "fas fa-balance-scale", "key": "balance_prueba"},
        ]
        
        sistema_items = [
            {"url": "/roles/", "label": "Roles", "icon": "fas fa-user-tag", "key": "roles"},
            {"url": "/chatbot/", "label": "Chatbot IA", "icon": "fas fa-robot", "key": "chatbot"},
            {"url": "/configuracion/", "label": "Configuración", "icon": "fas fa-cog", "key": "configuracion"},
            {"url": "/documentacion/", "label": "Documentación", "icon": "fas fa-book", "key": "documentacion"},
        ]
        
        def generate_menu_html(items):
            """Genera el HTML para un grupo de items del menú"""
            menu_html = ""
            for item in items:
                active_class = 'class="active"' if item["key"] == active_page else ""
                menu_html += f'<li><a href="{item["url"]}" {active_class} data-tooltip="{item["label"]}"><i class="{item["icon"]}"></i> <span>{item["label"]}</span></a></li>\n'
            return menu_html
        
        inventario_html = generate_menu_html(inventario_items)
        facturacion_html = generate_menu_html(facturacion_items)
        fiscal_html = generate_menu_html(fiscal_items)
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

            <!-- Sección Fiscal -->
            <div class="sidebar-section" data-section="fiscal">
                <div class="sidebar-section-header">
                    <div class="section-title">
                        <i class="fas fa-balance-scale"></i>
                        <span>Obligaciones Fiscales</span>
                    </div>
                    <button class="section-toggle" data-section="fiscal" aria-label="Toggle Fiscal">
                        <i class="fas fa-chevron-down"></i>
                    </button>
                </div>
                <ul class="sidebar-menu" data-section="fiscal">
                    {fiscal_html}
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
            <script src="/static/js/main.js?v=2"></script>
            <script src="/static/js/form-validator.js?v=1"></script>
            <script src="/static/js/sidebar.js"></script>
            <script src="/static/js/sidebar-sections.js"></script>
            <script>
                // Pasar estado del usuario y token CSRF al JavaScript
                // activo=1 -> true (puede modificar), activo=0 -> false (no puede modificar)
                window.userActive = {('true' if user.is_active else 'false')};
                window.csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '';
            </script>
            <script src="/static/js/protection.js"></script>
            {chatbot_script}
        </body>
        </html>
        """
