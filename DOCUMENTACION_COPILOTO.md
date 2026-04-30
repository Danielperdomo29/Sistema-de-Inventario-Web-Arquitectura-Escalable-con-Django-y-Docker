# Arquitectura Copiloto ERP: Tool Calling y Resolución de Entidades

Este documento resume la evolución del módulo de IA (Chatbot) hacia un **Copiloto Operativo** capaz de ejecutar acciones transaccionales reales en la base de datos (Ej: crear facturas, descontar stock) de forma segura y robusta.

## 1. Arquitectura de Servicios
El monolito original del chatbot fue refactorizado en componentes modulares:

*   **`ChatbotController`**: Orquestador principal. Ahora solo intercepta la solicitud HTTP, llama a los servicios, maneja la validación de seguridad y responde.
*   **`IntentService`**: Clasifica la intención del usuario para inyectar solo las herramientas que apliquen.
*   **`MetricsService`**: Agrega datos estadísticos (sin exponer registros confidenciales) para darle "conocimiento" de la empresa a la IA en tiempo real (Zero-Trust context).
*   **`PromptBuilder`**: Centraliza la construcción del `system prompt`, las instrucciones de confirmación y el contexto inyectado.
*   **`OpenRouterService`**: Maneja la comunicación con LLMs y soporta la inyección de `tools` (Herramientas), identificando automáticamente cuando el modelo responde con `tool_calls`.

## 2. Implementación de Tool Calling (Ejecución de Acciones)
La IA ya no solo conversa; puede solicitar la ejecución de métodos internos.

*   **`tools_definitions.py`**: Define el esquema JSON para que la IA sepa qué parámetros enviar. Se configuró para que la IA envíe **nombres en lenguaje natural** (`cliente_nombre`, `producto_nombre`) en lugar de IDs, lo cual previene alucinaciones.
*   **`ToolRouter`**: Actúa como la capa de ejecución (sandbox). Recibe la petición del LLM, valida los permisos, y ejecuta la acción real contra el ORM de Django (ej: `Sale.create()`).

## 3. Resolución de Entidades (NLP + Base de Datos)
El problema principal de los LLMs es mapear texto impreciso ("daniel", "test") a llaves foráneas en BD. Esto se solucionó con el **Entity Resolver**:

*   **`entity_resolver.py`**: Un motor híbrido que busca la entidad en la base de datos (filtrando productos inactivos/eliminados).
    1.  Aplica **Substring Matching**: Si la IA envía "daniel", el resolver busca si ese string existe dentro de "Daniel Perdomo Carvajal". Si coincide, lo enlaza al ID 5.
    2.  Aplica **Fuzzy Matching (`difflib`)**: Si hay errores ortográficos ("danel"), busca la coincidencia más aproximada matemáticamente.
*   **`tool_argument_enricher.py`**: Intercepta los argumentos JSON del LLM *antes* de que lleguen al `ToolRouter` y reemplaza los nombres por los IDs exactos de la Base de Datos.

## 4. Validaciones de Seguridad y Lógica de Negocio
Se integraron múltiples candados empresariales:

*   **Zero-Trust Prompting**: El LLM tiene estrictamente prohibido ejecutar alteraciones sin confirmación humana explícita.
*   **Confirmación de Doble Vía**: El `ChatbotController` tiene hardcodeada una lista de `CRITICAL_TOOLS` (ej: `crear_factura`). Si la IA intenta dispararla, el sistema aborta y pide confirmación humana al usuario (botón "Sí").
*   **Control de Stock**: Dentro del `ToolRouter`, antes de guardar la factura, se revisa que `p.stock_actual > 0` y que `p.stock_actual >= cantidad_solicitada`. Si falla, devuelve el error exacto a la IA para que notifique al humano.
*   **Descuento de Inventario**: Al llamar a `Sale.create()`, el detalle de la factura levanta un Signal nativo de Django (`app/signals/stock_signals.py`) que debita el inventario de forma segura y consistente.

## 5. Historial Continuo (Frontend)
El Widget del frontend se actualizó (`chatbot.js`) añadiendo:
*   Carga silenciosa asíncrona de todo el historial (`/chatbot/history/`) cada vez que el usuario navega entre módulos. Esto garantiza la persistencia del chat.
*   Botón para limpiar historial directamente en la cabecera (Trash Icon).
