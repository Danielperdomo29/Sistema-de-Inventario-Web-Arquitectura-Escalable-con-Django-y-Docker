"""
Servicio de IA para el chatbot usando Google Gemini.
Utiliza lazy imports para evitar problemas de dependencias circulares durante la inicialización de Django.
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Imports que no dependen de Django
try:
    import google.generativeai as genai
except ImportError:
    genai = None

import json



class AIService:
    """Servicio de IA para el chatbot usando Google Gemini"""
    
    def __init__(self):
        # Configurar la API key de Gemini desde variable de entorno
        if genai is None:
            raise ImportError(
                "google-generativeai no está instalado. "
                "Ejecuta: pip install google-generativeai"
            )
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key or api_key == 'tu-api-key-aqui':
            raise ValueError(
                "GEMINI_API_KEY no está configurada. "
                "Por favor, configura tu API key en el archivo .env"
            )
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def _get_models(self):
        """
        Lazy import de modelos Django para evitar dependencias circulares.
        Los modelos se importan solo cuando se necesitan.
        """
        from app.models.product import Product
        from app.models.category import Category
        from app.models.sale import Sale
        from app.models.purchase import Purchase
        from app.models.warehouse import Warehouse
        
        return {
            'Product': Product,
            'Category': Category,
            'Sale': Sale,
            'Purchase': Purchase,
            'Warehouse': Warehouse,
        }
    
    def get_inventory_context(self):
        """Obtiene contexto del inventario actual"""
        try:
            models = self._get_models()
            Product = models['Product']
            Category = models['Category']
            Warehouse = models['Warehouse']
            
            # Obtener estadísticas generales
            products = Product.get_all()
            categories = Category.get_all()
            warehouses = Warehouse.get_all()
            
            # Productos con stock bajo
            low_stock_products = [p for p in products if p.get('stock', 0) < 10]
            
            context = f"""
            INFORMACIÓN DEL SISTEMA DE INVENTARIO:
            
            Estadísticas Generales:
            - Total de productos: {len(products)}
            - Total de categorías: {len(categories)}
            - Total de almacenes: {len(warehouses)}
            - Productos con stock bajo (menos de 10 unidades): {len(low_stock_products)}
            
            """
            
            # Agregar productos con stock bajo si existen
            if low_stock_products:
                context += "\nProductos con Stock Bajo:\n"
                for product in low_stock_products[:5]:  # Solo los primeros 5
                    context += f"- {product.get('name', 'N/A')}: {product.get('stock', 0)} unidades\n"
            
            return context
        except Exception as e:
            return f"Error al obtener contexto del inventario: {str(e)}"

    
    
    def search_products(self, query):
        """Busca productos por nombre"""
        try:
            models = self._get_models()
            Product = models['Product']
            
            products = Product.get_all()
            query_lower = query.lower()
            
            results = [
                p for p in products 
                if query_lower in p.get('name', '').lower() or 
                   query_lower in p.get('description', '').lower()
            ]
            
            if not results:
                return "No se encontraron productos con ese criterio."
            
            response = f"Encontré {len(results)} producto(s):\n\n"
            for product in results[:5]:  # Limitar a 5 resultados
                response += f"• {product.get('name', 'N/A')}\n"
                response += f"  - Stock: {product.get('stock', 0)} unidades\n"
                response += f"  - Precio: ${product.get('price', 0):.2f}\n"
                response += f"  - Categoría: {product.get('category_name', 'N/A')}\n\n"
            
            return response
        except Exception as e:
            return f"Error al buscar productos: {str(e)}"

    
    def get_sales_summary(self):
        """Obtiene resumen de ventas"""
        try:
            models = self._get_models()
            Sale = models['Sale']
            
            sales = Sale.get_all()
            
            if not sales:
                return "No hay ventas registradas en el sistema."
            
            total_sales = len(sales)
            total_amount = sum(sale.get('total', 0) for sale in sales)
            
            response = f"Resumen de Ventas:\n\n"
            response += f"• Total de ventas: {total_sales}\n"
            response += f"• Monto total: ${total_amount:.2f}\n"
            
            # Últimas 3 ventas
            response += f"\nÚltimas 3 ventas:\n"
            for sale in sales[-3:]:
                response += f"• Venta #{sale.get('id', 'N/A')} - ${sale.get('total', 0):.2f} - {sale.get('date', 'N/A')}\n"
            
            return response
        except Exception as e:
            return f"Error al obtener resumen de ventas: {str(e)}"
    
    def get_purchases_summary(self):
        """Obtiene resumen de compras"""
        try:
            models = self._get_models()
            Purchase = models['Purchase']
            
            purchases = Purchase.get_all()
            
            if not purchases:
                return "No hay compras registradas en el sistema."
            
            total_purchases = len(purchases)
            total_amount = sum(purchase.get('total', 0) for purchase in purchases)
            
            response = f"Resumen de Compras:\n\n"
            response += f"• Total de compras: {total_purchases}\n"
            response += f"• Monto total: ${total_amount:.2f}\n"
            
            return response
        except Exception as e:
            return f"Error al obtener resumen de compras: {str(e)}"
    
    def process_query(self, user_message, user_id):
        """Procesa una consulta del usuario usando IA"""
        try:
            # Obtener contexto del inventario
            inventory_context = self.get_inventory_context()
            
            # Detectar intenciones específicas
            message_lower = user_message.lower()
            
            # Consulta general de productos
            if any(word in message_lower for word in ['todos los productos', 'listar productos', 'mostrar productos', 'cuántos productos', 'consulta', 'productos disponibles', 'stock bajo', 'productos con stock']):
                models = self._get_models()
                Product = models['Product']
                
                products = Product.get_all()
                if not products:
                    return "No hay productos registrados en el sistema."
                
                # Si pregunta por stock bajo, filtrar
                if 'stock bajo' in message_lower or 'bajo stock' in message_lower or 'poco stock' in message_lower:
                    low_stock = [p for p in products if p.get('stock_actual', 0) < 10]
                    if not low_stock:
                        return "¡Excelente! No hay productos con stock bajo (menos de 10 unidades)."
                    
                    response = f"Productos con Stock Bajo\n\n"
                    response += f"Se encontraron {len(low_stock)} productos con menos de 10 unidades:\n\n"
                    
                    for product in low_stock[:15]:
                        response += f"• **{product.get('nombre', 'N/A')}**\n"
                        response += f"  - Stock: {product.get('stock_actual', 0)} unidades ⚠️\n"
                        response += f"  - Precio: ${product.get('precio_venta', 0):.2f}\n\n"
                    
                    if len(low_stock) > 15:
                        response += f"\n... y {len(low_stock) - 15} productos más con stock bajo.\n"
                    
                    return response
                
                # Consulta general
                response = f"Resumen de Productos\n\n"
                response += f"Total de productos: {len(products)}\n\n"
                response += "Algunos productos destacados:\n\n"
                
                for product in products[:10]:  # Mostrar primeros 10
                    response += f"{product.get('nombre', 'N/A')}\n"
                    response += f"  - Stock: {product.get('stock_actual', 0)} unidades\n"
                    response += f"  - Precio: ${product.get('precio_venta', 0):.2f}\n"
                    if product.get('categoria'):
                        response += f"  - Categoría: {product.get('categoria')}\n"
                    response += "\n"
                
                if len(products) > 10:
                    response += f"\n... y {len(products) - 10} productos más.\n"
                
                return response
            
            # Búsqueda de productos específicos
            if 'buscar' in message_lower and not any(word in message_lower for word in ['todos', 'listar', 'mostrar']):
                # Extraer el término de búsqueda
                words_to_remove = ['buscar', 'encontrar', 'producto', 'productos', 'el', 'la', 'los', 'las', 'un', 'una']
                search_terms = [word for word in message_lower.split() if word not in words_to_remove]
                if search_terms:
                    return self.search_products(' '.join(search_terms))
                else:
                    return "Por favor, especifica qué producto estás buscando. Por ejemplo: 'buscar laptop' o 'buscar mouse'"
            
            # Resumen de ventas
            if any(word in message_lower for word in ['ventas', 'venta', 'vendido', 'vendidos']):
                return self.get_sales_summary()
            
            # Resumen de compras
            if any(word in message_lower for word in ['compras', 'compra', 'comprado', 'comprados']):
                return self.get_purchases_summary()
            
            # Para otras consultas, usar Gemini con contexto
            prompt = f"""
            Eres un asistente virtual experto en sistemas de inventario. Estás ayudando a un usuario con su sistema de gestión de inventario.
            
            {inventory_context}
            
            El usuario pregunta: {user_message}
            
            Proporciona una respuesta útil, clara y concisa. Si la pregunta es sobre datos específicos que no están en el contexto, 
            sugiere qué información necesitas o cómo el usuario puede encontrarla en el sistema.
            
            Si te preguntan sobre funcionalidades del sistema, explica cómo usar las diferentes secciones:
            - Productos: gestionar el catálogo de productos
            - Categorías: organizar productos por categorías
            - Ventas: registrar y consultar ventas
            - Compras: registrar y consultar compras
            - Almacenes: gestionar diferentes ubicaciones de almacenamiento
            - Movimientos de Inventario: registrar entradas y salidas
            - Reportes: generar informes y análisis
            
            Responde en español de manera amigable y profesional.
            """
            
            # Generar respuesta con Gemini
            response = self.model.generate_content(prompt)
            
            return response.text
            
        except Exception as e:
            return f"Lo siento, hubo un error al procesar tu consulta. Por favor, intenta de nuevo. Error: {str(e)}"
    
    def get_help_message(self):
        """Retorna mensaje de ayuda con los comandos básicos"""
        return (
            "Comandos básicos disponibles:\n"
            "- \"ayuda\" - Muestra qué puede hacer el chatbot\n"
            "- \"buscar producto [nombre]\" - Busca productos específicos\n"
            "- \"resumen de ventas\" - Muestra estadísticas de ventas\n"
            "- \"resumen de compras\" - Muestra estadísticas de compras\n"
            "- \"productos con stock bajo\" - Lista productos con poco inventario\n"
            "\n¿En qué puedo ayudarte hoy?"
        )
