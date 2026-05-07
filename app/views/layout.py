# -*- coding: utf-8 -*-
class Layout:
    """Layouts y componentes compartidos"""

    @staticmethod
    def get_styles():
        """Carga los estilos CSS desde archivo externo"""
        return """
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
        <link rel="stylesheet" href="/static/css/main.css?v=3.0">
        <link rel="stylesheet" href="/static/css/forms.css">
        <link rel="stylesheet" href="/static/css/dashboard.css">
        <link rel="stylesheet" href="/static/css/swal.css">
        <link rel="stylesheet" href="/static/css/chatbot.css">
        <link rel="stylesheet" href="/static/css/stock_alerts.css">
        <link rel="stylesheet" href="/static/css/responsive.css?v=8.0">
        <link rel="stylesheet" href="/static/css/theme-professional-neutral.css?v=16.0">
        <script src='https://cdn.jsdelivr.net/npm/sweetalert2@11'></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
        """

    @staticmethod
    def navbar(user, active_page=""):
        """Componente de Navbar (Estilo Facebook)"""
        # Determinar clases activas para el menu central
        active_dash = "active" if active_page == "dashboard" else ""
        active_prod = "active" if active_page == "productos" else ""
        active_sale = "active" if active_page == "ventas" else ""
        active_bot = "active" if active_page == "chatbot" else ""

        return f"""
        <div class="navbar">
            <div class="navbar-content">
                <!-- Izquierda: Brand -->
                <div class="navbar-left">
                    <button class="hamburger-menu" id="sidebarToggle" aria-label="Menu">
                        <i class="fas fa-bars"></i>
                    </button>
                    <div class="navbar-brand">
                        <h1>HUB DE GESTI&Oacute;N</h1>
                    </div>
                </div>

                <!-- Centro: Navegación Rápida -->
                <div class="navbar-center mobile-hidden">
                    <a href="/" class="nav-item-central {active_dash}" title="Dashboard">
                        <i class="fas fa-home"></i>
                    </a>
                    <a href="/productos/" class="nav-item-central {active_prod}" title="Productos">
                        <i class="fas fa-box"></i>
                    </a>
                    <a href="/ventas/" class="nav-item-central {active_sale}" title="Ventas">
                        <i class="fas fa-shopping-cart"></i>
                    </a>
                    <a href="/chatbot/" class="nav-item-central {active_bot}" title="Asistente IA">
                        <i class="fas fa-robot"></i>
                    </a>
                </div>

                <!-- Derecha: Acciones y Usuario (Estilo iOS) -->
                <div class="navbar-right">
                    {f'''
                    <a href="https://wa.me/{user.phone_number.replace("+", "").replace(" ", "")}" class="btn-whatsapp" title="Seguimiento WhatsApp" id="whatsapp-track-btn" target="_blank">
                        <i class="fab fa-whatsapp"></i>
                    </a>
                    ''' if hasattr(user, "phone_number") and user.phone_number else '''
                    <a href="/configuracion/" class="btn-whatsapp" title="Configurar WhatsApp" target="_self">
                        <i class="fab fa-whatsapp"></i>
                    </a>
                    '''}

                    <a href="/configuracion/" class="user-profile-pill" title="Mi Perfil">
                        <i class="fas fa-user-circle"></i>
                        <span class="mobile-hidden">{user.username}</span>
                    </a>

                    <a href="/logout/" class="navbar-icon-btn" title="Cerrar Sesi&oacute;n">
                        <i class="fas fa-right-from-bracket"></i>
                    </a>
                </div>
            </div>
        </div>
        """

    @staticmethod
    def sidebar(active_page=""):
        """Componente de Sidebar con secciones colapsables (Sincronizado con base.html)"""

        # Categorizacion de items del menu
        inventario_items = [
            {"url": "/", "label": "Dashboard", "icon": "fas fa-home", "key": "dashboard"},
            {"url": "/productos/", "label": "Productos", "icon": "fas fa-box", "key": "productos"},
            {"url": "/categorias/", "label": "Categor&iacute;as", "icon": "fas fa-tags", "key": "categorias"},
            {"url": "/almacenes/", "label": "Almacenes", "icon": "fas fa-warehouse", "key": "almacenes"},
            {
                "url": "/movimientos-inventario/",
                "label": "Movimientos Inventario",
                "icon": "fas fa-exchange-alt",
                "key": "movimientos-inventario",
            },
            {"url": "/proveedores/", "label": "Proveedores", "icon": "fas fa-truck", "key": "proveedores"},
            {"url": "/reportes/", "label": "Reportes", "icon": "fas fa-chart-bar", "key": "reportes"},
        ]

        facturacion_items = [
            {"url": "/clientes/", "label": "Clientes", "icon": "fas fa-users", "key": "clientes"},
            {"url": "/ventas/", "label": "Ventas", "icon": "fas fa-shopping-cart", "key": "ventas"},
            {"url": "/items-venta/", "label": "Detalles de Venta", "icon": "fas fa-receipt", "key": "items-venta"},
            {"url": "/compras/", "label": "Compras", "icon": "fas fa-shopping-bag", "key": "compras"},
            {
                "url": "/detalle-compras/",
                "label": "Detalle Compras",
                "icon": "fas fa-file-invoice",
                "key": "detalle-compras",
            },
        ]

        fiscal_items = [
            {
                "url": "/fiscal/reportes/declaracion-iva/",
                "label": "Declaraci&oacute;n IVA (300)",
                "icon": "fas fa-file-invoice-dollar",
                "key": "declaracion_iva",
            },
            {
                "url": "/fiscal/reportes/declaracion-retefuente/",
                "label": "Retenci&oacute;n Fte (350)",
                "icon": "fas fa-hand-holding-usd",
                "key": "declaracion_retefuente",
            },
            {
                "url": "/fiscal/reportes/libro-diario/",
                "label": "Libro Diario",
                "icon": "fas fa-book",
                "key": "libro_diario",
            },
            {
                "url": "/fiscal/reportes/balance-prueba/",
                "label": "Balance de Prueba",
                "icon": "fas fa-balance-scale",
                "key": "balance_prueba",
            },
        ]

        sistema_items = [
            {"url": "/roles/", "label": "Roles", "icon": "fas fa-user-tag", "key": "roles"},
            {"url": "/chatbot/", "label": "Chatbot IA", "icon": "fas fa-robot", "key": "chatbot"},
            {"url": "/analytics/", "label": "Analytics IA", "icon": "fas fa-brain", "key": "analytics"},
            {"url": "/configuracion/", "label": "Configuraci&oacute;n", "icon": "fas fa-cog", "key": "configuracion"},
            {"url": "/documentacion/", "label": "Documentaci&oacute;n", "icon": "fas fa-book", "key": "documentacion"},
        ]

        def generate_menu_html(items):
            """Genera el HTML para un grupo de items del menu"""
            menu_html = ""
            for item in items:
                is_active = False
                if active_page == item["key"]:
                    is_active = True

                active_class = 'class="active"' if is_active else ""
                menu_html += f'<li><a href="{item["url"]}" {active_class} data-tooltip="{item["label"]}"><i class="{item["icon"]}"></i> <span>{item["label"]}</span></a></li>\n'
            return menu_html

        inventario_html = generate_menu_html(inventario_items)
        facturacion_html = generate_menu_html(facturacion_items)
        fiscal_html = generate_menu_html(fiscal_items)
        sistema_html = generate_menu_html(sistema_items)

        return f"""

        <div class="sidebar" id="sidebar">

            <!-- Seccion Inventario -->
            <div class="sidebar-section" data-section="inventario">
                <div class="sidebar-section-header">
                    <div class="section-title">
                        <i class="fas fa-boxes"></i>
                        <span>Inventario</span>
                    </div>
                    <div class="section-toggle"><i class="fas fa-chevron-down"></i></div>
                </div>
                <ul class="sidebar-menu" data-section="inventario">
                    {inventario_html}
                </ul>
            </div>

            <!-- Seccion Facturacion -->
            <div class="sidebar-section" data-section="facturacion">
                <div class="sidebar-section-header">
                    <div class="section-title">
                        <i class="fas fa-file-invoice-dollar"></i>
                        <span>Facturaci&oacute;n</span>
                    </div>
                    <div class="section-toggle"><i class="fas fa-chevron-down"></i></div>
                </div>
                <ul class="sidebar-menu" data-section="facturacion">
                    {facturacion_html}
                </ul>
            </div>

            <!-- Seccion Fiscal -->
            <div class="sidebar-section" data-section="fiscal">
                <div class="sidebar-section-header">
                    <div class="section-title">
                        <i class="fas fa-balance-scale"></i>
                        <span>Obligaciones Fiscales</span>
                    </div>
                    <div class="section-toggle"><i class="fas fa-chevron-down"></i></div>
                </div>
                <ul class="sidebar-menu" data-section="fiscal">
                    {fiscal_html}
                </ul>
            </div>

            <!-- Seccion Sistema -->
            <div class="sidebar-section" data-section="sistema">
                <div class="sidebar-section-header">
                    <div class="section-title">
                        <i class="fas fa-cog"></i>
                        <span>Sistema</span>
                    </div>
                    <div class="section-toggle"><i class="fas fa-chevron-down"></i></div>
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
        navbar = Layout.navbar(user, active_page)
        sidebar = Layout.sidebar(active_page)

        chatbot_script = ""
        if active_page == "chatbot":
            chatbot_script = '<script src="/static/js/chatbot.js"></script>'

        # Build chatbot widget HTML outside the f-string to avoid nested triple-quote issues
        chatbot_widget = ""
        chatbot_js_tag = ""
        if active_page != "chatbot":
            chatbot_js_tag = '<script src="/static/js/chatbot.js"></script>'
            chatbot_widget = """
            <div id="chatbot-widget-container" style="z-index: 9999;">
                <button id="chatbot-fab" class="chatbot-fab" title="Asistente IA">
                    <i class="fas fa-robot"></i>
                </button>
                <div id="chatbot-widget-window" class="chatbot-widget-window">
                    <div class="chatbot-header chatbot-widget-header">
                        <h3><i class="fas fa-robot"></i> Asistente IA</h3>
                        <button id="chatbot-minimize" class="chatbot-widget-close"><i class="fas fa-times"></i></button>
                    </div>
                    <div id="chat-messages" class="chat-messages">
                        <!-- Messages go here -->
                        <div class="message bot-message">
                            <div class="message-content">
                                <div class="message-text">Hola, soy tu asistente virtual. &iquest;En qu&eacute; puedo ayudarte hoy?</div>
                            </div>
                        </div>
                    </div>
                    <div class="chat-input-container">
                        <textarea id="message-input" class="form-control" placeholder="Escribe tu consulta..." rows="1" style="resize: none;"></textarea>
                        <button id="voice-input-btn" class="btn btn-secondary" style="border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; margin-right: 5px;"><i class="fas fa-microphone"></i></button>
                        <button id="send-btn" class="btn btn-primary" style="border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;"><i class="fas fa-paper-plane"></i></button>
                    </div>
                </div>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title} - HUB DE GESTI&Oacute;N</title>
            <link rel="icon" type="image/png" href="https://cdn-icons-png.flaticon.com/512/2897/2897785.png">
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
            <script src="/static/js/sidebar-mobile.js"></script>
            <script src="/static/js/stock_alerts.js"></script>
            <script src="/static/js/kpi_charts.js"></script>
            <script>
                window.userActive = {('true' if user.is_active else 'false')};
                window.csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '';
                document.body.classList.add('theme-professional');
            </script>
            <script src="/static/js/protection.js"></script>
            {chatbot_script}
            {chatbot_js_tag}
            {chatbot_widget}
        </body>
        </html>
        """
