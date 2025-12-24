from django.shortcuts import redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.http import HttpResponse
from django.middleware.csrf import get_token
from app.models.user import User
from app.views.auth_view import AuthView

class AuthController:
    """Controlador de Autenticación"""
    
    @staticmethod
    def login(request):
        """Maneja login"""
        # Si ya está autenticado, redirigir al dashboard
        if request.user.is_authenticated:
            return redirect('/')

        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            # Autenticación usando sistema nativo de Django
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                auth_login(request, user)
                # Mantener compatibilidad con controllers viejos que usan session['user_id']
                request.session['user_id'] = user.id
                request.session['username'] = user.username
                return redirect('/')
            else:
                csrf_token = get_token(request)
                return HttpResponse(AuthView.login(error='Usuario o contraseña incorrectos', csrf_token=csrf_token))
        
        csrf_token = get_token(request)
        return HttpResponse(AuthView.login(csrf_token=csrf_token))
    
    @staticmethod
    def register(request):
        """Maneja registro"""
        if request.method == 'POST':
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            nombre_completo = request.POST.get('nombre_completo')
            
            # Validaciones básicas
            errors = []
            if not all([username, email, password, password_confirm, nombre_completo]):
                errors.append('Todos los campos son obligatorios')
            if password != password_confirm:
                errors.append('Las contraseñas no coinciden')
            if len(password) < 6:
                errors.append('La contraseña debe tener al menos 6 caracteres')
            
            if User.exists(username=username):
                errors.append('El nombre de usuario ya está en uso')
            if User.exists(email=email):
                errors.append('El email ya está registrado')
            
            if errors:
                csrf_token = get_token(request)
                return HttpResponse(AuthView.register(errors=errors, csrf_token=csrf_token, form_data=request.POST))
            
            # Crear usuario usando el modelo (que usa UserAccount.objects.create_user)
            user_id = User.create(username, email, password, nombre_completo)
            
            if user_id:
                # Login automático después del registro
                user = authenticate(request, username=username, password=password)
                if user:
                    auth_login(request, user)
                    request.session['user_id'] = user.id
                    request.session['username'] = user.username
                return redirect('/')
            else:
                csrf_token = get_token(request)
                return HttpResponse(AuthView.register(errors=['Error al crear el usuario'], csrf_token=csrf_token))
        
        csrf_token = get_token(request)
        return HttpResponse(AuthView.register(csrf_token=csrf_token))
    
    @staticmethod
    def logout(request):
        """Cierra sesión"""
        # Verificar si el usuario usa allauth
        uses_allauth = False
        if request.user.is_authenticated and hasattr(request.user, 'use_allauth'):
            uses_allauth = request.user.use_allauth
        
        auth_logout(request)  # Limpia la sesión de Django
        
        # Redirigir según el sistema usado
        if uses_allauth:
            return redirect('/accounts/login/')
        else:
            return redirect('/login/')
