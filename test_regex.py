"""
Test mejorado de patrones regex para facturas
"""

import re

# Nuevo patrón
pattern = r'(?i)total\s*[:\.\s]*[\$COP\s]*\s*([0-9]{1,3}(?:[.,][0-9]{3})+(?:[.,][0-9]{1,3})?)'

test_cases = [
    ("Total: 1.499.070", "1.499.070"),
    ("TOTAL: 1.499.070", "1.499.070"),
    ("total 1.499.070", "1.499.070"),
    ("Total factura: 1.499.070", "1.499.070"),
    ("TOTAL: $119,000.00", "119,000.00"),
    ("Total: 119,000.00", "119,000.00"),
    ("total a pagar: 1.234.567", "1.234.567"),
]

print("=" * 60)
print("PRUEBA DE PATRONES REGEX MEJORADOS")
print("=" * 60)

for text, expected in test_cases:
    matches = re.findall(pattern, text, re.IGNORECASE)
    if matches:
        result = matches[0]
        status = "[OK]" if result == expected else "[FAIL]"
    else:
        result = "NO MATCH"
        status = "[FAIL]"
    
    print(f"{status} Input: '{text}'")
    print(f"     Esperado: {expected}")
    print(f"     Obtenido: {result}")
    print()
