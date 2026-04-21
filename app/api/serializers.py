from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from app.models.category import Category
from app.models.product import Product
from app.models.supplier import Supplier


# ============================================================================
# JWT Token Serializer (Anti-Tampering)
# ============================================================================
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Generar claims personalizados
        token["username"] = user.username
        token["email"] = user.email
        token["role"] = (
            user.role.name
            if hasattr(user, "role") and user.role
            else "Cliente"
        )

        return token


# ============================================================================
# Serializers de Catálogo (Headless API - Fase 1)
# ============================================================================
class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "nombre", "descripcion"]


class ProveedorResumenSerializer(serializers.ModelSerializer):
    """Serializer resumido para anidamiento en Producto."""

    class Meta:
        model = Supplier
        fields = ["id", "nombre", "nit", "email", "telefono", "ciudad"]


class ProductoSerializer(serializers.ModelSerializer):
    """
    Serializer completo del modelo Producto.
    Incluye relaciones foráneas anidadas en lectura
    y acepta IDs planos en escritura.
    """

    # Lectura: expone datos anidados del FK
    categoria_detail = CategoriaSerializer(source="categoria", read_only=True)
    proveedor_detail = ProveedorResumenSerializer(
        source="proveedor", read_only=True
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "codigo",
            "nombre",
            "descripcion",
            "categoria",          # FK id (escritura)
            "categoria_detail",   # Objeto anidado (lectura)
            "proveedor",          # FK id (escritura)
            "proveedor_detail",   # Objeto anidado (lectura)
            "precio_compra",
            "precio_venta",
            "stock_actual",
            "stock_minimo",
            "activo",
            "tax_type_id",
            "tax_percentage",
            "is_tax_included",
        ]
        read_only_fields = ["id"]

    def to_representation(self, instance):
        """Oculta precio_compra para no administradores."""
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request and not request.user.is_superuser:
            user = request.user
            is_admin = (
                hasattr(user, "role")
                and user.role
                and user.role.name == "Administrador"
            )
            if not is_admin:
                data.pop("precio_compra", None)
        return data
