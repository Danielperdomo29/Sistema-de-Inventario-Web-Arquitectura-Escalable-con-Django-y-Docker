"""
Modelo PerfilFiscal - Información tributaria de terceros.

Almacena datos fiscales de clientes y proveedores para cumplimiento DIAN.
"""
from django.db import models
from django.core.exceptions import ValidationError
from app.fiscal.validators.nit_validator import NITValidator
from app.fiscal.validators.fiscal_validators import (
    validar_codigo_dane_departamento,
    validar_codigo_dane_municipio,
    validar_responsabilidades_tributarias,
    validar_codigo_ciiu,
    validar_numero_documento,
    sanitizar_texto
)


class PerfilFiscal(models.Model):
    """
    Perfil fiscal de terceros (clientes/proveedores).
    
    Almacena información tributaria necesaria para facturación electrónica
    y cumplimiento de obligaciones ante la DIAN.
    
    Attributes:
        cliente: Relación OneToOne con Client (opcional)
        proveedor: Relación OneToOne con Supplier (opcional)
        tipo_documento: Tipo de identificación tributaria
        numero_documento: Número de identificación
        dv: Dígito verificador (auto-calculado para NIT)
        tipo_persona: Jurídica o Natural
        responsabilidades: Lista de responsabilidades tributarias
        regimen: Régimen tributario
        departamento_codigo: Código DANE del departamento
        municipio_codigo: Código DANE del municipio
    
    Constraints:
        - Debe tener cliente O proveedor (no ambos, no ninguno)
        - DV se calcula automáticamente para NIT
        - Códigos DANE deben ser válidos
    
    Examples:
        >>> perfil = PerfilFiscal.objects.create(
        ...     cliente=cliente,
        ...     tipo_documento='31',
        ...     numero_documento='900123456',
        ...     tipo_persona='J',
        ...     regimen='48',
        ...     departamento_codigo='11',
        ...     municipio_codigo='001',
        ...     email_facturacion='facturacion@empresa.com',
        ...     direccion='Calle 123'
        ... )
        >>> perfil.dv
        '8'
    """
    
    # Choices
    TIPO_DOCUMENTO_CHOICES = [
        ('13', 'Cédula de Ciudadanía'),
        ('22', 'Cédula de Extranjería'),
        ('31', 'NIT'),
        ('41', 'Pasaporte'),
        ('42', 'Documento de Identificación Extranjero'),
    ]
    
    TIPO_PERSONA_CHOICES = [
        ('J', 'Jurídica'),
        ('N', 'Natural'),
    ]
    
    REGIMEN_CHOICES = [
        ('48', 'Responsable de IVA'),
        ('49', 'No responsable de IVA'),
    ]
    
    # Relaciones (OneToOne con Client o Supplier)
    cliente = models.OneToOneField(
        'Client',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='perfil_fiscal',
        help_text='Cliente asociado a este perfil fiscal'
    )
    
    proveedor = models.OneToOneField(
        'Supplier',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='perfil_fiscal',
        help_text='Proveedor asociado a este perfil fiscal'
    )
    
    # Identificación Tributaria
    tipo_documento = models.CharField(
        max_length=2,
        choices=TIPO_DOCUMENTO_CHOICES,
        help_text='Tipo de documento de identificación'
    )
    
    numero_documento = models.CharField(
        max_length=20,
        help_text='Número de identificación tributaria'
    )
    
    dv = models.CharField(
        max_length=1,
        blank=True,
        help_text='Dígito verificador (auto-calculado para NIT)'
    )
    
    # Tipo de Persona
    tipo_persona = models.CharField(
        max_length=1,
        choices=TIPO_PERSONA_CHOICES,
        help_text='Tipo de persona (Jurídica o Natural)'
    )
    
    # Responsabilidades Tributarias
    responsabilidades = models.JSONField(
        default=list,
        blank=True,
        help_text='Lista de responsabilidades tributarias (ej: ["O-13", "O-15"])'
    )
    
    # Régimen Tributario
    regimen = models.CharField(
        max_length=2,
        choices=REGIMEN_CHOICES,
        help_text='Régimen tributario'
    )
    
    # Ubicación Geográfica (DANE)
    departamento_codigo = models.CharField(
        max_length=2,
        help_text='Código DANE del departamento (2 dígitos)'
    )
    
    municipio_codigo = models.CharField(
        max_length=3,
        help_text='Código DANE del municipio (3 dígitos)'
    )
    
    # Información Adicional
    nombre_comercial = models.CharField(
        max_length=200,
        blank=True,
        help_text='Nombre comercial (opcional)'
    )
    
    actividad_economica = models.CharField(
        max_length=4,
        blank=True,
        help_text='Código CIIU de actividad económica (4 dígitos)'
    )
    
    # Contacto
    email_facturacion = models.EmailField(
        help_text='Email para envío de facturas electrónicas'
    )
    
    telefono = models.CharField(
        max_length=20,
        blank=True,
        help_text='Teléfono de contacto'
    )
    
    direccion = models.TextField(
        help_text='Dirección fiscal completa'
    )
    
    # Metadata
    activo = models.BooleanField(
        default=True,
        help_text='Indica si el perfil está activo'
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha de creación del perfil'
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text='Fecha de última actualización'
    )
    
    class Meta:
        db_table = 'perfil_fiscal'
        verbose_name = 'Perfil Fiscal'
        verbose_name_plural = 'Perfiles Fiscales'
        indexes = [
            models.Index(fields=['numero_documento']),
            models.Index(fields=['tipo_documento', 'numero_documento']),
        ]
    
    def clean(self):
        """
        Validaciones personalizadas del modelo.
        
        Valida:
        - Debe tener cliente O proveedor (no ambos, no ninguno)
        - Formato de número de documento
        - Códigos DANE
        - Responsabilidades tributarias
        - Email de facturación
        
        Raises:
            ValidationError: Si alguna validación falla
        """
        errors = {}
        
        # Validar que tenga cliente O proveedor
        if not self.cliente and not self.proveedor:
            errors['__all__'] = 'El perfil fiscal debe tener un cliente o un proveedor asociado'
        
        if self.cliente and self.proveedor:
            errors['__all__'] = 'El perfil fiscal no puede tener ambos cliente y proveedor'
        
        # Validar número de documento
        try:
            validar_numero_documento(self.numero_documento, self.tipo_documento)
        except ValidationError as e:
            errors['numero_documento'] = e.message
        
        # Validar códigos DANE
        try:
            validar_codigo_dane_departamento(self.departamento_codigo)
        except ValidationError as e:
            errors['departamento_codigo'] = e.message
        
        try:
            validar_codigo_dane_municipio(self.municipio_codigo)
        except ValidationError as e:
            errors['municipio_codigo'] = e.message
        
        # Validar responsabilidades
        if self.responsabilidades:
            try:
                validar_responsabilidades_tributarias(self.responsabilidades)
            except ValidationError as e:
                errors['responsabilidades'] = e.message
        
        # Validar código CIIU
        if self.actividad_economica:
            try:
                validar_codigo_ciiu(self.actividad_economica)
            except ValidationError as e:
                errors['actividad_economica'] = e.message
        
        # Validar email (prevenir injection)
        if self.email_facturacion and '\n' in self.email_facturacion:
            errors['email_facturacion'] = 'Email no puede contener saltos de línea'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Override save para auto-calcular DV y sanitizar datos.
        
        - Calcula DV automáticamente para NIT
        - Sanitiza nombre comercial y dirección
        - Ejecuta validaciones
        """
        # Auto-calcular DV para NIT
        if self.tipo_documento == '31':  # NIT
            self.dv = NITValidator.calcular_dv(self.numero_documento)
        else:
            self.dv = ''
        
        # Sanitizar textos
        if self.nombre_comercial:
            self.nombre_comercial = sanitizar_texto(self.nombre_comercial, 200)
        
        # Ejecutar validaciones
        self.full_clean()
        
        super().save(*args, **kwargs)
    
    def get_nombre_completo(self):
        """
        Retorna el nombre del cliente o proveedor asociado.
        
        Returns:
            str: Nombre del tercero
        """
        if self.cliente:
            return self.cliente.nombre
        elif self.proveedor:
            return self.proveedor.nombre
        return "Sin nombre"
    
    def get_nit_formateado(self):
        """
        Retorna el NIT formateado con puntos y guión.
        
        Returns:
            str: NIT formateado (ej: "900.123.456-8")
        
        Examples:
            >>> perfil.get_nit_formateado()
            "900.123.456-8"
        """
        if self.tipo_documento != '31':
            return self.numero_documento
        
        nit = self.numero_documento
        dv = self.dv or NITValidator.calcular_dv(nit)
        
        # Formatear con puntos: XXX.XXX.XXX-D
        if len(nit) == 9:
            return f"{nit[0:3]}.{nit[3:6]}.{nit[6:9]}-{dv}"
        elif len(nit) == 10:
            return f"{nit[0:3]}.{nit[3:6]}.{nit[6:10]}-{dv}"
        else:
            return f"{nit}-{dv}"
    
    def es_gran_contribuyente(self):
        """
        Verifica si tiene responsabilidad de Gran Contribuyente (O-13).
        
        Returns:
            bool: True si es gran contribuyente
        """
        return 'O-13' in self.responsabilidades
    
    def es_autoretenedor(self):
        """
        Verifica si tiene responsabilidad de Autoretenedor (O-15).
        
        Returns:
            bool: True si es autoretenedor
        """
        return 'O-15' in self.responsabilidades
    
    def __str__(self):
        """Representación en string del perfil fiscal"""
        nombre = self.get_nombre_completo()
        return f"{nombre} - {self.numero_documento}"
