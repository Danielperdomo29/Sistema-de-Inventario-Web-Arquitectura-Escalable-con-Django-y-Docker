from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.views import TokenObtainPairView

from app.api.permissions import IsAdminOrReadOnly
from app.api.serializers import CustomTokenObtainPairSerializer, ProductoSerializer
from app.models.product import Product


# ============================================================================
# JWT View (Anti-Tampering)
# ============================================================================
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# ============================================================================
# Paginación personalizada
# ============================================================================
class ProductoPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


# ============================================================================
# API ViewSet de Productos (Headless - Fase 1)
# ============================================================================
class ProductoViewSet(viewsets.ModelViewSet):
    """
    API endpoint CRUD para gestionar productos del inventario.
    Requiere autenticación JWT (Bearer Token).

    Endpoints generados automáticamente:
        GET    /api/v1/productos/          → Lista paginada
        POST   /api/v1/productos/          → Crear (solo Admin)
        GET    /api/v1/productos/{id}/     → Detalle
        PUT    /api/v1/productos/{id}/     → Actualizar (solo Admin)
        PATCH  /api/v1/productos/{id}/     → Actualizar parcial (solo Admin)
        DELETE /api/v1/productos/{id}/     → Eliminar (solo Admin)

    Filtros:
        ?search=laptop           → Busca en nombre, codigo, descripcion
        ?categoria=1             → Filtra por FK categoría
        ?proveedor=2             → Filtra por FK proveedor
        ?ordering=precio_venta   → Ordena por campo
        ?page=2&page_size=10     → Paginación
    """

    queryset = (
        Product.objects.filter(activo=True)
        .select_related("categoria", "proveedor")
        .order_by("nombre")
    )
    serializer_class = ProductoSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    pagination_class = ProductoPagination

    # Filtros, búsqueda y ordenamiento
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["categoria", "proveedor", "activo"]
    search_fields = ["nombre", "codigo", "descripcion"]
    ordering_fields = [
        "nombre",
        "precio_venta",
        "stock_actual",
        "codigo",
    ]
    ordering = ["nombre"]

    def perform_destroy(self, instance):
        """Soft delete: desactiva en lugar de borrar físicamente."""
        instance.activo = False
        instance.save()
