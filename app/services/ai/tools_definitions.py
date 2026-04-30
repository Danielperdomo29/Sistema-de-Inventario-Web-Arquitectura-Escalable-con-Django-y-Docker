TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "crear_factura",
            "description": "Crea una nueva factura en el sistema para un cliente dado con sus productos",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_nombre": {"type": "string", "description": "Nombre o aproximación del nombre del cliente"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "producto_nombre": {"type": "string", "description": "Nombre del producto"},
                                "cantidad": {"type": "number", "description": "Cantidad a facturar"},
                            },
                            "required": ["producto_nombre", "cantidad"],
                        },
                    },
                },
                "required": ["cliente_nombre", "items"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_stock",
            "description": "Consulta el stock actual de un producto mediante su nombre",
            "parameters": {
                "type": "object",
                "properties": {"producto_nombre": {"type": "string", "description": "Nombre del producto"}},
                "required": ["producto_nombre"],
            },
        },
    },
]
