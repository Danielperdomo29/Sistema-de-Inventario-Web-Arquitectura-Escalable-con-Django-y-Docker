# 🤖 Chatbot con IA - Sistema de Inventario

## Descripción

Asistente virtual con Inteligencia Artificial integrado al Sistema de Inventario. Utiliza Google Gemini AI para responder preguntas y ayudar con la gestión del inventario mediante lenguaje natural.

## ✨ Características

- 💬 **Chat en tiempo real** con interfaz moderna y responsiva
- 🧠 **Inteligencia Artificial** powered by Google Gemini
- 📊 **Consultas inteligentes** sobre productos, ventas, compras
- 🔍 **Búsqueda de productos** por nombre o descripción
- 📈 **Resúmenes automáticos** de ventas y compras
- 💾 **Historial de conversaciones** guardado por usuario
- 🎯 **Sugerencias rápidas** para consultas comunes

## 🚀 Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements-chatbot.txt
```

O instalar manualmente:

```bash
pip install google-generativeai
```

### 2. Obtener API Key de Google Gemini

1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Inicia sesión con tu cuenta de Google
3. Crea una nueva API Key
4. Copia la key generada

### 3. Configurar la API Key

**Opción A: Variable de entorno (Recomendado)**

```bash
export GEMINI_API_KEY='tu-api-key-aqui'
```

**Opción B: Modificar el código**

Edita `app/services/ai_service.py` línea 14:

```python
api_key = 'tu-api-key-aqui'
```

### 4. Inicializar la base de datos

```bash
python init_chatbot.py
```

Este script creará la tabla `chatbot_messages` necesaria para almacenar el historial.

### 5. Iniciar el servidor

```bash
python main.py
```

### 6. Acceder al chatbot

Abre tu navegador en: `http://localhost:8000/chatbot/`

## 📖 Uso

### Comandos básicos

- **"ayuda"** - Muestra qué puede hacer el chatbot
- **"buscar producto [nombre]"** - Busca productos específicos
- **"resumen de ventas"** - Muestra estadísticas de ventas
- **"resumen de compras"** - Muestra estadísticas de compras
- **"productos con stock bajo"** - Lista productos con poco inventario

### Ejemplos de consultas

```
Usuario: buscar laptop
Bot: Encontré 3 producto(s):
     • Laptop Dell XPS 15
       - Stock: 5 unidades
       - Precio: $1299.99
       ...

Usuario: ¿cuánto he vendido hoy?
Bot: Resumen de Ventas:
     • Total de ventas: 15
     • Monto total: $5,432.50
     ...

Usuario: ¿cómo registro una nueva venta?
Bot: Para registrar una nueva venta:
     1. Ve a la sección "Ventas" en el menú lateral
     2. Haz clic en "Crear Nueva Venta"
     ...
```

## 🏗️ Arquitectura

### Estructura de archivos

```
app/
├── controllers/
│   └── chatbot_controller.py      # Endpoints del chatbot
├── models/
│   └── chatbot_message.py         # Modelo de mensajes
├── services/
│   └── ai_service.py              # Servicio de IA con Gemini
├── views/
│   └── chatbot_view.py            # Vista HTML del chatbot
└── static/
    ├── css/
    │   └── chatbot.css            # Estilos del chat
    └── js/
        └── chatbot.js             # Lógica del frontend
```

### Rutas disponibles

- `GET /chatbot/` - Interfaz del chatbot
- `POST /chatbot/send/` - Enviar mensaje
- `POST /chatbot/clear-history/` - Limpiar historial
- `GET /chatbot/history/` - Obtener historial

## 🎨 Personalización

### Modificar respuestas de la IA

Edita `app/services/ai_service.py`:

```python
def process_query(self, user_message, user_id):
    # Personaliza el prompt aquí
    prompt = f"""
    Tu personalización aquí...
    """
```

### Cambiar estilos

Modifica `app/static/css/chatbot.css` para ajustar:
- Colores del tema
- Tamaño de fuentes
- Animaciones
- Layout responsive

### Agregar nuevas funcionalidades

En `app/services/ai_service.py`, agrega nuevos métodos:

```python
def tu_nueva_funcion(self):
    # Tu lógica aquí
    pass
```

## 🔒 Seguridad

- ✅ Autenticación requerida para acceder al chatbot
- ✅ Mensajes asociados al usuario autenticado
- ✅ API Key no expuesta en el frontend
- ✅ Validación de inputs del usuario
- ✅ Manejo de errores y excepciones

## 📊 Base de Datos

### Tabla: chatbot_messages

| Campo      | Tipo      | Descripción                    |
|------------|-----------|--------------------------------|
| id         | INTEGER   | ID único del mensaje           |
| user_id    | INTEGER   | ID del usuario (FK)            |
| message    | TEXT      | Mensaje enviado por el usuario |
| response   | TEXT      | Respuesta generada por la IA   |
| created_at | TIMESTAMP | Fecha y hora del mensaje       |

## 🐛 Solución de problemas

### Error: "Module 'google.generativeai' not found"

```bash
pip install google-generativeai
```

### Error: "API key not valid"

Verifica que:
1. Tu API key sea correcta
2. La variable de entorno esté configurada
3. La API de Gemini esté habilitada en tu cuenta de Google

### El chatbot no responde

1. Verifica la conexión a internet
2. Revisa los logs del servidor
3. Confirma que la tabla `chatbot_messages` existe
4. Verifica que el usuario esté autenticado

### Problemas de estilo

1. Limpia la caché del navegador (Ctrl + F5)
2. Verifica que `chatbot.css` esté cargando
3. Revisa la consola del navegador por errores

## 🔄 Actualización

Para actualizar a una nueva versión:

```bash
# Actualizar dependencias
pip install -U google-generativeai

# Actualizar base de datos si es necesario
python init_chatbot.py
```

## 📝 Notas

- El chatbot utiliza **Google Gemini Pro** (gratuito con límites)
- El historial se guarda en la base de datos local
- Las respuestas son generadas en tiempo real
- Se puede cambiar a otra IA (OpenAI, Claude, etc.) modificando `ai_service.py`

## 🤝 Contribuir

Para agregar nuevas funcionalidades:

1. Crea una nueva función en `AIService`
2. Agrega el endpoint en `ChatbotController`
3. Actualiza la documentación
4. Prueba exhaustivamente

## 📄 Licencia

Parte del Sistema de Inventario - Todos los derechos reservados

---

**¿Necesitas ayuda?** Escribe "ayuda" en el chatbot o consulta la documentación del sistema.
