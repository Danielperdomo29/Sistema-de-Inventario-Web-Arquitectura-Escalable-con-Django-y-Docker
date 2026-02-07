"""
Management command para generar datos de prueba para KPIs.
Crea productos, categorias, clientes y ventas de ejemplo.

Uso:
    python manage.py crear_datos_kpi
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random
import uuid


class Command(BaseCommand):
    help = 'Crea datos de prueba para validar graficas de KPI'

    def handle(self, *args, **options):
        from app.models import Product, Category, Client, Sale, SaleDetail, Supplier, UserAccount
        
        self.stdout.write('[INFO] Creando datos de prueba para KPIs...')
        
        # 0. Obtener o crear usuario para las ventas
        try:
            usuario = UserAccount.objects.first()
            if not usuario:
                self.stdout.write('[WARN] No hay usuarios, creando uno de prueba...')
                usuario = UserAccount.objects.create(
                    username='admin_test',
                    nombre='Admin Test',
                    correo='admin@test.com'
                )
        except Exception as e:
            self.stdout.write(f'[ERROR] No se pudo obtener usuario: {e}')
            return
        
        self.stdout.write(f'[OK] Usando usuario: {usuario.username}')
        
        # 1. Crear categorias si no existen
        categorias_data = [
            {'nombre': 'Electronica', 'descripcion': 'Productos electronicos'},
            {'nombre': 'Ropa', 'descripcion': 'Prendas de vestir'},
            {'nombre': 'Alimentos', 'descripcion': 'Productos alimenticios'},
            {'nombre': 'Hogar', 'descripcion': 'Articulos para el hogar'},
            {'nombre': 'Deportes', 'descripcion': 'Articulos deportivos'},
        ]
        
        categorias = []
        for cat_data in categorias_data:
            cat, created = Category.objects.get_or_create(
                nombre=cat_data['nombre'],
                defaults={'descripcion': cat_data['descripcion'], 'activo': True}
            )
            categorias.append(cat)
            if created:
                self.stdout.write(f'  [OK] Categoria: {cat.nombre}')
        
        # 2. Crear proveedor de prueba si no existe
        proveedor, created = Supplier.objects.get_or_create(
            nombre='Proveedor General',
            defaults={
                'telefono': '3001234567',
                'email': 'proveedor@example.com',
                'direccion': 'Calle Principal #123',
                'activo': True
            }
        )
        if created:
            self.stdout.write(f'  [OK] Proveedor: {proveedor.nombre}')
        
        # 3. Crear productos de prueba
        productos_data = [
            {'nombre': 'Laptop HP 15', 'codigo': 'KPI-ELEC001', 'categoria': 0, 'precio_compra': 800, 'precio_venta': 1200, 'stock': 50},
            {'nombre': 'Mouse Inalambrico', 'codigo': 'KPI-ELEC002', 'categoria': 0, 'precio_compra': 15, 'precio_venta': 35, 'stock': 200},
            {'nombre': 'Teclado Mecanico', 'codigo': 'KPI-ELEC003', 'categoria': 0, 'precio_compra': 50, 'precio_venta': 120, 'stock': 100},
            {'nombre': 'Monitor 24', 'codigo': 'KPI-ELEC004', 'categoria': 0, 'precio_compra': 200, 'precio_venta': 350, 'stock': 30},
            {'nombre': 'Audifonos Bluetooth', 'codigo': 'KPI-ELEC005', 'categoria': 0, 'precio_compra': 25, 'precio_venta': 65, 'stock': 150},
            {'nombre': 'Camiseta Algodon', 'codigo': 'KPI-ROPA001', 'categoria': 1, 'precio_compra': 8, 'precio_venta': 25, 'stock': 300},
            {'nombre': 'Pantalon Jean', 'codigo': 'KPI-ROPA002', 'categoria': 1, 'precio_compra': 20, 'precio_venta': 55, 'stock': 150},
            {'nombre': 'Zapatos Deportivos', 'codigo': 'KPI-ROPA003', 'categoria': 1, 'precio_compra': 40, 'precio_venta': 95, 'stock': 80},
            {'nombre': 'Arroz 1kg', 'codigo': 'KPI-ALIM001', 'categoria': 2, 'precio_compra': 2, 'precio_venta': 4, 'stock': 500},
            {'nombre': 'Aceite 1L', 'codigo': 'KPI-ALIM002', 'categoria': 2, 'precio_compra': 3, 'precio_venta': 5, 'stock': 400},
        ]
        
        productos = []
        for prod_data in productos_data:
            prod, created = Product.objects.get_or_create(
                codigo=prod_data['codigo'],
                defaults={
                    'nombre': prod_data['nombre'],
                    'categoria': categorias[prod_data['categoria']],
                    'proveedor': proveedor,
                    'precio_compra': Decimal(str(prod_data['precio_compra'])),
                    'precio_venta': Decimal(str(prod_data['precio_venta'])),
                    'stock_actual': prod_data['stock'],
                    'stock_minimo': 10,
                    'activo': True
                }
            )
            productos.append(prod)
            if created:
                self.stdout.write(f'  [OK] Producto: {prod.nombre}')
        
        # 4. Crear clientes de prueba
        clientes_data = [
            {'nombre': 'Juan Perez KPI', 'email': 'juan.kpi@example.com', 'telefono': '3001234567'},
            {'nombre': 'Maria Garcia KPI', 'email': 'maria.kpi@example.com', 'telefono': '3007654321'},
            {'nombre': 'Carlos Lopez KPI', 'email': 'carlos.kpi@example.com', 'telefono': '3009876543'},
        ]
        
        clientes = []
        for cli_data in clientes_data:
            cli, created = Client.objects.get_or_create(
                email=cli_data['email'],
                defaults={
                    'nombre': cli_data['nombre'],
                    'telefono': cli_data['telefono'],
                    'activo': True
                }
            )
            clientes.append(cli)
            if created:
                self.stdout.write(f'  [OK] Cliente: {cli.nombre}')
        
        # 5. Crear ventas de los ultimos 7 dias
        self.stdout.write('\n[INFO] Generando ventas de prueba...')
        
        ventas_creadas = 0
        
        # Frecuencia de ventas por producto (cuantas ventas en 7 dias)
        frecuencia = {
            'KPI-ELEC001': 5,   # Laptop - 5 ventas
            'KPI-ELEC002': 20,  # Mouse - muy vendido
            'KPI-ELEC003': 10,  # Teclado
            'KPI-ELEC004': 3,   # Monitor
            'KPI-ELEC005': 15,  # Audifonos
            'KPI-ROPA001': 25,  # Camiseta - muy vendida
            'KPI-ROPA002': 12,  # Pantalon
            'KPI-ROPA003': 8,   # Zapatos
            'KPI-ALIM001': 50,  # Arroz - alta rotacion
            'KPI-ALIM002': 40,  # Aceite
        }
        
        for prod in productos:
            num_ventas = frecuencia.get(prod.codigo, 5)
            
            for i in range(num_ventas):
                # Fecha en los ultimos 7 dias
                dias_atras = random.randint(0, 6)
                horas = random.randint(8, 17)
                minutos = random.randint(0, 59)
                fecha_venta = timezone.now() - timedelta(days=dias_atras, hours=horas, minutes=minutos)
                
                # Cantidad aleatoria (1-5 unidades)
                cantidad = random.randint(1, 5)
                cliente = random.choice(clientes)
                
                # Calcular totales
                subtotal = prod.precio_venta * cantidad
                iva = subtotal * Decimal('0.19')
                total = subtotal + iva
                
                # Numero de factura unico
                numero_factura = f"KPI-{uuid.uuid4().hex[:8].upper()}"
                
                try:
                    # Crear venta
                    venta = Sale.objects.create(
                        numero_factura=numero_factura,
                        cliente=cliente,
                        usuario=usuario,
                        fecha=fecha_venta,
                        subtotal=subtotal,
                        iva_total=iva,
                        total=total,
                        estado='completada',
                        tipo_pago='efectivo'
                    )
                    
                    # Crear detalle de venta
                    SaleDetail.objects.create(
                        venta=venta,
                        producto=prod,
                        cantidad=cantidad,
                        precio_unitario=prod.precio_venta,
                        subtotal=subtotal
                    )
                    ventas_creadas += 1
                    
                except Exception as e:
                    self.stdout.write(f'  [WARN] Error: {str(e)[:50]}')
        
        self.stdout.write(self.style.SUCCESS(f'\n[OK] {ventas_creadas} ventas creadas'))
        
        # 6. Resumen
        self.stdout.write(self.style.SUCCESS('\n[RESUMEN]:'))
        self.stdout.write(f'  - Productos KPI: {Product.objects.filter(codigo__startswith="KPI-").count()}')
        self.stdout.write(f'  - Clientes KPI: {Client.objects.filter(email__contains="kpi").count()}')
        self.stdout.write(f'  - Ventas KPI: {Sale.objects.filter(numero_factura__startswith="KPI-").count()}')
        self.stdout.write(self.style.SUCCESS('\n[OK] Datos de prueba creados!'))
