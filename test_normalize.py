"""
Test completo del flujo de normalización
"""

def normalize_amount(amount_str):
    """Copia del método de ocr_service"""
    # Limpiar espacios y símbolos de moneda
    amount_str = amount_str.replace(' ', '').replace('$', '').replace('COP', '')
    
    # Contar puntos y comas
    dot_count = amount_str.count('.')
    comma_count = amount_str.count(',')
    
    # Determinar el formato
    if dot_count > 0 and comma_count > 0:
        # Ambos presentes: determinar cuál es el decimal
        last_dot_pos = amount_str.rfind('.')
        last_comma_pos = amount_str.rfind(',')
        
        if last_dot_pos > last_comma_pos:
            # Formato: 1,499.99 (punto es decimal)
            amount_str = amount_str.replace(',', '')
        else:
            # Formato: 1.499,99 (coma es decimal)
            amount_str = amount_str.replace('.', '').replace(',', '.')
            
    elif dot_count > 1 and comma_count == 0:
        # Formato: 1.499.070 (puntos son separadores de miles)
        amount_str = amount_str.replace('.', '')
        
    elif comma_count > 1 and dot_count == 0:
        # Formato: 1,499,070 (comas son separadores de miles)
        amount_str = amount_str.replace(',', '')
        
    elif dot_count == 1 and comma_count == 0:
        # Un solo punto: podría ser miles o decimal
        parts = amount_str.split('.')
        if len(parts[1]) == 3 and len(parts[0]) <= 3:
            # Formato: 119.000 (punto es separador de miles)
            amount_str = amount_str.replace('.', '')
        # Sino, asumir que es decimal (formato: 123.45)
        
    elif comma_count == 1 and dot_count == 0:
        # Una sola coma: probablemente decimal europeo
        amount_str = amount_str.replace(',', '.')
    
    return float(amount_str)

# Test cases
test_cases = [
    ("1.499.070", 1499070.0),
    ("1.499", 1499.0),  # El problema actual
    ("119,000.00", 119000.0),
    ("1,499.99", 1499.99),
]

print("=== TEST DE NORMALIZACION ===\n")
for input_val, expected in test_cases:
    result = normalize_amount(input_val)
    status = "OK" if result == expected else "FAIL"
    print(f"[{status}] '{input_val}' -> {result} (esperado: {expected})")
    if result != expected:
        print(f"     DIFERENCIA: {result} vs {expected}")
