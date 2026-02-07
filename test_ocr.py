"""
Script de prueba para verificar la extracción OCR con diferentes formatos de números
"""

from app.services.ocr_service import ReceiptOCRExtractor

def test_number_normalization():
    """Prueba la normalización de números"""
    extractor = ReceiptOCRExtractor()
    
    test_cases = [
        ("1.499.070", 1499070.0, "Formato colombiano con puntos"),
        ("119,000.00", 119000.0, "Formato USA con coma de miles"),
        ("1,499.99", 1499.99, "Formato USA decimal"),
        ("1.234,56", 1234.56, "Formato europeo"),
        ("119.000", 119000.0, "Formato con punto de miles"),
        ("$250.50", 250.50, "Con simbolo de dolar"),
        ("COP 1.500.000", 1500000.0, "Con codigo COP"),
    ]
    
    print("=" * 60)
    print("PRUEBA DE NORMALIZACION DE NUMEROS")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for input_val, expected, description in test_cases:
        try:
            result = extractor._normalize_amount(input_val)
            if result == expected:
                status = "[OK]"
                passed += 1
            else:
                status = "[FAIL]"
                failed += 1
            
            print(f"{status} {description}")
            print(f"  Input: {input_val}")
            print(f"  Esperado: {expected}")
            print(f"  Obtenido: {result}")
            if result != expected:
                print(f"  ERROR: No coincide!")
            print()
        except Exception as e:
            status = "[ERROR]"
            failed += 1
            print(f"{status} {description}")
            print(f"  Input: {input_val}")
            print(f"  ERROR: {str(e)}")
            print()

    print("=" * 60)
    print(f"RESUMEN: {passed} pasaron, {failed} fallaron")
    print("=" * 60)

if __name__ == "__main__":
    test_number_normalization()
    
    print("\n" + "=" * 60)
    print("Para probar con un archivo real:")
    print("=" * 60)
    print("""
from app.services.ocr_service import receipt_extractor

# Prueba con tu factura
result = receipt_extractor.extract_total('media/receipts/2026/01/tu_factura.pdf')

print(f"Exito: {result['success']}")
print(f"Total extraido: ${result['total']:,.2f}")
print(f"Confianza: {result['confidence']*100:.1f}%")
print(f"Patron usado: {result['found_pattern']}")
print(f"\\nTexto extraido:\\n{result['extracted_text']}")
""")
