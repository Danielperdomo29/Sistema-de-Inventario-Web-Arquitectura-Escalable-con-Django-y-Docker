from django.db import models


class Supplier(models.Model):
    """Modelo de Proveedor - Adaptado para Colombia"""

    nombre = models.CharField(max_length=200, verbose_name="Nombre/Razón Social")
    
    # Identificación tributaria Colombia
    nit = models.CharField(
        max_length=15, 
        blank=True, 
        null=True, 
        verbose_name="NIT",
        help_text="Número de Identificación Tributaria (sin dígito de verificación)"
    )
    digito_verificacion = models.CharField(
        max_length=1, 
        blank=True, 
        null=True, 
        verbose_name="DV",
        help_text="Dígito de verificación del NIT"
    )
    rut = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        verbose_name="RUT",
        help_text="Registro Único Tributario"
    )
    
    # Información de contacto
    telefono = models.CharField(max_length=50, blank=True, null=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo electrónico")
    direccion = models.TextField(blank=True, null=True, verbose_name="Dirección")
    ciudad = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ciudad")
    
    activo = models.BooleanField(default=True)

    # Campos para retención en la fuente
    is_tax_declarant = models.BooleanField(
        default=False,
        verbose_name="Es declarante de renta",
        help_text="Marque si el proveedor es declarante de renta (afecta tarifas de retención)"
    )
    
    tax_identification_type = models.CharField(
        max_length=20,
        choices=[
            ('NIT', 'NIT'),
            ('CEDULA', 'Cédula'),
            ('PASAPORTE', 'Pasaporte'),
            ('EXTRANJERIA', 'Cédula de extranjería'),
        ],
        default='NIT',
        verbose_name="Tipo de identificación tributaria"
    )
    
    retention_responsibility = models.CharField(
        max_length=50,
        choices=[
            ('RESPONSABLE', 'Responsable de IVA'),
            ('NO_RESPONSABLE', 'No responsable de IVA'),
            ('SIMPLIFICADO', 'Régimen simplificado'),
            ('EXENTO', 'Exento'),
        ],
        default='RESPONSABLE',
        verbose_name="Responsabilidad de retención"
    )
    
    retention_concepts = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Conceptos de retención aplicables",
        help_text="Lista de conceptos de retención que aplican a este proveedor"
    )

    class Meta:
        db_table = "proveedores"
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

    def __str__(self):
        if self.nit:
            return f"{self.nombre} (NIT: {self.nit}-{self.digito_verificacion or '?'})"
        return self.nombre
    
    @property
    def nit_completo(self):
        """Retorna NIT con dígito de verificación"""
        if self.nit:
            return f"{self.nit}-{self.digito_verificacion or '?'}"
        return None

    @staticmethod
    def get_all():
        """Obtener todos los proveedores activos"""
        return list(Supplier.objects.filter(activo=True).values().order_by("nombre"))

    @staticmethod
    def get_by_id(supplier_id):
        """Obtener un proveedor por ID"""
        try:
            return Supplier.objects.filter(id=supplier_id, activo=True).values().first()
        except Exception:
            return None

    @staticmethod
    def count():
        """Contar total de proveedores activos"""
        return Supplier.objects.filter(activo=True).count()

    @staticmethod
    def create(data):
        """Crear un nuevo proveedor"""
        supplier = Supplier.objects.create(
            nombre=data["nombre"],
            nit=data.get("nit", ""),
            digito_verificacion=data.get("digito_verificacion", ""),
            rut=data.get("rut", ""),
            telefono=data.get("telefono", ""),
            email=data.get("email", ""),
            direccion=data.get("direccion", ""),
            ciudad=data.get("ciudad", ""),
            activo=True,
        )
        return supplier.id

    @staticmethod
    def update(supplier_id, data):
        """Actualizar un proveedor"""
        return Supplier.objects.filter(id=supplier_id).update(
            nombre=data["nombre"],
            nit=data.get("nit", ""),
            digito_verificacion=data.get("digito_verificacion", ""),
            rut=data.get("rut", ""),
            telefono=data.get("telefono", ""),
            email=data.get("email", ""),
            direccion=data.get("direccion", ""),
            ciudad=data.get("ciudad", ""),
        )

    @staticmethod
    def delete(supplier_id):
        """Eliminar lógicamente un proveedor"""
        return Supplier.objects.filter(id=supplier_id).update(activo=False)

    def get_applicable_retention_rate(self, concept_key):
        """
        Obtiene la tarifa de retención aplicable para este proveedor
        """
        from app.fiscal.services.retention_service import WithholdingTaxService
        from decimal import Decimal
        
        concept = WithholdingTaxService.RETENTION_CONCEPTS.get(concept_key)
        if not concept:
            return Decimal('0.00')
        
        if self.is_tax_declarant:
            return concept['declarant_rate']
        else:
            return concept['non_declarant_rate']

