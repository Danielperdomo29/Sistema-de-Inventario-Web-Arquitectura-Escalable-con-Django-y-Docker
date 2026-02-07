"""
Comando de Django para generar datos de prueba para Analytics ML

Genera ventas históricas realistas para entrenar modelos de predicción.

Uso:
    python manage.py crear_datos_analytics --dias 180 --productos 10
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Genera datos de prueba para Analytics ML (ventas históricas)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=180,
            help='Días de historia a generar (default: 180)'
        )
        parser.add_argument(
            '--productos',
            type=int,
            default=10,
            help='Número de productos a incluir (default: 10)'
        )
        parser.add_argument(
            '--ventas-dia',
            type=int,
            default=5,
            help='Promedio de ventas por día (default: 5)'
        )
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Limpiar ventas existentes antes de crear nuevas'
        )
    
    def handle(self, *args, **options):
        dias = options['dias']
        num_productos = options['productos']
        ventas_dia = options['ventas_dia']
        limpiar = options['limpiar']
        
        self.stdout.write(self.style.NOTICE(
            f"\n[ANALYTICS] Generando datos de prueba para Analytics ML..."
        ))
        self.stdout.write(f"   - Dias de historia: {dias}")
        self.stdout.write(f"   - Productos: {num_productos}")
        self.stdout.write(f"   - Ventas/dia promedio: {ventas_dia}\n")
        
        try:
            from app.models import Product, Sale, SaleDetail, Client, Category, Warehouse
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            
            # Obtener o crear usuario admin
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.create_superuser(
                    username='admin_analytics',
                    email='admin@analytics.test',
                    password='admin123'
                )
                self.stdout.write(self.style.SUCCESS("[OK] Usuario admin creado"))
            
            # Obtener o crear cliente genérico
            cliente, _ = Client.objects.get_or_create(
                documento='9999999999',
                defaults={
                    'nombre': 'Cliente Genérico Analytics',
                    'telefono': '0000000000',
                    'direccion': 'Dirección de prueba',
                    'email': 'cliente@analytics.test'
                }
            )
            
            # Obtener o crear categoría
            categoria, _ = Category.objects.get_or_create(
                nombre='Categoría Analytics Test',
                defaults={'descripcion': 'Categoría para pruebas de ML'}
            )
            
            # Obtener o crear bodega
            bodega = Warehouse.objects.first()
            if not bodega:
                bodega = Warehouse.objects.create(
                    nombre='Bodega Principal',
                    direccion='Dirección bodega',
                    capacidad_maxima=10000
                )
            
            # Obtener o crear productos
            productos = list(Product.objects.filter(activo=True)[:num_productos])
            
            if len(productos) < num_productos:
                self.stdout.write(self.style.WARNING(
                    f"[!] Solo hay {len(productos)} productos activos. Creando productos de prueba..."
                ))
                
                for i in range(len(productos), num_productos):
                    producto = Product.objects.create(
                        codigo=f'ANALYTICS-{i:03d}',
                        nombre=f'Producto Analytics Test {i+1}',
                        descripcion=f'Producto de prueba para Analytics ML',
                        precio_compra=Decimal(random.uniform(10000, 100000)),
                        precio_venta=Decimal(random.uniform(15000, 150000)),
                        stock_actual=random.randint(50, 500),
                        stock_minimo=random.randint(10, 50),
                        categoria=categoria,
                        activo=True
                    )
                    productos.append(producto)
                
                self.stdout.write(self.style.SUCCESS(
                    f"[OK] Creados {num_productos - len(productos)} productos de prueba"
                ))
            
            productos = productos[:num_productos]
            
            # Limpiar ventas si se solicita
            if limpiar:
                deleted = Sale.objects.filter(descripcion__contains='[Analytics Test]').delete()
                self.stdout.write(self.style.WARNING(
                    f"[CLEAN] Eliminadas {deleted[0]} ventas de prueba anteriores"
                ))
            
            # Generar ventas históricas
            fecha_inicio = date.today() - timedelta(days=dias)
            ventas_creadas = 0
            detalles_creados = 0
            
            # Patrones de estacionalidad
            # - Fines de semana: más ventas
            # - Quincenas: pico de ventas
            # - Festivos: menos ventas
            
            self.stdout.write("\n[PROGRESS] Generando ventas...")
            
            for dia_offset in range(dias):
                fecha_venta = fecha_inicio + timedelta(days=dia_offset)
                
                # Calcular número de ventas del día
                base_ventas = ventas_dia
                
                # Ajustar por día de la semana
                if fecha_venta.weekday() >= 5:  # Fin de semana
                    base_ventas = int(base_ventas * 1.3)
                elif fecha_venta.weekday() == 0:  # Lunes
                    base_ventas = int(base_ventas * 0.8)
                
                # Ajustar por quincena
                if fecha_venta.day in [15, 16, 30, 31, 1, 2]:
                    base_ventas = int(base_ventas * 1.5)
                
                # Variación aleatoria
                num_ventas = max(1, int(base_ventas * random.uniform(0.7, 1.3)))
                
                for _ in range(num_ventas):
                    # Generar número de factura único
                    timestamp = timezone.now().strftime('%Y%m%d%H%M%S%f')
                    numero_factura = f'ANA-{fecha_venta.strftime("%Y%m%d")}-{random.randint(1000, 9999)}-{timestamp[-6:]}'
                    
                    # Crear venta
                    venta = Sale.objects.create(
                        numero_factura=numero_factura,
                        fecha=timezone.make_aware(
                            timezone.datetime.combine(
                                fecha_venta, 
                                timezone.datetime.min.time().replace(
                                    hour=random.randint(8, 20),
                                    minute=random.randint(0, 59)
                                )
                            )
                        ),
                        cliente=cliente,
                        usuario=admin_user,
                        notas='[Analytics Test] Venta generada para pruebas ML',
                        estado='completada',
                        total=Decimal('0')
                    )
                    ventas_creadas += 1
                    
                    # Agregar detalles (1-3 productos por venta)
                    num_items = random.randint(1, min(3, len(productos)))
                    productos_venta = random.sample(productos, num_items)
                    
                    subtotal = Decimal('0')
                    
                    for producto in productos_venta:
                        cantidad = random.randint(1, 5)
                        precio = producto.precio_venta or Decimal('50000')
                        
                        # Variación de precio (descuentos ocasionales)
                        if random.random() < 0.2:  # 20% descuento
                            precio = precio * Decimal('0.9')
                        
                        linea_subtotal = cantidad * precio
                        iva_linea = linea_subtotal * Decimal('0.19')
                        
                        SaleDetail.objects.create(
                            venta=venta,
                            producto=producto,
                            cantidad=cantidad,
                            precio_unitario=precio,
                            subtotal_sin_iva=linea_subtotal,
                            iva_tasa=Decimal('19.00'),
                            iva_valor=iva_linea,
                            subtotal=linea_subtotal + iva_linea
                        )
                        detalles_creados += 1
                        subtotal += linea_subtotal + iva_linea
                    
                    # Actualizar totales de venta
                    venta.calculate_totals()
                    venta.save()
                
                # Mostrar progreso cada 30 días
                if dia_offset % 30 == 0 and dia_offset > 0:
                    self.stdout.write(f"   -> Procesados {dia_offset}/{dias} dias...")
            
            self.stdout.write(self.style.SUCCESS(f"""
[OK] Datos de prueba generados exitosamente:
   - Ventas creadas: {ventas_creadas}
   - Detalles creados: {detalles_creados}
   - Productos incluidos: {len(productos)}
   - Periodo: {fecha_inicio} a {date.today()}

[INFO] Ahora puedes entrenar los modelos de prediccion:
   - API: GET /api/analytics/entrenar/?producto_id=<ID>
   - O ejecuta predicciones directamente
"""))
            
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f"[ERROR] Importacion: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[ERROR] {e}"))
            raise
