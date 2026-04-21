from django.db import models


class UIConfig(models.Model):
    """Modelo para configuración dinámica de la interfaz de usuario."""

    name = models.CharField(max_length=100, default="Configuración por defecto")
    primary_color = models.CharField(max_length=20, default="#3B82F6")
    secondary_color = models.CharField(max_length=20, default="#1E40AF")
    welcome_title = models.CharField(max_length=200, default="PayRoll")
    welcome_subtitle = models.CharField(max_length=500, default="Fill in your details to get started")
    logo = models.ImageField(upload_to="ui/logos/", null=True, blank=True)
    footer_text = models.CharField(
        max_length=500,
        default="Free 14-day trial • No credit card required • Cancel anytime",
    )
    enable_social_login = models.BooleanField(default=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración de UI"
        verbose_name_plural = "Configuraciones de UI"

    def __str__(self):
        return self.name

    @classmethod
    def get_active(cls):
        """Obtiene la configuración activa o crea una por defecto."""
        config = cls.objects.filter(is_active=True).first()
        if not config:
            config, _ = cls.objects.get_or_create(name="Configuración Inicial", defaults={"is_active": True})
        return config

    def save(self, *args, **kwargs):
        """Asegura que solo haya una configuración activa."""
        if self.is_active:
            UIConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class BackgroundImage(models.Model):
    """Imágenes de fondo para el carrusel de login."""

    ui_config = models.ForeignKey(UIConfig, related_name="background_images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="ui/backgrounds/")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Imagen de Fondo"
        verbose_name_plural = "Imágenes de Fondo"
        ordering = ["order"]

    def __str__(self):
        return f"Imagen {self.order} para {self.ui_config.name}"
