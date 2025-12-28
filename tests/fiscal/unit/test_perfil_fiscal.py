"""
Tests unitarios para PerfilFiscal model.
Siguiendo TDD: Tests primero, implementación después.
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from app.fiscal.models.perfil_fiscal import PerfilFiscal
from app.models import Client, Supplier


pytestmark = pytest.mark.django_db


class TestPerfilFiscalCreation:
    """Tests para creación de perfiles fiscales"""
    
    def test_crear_perfil_fiscal_con_cliente_valido(self):
        """Test: Crea perfil fiscal asociado a cliente"""
        # Given
        cliente = Client.objects.create(
            nombre="Empresa Test SAS",
            email="test@empresa.com"
        )
        
        # When
        perfil = PerfilFiscal.objects.create(
            cliente=cliente,
            tipo_documento='31',  # NIT
            numero_documento='900123456',
            tipo_persona='J',
            regimen='48',
            departamento_codigo='11',
            municipio_codigo='001',
            email_facturacion='facturacion@empresa.com',
            direccion='Calle 123 #45-67'
        )
        
        # Then
        assert perfil.id is not None
        assert perfil.cliente == cliente
        assert perfil.dv == '8'  # Auto-calculado
    
    def test_crear_perfil_fiscal_con_proveedor_valido(self):
        """Test: Crea perfil fiscal asociado a proveedor"""
        # Given
        proveedor = Supplier.objects.create(
            nombre="Proveedor XYZ",
            email="contacto@proveedor.com"
        )
        
        # When
        perfil = PerfilFiscal.objects.create(
            proveedor=proveedor,
            tipo_documento='31',
            numero_documento='800123456',
            tipo_persona='J',
            regimen='48',
            departamento_codigo='05',
            municipio_codigo='001',
            email_facturacion='ventas@proveedor.com',
            direccion='Carrera 10 #20-30'
        )
        
        # Then
        assert perfil.id is not None
        assert perfil.proveedor == proveedor
    
    def test_crear_perfil_sin_cliente_ni_proveedor_falla(self):
        """Test: Falla si no tiene cliente ni proveedor"""
        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            perfil = PerfilFiscal(
                tipo_documento='31',
                numero_documento='900123456',
                tipo_persona='J',
                regimen='48',
                departamento_codigo='11',
                municipio_codigo='001',
                email_facturacion='test@test.com',
                direccion='Calle 1'
            )
            perfil.full_clean()
        
        # Verificar que el mensaje de error esté en el diccionario
        error_dict = exc_info.value.message_dict
        assert '__all__' in error_dict
        assert "debe tener" in str(error_dict['__all__']).lower()
    
    def test_crear_perfil_con_ambos_cliente_y_proveedor_falla(self):
        """Test: Falla si tiene ambos cliente y proveedor"""
        # Given
        cliente = Client.objects.create(nombre="Cliente", email="c@test.com")
        proveedor = Supplier.objects.create(nombre="Proveedor", email="p@test.com")
        
        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            perfil = PerfilFiscal(
                cliente=cliente,
                proveedor=proveedor,
                tipo_documento='31',
                numero_documento='900123456',
                tipo_persona='J',
                regimen='48',
                departamento_codigo='11',
                municipio_codigo='001',
                email_facturacion='test@test.com',
                direccion='Calle 1'
            )
            perfil.full_clean()
        
        assert "no puede tener ambos" in str(exc_info.value).lower()
    
    def test_auto_calcular_dv_para_nit(self):
        """Test: Auto-calcula DV para tipo documento NIT"""
        # Given
        cliente = Client.objects.create(nombre="Test", email="test@test.com")
        
        # When
        perfil = PerfilFiscal.objects.create(
            cliente=cliente,
            tipo_documento='31',  # NIT
            numero_documento='900123456',
            tipo_persona='J',
            regimen='48',
            departamento_codigo='11',
            municipio_codigo='001',
            email_facturacion='test@test.com',
            direccion='Calle 1'
        )
        
        # Then
        assert perfil.dv == '8'
    
    def test_no_calcular_dv_para_cedula(self):
        """Test: No calcula DV para cédula"""
        # Given
        cliente = Client.objects.create(nombre="Test", email="test@test.com")
        
        # When
        perfil = PerfilFiscal.objects.create(
            cliente=cliente,
            tipo_documento='13',  # Cédula
            numero_documento='1234567890',
            tipo_persona='N',
            regimen='49',
            departamento_codigo='11',
            municipio_codigo='001',
            email_facturacion='test@test.com',
            direccion='Calle 1'
        )
        
        # Then
        assert perfil.dv == ''


class TestPerfilFiscalValidation:
    """Tests para validaciones de perfiles fiscales"""
    
    def test_validar_tipo_documento_valido(self):
        """Test: Acepta tipos de documento válidos"""
        tipos_validos = ['13', '22', '31', '41', '42']
        cliente = Client.objects.create(nombre="Test", email="test@test.com")
        
        for tipo in tipos_validos:
            perfil = PerfilFiscal(
                cliente=cliente,
                tipo_documento=tipo,
                numero_documento='123456789',
                tipo_persona='N',
                regimen='49',
                departamento_codigo='11',
                municipio_codigo='001',
                email_facturacion='test@test.com',
                direccion='Calle 1'
            )
            # No debe lanzar excepción
            perfil.full_clean()
    
    def test_validar_numero_documento_formato(self):
        """Test: Valida formato de número de documento"""
        cliente = Client.objects.create(nombre="Test", email="test@test.com")
        
        # Número documento con caracteres especiales
        with pytest.raises(ValidationError):
            perfil = PerfilFiscal(
                cliente=cliente,
                tipo_documento='31',
                numero_documento='900-123-456',  # Inválido
                tipo_persona='J',
                regimen='48',
                departamento_codigo='11',
                municipio_codigo='001',
                email_facturacion='test@test.com',
                direccion='Calle 1'
            )
            perfil.full_clean()
    
    def test_validar_responsabilidades_formato(self):
        """Test: Valida formato de responsabilidades tributarias"""
        cliente = Client.objects.create(nombre="Test", email="test@test.com")
        
        # Responsabilidades válidas
        perfil = PerfilFiscal(
            cliente=cliente,
            tipo_documento='31',
            numero_documento='900123456',
            tipo_persona='J',
            regimen='48',
            responsabilidades=['O-13', 'O-15', 'O-23'],
            departamento_codigo='11',
            municipio_codigo='001',
            email_facturacion='test@test.com',
            direccion='Calle 1'
        )
        perfil.full_clean()  # No debe fallar
    
    def test_validar_departamento_codigo_dane(self):
        """Test: Valida código DANE de departamento"""
        cliente = Client.objects.create(nombre="Test", email="test@test.com")
        
        # Código inválido (debe ser 2 dígitos)
        with pytest.raises(ValidationError):
            perfil = PerfilFiscal(
                cliente=cliente,
                tipo_documento='31',
                numero_documento='900123456',
                tipo_persona='J',
                regimen='48',
                departamento_codigo='1',  # Inválido (1 dígito)
                municipio_codigo='001',
                email_facturacion='test@test.com',
                direccion='Calle 1'
            )
            perfil.full_clean()
    
    def test_validar_municipio_codigo_dane(self):
        """Test: Valida código DANE de municipio"""
        cliente = Client.objects.create(nombre="Test", email="test@test.com")
        
        # Código inválido (debe ser 3 dígitos)
        with pytest.raises(ValidationError):
            perfil = PerfilFiscal(
                cliente=cliente,
                tipo_documento='31',
                numero_documento='900123456',
                tipo_persona='J',
                regimen='48',
                departamento_codigo='11',
                municipio_codigo='1',  # Inválido (1 dígito)
                email_facturacion='test@test.com',
                direccion='Calle 1'
            )
            perfil.full_clean()
    
    def test_validar_email_facturacion(self):
        """Test: Valida formato de email de facturación"""
        cliente = Client.objects.create(nombre="Test", email="test@test.com")
        
        # Email inválido
        with pytest.raises(ValidationError):
            perfil = PerfilFiscal(
                cliente=cliente,
                tipo_documento='31',
                numero_documento='900123456',
                tipo_persona='J',
                regimen='48',
                departamento_codigo='11',
                municipio_codigo='001',
                email_facturacion='email-invalido',  # Sin @
                direccion='Calle 1'
            )
            perfil.full_clean()


class TestPerfilFiscalMethods:
    """Tests para métodos del modelo PerfilFiscal"""
    
    def test_get_nombre_completo_con_cliente(self):
        """Test: Retorna nombre del cliente"""
        cliente = Client.objects.create(nombre="Empresa ABC", email="test@test.com")
        perfil = PerfilFiscal.objects.create(
            cliente=cliente,
            tipo_documento='31',
            numero_documento='900123456',
            tipo_persona='J',
            regimen='48',
            departamento_codigo='11',
            municipio_codigo='001',
            email_facturacion='test@test.com',
            direccion='Calle 1'
        )
        
        assert perfil.get_nombre_completo() == "Empresa ABC"
    
    def test_get_nit_formateado(self):
        """Test: Formatea NIT con puntos y guión"""
        cliente = Client.objects.create(nombre="Test", email="test@test.com")
        perfil = PerfilFiscal.objects.create(
            cliente=cliente,
            tipo_documento='31',
            numero_documento='900123456',
            tipo_persona='J',
            regimen='48',
            departamento_codigo='11',
            municipio_codigo='001',
            email_facturacion='test@test.com',
            direccion='Calle 1'
        )
        
        assert perfil.get_nit_formateado() == "900.123.456-8"
    
    def test_es_gran_contribuyente(self):
        """Test: Detecta si es gran contribuyente (O-13)"""
        cliente = Client.objects.create(nombre="Test", email="test@test.com")
        perfil = PerfilFiscal.objects.create(
            cliente=cliente,
            tipo_documento='31',
            numero_documento='900123456',
            tipo_persona='J',
            regimen='48',
            responsabilidades=['O-13', 'O-15'],
            departamento_codigo='11',
            municipio_codigo='001',
            email_facturacion='test@test.com',
            direccion='Calle 1'
        )
        
        assert perfil.es_gran_contribuyente() is True
    
    def test_es_autoretenedor(self):
        """Test: Detecta si es autoretenedor (O-15)"""
        cliente = Client.objects.create(nombre="Test", email="test@test.com")
        perfil = PerfilFiscal.objects.create(
            cliente=cliente,
            tipo_documento='31',
            numero_documento='900123456',
            tipo_persona='J',
            regimen='48',
            responsabilidades=['O-15', 'O-23'],
            departamento_codigo='11',
            municipio_codigo='001',
            email_facturacion='test@test.com',
            direccion='Calle 1'
        )
        
        assert perfil.es_autoretenedor() is True
    
    def test_str_representation(self):
        """Test: Representación en string del perfil"""
        cliente = Client.objects.create(nombre="Empresa XYZ", email="test@test.com")
        perfil = PerfilFiscal.objects.create(
            cliente=cliente,
            tipo_documento='31',
            numero_documento='900123456',
            tipo_persona='J',
            regimen='48',
            departamento_codigo='11',
            municipio_codigo='001',
            email_facturacion='test@test.com',
            direccion='Calle 1'
        )
        
        assert "Empresa XYZ" in str(perfil)
        assert "900123456" in str(perfil)


class TestPerfilFiscalSecurity:
    """Tests de seguridad para PerfilFiscal"""
    
    def test_sql_injection_en_numero_documento(self):
        """Test: Previene SQL injection en número de documento"""
        cliente = Client.objects.create(nombre="Test", email="test@test.com")
        
        with pytest.raises(ValidationError):
            perfil = PerfilFiscal(
                cliente=cliente,
                tipo_documento='31',
                numero_documento="900'; DROP TABLE perfil_fiscal;--",
                tipo_persona='J',
                regimen='48',
                departamento_codigo='11',
                municipio_codigo='001',
                email_facturacion='test@test.com',
                direccion='Calle 1'
            )
            perfil.full_clean()
    
    def test_xss_en_nombre_comercial(self):
        """Test: Previene XSS en nombre comercial"""
        cliente = Client.objects.create(nombre="Test", email="test@test.com")
        
        perfil = PerfilFiscal.objects.create(
            cliente=cliente,
            tipo_documento='31',
            numero_documento='900123456',
            tipo_persona='J',
            regimen='48',
            nombre_comercial="<script>alert('xss')</script>",
            departamento_codigo='11',
            municipio_codigo='001',
            email_facturacion='test@test.com',
            direccion='Calle 1'
        )
        
        # Debe sanitizar el contenido
        assert "<script>" not in perfil.nombre_comercial
    
    def test_validar_responsabilidades_maliciosas(self):
        """Test: Valida que responsabilidades sean códigos válidos"""
        cliente = Client.objects.create(nombre="Test", email="test@test.com")
        
        with pytest.raises(ValidationError):
            perfil = PerfilFiscal(
                cliente=cliente,
                tipo_documento='31',
                numero_documento='900123456',
                tipo_persona='J',
                regimen='48',
                responsabilidades=["<script>", "'; DROP TABLE"],
                departamento_codigo='11',
                municipio_codigo='001',
                email_facturacion='test@test.com',
                direccion='Calle 1'
            )
            perfil.full_clean()
    
    def test_email_injection_prevention(self):
        """Test: Previene email injection"""
        cliente = Client.objects.create(nombre="Test", email="test@test.com")
        
        with pytest.raises(ValidationError):
            perfil = PerfilFiscal(
                cliente=cliente,
                tipo_documento='31',
                numero_documento='900123456',
                tipo_persona='J',
                regimen='48',
                departamento_codigo='11',
                municipio_codigo='001',
                email_facturacion='test@test.com\nBcc: hacker@evil.com',
                direccion='Calle 1'
            )
            perfil.full_clean()
    
    def test_unicode_en_direccion(self):
        """Test: Maneja correctamente caracteres Unicode en dirección"""
        cliente = Client.objects.create(nombre="Test", email="test@test.com")
        
        perfil = PerfilFiscal.objects.create(
            cliente=cliente,
            tipo_documento='31',
            numero_documento='900123456',
            tipo_persona='J',
            regimen='48',
            departamento_codigo='11',
            municipio_codigo='001',
            email_facturacion='test@test.com',
            direccion='Calle 123 #45-67 Bogotá D.C.'  # Caracteres válidos
        )
        
        assert perfil.direccion == 'Calle 123 #45-67 Bogotá D.C.'
