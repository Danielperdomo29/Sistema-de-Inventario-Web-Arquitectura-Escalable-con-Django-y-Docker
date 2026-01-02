from django.db import models
from django.utils.translation import gettext_lazy as _
from app.fiscal.core.security.encryption import FiscalEncryptionManager

class FiscalConfig(models.Model):
    """
    Configuración centralizada para Facturación Electrónica DIAN.
    Almacena certificados y credenciales de forma segura.
    """
    
    ENVIRONMENT_CHOICES = [
        (1, 'Producción'),
        (2, 'Habilitación (Pruebas)'),
    ]

    # Identificación del Emisor
    nit_emisor = models.CharField(_("NIT Emisor"), max_length=20, help_text="Sin dígito de verificación")
    dv_emisor = models.CharField(_("Dígito Verificación"), max_length=1)
    razon_social = models.CharField(_("Razón Social"), max_length=255)
    
    # Proveedor Tecnológico (Si aplica, o Propio)
    software_id = models.CharField(_("ID Software"), max_length=100, help_text="Proporcionado por la DIAN")
    pin_software = models.CharField(_("PIN Software"), max_length=100, help_text="Para calcular la SoftwareSecurityCode")
    
    # Configuración Técnica
    ambiente = models.IntegerField(choices=ENVIRONMENT_CHOICES, default=2)
    test_set_id = models.CharField(_("Test Set ID"), max_length=255, blank=True, null=True, help_text="Solo para habilitación")
    
    # Resolución de Facturación
    numero_resolucion = models.CharField(_("Num. Resolución"), max_length=50, default="18760000001")
    fecha_resolucion = models.DateField(_("Fecha Resolución"), null=True, blank=True)
    prefijo = models.CharField(_("Prefijo"), max_length=10, default="SETP")
    rango_desde = models.BigIntegerField(_("Rango Desde"), default=99000000)
    rango_hasta = models.BigIntegerField(_("Rango Hasta"), default=99500000)
    clave_tecnica = models.CharField(_("Clave Técnica"), max_length=255, default="fc8eac422eba16e22ffd8c6f94b3f40a6e38162c")
    
    # Certificado Digital
    certificado_archivo = models.FileField(upload_to='fiscal/certs/', help_text="Archivo .p12 o .pfx")
    _certificado_password = models.CharField(_("Contraseña Certificado (Encriptada)"), max_length=512)
    
    # Metadatos
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Configuración Fiscal DIAN"
        verbose_name_plural = "Configuraciones Fiscales"

    def set_password(self, raw_password):
        """Encripta la contraseña del certificado antes de guardar"""
        self._certificado_password = FiscalEncryptionManager.encrypt(raw_password)

    def get_password(self):
        """Desencripta la contraseña para uso interno"""
        try:
            return FiscalEncryptionManager.decrypt(self._certificado_password)
        except Exception:
            return None

    def __str__(self):
        return f"Configuración DIAN ({self.get_ambiente_display()}) - {self.nit_emisor}"
