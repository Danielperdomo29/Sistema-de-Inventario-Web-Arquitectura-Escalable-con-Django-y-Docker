from django.db import models
from core.mixins import SoftDeleteMixin


class Supplier(SoftDeleteMixin, models.Model):
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

    # Configuración del mixin CRUD
    crud_order_by = 'nombre'

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
