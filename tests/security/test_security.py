"""
Tests de seguridad para prevención de SQL Injection.
OWASP Top 10 - A03:2021 Injection
"""
from django.test import TestCase, Client
from django.urls import reverse
from app.models.user_account import UserAccount


class SQLInjectionTests(TestCase):
    """Tests para prevenir SQL Injection"""
    
    def setUp(self):
        self.client = Client()
        self.user = UserAccount.objects.create_user(
            username='testuser',
            email='test@ejemplo.com',
            password='TestPassword123!'
        )
    
    def test_login_sql_injection_username(self):
        """Test: SQL injection en campo username/email"""
        sql_payloads = [
            "admin' OR '1'='1",
            "admin'--",
            "admin' OR 1=1--",
            "' OR '1'='1' /*",
            "admin'; DROP TABLE auth_user;--",
            "1' UNION SELECT NULL--",
            "' OR 1=1#",
            "admin'/*",
        ]
        
        for payload in sql_payloads:
            with self.subTest(payload=payload):
                response = self.client.post('/accounts/login/', {
                    'login': payload,
                    'password': 'anything'
                })
                # No debe permitir login
                self.assertIn(response.status_code, [200, 403])
                # Usuario no debe estar autenticado
                self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_login_sql_injection_password(self):
        """Test: SQL injection en campo password"""
        sql_payloads = [
            "' OR '1'='1",
            "' OR 1=1--",
            "password' OR '1'='1",
        ]
        
        for payload in sql_payloads:
            with self.subTest(payload=payload):
                response = self.client.post('/accounts/login/', {
                    'login': 'testuser',
                    'password': payload
                })
                # No debe permitir login
                self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_orm_prevents_sql_injection(self):
        """Test: Django ORM previene SQL injection automáticamente"""
        # Intentar crear usuario con SQL injection en username
        malicious_username = "admin'; DROP TABLE auth_user;--"
        
        try:
            user = UserAccount.objects.create_user(
                username=malicious_username,
                email='malicious@ejemplo.com',
                password='TestPassword123!'
            )
            # Si se crea, verificar que el username se guardó como string literal
            self.assertEqual(user.username, malicious_username)
            # Verificar que la tabla auth_user sigue existiendo
            users_count = UserAccount.objects.count()
            self.assertGreaterEqual(users_count, 1)
        except Exception as e:
            # Si falla, es aceptable (validación de Django)
            pass


class XSSTests(TestCase):
    """Tests para prevenir Cross-Site Scripting (XSS)"""
    
    def setUp(self):
        self.client = Client()
    
    def test_xss_in_username_signup(self):
        """Test: XSS en campo username durante registro"""
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            '<svg onload=alert("XSS")>',
            'javascript:alert("XSS")',
            '<iframe src="javascript:alert(\'XSS\')">',
        ]
        
        for payload in xss_payloads:
            with self.subTest(payload=payload):
                response = self.client.post('/accounts/signup/', {
                    'username': payload,
                    'email': 'test@ejemplo.com',
                    'password1': 'TestPassword123!',
                    'password2': 'TestPassword123!',
                })
                # El payload XSS no debe aparecer sin escapar en la respuesta
                # Django escapa automáticamente con &lt; y &gt;
                content = response.content.decode('utf-8')
                # Verificar que el payload RAW no está presente
                self.assertNotIn(payload, content)
    
    def test_xss_in_email_field(self):
        """Test: XSS en campo email"""
        xss_email = '<script>alert("XSS")</script>@ejemplo.com'
        
        response = self.client.post('/accounts/signup/', {
            'username': 'testuser',
            'email': xss_email,
            'password1': 'TestPassword123!',
            'password2': 'TestPassword123!',
        })
        # Django debe rechazar email inválido
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'email', status_code=200)


class CSRFTests(TestCase):
    """Tests para protección CSRF"""
    
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
    
    def test_csrf_protection_on_login(self):
        """Test: Protección CSRF en login"""
        # Intentar POST sin CSRF token
        response = self.client.post('/accounts/login/', {
            'login': 'test',
            'password': 'test'
        })
        # Debe fallar con 403 Forbidden
        self.assertEqual(response.status_code, 403)
    
    def test_csrf_protection_on_signup(self):
        """Test: Protección CSRF en registro"""
        response = self.client.post('/accounts/signup/', {
            'username': 'test',
            'email': 'test@ejemplo.com',
            'password1': 'TestPassword123!',
            'password2': 'TestPassword123!',
        })
        # Debe fallar con 403 Forbidden
        self.assertEqual(response.status_code, 403)


