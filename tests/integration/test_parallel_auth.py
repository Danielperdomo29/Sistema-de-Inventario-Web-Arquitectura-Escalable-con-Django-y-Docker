"""
Tests de integración para verificar que ambos sistemas de autenticación
(antiguo y allauth) funcionan en paralelo sin conflictos.
"""
from django.test import TestCase, Client
from django.urls import reverse
from app.models.user_account import UserAccount
from allauth.account.models import EmailAddress


class ParallelAuthenticationTests(TestCase):
    """Tests para verificar coexistencia de ambos sistemas"""
    
    def setUp(self):
        self.client = Client()
        
        # Crear usuario con sistema antiguo
        self.legacy_user = UserAccount.objects.create_user(
            username='legacy_user',
            email='legacy@ejemplo.com',
            password='LegacyPassword123!',
            rol_id=2,
            use_allauth=False
        )
        
        # Crear usuario con allauth
        self.allauth_user = UserAccount.objects.create_user(
            username='allauth_user',
            email='allauth@ejemplo.com',
            password='AllauthPassword123!',
            rol_id=2,
            use_allauth=True,
            email_verified=True
        )
        
        # Crear EmailAddress para usuario allauth
        EmailAddress.objects.create(
            user=self.allauth_user,
            email=self.allauth_user.email,
            primary=True,
            verified=True
        )
    
    def test_legacy_user_can_login_with_old_system(self):
        """Test: Usuario antiguo puede login con /login/"""
        response = self.client.post('/login/', {
            'username': 'legacy_user',
            'password': 'LegacyPassword123!'
        }, follow=True)
        
        # Debe estar autenticado
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, 'legacy_user')
    
    def test_allauth_user_can_login_with_allauth(self):
        """Test: Usuario allauth puede login con /accounts/login/"""
        # Obtener CSRF token
        response = self.client.get('/accounts/login/')
        csrftoken = response.cookies.get('csrftoken')
        
        response = self.client.post('/accounts/login/', {
            'login': 'allauth_user',
            'password': 'AllauthPassword123!',
            'csrfmiddlewaretoken': csrftoken.value if csrftoken else ''
        }, follow=True)
        
        # Debe estar autenticado
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, 'allauth_user')
    
    def test_allauth_user_can_login_with_email(self):
        """Test: Usuario allauth puede login con email"""
        response = self.client.get('/accounts/login/')
        csrftoken = response.cookies.get('csrftoken')
        
        response = self.client.post('/accounts/login/', {
            'login': 'allauth@ejemplo.com',  # Email en lugar de username
            'password': 'AllauthPassword123!',
            'csrfmiddlewaretoken': csrftoken.value if csrftoken else ''
        }, follow=True)
        
        # Debe estar autenticado
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.email, 'allauth@ejemplo.com')
    
    def test_legacy_user_has_correct_permissions(self):
        """Test: Usuario antiguo tiene permisos correctos"""
        self.client.force_login(self.legacy_user)
        
        # Debe poder acceder al dashboard
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Debe poder acceder a productos
        response = self.client.get('/productos/')
        self.assertEqual(response.status_code, 200)
    
    def test_allauth_user_has_correct_permissions(self):
        """Test: Usuario allauth tiene permisos correctos"""
        self.client.force_login(self.allauth_user)
        
        # Debe poder acceder al dashboard
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Debe poder acceder a productos
        response = self.client.get('/productos/')
        self.assertEqual(response.status_code, 200)
    
    def test_middleware_assigns_rol_id(self):
        """Test: Middleware asigna rol_id automáticamente"""
        # Crear usuario sin rol_id
        user = UserAccount.objects.create_user(
            username='no_role_user',
            email='norole@ejemplo.com',
            password='Password123!'
        )
        user.rol_id = None
        user.save()
        
        # Login
        self.client.force_login(user)
        
        # Hacer request para activar middleware
        self.client.get('/')
        
        # Recargar usuario
        user.refresh_from_db()
        
        # Debe tener rol_id asignado
        self.assertIsNotNone(user.rol_id)
        self.assertEqual(user.rol_id, 2)


class UserMigrationTests(TestCase):
    """Tests para comando de migración de usuarios"""
    
    def setUp(self):
        # Crear usuarios sin migrar
        self.user1 = UserAccount.objects.create_user(
            username='user1',
            email='user1@ejemplo.com',
            password='Password123!',
            rol_id=2,
            use_allauth=False
        )
        
        self.user2 = UserAccount.objects.create_user(
            username='user2',
            email='user2@ejemplo.com',
            password='Password123!',
            rol_id=2,
            use_allauth=False
        )
    
    def test_migration_creates_email_address(self):
        """Test: Migración crea EmailAddress"""
        from django.core.management import call_command
        
        # Ejecutar migración
        call_command('migrate_users_to_allauth', '--auto-verify')
        
        # Verificar que se crearon EmailAddress
        self.assertTrue(
            EmailAddress.objects.filter(user=self.user1).exists()
        )
        self.assertTrue(
            EmailAddress.objects.filter(user=self.user2).exists()
        )
    
    def test_migration_marks_use_allauth(self):
        """Test: Migración marca use_allauth=True"""
        from django.core.management import call_command
        
        call_command('migrate_users_to_allauth', '--auto-verify')
        
        # Recargar usuarios
        self.user1.refresh_from_db()
        self.user2.refresh_from_db()
        
        # Verificar flag
        self.assertTrue(self.user1.use_allauth)
        self.assertTrue(self.user2.use_allauth)
    
    def test_migration_verifies_emails(self):
        """Test: Migración con --auto-verify marca emails como verificados"""
        from django.core.management import call_command
        
        call_command('migrate_users_to_allauth', '--auto-verify')
        
        # Verificar EmailAddress
        email1 = EmailAddress.objects.get(user=self.user1)
        email2 = EmailAddress.objects.get(user=self.user2)
        
        self.assertTrue(email1.verified)
        self.assertTrue(email2.verified)


class DashboardAccessTests(TestCase):
    """Tests de acceso al dashboard y funcionalidades"""
    
    def setUp(self):
        self.client = Client()
        self.user = UserAccount.objects.create_user(
            username='testuser',
            email='test@ejemplo.com',
            password='TestPassword123!',
            rol_id=2,
            use_allauth=True,
            email_verified=True
        )
    
    def test_authenticated_user_can_access_dashboard(self):
        """Test: Usuario autenticado puede acceder al dashboard"""
        self.client.force_login(self.user)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_authenticated_user_can_access_products(self):
        """Test: Usuario autenticado puede acceder a productos"""
        self.client.force_login(self.user)
        response = self.client.get('/productos/')
        self.assertEqual(response.status_code, 200)
    
    def test_authenticated_user_can_access_categories(self):
        """Test: Usuario autenticado puede acceder a categorías"""
        self.client.force_login(self.user)
        response = self.client.get('/categorias/')
        self.assertEqual(response.status_code, 200)
    
    def test_unauthenticated_user_redirected_to_login(self):
        """Test: Usuario no autenticado es redirigido al login"""
        response = self.client.get('/productos/')
        # Debe redirigir al login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
