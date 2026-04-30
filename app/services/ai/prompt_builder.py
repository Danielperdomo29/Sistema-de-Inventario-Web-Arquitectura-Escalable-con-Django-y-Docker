import os


class PromptBuilder:
    TEMPLATE_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates_ai", "base_prompt.txt"
    )

    @staticmethod
    def _load_base_prompt():
        with open(PromptBuilder.TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def build(user_message, metrics, intent, context):
        base_prompt = PromptBuilder._load_base_prompt()

        system_prompt = base_prompt.format(
            clientes=metrics["clientes_totales"],
            productos=metrics["productos_totales"],
            stock=metrics["stock_bajo"],
            almacenes=metrics["almacenes"],
            ventas=metrics["ventas_totales"],
            ingresos=metrics["ingresos_totales"],
        )

        # Ajuste por intención
        if intent == "analytics":
            system_prompt += "\nPrioriza análisis ejecutivo."
        elif intent == "inventory":
            system_prompt += "\nPrioriza estado de inventario."
        elif intent == "accounting":
            system_prompt += "\nPrioriza lógica contable."
        elif intent == "support":
            system_prompt += "\nDa pasos claros para resolver problemas."

        messages = [{"role": "system", "content": system_prompt}]

        for item in context[-4:]:
            messages.append({"role": "user", "content": item["message"]})
            messages.append({"role": "assistant", "content": item["response"]})

        messages.append({"role": "user", "content": user_message})

        return messages
