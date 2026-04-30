class IntentService:
    @staticmethod
    def detect(message: str) -> str:
        text = message.lower()

        if any(k in text for k in ["ventas", "ingresos", "kpi", "resumen"]):
            return "analytics"

        if any(k in text for k in ["asiento", "contabilidad", "balance"]):
            return "accounting"

        if any(k in text for k in ["stock", "inventario", "producto"]):
            return "inventory"

        if any(k in text for k in ["error", "no funciona", "ayuda"]):
            return "support"

        return "general"
