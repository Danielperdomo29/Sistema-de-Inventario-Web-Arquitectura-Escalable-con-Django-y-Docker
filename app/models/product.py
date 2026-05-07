from django.db import models

from app.models.category import Category
from app.models.supplier import Supplier
from app.services.cache_service import CacheService


class Product(models.Model):
    """Modelo de Producto"""

    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        db_column="categoria_id",
        related_name="productos",
    )
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    stock_minimo = models.IntegerField(default=10)
    stock_actual = models.IntegerField(default=0)
    proveedor = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        db_column="proveedor_id",
        related_name="productos",
    )

    activo = models.BooleanField(default=True)

    # Campos Tributarios DIAN
    IVA_TIPOS = [
        ("GRAVADO", "Gravado"),
        ("EXENTO", "Exento"),
        ("EXCLUIDO", "Excluido"),
    ]

    codigo_dian = models.CharField(max_length=20, blank=True, null=True, help_text="Código estándar DIAN (ej. UNSPSC)")

    iva_tipo = models.CharField(max_length=10, choices=IVA_TIPOS, default="GRAVADO", verbose_name="Tipo de IVA")

    iva_porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2, default=19.00, verbose_name="Porcentaje de IVA"
    )

    unidad_medida = models.CharField(
        max_length=5, default="94", verbose_name="Unidad de Medida"  # 94 es 'Unidad' estándar DIAN
    )

    impoconsumo = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="Impoconsumo (%)")

    descuento = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, help_text="Porcentaje de descuento por defecto (%)"
    )

    # Legacy (se mantendrán para compatibilidad temporal)
    tax_type_id = models.CharField(max_length=4, default="01", verbose_name="Código Impuesto DIAN")  # 01=IVA, 04=INC
    tax_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=19.00, verbose_name="Porcentaje Impuesto"
    )
    is_tax_included = models.BooleanField(default=False, verbose_name="Impuesto incluido en precio")

    class Meta:
        db_table = "productos"
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        indexes = [
            models.Index(fields=["codigo"], name="idx_prod_codigo"),
            models.Index(fields=["categoria"], name="idx_prod_categoria"),
            models.Index(fields=["activo"], name="idx_prod_activo"),
            models.Index(fields=["stock_actual"], name="idx_prod_stock"),
            models.Index(fields=["activo", "stock_actual"], name="idx_prod_activo_stock"),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.iva_tipo})"

    @staticmethod
    @CacheService.cache_product_catalog()
    def get_all():
        """Obtiene todos los productos activos"""
        products = Product.objects.filter(activo=True).select_related("categoria").order_by("-id")
        data = []
        for p in products:
            data.append(
                {
                    "id": p.id,
                    "codigo": p.codigo,
                    "nombre": p.nombre,
                    "descripcion": p.descripcion,
                    "categoria_id": p.categoria_id,
                    "categoria": p.categoria.nombre if p.categoria else None,
                    "precio_compra": p.precio_compra,
                    "precio_venta": p.precio_venta,
                    "stock_minimo": p.stock_minimo,
                    "stock_actual": p.stock_actual,
                    "proveedor_id": p.proveedor_id,
                    "activo": p.activo,
                    "iva_porcentaje": float(p.iva_porcentaje),
                    "iva_tipo": p.iva_tipo,
                    "codigo_dian": p.codigo_dian,
                    "unidad_medida": p.unidad_medida,
                    "impoconsumo": float(p.impoconsumo),
                    "descuento": float(p.descuento),
                }
            )
        return data

    @staticmethod
    def get_by_id(product_id):
        """Obtiene un producto por ID"""
        try:
            p = Product.objects.select_related("categoria").get(id=product_id)
            return {
                "id": p.id,
                "codigo": p.codigo,
                "nombre": p.nombre,
                "descripcion": p.descripcion,
                "categoria_id": p.categoria_id,
                "categoria": p.categoria.nombre if p.categoria else None,
                "precio_compra": p.precio_compra,
                "precio_venta": p.precio_venta,
                "stock_minimo": p.stock_minimo,
                "stock_actual": p.stock_actual,
                "proveedor_id": p.proveedor_id,
                "activo": p.activo,
                "iva_porcentaje": float(p.iva_porcentaje),
                "iva_tipo": p.iva_tipo,
                "codigo_dian": p.codigo_dian,
                "unidad_medida": p.unidad_medida,
                "impoconsumo": float(p.impoconsumo),
                "descuento": float(p.descuento),
            }
        except Product.DoesNotExist:
            return None

    @staticmethod
    def count():
        """Cuenta el total de productos activos"""
        return Product.objects.filter(activo=True).count()

    @staticmethod
    def create(data):
        """Crea un nuevo producto"""
        p = Product.objects.create(
            codigo=data["codigo"],
            nombre=data["nombre"],
            descripcion=data.get("descripcion", ""),
            categoria_id=data["categoria_id"],
            precio_compra=data["precio_compra"],
            precio_venta=data["precio_venta"],
            stock_minimo=data.get("stock_minimo", 10),
            stock_actual=data.get("stock_actual", 0),
            proveedor_id=data.get("proveedor_id"),
            activo=data.get("activo", True),
            codigo_dian=data.get("codigo_dian"),
            iva_tipo=data.get("iva_tipo", "GRAVADO"),
            iva_porcentaje=data.get("iva_porcentaje", 19.00),
            unidad_medida=data.get("unidad_medida", "94"),
            impoconsumo=data.get("impoconsumo", 0.00),
            descuento=data.get("descuento", 0.00),
        )
        return p.id

    @staticmethod
    def update(product_id, data):
        """Actualiza un producto existente"""
        return Product.objects.filter(id=product_id).update(
            codigo=data["codigo"],
            nombre=data["nombre"],
            descripcion=data.get("descripcion", ""),
            categoria_id=data["categoria_id"],
            precio_compra=data["precio_compra"],
            precio_venta=data["precio_venta"],
            stock_minimo=data.get("stock_minimo", 10),
            stock_actual=data.get("stock_actual", 0),
            proveedor_id=data.get("proveedor_id"),
            activo=data.get("activo", True),
            codigo_dian=data.get("codigo_dian"),
            iva_tipo=data.get("iva_tipo"),
            iva_porcentaje=data.get("iva_porcentaje"),
            unidad_medida=data.get("unidad_medida"),
            impoconsumo=data.get("impoconsumo"),
            descuento=data.get("descuento"),
        )

    @staticmethod
    def delete(product_id):
        """Elimina un producto (soft delete cambiando activo a 0)"""
        return Product.objects.filter(id=product_id).update(activo=False)

    @staticmethod
    def get_low_stock(limit=10):
        """Obtiene productos con stock bajo"""
        products = (
            Product.objects.filter(stock_actual__lt=10, activo=True)
            .select_related("categoria")
            .order_by("stock_actual")[:limit]
        )
        data = []
        for p in products:
            data.append(
                {
                    "id": p.id,
                    "nombre": p.nombre,
                    "stock_actual": p.stock_actual,
                    "categoria": p.categoria.nombre if p.categoria else None,
                }
            )
        return data
