from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Generar claims personalizados
        token["username"] = user.username
        token["email"] = user.email
        token["role"] = user.role.name if hasattr(user, "role") and user.role else "Cliente"

        return token
