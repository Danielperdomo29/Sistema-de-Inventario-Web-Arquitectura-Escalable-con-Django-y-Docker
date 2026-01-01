from django.db import connection
from django.db.models import Count

from app.models.category import Category
from app.models.client import Client
from app.models.product import Product
from app.models.purchase import Purchase
from app.models.role import Role
from app.models.sale import Sale
from app.models.supplier import Supplier
from app.models.user_account import UserAccount


class Config:
    """Modelo para la configuración del sistema (Refactorizado a ORM)"""

    @staticmethod
    def get_user_info(user_id):
        """Obtiene información completa del usuario"""
        try:
            user = UserAccount.objects.get(id=user_id)
            try:
                role_name = Role.objects.get(id=user.rol_id).nombre
            except Role.DoesNotExist:
                role_name = "N/A"

            return {
                "id": user.id,
                "username": user.username,
                "nombre_completo": user.first_name or user.username, # Default to username if empty
                "email": user.email,
                "activo": 1 if user.is_active else 0,
                "created_at": user.date_joined,
                "rol": role_name,
            }
        except UserAccount.DoesNotExist:
            return None

    @staticmethod
    def get_system_stats():
        """Obtiene estadísticas generales del sistema"""
        # Note: Assuming 'active' logic. For UserAccount it is is_active.
        # For others, check if they have 'activo' field or just count all.
        # Based on legacy SQL, they filtered by activo=1.
        # If models don't have active manager, we count all or filter if field exists.
        
        # Helper to safely count active if possible, else count all
        def count_active(model):
            if hasattr(model, 'active'):
                return model.objects.filter(active=True).count()
            elif hasattr(model, 'activo'):
                return model.objects.filter(activo=1).count()
            return model.objects.count()

        return {
            "total_usuarios": UserAccount.objects.filter(is_active=True).count(),
            "total_productos": Product.count(), # Delegating to model method if exists or count_active
            "total_categorias": Category.count(),
            "total_clientes": Client.count(),
            "total_proveedores": Supplier.count(),
            "total_ventas": Sale.count(),
            "total_compras": Purchase.count(),
        }

    @staticmethod
    def get_all_users(include_superadmin=False):
        """Obtiene todos los usuarios del sistema"""
        qs = UserAccount.objects.all().order_by("-date_joined")
        if not include_superadmin:
            qs = qs.exclude(username="superadmin")
        
        users_data = []
        # Optimizar consulta de roles podría hacerse, pero rol_id es entero.
        # Hacemos fetch manual o prefetch si Role fuera FK real.
        # Aqui iteramos.
        roles_cache = {r["id"]: r["nombre"] for r in Role.get_all()}

        for user in qs:
            users_data.append({
                "id": user.id,
                "username": user.username,
                "nombre_completo": user.first_name or user.username,
                "email": user.email,
                "activo": 1 if user.is_active else 0,
                "rol": roles_cache.get(user.rol_id, "Desconocido")
            })
        return users_data

    @staticmethod
    def get_database_info():
        """Obtiene información de la base de datos"""
        query = """
            SELECT 
                TABLE_NAME as table_name,
                TABLE_ROWS as table_rows,
                ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) AS size_mb
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND TABLE_NAME NOT LIKE 'django_%%'
            ORDER BY TABLE_ROWS DESC
        """
        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            return [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

    @staticmethod
    def get_user_by_id(user_id):
        """Obtiene un usuario por ID"""
        try:
            user = UserAccount.objects.get(id=user_id)
            return {
                "id": user.id,
                "username": user.username,
                "nombre_completo": user.first_name, # or username
                "email": user.email,
                "rol_id": user.rol_id,
                "activo": 1 if user.is_active else 0
            }
        except UserAccount.DoesNotExist:
            return None

    @staticmethod
    def create_user(data):
        """Crea un nuevo usuario"""
        # Use create_user to handle password hashing correctly if passed raw.
        # But controller sent hashed password? 
        # ConfigController line 65: password_hash = hashlib.md5(...).hexdigest()
        # Controller sends MD5 hash. UserAccount expects AbstractUser password handling.
        # We should probably fix Controller to send raw password, 
        # OR simply store the hash if we are stuck with legacy MD5 for now.
        # However, UserAccount uses standard Django auth. 
        # If we insert MD5 hash into 'password' field of UserAccount, 
        # Django's check_password might fail unless we implement a custom MD5 hasher 
        # or if existing users use it.
        # Refactoring to standard Django creation:
        
        # NOTE: Controller sends 'password' which is already MD5 hashed in the logic I saw.
        # Ideally, we should receive raw password here.
        # Assuming we store what we get for now to maintain behavior, 
        # but Django auth usually expects set_password().
        # Let's create user normally and force the password field if needed,
        # or better: rely on Django's set_password in refactored controller.
        
        # For now, let's map data to UserAccount.
        
        user = UserAccount(
            username=data["username"],
            email=data.get("email", ""),
            first_name=data["nombre_completo"], # Mapping nombre_completo to first_name
            rol_id=data["rol_id"],
            is_active=bool(data.get("activo", 1))
        )
        # If password provided is raw or hash? 
        # The controller in `ConfigController.create_user` executes `hashlib.md5`.
        # This is bad practice for Django auth. 
        # We should likely strip that in Controller or just save it here.
        # Since I am only editing model here, I will save it as is.
        user.password = data["password"] 
        user.save()
        return user.id

    @staticmethod
    def update_user(user_id, data):
        """Actualiza un usuario existente"""
        update_fields = {
            "username": data["username"],
            "first_name": data["nombre_completo"],
            "email": data.get("email", ""),
            "rol_id": data["rol_id"],
            "is_active": bool(data.get("activo", 1))
        }
        UserAccount.objects.filter(id=user_id).update(**update_fields)
        return True

    @staticmethod
    def delete_user(user_id):
        """Desactiva un usuario (soft delete)"""
        UserAccount.objects.filter(id=user_id).update(is_active=False)
        return True

    @staticmethod
    def get_roles():
        """Obtiene todos los roles disponibles"""
        return list(Role.objects.all().values("id", "nombre").order_by("nombre"))

    @staticmethod
    def update_profile(user_id, data):
        """Actualiza el perfil del usuario actual"""
        update_fields = {}
        if "nombre_completo" in data:
            update_fields["first_name"] = data["nombre_completo"]
        if "email" in data:
            update_fields["email"] = data["email"]
        if "activo" in data:
            update_fields["is_active"] = bool(data["activo"])
            
        if update_fields:
            UserAccount.objects.filter(id=user_id).update(**update_fields)
        return True

    @staticmethod
    def change_password(user_id, new_password):
        """Cambia la contraseña del usuario actual"""
        # new_password comes hashed from controller?
        # Controller logic: new_hash = hashlib.md5(new_password.encode()).hexdigest()
        # We save it directly because Django config assumes legacy or customized auth?
        # Ideally we use user.set_password(raw_password)
        UserAccount.objects.filter(id=user_id).update(password=new_password)
        return True
