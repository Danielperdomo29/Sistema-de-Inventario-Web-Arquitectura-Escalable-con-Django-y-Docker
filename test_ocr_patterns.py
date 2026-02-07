import re

# Texto de ejemplo de la factura
text = """
ALKOMPRAR S.A.S
NIT: 901234567-1
Factura N° 000946000
Fecha: 06/01/2026

Producto A    500.000
Producto B    999.070
TOTAL: 1.499.070
"""

# Patrones actuales MEJORADOS v3
PATTERNS = [
    r'(?i)total\s*[:\.\s]*[\$COP\s]*\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,3})?)',
    r'(?i)total\s*a\s*pagar\s*[:\.\s]*[\$COP\s]*\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,3})?)',
]

print("=== PRUEBA DE EXTRACCIÓN DE TOTAL ===\n")
print(f"Texto:\n{text}\n")

for i, pattern in enumerate(PATTERNS, 1):
    matches = re.findall(pattern, text)
    print(f"Patrón {i}: {pattern}")
    print(f"Resultados: {matches}")
    if matches:
        print(f"✅ Último match: {matches[-1]}")
    print()

# Probar con variaciones
test_cases = [
    "TOTAL: 1.499.070",
    "Total 1.499.070",
    "TOTAL $1.499.070",
    "Total: $ 1.499.070", 
    "TOTAL COP 1.499.070",
    "Total a pagar: 1.499.070",
]

print("\n=== CASOS DE PRUEBA ===\n")
for case in test_cases:
    for pattern in PATTERNS[:2]:  # Solo primeros 2 patrones
        matches = re.findall(pattern, case)
        status = "✅" if matches and matches[0] == "1.499.070" else "❌"
        print(f"{status} '{case}' → {matches}")
