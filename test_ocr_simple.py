"""
Test simple de OCR sin Django
"""
import sys
sys.path.insert(0, r'C:\dev\Sistema-de-Inventario-Web-Arquitectura-Escalable-con-Django-y-Docker')

print("=" * 60)
print("TEST DE OCR - MODO SIMPLE")
print("=" * 60)

# Importar solo lo necesario
from PIL import Image
import pytesseract
import re
import os

# Configurar Tesseract (ajusta la ruta si es necesaria)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Solicitar ruta de imagen
ruta_imagen = input("\nRuta de la imagen: ")

if not os.path.exists(ruta_imagen):
    print(f"❌ Archivo no existe: {ruta_imagen}")
    sys.exit(1)

print(f"\n✅ Archivo encontrado")
print(f"📏 Tamaño: {os.path.getsize(ruta_imagen) / 1024:.1f} KB")

# Test básico primero
print("\n" + "=" * 60)
print("TEST 1: EXTRACCIÓN BÁSICA (sin OpenCV)")
print("=" * 60)

try:
    image = Image.open(ruta_imagen)
    print(f"📐 Dimensiones: {image.size}")
    print(f"🎨 Modo: {image.mode}")
    
    # Convertir a escala de grises
    if image.mode != 'L':
        image = image.convert('L')
        print("✅ Convertido a escala de grisis")
    
    print("🔤 Ejecutando Tesseract...")
    text = pytesseract.image_to_string(image, lang='spa+eng', config='--oem 3 --psm 6')
    
    print(f"\n✅ Texto extraído: {len(text)} caracteres")
    print("\n--- TEXTO COMPLETO ---")
    print(text)
    print("--- FIN TEXTO ---\n")
    
    # Buscar total
    print("🔍 Buscando TOTAL...")
    patterns = [
        r'(?i)total\s*[:\.\s]*[\$COP\s]*\s*([0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]{1,3})?)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            print(f"✅ ENCONTRADO: {matches}")
            break
    else:
        print("❌ Total NO encontrado")
        
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

# Test con OpenCV
print("\n" + "=" * 60)
print("TEST 2: EXTRACCIÓN CON OPENCV")
print("=" * 60)

try:
    import cv2
    import numpy as np
    
    print("✅ OpenCV disponible")
    
    image = Image.open(ruta_imagen)
    img_array = np.array(image)
    
    # Convertir a grises
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    height, width = gray.shape
    print(f"📏 Dimensiones: {width}x{height}")
    
    # Redimensionar si es pequeña
    if width < 1000:
        scale = 2000 / width
        new_width = int(width * scale)
        new_height = int(height * scale)
        gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        print(f"🔍 Redimensionada a: {new_width}x{new_height}")
    
    # Denoise
    print("🧹 Aplicando denoise...")
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    
    # Contraste
    print("🌟 Mejorando contraste...")
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    
    # Binarización
    print("⚫⚪ Binarizando...")
    binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # Convertir a PIL
    processed_image = Image.fromarray(binary)
    
    print("🔤 Ejecutando Tesseract con imagen procesada...")
    text = pytesseract.image_to_string(processed_image, lang='spa+eng', config='--oem 3 --psm 6')
    
    print(f"\n✅ Texto extraído: {len(text)} caracteres")
    print("\n--- TEXTO COMPLETO ---")
    print(text)
    print("--- FIN TEXTO ---\n")
    
    # Buscar total
    print("🔍 Buscando TOTAL...")
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            print(f"✅ ENCONTRADO: {matches}")
            break
    else:
        print("❌ Total NO encontrado")
    
except ImportError:
    print("⚠️ OpenCV no disponible")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("FIN DEL TEST")
print("=" * 60)
