import json

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from app.models.chatbot_message import ChatbotMessage
from app.models.user import User
from app.views.chatbot_view import ChatbotView


class ChatbotController:
    """Controlador del Chatbot con IA"""

    @staticmethod
    @ensure_csrf_cookie
    def index(request):
        """Muestra la interfaz del chatbot"""
        user_id = request.session.get("user_id")
        if not user_id:
            return HttpResponseRedirect("/login/")

        user = User.get_by_id(user_id)
        if not user:
            request.session.flush()
            return HttpResponseRedirect("/login/")

        history = ChatbotMessage.get_history(user_id, limit=20)
        return HttpResponse(ChatbotView.render(user, history, request))

    @staticmethod
    @ensure_csrf_cookie
    def send_message(request):
        """Procesa un mensaje del usuario - Con consultas a datos reales"""
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"success": False, "error": "No autenticado"}, status=401)
        if request.method != "POST":
            return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)
        try:
            body = json.loads(request.body.decode("utf-8"))
            user_message = body.get("message", "").strip()
            if not user_message:
                return JsonResponse({"success": False, "error": "Mensaje vacío"}, status=400)
            
            # Importar modelos para consultas
            from app.models.sale import Sale
            from app.models.product import Product
            from app.models.purchase import Purchase
            from app.models.client import Client
            from app.models.warehouse import Warehouse
            from datetime import date
            
            msg_lower = user_message.lower()
            
            # VENTAS - Con datos reales
            if any(word in msg_lower for word in ['venta', 'vend', 'factura', 'ingreso']):
                try:
                    sales = Sale.get_all()
                    today_sales = [s for s in sales if s.get('fecha_venta', '').startswith(str(date.today()))]
                    total_today = sum(s.get('total', 0) for s in today_sales)
                    total_all = sum(s.get('total', 0) for s in sales)
                    
                    response = f"💰 **Resumen de Ventas**\n\n"
                    response += f"📅 **Hoy**: ${total_today:,.0f} ({len(today_sales)} ventas)\n"
                    response += f"📊 **Total histórico**: ${total_all:,.0f} ({len(sales)} ventas)\n\n"
                    response += "Ver más en: Dashboard o Módulo de Ventas"
                except:
                    response = "💰 **Ventas**: Dashboard → Estadísticas | Ventas → Lista completa"
            
            # PRODUCTOS - Con conteo real
            elif any(word in msg_lower for word in ['producto', 'articulo', 'cuanto']):
                try:
                    products = Product.get_all()
                    total_products = len(products)
                    total_stock = sum(p.get('stock_actual', 0) for p in products)
                    
                    response = f"📦 **Inventario de Productos**\n\n"
                    response += f"🏷️ **Total productos**: {total_products}\n"
                    response += f"📊 **Stock total**: {total_stock:,} unidades\n\n"
                    response += "Ver catálogo completo en: Productos"
                except:
                    response = "📦 **Productos**: Productos → Catálogo completo"
            
            # STOCK - Con datos de stock bajo
            elif any(word in msg_lower for word in ['stock', 'inventario', 'existencia']):
                try:
                    products = Product.get_all()
                    low_stock = [p for p in products if p.get('stock_actual', 0) < 10]
                    
                    response = f"📦 **Estado del Stock**\n\n"
                    if low_stock:
                        response += f"⚠️ **{len(low_stock)} productos** con stock bajo:\n\n"
                        for p in low_stock[:5]:
                            response += f"• {p.get('nombre', 'N/A')}: {p.get('stock_actual', 0)} unidades\n"
                        if len(low_stock) > 5:
                            response += f"\n...y {len(low_stock) - 5} más"
                    else:
                        response += "✅ Todos los productos tienen stock suficiente"
                    response += "\n\nVer detalles en: Dashboard → Stock Bajo"
                except:
                    response = "📦 **Stock**: Dashboard → Productos con stock bajo"
            
            # ALMACENES - Con conteo
            elif any(word in msg_lower for word in ['almacen', 'bodega']):
                try:
                    warehouses = Warehouse.get_all()
                    response = f"🏢 **Almacenes**\n\n"
                    response += f"📍 Tienes **{len(warehouses)} almacenes** registrados\n\n"
                    for w in warehouses[:5]:
                        response += f"• {w.get('nombre', 'N/A')}\n"
                    response += "\nGestiona en: Almacenes"
                except:
                    response = "🏢 **Almacenes**: Almacenes → Ver todos"
            
            # COMPRAS - Con totales
            elif any(word in msg_lower for word in ['compra', 'proveedor']):
                try:
                    purchases = Purchase.get_all()
                    total_purchases = sum(p.get('total', 0) for p in purchases)
                    response = f"🛒 **Resumen de Compras**\n\n"
                    response += f"📦 Total compras: **{len(purchases)}**\n"
                    response += f"💵 Monto total: **${total_purchases:,.0f}**\n\n"
                    response += "Ver detalles en: Compras"
                except:
                    response = "🛒 **Compras**: Compras → Lista de órdenes"
            
            # CLIENTES - Con conteo
            elif any(word in msg_lower for word in ['cliente', 'comprador']):
                try:
                    clients = Client.get_all()
                    response = f"👥 **Base de Clientes**\n\n"
                    response += f"Tienes **{len(clients)} clientes** registrados\n\n"
                    response += "Gestiona en: Clientes"
                except:
                    response = "👥 **Clientes**: Clientes → Gestión de cartera"
            
            # REPORTES/ANÁLISIS
            elif any(word in msg_lower for word in ['reporte', 'analisis', 'estadistica', 'kpi']):
                response = "📊 **Centro de Análisis**\n\n• Dashboard → KPIs en tiempo real\n• Reportes → Informes detallados\n• Analytics IA → Consultas inteligentes"
            
            # SALUDOS
            elif any(word in msg_lower for word in ['hola', 'buenos', 'hey']):
                response = "¡Hola! 😊 Asistente de **HUB DE GESTIÓN**\n\n¿En qué puedo ayudarte?\nPuedo darte números reales sobre ventas, productos, stock, clientes, etc."
            
            # DESPEDIDAS
            elif any(word in msg_lower for word in ['gracias', 'adios']):
                response = "¡De nada! 😊 ¡Que tengas un excelente día!"
            
            # FALLBACK
            else:
                response = f"🤔 No entendí \"{user_message}\"\n\nPregúntame sobre:\n• Ventas de hoy\n• Cuántos productos tengo\n• Stock bajo\n• Total de clientes\n• Resumen de compras"
            
            ChatbotMessage.save_message(user_id, user_message, response)
            return JsonResponse({"success": True, "message": user_message, "response": response})
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

            body = json.loads(request.body.decode("utf-8"))
            user_message = body.get("message", "").strip()
            if not user_message:
                return JsonResponse({"success": False, "error": "Mensaje vacío"}, status=400)
            
            # Sistema inteligente de respuestas por palabras clave
            msg_lower = user_message.lower()
            
            # Análisis de intención
            if any(word in msg_lower for word in ['venta', 'vend', 'factura', 'ingreso']):
                response = "💰 **Módulo de Ventas**\n\nConsulta ventas en:\n• Dashboard → Estadísticas generales\n• Ventas → Lista completa\n• Reportes → Análisis detallado\n\nFiltra por fecha, cliente o producto."
            
            elif any(word in msg_lower for word in ['stock', 'inventario', 'existencia']):
                response = "📦 **Gestión de Stock**\n\nRevisa tu inventario:\n• Dashboard → Stock bajo (alertas)\n• Productos → Stock actual\n• Movimientos → Historial\n\nConfigura alertas de stock mínimo."
            
            elif any(word in msg_lower for word in ['almacen', 'bodega']):
                response = "🏢 **Almacenes**\n\nGestiona ubicaciones:\n• Almacenes → Ver todos\n• Control multi-almacén\n• Asignación por producto"
            
            elif any(word in msg_lower for word in ['producto', 'articulo']):
                response = "📦 **Productos**\n\n• Productos → Catálogo completo\n• Categorías → Organización\n• Stock y precios\n• Trazabilidad"
            
            elif any(word in msg_lower for word in ['compra', 'proveedor']):
                response = "🛒 **Compras**\n\n• Compras → Órdenes\n• Proveedores → Gestión\n• Múltiples productos\n• Detalle completo"
            
            elif any(word in msg_lower for word in ['cliente', 'comprador']):
                response = "👥 **Clientes**\n\n• Clientes → Cartera\n• Historial de compras\n• Facturas generadas\n• Datos de contacto"
            
            elif any(word in msg_lower for word in ['reporte', 'analisis', 'estadistica']):
                response = "📊 **Reportes**\n\n• Dashboard → KPIs\n• Reportes → Detallados\n• Analytics IA → Análisis avanzado\n• Gráficas de evolución"
            
            elif any(word in msg_lower for word in ['hola', 'buenos', 'hey']):
                response = "¡Hola! 😊 Asistente de **HUB DE GESTIÓN**\n\n¿En qué puedo ayudarte?\nPregúntame sobre ventas, inventario, compras, etc."
            
            elif any(word in msg_lower for word in ['gracias', 'adios']):
                response = "¡De nada! 😊 Estoy aquí para ayudarte.\n¡Que tengas un excelente día!"
            
            else:
                response = f"🤔 **Pregunta**: \"{user_message}\"\n\nPuedo ayudarte con:\n• Ventas y estadísticas\n• Stock e inventario\n• Compras y proveedores\n• Reportes y análisis\n\nReformula con palabras clave."

            
            ChatbotMessage.save_message(user_id, user_message, response)
            return JsonResponse({"success": True, "message": user_message, "response": response})
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    @staticmethod
    @ensure_csrf_cookie
    def clear_history(request):
        """Limpia el historial de conversación del usuario"""
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"success": False, "error": "No autenticado"}, status=401)

        if request.method != "POST":
            return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)

        try:
            ChatbotMessage.delete_history(user_id)
            return JsonResponse({"success": True, "message": "Historial eliminado correctamente"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    @staticmethod
    def get_history(request):
        """Obtiene el historial de conversación"""
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"success": False, "error": "No autenticado"}, status=401)

        try:
            history = ChatbotMessage.get_history(user_id, limit=50)
            return JsonResponse({"success": True, "history": history})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
