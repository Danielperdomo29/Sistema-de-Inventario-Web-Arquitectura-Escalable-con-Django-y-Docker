from difflib import get_close_matches


class EntityResolver:
    """
    Resuelve nombres provistos por la IA contra entidades reales de la base de datos.
    Solo considera entidades activas.
    """

    @staticmethod
    def resolve_cliente(nombre_cliente: str):
        if not nombre_cliente:
            return None

        try:
            from app.models.client import Client

            clientes = Client.get_all()  # Idealmente en el futuro: Client.objects.filter(activo=True)
            if not clientes:
                return None

            termino = nombre_cliente.lower().strip()

            # 1. Búsqueda por substring (ideal para nombres parciales como "Daniel")
            matches_substring = [c for c in clientes if termino in c["nombre"].lower()]
            if matches_substring:
                cliente = matches_substring[0]  # Tomamos la primera coincidencia
                return {"id": cliente["id"], "nombre": cliente["nombre"]}

            # 2. Si falla, usar difflib para typos (ej: "Danel")
            nombres = [c["nombre"].lower() for c in clientes]
            best = get_close_matches(termino, nombres, n=1, cutoff=0.5)

            if not best:
                return None

            cliente = next(c for c in clientes if c["nombre"].lower() == best[0])
            return {"id": cliente["id"], "nombre": cliente["nombre"]}
        except Exception:
            return None

    @staticmethod
    def resolve_producto(nombre_producto: str):
        if not nombre_producto:
            return None

        try:
            from app.models.product import Product

            # Solo buscar en productos activos
            productos = Product.objects.filter(activo=True).values("id", "nombre", "precio_venta", "stock_actual")
            if not productos:
                return None

            termino = nombre_producto.lower().strip()

            # 1. Búsqueda por substring (ideal para "test" dentro de "Producto test")
            matches_substring = [p for p in productos if termino in p["nombre"].lower()]
            if matches_substring:
                return matches_substring[0]

            # 2. Si falla, usar difflib para typos
            nombres = [p["nombre"].lower() for p in productos]
            best = get_close_matches(termino, nombres, n=1, cutoff=0.4)

            if not best:
                return None

            producto = next(p for p in productos if p["nombre"].lower() == best[0])
            return producto
        except Exception:
            return None
