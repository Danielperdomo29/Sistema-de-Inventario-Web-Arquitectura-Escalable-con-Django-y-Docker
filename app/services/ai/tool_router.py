class ToolRouter:
    @staticmethod
    def execute(tool_name, arguments, user):
        if tool_name == "crear_factura":
            return ToolRouter._crear_factura(arguments, user)

        if tool_name == "consultar_stock":
            return ToolRouter._consultar_stock(arguments)

        return {"error": "Tool no soportada"}

    @staticmethod
    def _crear_factura(args, user):
        from datetime import datetime

        from django.utils import timezone

        from app.models.product import Product
        from app.models.sale import Sale

        try:
            cliente_id = args.get("cliente_id")
            cliente_nombre_db = args.get("cliente_nombre_db", "Cliente Desconocido")
            items = args.get("items", [])

            if not cliente_id:
                return {
                    "error": "No pude identificar con certeza al cliente en la base de datos "
                    "basándome en el nombre proporcionado."
                }

            if not items:
                return {"error": "Faltan datos de los productos."}

            numero_factura = f"F-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Fetch products to get prices and calculate totals
            details = []
            total = 0.0
            errores = []

            for item in items:
                prod_id = item.get("producto_id")
                qty = float(item.get("cantidad", 1))
                nombre_buscado = item.get("producto_nombre", "Desconocido")

                if not prod_id:
                    errores.append(f"No pude encontrar el producto '{nombre_buscado}' en el catálogo activo.")
                    continue

                try:
                    p = Product.objects.get(id=prod_id, activo=True)

                    if p.stock_actual <= 0:
                        errores.append(
                            f"El producto '{p.nombre}' está agotado (Stock: 0). "
                            "Por favor añade inventario antes de vender."
                        )
                        continue

                    if qty > p.stock_actual:
                        errores.append(
                            f"No hay stock suficiente para '{p.nombre}'. "
                            f"Solicitas {qty}, pero solo hay {p.stock_actual} disponibles."
                        )
                        continue

                    precio = float(p.precio_venta)
                    subtotal = precio * qty

                    details.append(
                        {"producto_id": prod_id, "cantidad": qty, "precio_unitario": precio, "subtotal": subtotal}
                    )
                    total += subtotal
                except Product.DoesNotExist:
                    errores.append(f"El producto '{nombre_buscado}' (ID {prod_id}) no existe o fue eliminado.")

            if errores:
                # Si hubo algún error de stock o resolución, abortar la venta
                return {"error": "Validación fallida", "detalles": errores}

            data = {
                "numero_factura": numero_factura,
                "cliente_id": cliente_id,
                "usuario_id": user.id,
                "fecha": timezone.now(),
                "total": total,
                "estado": "completada",
                "tipo_pago": "efectivo",
                "notas": "Generado automáticamente por Asistente IA",
            }

            sale_id = Sale.create(data, details)

            # Nota: El stock_actual se disminuye automáticamente gracias al signal
            # '@receiver(post_save, sender='app.SaleDetail')' en stock_signals.py

            return {
                "status": "ok",
                "factura_id": numero_factura,
                "total": total,
                "mensaje": f"Factura creada con éxito para {cliente_nombre_db}. ID BD: {sale_id}",
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def _consultar_stock(args):
        try:
            from app.models.product import Product

            product = Product.get_by_id(args["producto_id"])
            if product:
                return {"producto": product.get("nombre", "Desconocido"), "stock": product.get("stock_actual", 0)}
            else:
                return {"error": "Producto no encontrado"}
        except Exception as e:
            return {"error": str(e)}
