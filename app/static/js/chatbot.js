/**
 * Chatbot IA - Sistema de Inventario
 * Maneja la comunicación con el backend de IA con notificaciones SweetAlert2
 */

document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const typingIndicator = document.getElementById('typing-indicator'); // Ensure this ID exists in HTML
    const clearHistoryBtn = document.getElementById('clear-history-btn');

    // ============================================================================
    // SISTEMA DE NOTIFICACIONES CON SWEETALERT2
    // ============================================================================

    const Notifications = {
        /**
         * Toast notification - Esquina superior derecha
         */
        toast: (message, icon = 'info', timer = 3000) => {
            const Toast = Swal.mixin({
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: timer,
                timerProgressBar: true,
                didOpen: (toast) => {
                    toast.addEventListener('mouseenter', Swal.stopTimer);
                    toast.addEventListener('mouseleave', Swal.resumeTimer);
                },
                backdrop: false
            });

            Toast.fire({
                icon: icon,
                title: message
            });
        },

        /**
         * Notificación de éxito
         */
        success: (title, message = '') => {
            Swal.fire({
                icon: 'success',
                title: title,
                text: message,
                confirmButtonColor: '#4CAF50',
                timer: 2000,
                showConfirmButton: false
            });
        },

        /**
         * Notificación de error
         */
        error: (title, message = '') => {
            Swal.fire({
                icon: 'error',
                title: title,
                text: message,
                confirmButtonColor: '#f44336',
                confirmButtonText: 'Entendido'
            });
        },

        /**
         * Notificación de advertencia
         */
        warning: (title, message = '') => {
            Swal.fire({
                icon: 'warning',
                title: title,
                text: message,
                confirmButtonColor: '#ff9800',
                confirmButtonText: 'OK'
            });
        },

        /**
         * Cuadro de confirmación
         */
        confirm: async (title, message, confirmText = 'Sí', cancelText = 'No') => {
            const result = await Swal.fire({
                title: title,
                text: message,
                icon: 'question',
                showCancelButton: true,
                confirmButtonColor: '#2196F3',
                cancelButtonColor: '#757575',
                confirmButtonText: confirmText,
                cancelButtonText: cancelText,
                reverseButtons: true
            });
            return result.isConfirmed;
        },

        /**
         * Notificación de información
         */
        info: (title, message = '') => {
            Swal.fire({
                icon: 'info',
                title: title,
                text: message,
                confirmButtonColor: '#2196F3',
                confirmButtonText: 'Entendido'
            });
        },

        /**
         * Loading spinner
         */
        loading: (title = 'Procesando...') => {
            Swal.fire({
                title: title,
                allowOutsideClick: false,
                allowEscapeKey: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });
        },

        /**
         * Cerrar loading
         */
        close: () => {
            Swal.close();
        }
    };

    // ============================================================================
    // FUNCIONES AUXILIARES
    // ============================================================================

    /**
     * Obtener CSRF token
     */
    function getCsrfToken() {
        // Intentar desde cookie primero
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }

        // Fallback a input hidden
        const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfInput) {
            return csrfInput.value;
        }

        return '';
    }

    /**
     * Scroll al final del chat
     */
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    /**
     * Escapar HTML para prevenir XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Agregar mensaje al chat
     */
    function addMessage(text, isUser = false, timestamp = null) {
        const welcomeMessage = chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

        const time = timestamp || new Date().toLocaleTimeString('es-CO', {
            hour: '2-digit',
            minute: '2-digit'
        });

        messageDiv.innerHTML = `
            <div class="message-content">
                <i class="fas ${isUser ? 'fa-user' : 'fa-robot'} message-icon"></i>
                <div class="message-text">${escapeHtml(text)}</div>
            </div>
            <div class="message-time">${time}</div>
        `;

        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    /**
     * Mostrar/ocultar indicador de escritura
     */
    function showTyping(show) {
        if (typingIndicator) {
            typingIndicator.style.display = show ? 'flex' : 'none';
            if (show) scrollToBottom();
        }
    }

    // ============================================================================
    // FUNCIONES PRINCIPALES
    // ============================================================================

    /**
     * Enviar mensaje al servidor
     */
    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) {
            Notifications.toast('Por favor escribe un mensaje', 'warning', 2000);
            return;
        }

        // Deshabilitar input mientras procesa
        messageInput.disabled = true;
        sendBtn.disabled = true;
        messageInput.value = '';

        // Mostrar mensaje del usuario
        addMessage(message, true);
        showTyping(true);

        try {
            const csrfToken = getCsrfToken();

            if (!csrfToken) {
                throw new Error('Token de seguridad no encontrado. Recarga la página.');
            }

            const response = await fetch('/chatbot/send/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({ message: message }),
                credentials: 'same-origin'
            });

            if (!response.ok) {
                // Manejar errores HTTP específicos
                if (response.status === 403) {
                    throw new Error('Error de autenticación. Por favor, recarga la página.');
                } else if (response.status === 401) {
                    Notifications.warning(
                        'Sesión Expirada',
                        'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.'
                    );
                    setTimeout(() => {
                        window.location.href = '/login/';
                    }, 2000);
                    return;
                } else if (response.status === 500) {
                    throw new Error('Error interno del servidor. El equipo técnico ha sido notificado.');
                } else {
                    throw new Error(`Error del servidor (${response.status}). Intenta de nuevo.`);
                }
            }

            const data = await response.json();

            if (data.success) {
                addMessage(data.response, false);
                Notifications.toast('Respuesta recibida', 'success', 1500);
            } else {
                addMessage(`Error: ${data.error || 'Error desconocido'}`, false);
                Notifications.error('Error', data.error || 'No se pudo procesar tu mensaje');
            }
        } catch (error) {
            console.error('Error al enviar mensaje:', error);

            // Mensaje amigable en el chat
            addMessage('⚠️ No se pudo conectar con el asistente. Verifica tu conexión.', false);

            // Notificación de error
            Notifications.error(
                'Error de Conexión',
                error.message || 'Verifica tu internet e intenta de nuevo.'
            );
        } finally {
            showTyping(false);
            messageInput.disabled = false;
            sendBtn.disabled = false;
            messageInput.focus();
        }
    }

    /**
     * Limpiar historial
     */
    async function clearHistory() {
        const confirmed = await Notifications.confirm(
            '¿Limpiar Historial?',
            'Se eliminará toda la conversación. Esta acción no se puede deshacer.',
            'Sí, limpiar',
            'Cancelar'
        );

        if (!confirmed) return;

        Notifications.loading('Limpiando historial...');

        try {
            const csrfToken = getCsrfToken();

            const response = await fetch('/chatbot/clear-history/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                credentials: 'same-origin'
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    chatMessages.innerHTML = `
                        <div class='welcome-message'>
                            <i class='fas fa-robot welcome-icon'></i>
                            <h3>¡Historial limpiado!</h3>
                            <p>Puedes comenzar una nueva conversación.</p>
                        </div>
                    `;

                    Notifications.close();
                    Notifications.success('¡Listo!', 'Historial eliminado correctamente');
                } else {
                    throw new Error(data.error || 'No se pudo limpiar el historial');
                }
            } else {
                throw new Error(`Error del servidor (${response.status})`);
            }
        } catch (error) {
            console.error('Error al limpiar historial:', error);
            Notifications.error(
                'Error',
                error.message || 'No se pudo limpiar el historial. Intenta de nuevo.'
            );
        }
    }

    // ============================================================================
    // EVENT LISTENERS
    // ============================================================================

    sendBtn.addEventListener('click', sendMessage);

    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize del textarea
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 150) + 'px';
    });

    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', clearHistory);
    }

    // Scroll inicial al final
    scrollToBottom();

    // Focus en el input
    // Solo si no estamos en modo widget (o si el widget está abierto por defecto)
    // messageInput.focus(); // Comentado para evitar teclado en móviles al cargar

    // Toast de bienvenida (opcional, solo si no hay historial)
    const hasHistory = chatMessages.querySelector('.message');
    if (!hasHistory) {
        setTimeout(() => {
            Notifications.toast('¡Hola! Soy tu asistente de inventario 🤖', 'info', 4000);
        }, 500);
    }

    // ============================================================================
    // WIDGET TOGGLE LOGIC
    // ============================================================================
    const chatbotFab = document.getElementById('chatbot-fab');
    const chatbotWindow = document.getElementById('chatbot-widget-window');
    const chatbotClose = document.getElementById('chatbot-minimize');

    if (chatbotFab && chatbotWindow) {
        chatbotFab.addEventListener('click', function() {
            chatbotWindow.classList.toggle('active');
            chatbotFab.style.display = chatbotWindow.classList.contains('active') ? 'none' : 'flex';

            if (chatbotWindow.classList.contains('active')) {
                scrollToBottom();
                if (window.innerWidth > 768) {
                     messageInput.focus();
                }
            }
        });

        if (chatbotClose) {
            chatbotClose.addEventListener('click', function() {
                chatbotWindow.classList.remove('active');
                chatbotFab.style.display = 'flex';
            });
        }
    }

    // ============================================================================
    // VOICE INPUT (SPEECH-TO-TEXT)
    // ============================================================================
    const voiceBtn = document.getElementById('voice-input-btn');

    if (voiceBtn && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();

        recognition.continuous = false;
        recognition.lang = 'es-ES';
        recognition.interimResults = false;

        voiceBtn.addEventListener('click', function() {
            if (voiceBtn.classList.contains('listening')) {
                recognition.stop();
            } else {
                recognition.start();
            }
        });

        recognition.onstart = function() {
            voiceBtn.classList.add('listening');
            voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
            voiceBtn.style.backgroundColor = '#ff4757';
            voiceBtn.style.color = 'white';
            Notifications.toast('Escuchando...', 'info', 2000);
        };

        recognition.onend = function() {
            voiceBtn.classList.remove('listening');
            voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
            voiceBtn.style.backgroundColor = ''; // Reset
            voiceBtn.style.color = '';
        };

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            messageInput.value = transcript;
            messageInput.focus();
            // Opcional: Enviar automáticamente
            // sendMessage();
        };

        recognition.onerror = function(event) {
            console.error('Error de reconocimiento de voz:', event.error);
            Notifications.toast('Error al escuchar. Intenta de nuevo.', 'error');
            voiceBtn.classList.remove('listening');
            voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        };
    } else if (voiceBtn) {
        voiceBtn.style.display = 'none'; // Ocultar si no es compatible
    }
});
