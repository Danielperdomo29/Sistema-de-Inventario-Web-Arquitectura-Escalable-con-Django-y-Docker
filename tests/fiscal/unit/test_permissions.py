"""
Tests para control de acceso fiscal.
"""
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from app.fiscal.permissions import FiscalDataPermission
from app.fiscal.decorators import require_fiscal_permission


User = get_user_model()
pytestmark = pytest.mark.django_db


class TestFiscalDataPermission:
    """Tests para permisos de datos fiscales"""
    
    def test_unauthenticated_user_denied(self):
        """Test: Usuario no autenticado es rechazado"""
        permission = FiscalDataPermission()
        factory = RequestFactory()
        request = factory.get('/api/fiscal/')
        request.user = None
        
        assert permission.has_permission(request, None) is False
    
    def test_superuser_has_all_permissions(self):
        """Test: Superusuario tiene todos los permisos"""
        permission = FiscalDataPermission()
        factory = RequestFactory()
        
        # Crear superusuario
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='test123'
        )
        
        # GET request
        request = factory.get('/api/fiscal/')
        request.user = superuser
        assert permission.has_permission(request, None) is True
        
        # POST request
        request = factory.post('/api/fiscal/')
        request.user = superuser
        assert permission.has_permission(request, None) is True
        
        # DELETE request
        request = factory.delete('/api/fiscal/1/')
        request.user = superuser
        assert permission.has_permission(request, None) is True
    
    def test_user_with_view_permission(self):
        """Test: Usuario con permiso view_fiscal puede ver"""
        permission = FiscalDataPermission()
        factory = RequestFactory()
        
        # Crear usuario
        user = User.objects.create_user(
            username='viewer',
            email='viewer@test.com',
            password='test123'
        )
        
        # Crear permiso view_fiscal
        content_type = ContentType.objects.get_for_model(User)
        view_perm = Permission.objects.create(
            codename='view_fiscal',
            name='Can view fiscal data',
            content_type=content_type
        )
        user.user_permissions.add(view_perm)
        
        # GET request - debe permitir
        request = factory.get('/api/fiscal/')
        request.user = user
        assert permission.has_permission(request, None) is True
        
        # POST request - debe denegar (no tiene add_fiscal)
        request = factory.post('/api/fiscal/')
        request.user = user
        assert permission.has_permission(request, None) is False
    
    def test_user_without_permission_denied(self):
        """Test: Usuario sin permisos es rechazado"""
        permission = FiscalDataPermission()
        factory = RequestFactory()
        
        # Crear usuario sin permisos
        user = User.objects.create_user(
            username='noone',
            email='noone@test.com',
            password='test123'
        )
        
        # GET request - debe denegar
        request = factory.get('/api/fiscal/')
        request.user = user
        assert permission.has_permission(request, None) is False


class TestFiscalDecorators:
    """Tests para decoradores de seguridad"""
    
    def test_require_fiscal_permission_with_permission(self):
        """Test: Decorador permite acceso con permiso correcto"""
        # Crear usuario con permiso
        user = User.objects.create_user(
            username='editor',
            email='editor@test.com',
            password='test123'
        )
        
        content_type = ContentType.objects.get_for_model(User)
        change_perm = Permission.objects.create(
            codename='change_fiscal',
            name='Can change fiscal data',
            content_type=content_type
        )
        user.user_permissions.add(change_perm)
        
        # Crear vista decorada
        @require_fiscal_permission('change_fiscal')
        def test_view(request):
            return "success"
        
        # Crear request
        factory = RequestFactory()
        request = factory.post('/test/')
        request.user = user
        
        # Debe permitir acceso
        result = test_view(request)
        assert result == "success"
    
    def test_require_fiscal_permission_without_permission(self):
        """Test: Decorador bloquea acceso sin permiso"""
        # Crear usuario sin permiso
        user = User.objects.create_user(
            username='noone',
            email='noone@test.com',
            password='test123'
        )
        
        # Crear vista decorada
        @require_fiscal_permission('change_fiscal')
        def test_view(request):
            return "success"
        
        # Crear request
        factory = RequestFactory()
        request = factory.post('/test/')
        request.user = user
        
        # Debe lanzar PermissionDenied
        with pytest.raises(PermissionDenied):
            test_view(request)
