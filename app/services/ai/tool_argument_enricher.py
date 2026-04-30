from app.services.ai.entity_resolver import EntityResolver


class ToolArgumentEnricher:
    """
    Convierte los nombres en lenguaje natural que envía el LLM en IDs reales de la base de datos.
    """

    @staticmethod
    def enrich(tool_name, arguments, user_message=None):
        # --- FACTURA ---
        if tool_name == "crear_factura":

            # Resolver Cliente
            if "cliente_nombre" in arguments:
                cliente = EntityResolver.resolve_cliente(arguments["cliente_nombre"])
                if cliente:
                    arguments["cliente_id"] = cliente["id"]
                    arguments["cliente_nombre_db"] = cliente["nombre"]

            # Resolver Productos
            if "items" in arguments:
                for item in arguments["items"]:
                    if "producto_nombre" in item:
                        producto = EntityResolver.resolve_producto(item["producto_nombre"])
                        if producto:
                            item["producto_id"] = producto["id"]
                            item["producto_nombre_db"] = producto["nombre"]

        # --- STOCK ---
        if tool_name == "consultar_stock":
            if "producto_nombre" in arguments:
                producto = EntityResolver.resolve_producto(arguments["producto_nombre"])
                if producto:
                    arguments["producto_id"] = producto["id"]
                    arguments["producto_nombre_db"] = producto["nombre"]

        return arguments
