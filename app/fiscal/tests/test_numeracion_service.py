"""
Tests para el servicio de numeración de facturas DIAN.
"""
import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from app.fiscal.models import FiscalConfig, RangoNumeracion
from app.fiscal.services.numeracion_service import NumeracionService
from django.core.exceptions import ValidationError


@pytest.mark.django_db
class TestNumeracionService(TestCase):
    """Test suite para NumeracionService."""
    
    def setUp(self):
        """Configuración inicial para tests."""
        # Crear configuración fiscal de prueba
        self.fiscal_config = FiscalConfig.objects.create(
            nit_emisor='900123456',
            dv_emisor='7',
            razon_social='Empresa de Prueba SAS',
            software_id='test-software-id',
            pin_software='test-pin',
            ambiente=2,  # Habilitación
            numero_resolucion='18760000001',
            prefijo='TEST',
            rango_desde=1,
            rango_hasta=1000,
            clave_tecnica='fc8eac422eba16e22ffd8c6f94b3f40a6e38162c',
            is_active=True
        )
        
        # Crear rango de numeración
        self.rango = RangoNumeracion.objects.create(
            fiscal_config=self.fiscal_config,
            numero_resolucion='18760000001',
            fecha_resolucion=timezone.now().date(),
            fecha_inicio_vigencia=timezone.now().date(),
            fecha_fin_vigencia=timezone.now().date() + timedelta(days=365),
            prefijo='TEST',
            rango_desde=1,
            rango_hasta=100,
            consecutivo_actual=1,
            clave_tecnica='fc8eac422eba16e22ffd8c6f94b3f40a6e38162c',
            estado='activo',
            is_default=True,
            porcentaje_alerta=Decimal('10.00')
        )
    
    def test_obtener_siguiente_numero_basico(self):
        """Test básico de asignación de número."""
        numero, rango = NumeracionService.obtener_siguiente_numero(
            fiscal_config_id=self.fiscal_config.id
        )
        
        # Verificar formato
        self.assertTrue(numero.startswith('TEST'))
        self.assertIsNotNone(rango)
        
        # Verificar que el consecutivo se incrementó
        rango.refresh_from_db()
        self.assertEqual(rango.consecutivo_actual, 2)
    
    def test_obtener_siguiente_numero_con_prefijo(self):
        """Test de asignación especificando prefijo."""
        numero, rango = NumeracionService.obtener_siguiente_numero(
            fiscal_config_id=self.fiscal_config.id,
            prefijo='TEST'
        )
        
        self.assertEqual(numero, 'TEST001')
    
    def test_formato_numero_con_padding(self):
        """Test que verifica el padding correcto del número."""
        # Obtener varios números
        nums = []
        for _ in range(3):
            numero, _ = NumeracionService.obtener_siguiente_numero(
                fiscal_config_id=self.fiscal_config.id
            )
            nums.append(numero)
        
        # Verificar formato consistente
        self.assertEqual(nums[0], 'TEST001')
        self.assertEqual(nums[1], 'TEST002')
        self.assertEqual(nums[2], 'TEST003')
    
    def test_validar_disponibilidad_con_numeros(self):
        """Test de validación de disponibilidad."""
        disponibilidad = NumeracionService.validar_disponibilidad(
            fiscal_config_id=self.fiscal_config.id
        )
        
        self.assertTrue(disponibilidad['disponible'])
        self.assertEqual(disponibilidad['numeros_restantes'], 100)
        self.assertIsNotNone(disponibilidad['rango_activo'])
    
    def test_error_sin_rangos_activos(self):
        """Test que verifica error cuando no hay rangos activos."""
        # Desactivar rango
        self.rango.estado = 'inactivo'
        self.rango.save()
        
        # Intentar obtener número debe fallar
        with self.assertRaises(ValidationError):
            NumeracionService.obtener_siguiente_numero(
                fiscal_config_id=self.fiscal_config.id
            )
    
    def test_rango_se_agota(self):
        """Test que verifica comportamiento cuando se agota el rango."""
        # Establecer rango pequeño
        self.rango.rango_hasta = 3
        self.rango.consecutivo_actual = 1
        self.rango.save()
        
        # Obtener 3 números (agotar el rango)
        for _ in range(3):
            NumeracionService.obtener_siguiente_numero(
                fiscal_config_id=self.fiscal_config.id
            )
        
        # Verificar que el rango cambió a agotado
        self.rango.refresh_from_db()
        self.assertEqual(self.rango.estado, 'agotado')
        
        # Intentar obtener otro número debe fallar
        with self.assertRaises(ValidationError):
            NumeracionService.obtener_siguiente_numero(
                fiscal_config_id=self.fiscal_config.id
            )
    
    def test_propiedades_calculadas_rango(self):
        """Test de propiedades calculadas del rango."""
        self.rango.consecutivo_actual = 50
        self.rango.save()
        
        # Números disponibles
        self.assertEqual(self.rango.numeros_disponibles, 51)  # 100 - 50 + 1
        
        # Números usados
        self.assertEqual(self.rango.numeros_usados, 49)  # 50 - 1
        
        # Porcentaje de uso
        porcentaje = self.rango.porcentaje_uso
        self.assertAlmostEqual(float(porcentaje), 49.0, places=1)
    
    def test_alerta_agotamiento(self):
        """Test de alerta cuando se alcanza el umbral."""
        # Configurar para que alerte al 90%
        self.rango.porcentaje_alerta = Decimal('90.00')
        self.rango.rango_hasta = 100
        self.rango.consecutivo_actual = 91  # 90% uso
        self.rango.alerta_enviada = False
        self.rango.save()
        
        # Verificar que requiere alerta
        self.assertTrue(self.rango.requiere_alerta)
    
    def test_obtener_rango_activo(self):
        """Test de obtención de rango activo."""
        rango = NumeracionService.obtener_rango_activo(
            fiscal_config_id=self.fiscal_config.id
        )
        
        self.assertIsNotNone(rango)
        self.assertEqual(rango.id, self.rango.id)
    
    def test_validar_numero_en_rango(self):
        """Test de validación de número dentro de rango."""
        # Número dentro del rango
        self.assertTrue(
            NumeracionService.validar_numero_en_rango(50, self.rango.id)
        )
        
        # Número fuera del rango
        self.assertFalse(
            NumeracionService.validar_numero_en_rango(150, self.rango.id)
        )
