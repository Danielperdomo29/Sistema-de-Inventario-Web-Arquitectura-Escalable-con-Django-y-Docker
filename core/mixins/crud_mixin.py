"""
CRUDMixin - Operaciones CRUD estandarizadas para modelos Django.

Este mixin proporciona métodos estáticos get_all(), get_by_id(), count(),
create(), update() y delete() que retornan diccionarios (no instancias),
manteniendo compatibilidad con la API existente de los modelos.

Uso:
    class MyModel(CRUDMixin, models.Model):
        # Campos del modelo
        nombre = models.CharField(max_length=100)

        class Meta:
            db_table = "my_table"

        # Configurar campos para serialización
        crud_fields = ['id', 'nombre', 'descripcion']  # Opcional
        crud_order_by = 'nombre'  # Opcional, default: '-id'

Para modelos con soft delete (campo `activo`), usar SoftDeleteMixin en su lugar.
"""

from typing import Any, Dict, List, Optional


class CRUDMixin:
    """
    Mixin que proporciona operaciones CRUD básicas.
    Retorna diccionarios para compatibilidad con controladores existentes.

    Configuración via atributos de clase:
        - crud_fields: List[str] - campos a incluir en serialización
        - crud_order_by: str - campo para ordenar (default: '-id')
        - crud_uses_soft_delete: bool - si usa campo 'activo' (default: False)
        - select_related_default: List[str] - relaciones FK a pre-cargar
        - prefetch_related_default: List[str] - relaciones M2M a pre-cargar
    """

    # Atributos de configuración (pueden ser sobreescritos en subclases)
    crud_fields: Optional[List[str]] = None
    crud_order_by: str = "-id"
    crud_uses_soft_delete: bool = False
    select_related_default: Optional[List[str]] = None
    prefetch_related_default: Optional[List[str]] = None

    @classmethod
    def _get_base_queryset(cls, with_relations: bool = False):
        """
        Retorna el queryset base, filtrado por activo si aplica.

        Args:
            with_relations: Si True, aplica select_related y prefetch_related.
        """
        qs = cls.objects.all()
        if cls.crud_uses_soft_delete and hasattr(cls, "activo"):
            qs = qs.filter(activo=True)

        if with_relations:
            if cls.select_related_default:
                qs = qs.select_related(*cls.select_related_default)
            if cls.prefetch_related_default:
                qs = qs.prefetch_related(*cls.prefetch_related_default)

        return qs

    @classmethod
    def _get_fields(cls) -> List[str]:
        """Retorna la lista de campos para serialización."""
        if cls.crud_fields:
            return cls.crud_fields
        # Default: todos los campos del modelo excepto relaciones complejas
        return [f.name for f in cls._meta.fields if not f.is_relation or f.many_to_one]

    @classmethod
    def get_all(cls) -> List[Dict[str, Any]]:
        """
        Obtiene todos los registros activos.

        Returns:
            Lista de diccionarios con los campos configurados.
        """
        return list(cls._get_base_queryset().values(*cls._get_fields()).order_by(cls.crud_order_by))

    @classmethod
    def get_by_id(cls, obj_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un registro por su ID.

        Args:
            obj_id: ID del registro a buscar.

        Returns:
            Diccionario con los datos del registro, o None si no existe.
        """
        try:
            qs = cls._get_base_queryset().filter(id=obj_id)
            return qs.values(*cls._get_fields()).first()
        except Exception:
            return None

    @classmethod
    def get_all_instances(cls) -> List:
        """
        Obtiene todos los registros como instancias de modelo (no diccionarios).
        Aplica select_related y prefetch_related si están configurados.

        Usar para modelos con FK que necesitan acceder a relaciones.

        Returns:
            Lista de instancias del modelo.
        """
        return list(cls._get_base_queryset(with_relations=True).order_by(cls.crud_order_by))

    @classmethod
    def get_instance_by_id(cls, obj_id: int):
        """
        Obtiene una instancia del modelo por ID.
        Aplica select_related y prefetch_related si están configurados.

        Args:
            obj_id: ID del registro a buscar.

        Returns:
            Instancia del modelo o None.
        """
        try:
            return cls._get_base_queryset(with_relations=True).get(id=obj_id)
        except cls.DoesNotExist:
            return None

    @classmethod
    def count(cls) -> int:
        """
        Cuenta el total de registros activos.

        Returns:
            Número total de registros.
        """
        return cls._get_base_queryset().count()

    @classmethod
    def create(cls, data: Dict[str, Any]) -> int:
        """
        Crea un nuevo registro.

        Args:
            data: Diccionario con los datos del registro.

        Returns:
            ID del registro creado.
        """
        # Filtrar solo campos válidos del modelo
        valid_fields = {f.name for f in cls._meta.fields}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}

        instance = cls.objects.create(**filtered_data)
        return instance.id

    @classmethod
    def update(cls, obj_id: int, data: Dict[str, Any]) -> int:
        """
        Actualiza un registro existente.

        Args:
            obj_id: ID del registro a actualizar.
            data: Diccionario con los datos a actualizar.

        Returns:
            Número de registros actualizados (0 o 1).
        """
        # Filtrar solo campos válidos del modelo (excepto id)
        valid_fields = {f.name for f in cls._meta.fields if f.name != "id"}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}

        return cls.objects.filter(id=obj_id).update(**filtered_data)

    @classmethod
    def delete(cls, obj_id: int) -> Any:
        """
        Elimina un registro.
        - Si crud_uses_soft_delete=True: marca activo=False
        - Si crud_uses_soft_delete=False: elimina de la BD

        Args:
            obj_id: ID del registro a eliminar.

        Returns:
            Resultado de la operación (int para soft delete, tuple para hard delete).
        """
        if cls.crud_uses_soft_delete:
            return cls.objects.filter(id=obj_id).update(activo=False)
        else:
            return cls.objects.filter(id=obj_id).delete()


class SoftDeleteMixin(CRUDMixin):
    """
    Extensión de CRUDMixin con soft delete habilitado por defecto.
    Usar para modelos que tienen campo `activo`.

    Ejemplo:
        class Category(SoftDeleteMixin, models.Model):
            nombre = models.CharField(max_length=100)
            activo = models.BooleanField(default=True)

            crud_fields = ['id', 'nombre', 'descripcion']
            crud_order_by = 'nombre'
    """

    crud_uses_soft_delete = True
