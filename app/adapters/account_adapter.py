"""
Custom Account Adapter para django-allauth.
Sincroniza usuarios de allauth con el sistema existente.
"""

from django.utils import timezone

from allauth.account.adapter import DefaultAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Adapter personalizado para sincronizar allauth con sistema existente
    """

    def save_user(self, request, user, form, commit=True):
        """
        Guarda el usuario y configura valores por defecto del sistema
        """
        user = super().save_user(request, user, form, commit=False)

        # Configurar rol por defecto (2 = Usuario)
        if not hasattr(user, "rol_id") or user.rol_id is None:
            user.rol_id = 2

        # Marcar que usa allauth
        user.use_allauth = True

        if commit:
            user.save()

        return user

    def populate_username(self, request, user):
        """
        Genera username automáticamente desde email si no existe
        """
        if not user.username:
            # Usar parte del email como username
            email_parts = user.email.split("@")
            base_username = email_parts[0]

            # Asegurar que sea único
            from app.models.user_account import UserAccount

            username = base_username
            counter = 1
            while UserAccount.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user.username = username

        return user

    def confirm_email(self, request, email_address):
        """
        Callback cuando se confirma un email
        """
        super().confirm_email(request, email_address)

        # Marcar email_verified en UserAccount
        user = email_address.user
        if hasattr(user, "email_verified"):
            user.email_verified = True
            user.email_verified_at = timezone.now()
            user.save(update_fields=["email_verified", "email_verified_at"])

    def get_login_redirect_url(self, request):
        """
        Redirige al dashboard después de login exitoso
        """
        # Siempre redirigir al dashboard principal
        return "/"

    def get_signup_redirect_url(self, request):
        """
        Redirige al dashboard después de registro exitoso
        """
        # Después de confirmar email, ir al dashboard
        return "/"
