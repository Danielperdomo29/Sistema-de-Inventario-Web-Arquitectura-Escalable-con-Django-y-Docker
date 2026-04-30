import json
import logging
import re

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from app.models.chatbot_message import ChatbotMessage
from app.services.ai.intent_service import IntentService
from app.services.ai.prompt_builder import PromptBuilder
from app.services.ai.tool_argument_enricher import ToolArgumentEnricher
from app.services.ai.tool_router import ToolRouter

# Importar arquitectura de servicios
from app.services.metrics_service import MetricsService
from app.services.openrouter_service import get_ai_service
from app.views.chatbot_view import ChatbotView


def has_tool_call(response):
    """Verifica de forma segura si la respuesta del LLM contiene un llamado a función"""
    return isinstance(response, dict) and response.get("tool_calls") and len(response["tool_calls"]) > 0


def safe_parse_arguments(tool_call):
    """Extrae de forma segura los argumentos del JSON devuelto por la IA"""
    try:
        args = json.loads(tool_call["function"]["arguments"])
        if not isinstance(args, dict):
            return None
        return args
    except Exception:
        return None


class ChatbotController:
    """
    Controlador del chatbot con IA. Actúa como orquestador puro (Copiloto Operativo).
    """

    MAX_SESSION_TURNS = 4
    MAX_RESPONSE_TOKENS = 350
    TEMPERATURE = 0.3

    # Herramientas que requieren confirmación explícita del usuario
    CRITICAL_TOOLS = ["crear_factura"]

    @staticmethod
    @ensure_csrf_cookie
    def index(request):
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user
        history = ChatbotMessage.get_history(user.id, limit=20)
        return HttpResponse(ChatbotView.render(user, history, request))

    @staticmethod
    @ensure_csrf_cookie
    def send_message(request):
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "error": "No autenticado"}, status=401)

        if request.method != "POST":
            return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)

        try:
            payload = json.loads(request.body.decode("utf-8"))
            user_message = (payload.get("message") or "").strip()

            if not user_message:
                return JsonResponse({"success": False, "error": "Mensaje vacío"}, status=400)

            user_id = request.user.id

            # 1. Obtener contexto de sesión
            session_context = request.session.get("chatbot_context", [])

            # 2. Servicios - Delegación total de lógica
            metrics = MetricsService.get_metrics()
            intent = IntentService.detect(user_message)

            messages = PromptBuilder.build(
                user_message=user_message, metrics=metrics, intent=intent, context=session_context
            )

            # 3. IA - Llamada principal con Tools
            ai = get_ai_service()
            try:
                ai_response_dict = ai.chat_with_tools(
                    messages=messages,
                    max_tokens=ChatbotController.MAX_RESPONSE_TOKENS,
                    temperature=ChatbotController.TEMPERATURE,
                )
            except Exception as ai_err:
                logging.error(f"Error AI Service en Chatbot: {ai_err}", exc_info=True)
                raw_response = "Lo siento, mi conexión inteligente está intermitente. Inténtalo de nuevo."
                return ChatbotController._finalize_response(
                    request, user_id, user_message, raw_response, intent, session_context
                )

            # 4. Procesamiento de Tool Calling (Ejecución de acciones)
            if has_tool_call(ai_response_dict):
                tool_call = ai_response_dict["tool_calls"][0]
                tool_name = tool_call["function"]["name"]

                # Parsear de forma segura
                arguments = safe_parse_arguments(tool_call)
                if arguments is None:
                    raw_response = "No pude procesar los datos para ejecutar la acción."
                    return ChatbotController._finalize_response(
                        request, user_id, user_message, raw_response, intent, session_context
                    )

                # 🔥 ENRIQUECER CON NLP (Entity Resolution)
                arguments = ToolArgumentEnricher.enrich(tool_name, arguments, user_message)

                # 🔥 CONFIRMACIÓN DE ACCIONES CRÍTICAS
                if tool_name in ChatbotController.CRITICAL_TOOLS and not arguments.get("confirmado"):
                    # Ver si el usuario ya dijo "sí" en el mensaje actual como confirmación
                    # de un prompt anterior (lógica simplificada para el demo)
                    if user_message.lower() in ["si", "sí", "confirmar", "ok", "hazlo"]:
                        arguments["confirmado"] = True
                    else:
                        # Retornar pidiendo confirmación
                        raw_response = (
                            f"¿Confirmas que deseas ejecutar la acción '{tool_name}' "
                            f"con estos datos? Responde 'sí' para continuar."
                        )
                        return ChatbotController._finalize_response(
                            request, user_id, user_message, raw_response, intent, session_context
                        )

                # Validación mínima post-enriquecimiento (Removido para delegar al ToolRouter)

                # Ejecutar acción real en el negocio
                result = ToolRouter.execute(tool_name, arguments, request.user)

                # Segunda llamada a IA con resultado
                messages.append(ai_response_dict)
                messages.append(
                    {
                        "role": "tool",
                        "name": tool_name,
                        "content": json.dumps(result),
                        "tool_call_id": tool_call.get("id", "call_01"),
                    }
                )

                try:
                    # La IA formula la respuesta final al usuario
                    raw_response = ai.chat(messages, temperature=ChatbotController.TEMPERATURE)
                except Exception as ai_err:
                    logging.error(f"Error AI Service Tool Callback: {ai_err}")
                    raw_response = f"Acción '{tool_name}' ejecutada, pero no pude generar la confirmación final."
            else:
                # Flujo normal sin tools
                if isinstance(ai_response_dict, dict) and "content" in ai_response_dict:
                    raw_response = ai_response_dict["content"]
                else:
                    raw_response = str(ai_response_dict)

            return ChatbotController._finalize_response(
                request, user_id, user_message, raw_response, intent, session_context
            )

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Formato de mensaje inválido"}, status=400)
        except Exception as e:
            logging.error(f"ChatbotController Critical Error: {str(e)}", exc_info=True)
            return JsonResponse({"success": False, "error": "Error interno del servidor."}, status=500)

    @staticmethod
    def _finalize_response(request, user_id, user_message, raw_response, intent, session_context):
        """Helper para sanitizar y guardar el mensaje antes de devolverlo al frontend"""
        response = ChatbotController._sanitize_response(raw_response)

        # Guardar memoria corta en sesión
        session_context.append({"message": user_message, "response": response})
        request.session["chatbot_context"] = session_context[-ChatbotController.MAX_SESSION_TURNS :]

        # Guardar historial persistente
        ChatbotMessage.save_message(user_id, user_message, response)

        return JsonResponse({"success": True, "message": user_message, "response": response, "intent": intent})

    @staticmethod
    @ensure_csrf_cookie
    def clear_history(request):
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "error": "No autenticado"}, status=401)

        if request.method != "POST":
            return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)

        try:
            ChatbotMessage.delete_history(request.user.id)
            request.session["chatbot_context"] = []
            return JsonResponse({"success": True, "message": "Historial y contexto eliminados"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    @staticmethod
    def get_history(request):
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "error": "No autenticado"}, status=401)

        try:
            history = ChatbotMessage.get_history(request.user.id, limit=50)
            return JsonResponse({"success": True, "history": history})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    @staticmethod
    def _sanitize_response(text: str) -> str:
        if not text:
            return "No pude generar una respuesta en este momento."

        # Quitar frases meta o explicaciones indeseadas
        patterns = [
            r"Este comportamiento es muy común.*?(?:\n|$)",
            r"No se considera un error.*?(?:\n|$)",
            r"Como IA.*?(?:\n|$)",
            r"Soy un modelo de lenguaje.*?(?:\n|$)",
        ]

        clean = text.strip()
        for pattern in patterns:
            clean = re.sub(pattern, "", clean, flags=re.IGNORECASE | re.DOTALL)

        # Limitar a dos párrafos
        paragraphs = [p.strip() for p in clean.split("\n\n") if p.strip()]
        clean = "\n\n".join(paragraphs[:2])

        return clean.strip() or "No pude generar una respuesta útil en este momento."
