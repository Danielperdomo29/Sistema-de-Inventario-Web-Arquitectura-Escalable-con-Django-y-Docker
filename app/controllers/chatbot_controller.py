import json
from datetime import date

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from app.models.chatbot_message import ChatbotMessage
from app.models.user import User
from app.views.chatbot_view import ChatbotView


class ChatbotController:
    """Controlador del Chatbot con IA y memoria contextual"""

    @staticmethod
    @ensure_csrf_cookie
    def index(request):
        """Muestra la interfaz del chatbot"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        user = request.user
        user_id = user.id

        history = ChatbotMessage.get_history(user_id, limit=20)
        return HttpResponse(ChatbotView.render(user, history, request))

    @staticmethod
    @ensure_csrf_cookie
    def send_message(request):
        """Procesa mensaje con memoria contextual (últimas 3 interacciones)"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "error": "No autenticado"}, status=401)

        user_id = request.user.id
        if request.method != "POST":
            return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)

        try:
            body = json.loads(request.body.decode("utf-8"))
            user_message = body.get("message", "").strip()
            if not user_message:
                return JsonResponse({"success": False, "error": "Mensaje vacío"}, status=400)

            # Obtener contexto de sesión (últimas 3 interacciones)
            context = request.session.get("chatbot_context", [])

            # Importar modelos
            from app.models.client import Client
            from app.models.product import Product
            from app.models.purchase import Purchase
            from app.models.sale import Sale
            from app.models.warehouse import Warehouse

            msg_lower = user_message.lower()
            response = None
            intent = None  # Para guardar en contexto

            # Sistema de detección con PRIORIDAD (específico → genérico)

            # AYUDA
            if any(word in msg_lower for word in ["ayuda", "help", "comandos", "que puedes", "qué puedes"]):
                intent = "ayuda"
                response = "🤖 **Asistente HUB DE GESTIÓN**\n\nPuedo responderte:\n\n💰 Ventas: 'ventas de hoy'\n📦 Productos: 'cuántos productos'\n📊 Stock: 'stock bajo'\n👥 Clientes: 'total clientes'\n🏢 Almacenes: 'cuántos almacenes'\n🛒 Compras: 'resumen compras'\n\n¡Pregunta lo que necesites!"

            # CLIENTES (antes que genéricos)
            elif any(word in msg_lower for word in ["cliente", "comprador", "cartera"]):
                intent = "clientes"
                try:
                    clients = Client.get_all()
                    response = f"👥 **Base de Clientes**\n\nTienes **{len(clients)} clientes** registrados\n\nGestiona en: Clientes"
                except:
                    response = "👥 **Clientes**: Clientes → Gestión"

            # ALMACENES (específico)
            elif any(word in msg_lower for word in ["almacen", "bodega", "ubicacion"]):
                intent = "almacenes"
                try:
                    warehouses = Warehouse.get_all()
                    response = f"🏢 **Almacenes**\n\n📍 **{len(warehouses)} almacenes**:\n"
                    for w in warehouses[:5]:
                        response += f"• {w.get('nombre', 'N/A')}\n"
                    response += "\nGestiona en: Almacenes"
                except:
                    response = "🏢 **Almacenes**: Ver todos"

            # VENTAS
            elif any(word in msg_lower for word in ["venta", "vend", "factura", "ingreso", "gané", "vendí"]):
                intent = "ventas"
                try:
                    sales = Sale.get_all()
                    today_sales = [s for s in sales if s.get("fecha_venta", "").startswith(str(date.today()))]
                    total_today = sum(s.get("total", 0) for s in today_sales)
                    total_all = sum(s.get("total", 0) for s in sales)

                    response = f"💰 **Ventas**\n\n📅 Hoy: ${total_today:,.0f} ({len(today_sales)} ventas)\n📊 Total: ${total_all:,.0f} ({len(sales)} ventas)\n\nVer más: Dashboard"
                except:
                    response = "💰 **Ventas**: Dashboard → Estadísticas"

            # STOCK (antes de productos)
            elif any(word in msg_lower for word in ["stock", "inventario", "existencia", "disponible"]):
                intent = "stock"
                try:
                    products = Product.get_all()
                    low_stock = [p for p in products if p.get("stock_actual", 0) < 10]

                    if low_stock:
                        response = f"📦 **Stock Bajo**\n\n⚠️ {len(low_stock)} productos:\n"
                        for p in low_stock[:5]:
                            response += f"• {p.get('nombre', 'N/A')}: {p.get('stock_actual', 0)} u\n"
                        if len(low_stock) > 5:
                            response += f"\n+{len(low_stock) - 5} más"
                    else:
                        response = "✅ **Stock OK**\n\nTodos los productos tienen suficiente"
                    response += "\n\nVer: Dashboard → Stock Bajo"
                except:
                    response = "📦 **Stock**: Dashboard"

            # PRODUCTOS (después de específicos)
            elif any(word in msg_lower for word in ["producto", "articulo", "cuanto", "cuánto", "total"]):
                intent = "productos"
                try:
                    products = Product.get_all()
                    total_stock = sum(p.get("stock_actual", 0) for p in products)

                    response = f"📦 **Inventario**\n\n🏷️ Productos: {len(products)}\n📊 Stock total: {total_stock:,} u\n\nVer: Productos"
                except:
                    response = "📦 **Productos**: Ver catálogo"

            # COMPRAS
            elif any(word in msg_lower for word in ["compra", "proveedor", "orden"]):
                intent = "compras"
                try:
                    purchases = Purchase.get_all()
                    total = sum(p.get("total", 0) for p in purchases)
                    response = f"🛒 **Compras**\n\n📦 Total: {len(purchases)}\n💵 Monto: ${total:,.0f}\n\nVer: Compras"
                except:
                    response = "🛒 **Compras**: Ver órdenes"

            # REPORTES
            elif any(word in msg_lower for word in ["reporte", "analisis", "estadistica", "kpi"]):
                intent = "reportes"
                response = "📊 **Análisis**\n\n• Dashboard → KPIs\n• Reportes → Detallados\n• Analytics IA → Avanzado"

            # SALUDOS
            elif any(word in msg_lower for word in ["hola", "buenos", "hey", "saludos"]):
                intent = "saludo"
                response = "¡Hola! 😊 **HUB DE GESTIÓN**\n\n¿En qué ayudo?\nEscribe 'ayuda' para opciones"

            # DESPEDIDAS
            elif any(word in msg_lower for word in ["gracias", "adios", "chao", "bye"]):
                intent = "despedida"
                response = "¡De nada! 😊 ¡Excelente día!"

            # FALLBACK con contexto
            else:
                # Intentar usar contexto de conversación anterior
                if context and len(context) > 0:
                    last_intent = context[-1].get("intent")
                    if last_intent == "ventas" and any(w in msg_lower for w in ["más", "detalle", "cuál"]):
                        response = "💡 Para ver detalles de ventas específicas ve a:\n• Ventas → Lista completa\n• Reportes → Análisis detallado"
                    else:
                        response = f"🤔 No entendí \"{user_message}\"\n\nEscribe 'ayuda' para ver comandos"
                else:
                    response = f"🤔 No entendí \"{user_message}\"\n\n'ayuda' → ver comandos"
                intent = "unknown"

            # Guardar en contexto (últimas 3)
            context.append({"message": user_message, "intent": intent, "response": response[:50]})
            if len(context) > 3:
                context = context[-3:]  # Solo últimas 3
            request.session["chatbot_context"] = context

            # Guardar en BD
            ChatbotMessage.save_message(user_id, user_message, response)
            return JsonResponse({"success": True, "message": user_message, "response": response})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    @staticmethod
    @ensure_csrf_cookie
    def clear_history(request):
        """Limpia historial Y contexto de sesión"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "error": "No autenticado"}, status=401)

        user_id = request.user.id

        if request.method != "POST":
            return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)

        try:
            ChatbotMessage.delete_history(user_id)
            # Limpiar contexto de sesión
            request.session["chatbot_context"] = []
            return JsonResponse({"success": True, "message": "Historial y contexto eliminados"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    @staticmethod
    def get_history(request):
        """Obtiene historial"""
        # Usar autenticación nativa de Django
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "error": "No autenticado"}, status=401)

        user_id = request.user.id

        try:
            history = ChatbotMessage.get_history(user_id, limit=50)
            return JsonResponse({"success": True, "history": history})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