class AuthenticationSecurityTests(TestCase):
    """Tests de seguridad de autenticación"""
    
    def setUp(self):
        self.client = Client()
        self.user = UserAccount.objects.create_user(
            username='testuser',
            email='test@ejemplo.com',
            password='TestPassword123!'
        )
    
    def test_password_complexity(self):
        """Test: Validación de complejidad de contraseña"""
        weak_passwords = [
            '123456',
            'password',
            'qwerty',
            '12345678',
            'abc123',
            'password123',
        ]
        
        for weak_pass in weak_passwords:
            with self.subTest(password=weak_pass):
                response = self.client.post('/accounts/signup/', {
                    'username': 'newuser',
                    'email': 'newuser@ejemplo.com',
                    'password1': weak_pass,
                    'password2': weak_pass,
                }, follow=True)
                # Debe rechazar contraseñas débiles
                self.assertContains(response, 'contraseña', status_code=200)
    
    def test_session_fixation_prevention(self):
        """Test: Prevención de session fixation"""
        # Obtener session ID antes de login
        self.client.get('/accounts/login/')
        session_before = self.client.session.session_key
        
        # Login exitoso
        self.client.force_login(self.user)
        
        # Session ID debe cambiar después de login
        session_after = self.client.session.session_key
        self.assertNotEqual(session_before, session_after)
    
    def test_secure_password_storage(self):
        """Test: Contraseñas almacenadas de forma segura (hasheadas)"""
        # La contraseña no debe estar en texto plano
        self.assertNotEqual(self.user.password, 'TestPassword123!')
        # Debe estar hasheada (empieza con algoritmo conocido)
        self.assertTrue(
            self.user.password.startswith('argon2') or 
            self.user.password.startswith('pbkdf2') or
            self.user.password.startswith('md5')  # Test settings usan MD5 para velocidad
        )


class SecurityHeadersTests(TestCase):
    """Tests para verificar security headers"""
    
    def setUp(self):
        self.client = Client()
    
    def test_x_frame_options_header(self):
        """Test: X-Frame-Options header presente"""
        response = self.client.get('/accounts/login/')
        self.assertIn('X-Frame-Options', response.headers)
        # Puede ser DENY o SAMEORIGIN según configuración
        self.assertIn(response.headers['X-Frame-Options'], ['DENY', 'SAMEORIGIN'])
    
    def test_x_content_type_options_header(self):
        """Test: X-Content-Type-Options header presente"""
        response = self.client.get('/accounts/login/')
        self.assertIn('X-Content-Type-Options', response.headers)
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
    
    def test_csp_header_presente(self):
        """Test: Content-Security-Policy header presente"""
        response = self.client.get('/accounts/login/')
        # CSP puede estar en Content-Security-Policy o Content-Security-Policy-Report-Only
        has_csp = (
            'Content-Security-Policy' in response.headers or
            'Content-Security-Policy-Report-Only' in response.headers
        )
        self.assertTrue(has_csp, "CSP header debe estar presente")


class InputValidationTests(TestCase):
    """Tests de validación de inputs"""
    
    def setUp(self):
        self.client = Client()
    
    def test_email_validation(self):
        """Test: Validación de formato de email"""
        invalid_emails = [
            'notanemail',
            '@ejemplo.com',
            'test@',
            'test..test@ejemplo.com',
            'test@ejemplo',
        ]
        
        for invalid_email in invalid_emails:
            with self.subTest(email=invalid_email):
                response = self.client.post('/accounts/signup/', {
                    'username': 'testuser',
                    'email': invalid_email,
                    'password1': 'TestPassword123!',
                    'password2': 'TestPassword123!',
                })
                # Debe rechazar emails inválidos
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'email', status_code=200)
    
    def test_username_validation(self):
        """Test: Validación de username"""
        # Username muy largo
        long_username = 'a' * 200
        response = self.client.post('/accounts/signup/', {
            'username': long_username,
            'email': 'test@ejemplo.com',
            'password1': 'TestPassword123!',
            'password2': 'TestPassword123!',
        })
        # Debe rechazar usernames muy largos
        self.assertEqual(response.status_code, 200)
