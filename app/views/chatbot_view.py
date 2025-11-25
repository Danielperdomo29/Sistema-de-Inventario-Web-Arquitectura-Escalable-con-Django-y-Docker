from django.http import HttpResponse
from app.views.layout import Layout

class ChatbotView:
    """Vista del Chatbot con IA"""
    
    @staticmethod
    def render(user, history):
        """Renderiza la interfaz del chatbot"""
        
        # Construir mensajes del historial
        history_html = ""
        if history:
            for msg in history:
                history_html += f"""
                <div class='message user-message'>
                    <div class='message-content'>
                        <i class='fas fa-user message-icon'></i>
                        <div class='message-text'>{msg['message']}</div>
                    </div>
                    <div class='message-time'>{msg['created_at']}</div>
                </div>
                <div class='message bot-message'>
                    <div class='message-content'>
                        <i class='fas fa-robot message-icon'></i>
                        <div class='message-text'>{msg['response'].replace('•', '').replace('-', '').replace('•', '')}</div>
                    </div>
                    <div class='message-time'>{msg['created_at']}</div>
                </div>
                """
        else:
            history_html = """
            <div class='welcome-message'>
                <i class='fas fa-robot welcome-icon'></i>
                <h3>¡Bienvenido al Asistente Virtual!</h3>
                <p>Soy tu asistente de inventario con inteligencia artificial.</p>
                <p>Puedo ayudarte con consultas sobre productos, ventas, compras y más.</p>
                <p>Escribe <strong>\"ayuda\"</strong> para ver qué puedo hacer.</p>
            </div>
            <div id='help-list' class='help-list'>
                <h4><i class='fas fa-question-circle'></i> ¿En qué puedo ayudarte?</h4>
                <ul class='list-group'>
                    <li class='list-group-item'>
                        <label><input type='checkbox' class='help-checkbox' value='consulta sobre productos'> Consulta sobre productos</label>
                    </li>
                    <li class='list-group-item'>
                        <label><input type='checkbox' class='help-checkbox' value='¿Qué productos tienen stock bajo?'> Productos con stock bajo</label>
                    </li>
                    <li class='list-group-item'>
                        <label><input type='checkbox' class='help-checkbox' value='Resumen de ventas'> Resumen de ventas</label>
                    </li>
                    <li class='list-group-item'>
                        <label><input type='checkbox' class='help-checkbox' value='Resumen de compras'> Resumen de compras</label>
                    </li>
                </ul>
            </div>
        """
        content = f"""
        <div class='card'>
            <div class='card-header'>
                <span><i class='fas fa-robot'></i> Asistente Virtual con IA</span>
                <button class='btn btn-secondary' id='clear-history-btn'>
                    <i class='fas fa-trash'></i> Limpiar Historial
                </button>
            </div>
            <div class='card-body chatbot-container'>
                <div id='chat-messages' class='chat-messages'>
                    {history_html}
                </div>
                <div id='typing-indicator' style='display:none;align-items:center;gap:8px;margin:10px 0;'>
                    <span class='spinner-border spinner-border-sm text-primary'></span>
                    <span>El asistente está escribiendo...</span>
                </div>
                <div class='chat-input-container'>
                    <div class='chat-input-wrapper'>
                        <textarea id='message-input' class='chat-input' rows='1' placeholder='Escribe tu mensaje...'></textarea>
                        <button id='send-btn' class='send-btn'><i class='fas fa-paper-plane'></i></button>
                    </div>
                    <div class='chat-suggestions'>
                        <button class='suggestion-btn' data-message='ayuda'>Ayuda</button>
                        <button class='suggestion-btn' data-message='¿Qué productos tienen stock bajo?'>Stock bajo</button>
                        <button class='suggestion-btn' data-message='Resumen de ventas'>Resumen de ventas</button>
                        <button class='suggestion-btn' data-message='Resumen de compras'>Resumen de compras</button>
                    </div>
                </div>
            </div>
        </div>
        <script src='/static/js/chatbot.js'></script>
        """
        html = Layout.render(
            title="Chatbot IA",
            user=user,
            active_page="chatbot",
            content=content
        )
        return HttpResponse(html)
