"""
Tests de Seguridad Contable - Anti-fraude
Valida que las medidas de seguridad previenen manipulaciones
"""
import pytest
from decimal import Decimal
from datetime import date, datetime
from django.contrib.auth import get_user_model
from app.fiscal.models import (
    AsientoContable,
    DetalleAsiento,
    PeriodoContable,
    CuentaContable,
    LogAuditoriaContable
)
from app.fiscal.services.hash_manager import HashManager

User = get_user_model()


@pytest.mark.django_db
class TestSeguridadHash:
    """
    Tests de seguridad de hashes
    Previene manipulación manual de hashes
    """
    
    def test_no_permite_modificar_hash_manual(self):
        """No debe permitir modificar hash manualmente"""
        usuario = User.objects.create_user(username='testuser', password='test123')
        cuenta = CuentaContable.objects.create(
            codigo='1',
            nombre='Activo',
            nivel=1,
            naturaleza='D',
            tipo='ACTIVO',
            acepta_movimiento=True,
            activa=True
        )
        
        # Crear asiento
        asiento = AsientoContable.objects.create(
            numero_asiento=1,
            fecha_contable=date(2025, 1, 15),
            tipo_asiento='MANUAL',
            descripcion='Asiento de prueba',
            total_debito=Decimal('1000.00'),
            total_credito=Decimal('1000.00'),
            usuario_creacion=usuario,
            hash_integridad='hash_inicial'
        )
        
        # Crear detalle
        DetalleAsiento.objects.create(
            asiento=asiento,
            cuenta_contable=cuenta,
            orden=1,
            debito=Decimal('1000.00'),
            credito=Decimal('0.00'),
            descripcion_detalle='Detalle 1'
        )
        
        # Actualizar totales (esto recalcula el hash)
        asiento.actualizar_totales()
        asiento.refresh_from_db()
        
        # El hash debe haber cambiado del inicial
        assert asiento.hash_integridad != 'hash_inicial'
        assert len(asiento.hash_integridad) == 64
    
    def test_detecta_manipulacion_datos(self):
        """Debe detectar cuando los datos no coinciden con el hash"""
        usuario = User.objects.create_user(username='testuser', password='test123')
        cuenta = CuentaContable.objects.create(
            codigo='1',
            nombre='Activo',
            nivel=1,
            naturaleza='D',
            tipo='ACTIVO',
            acepta_movimiento=True,
            activa=True
        )
        
        # Crear asiento
        asiento = AsientoContable.objects.create(
            numero_asiento=1,
            fecha_contable=date(2025, 1, 15),
            tipo_asiento='MANUAL',
            descripcion='Asiento original',
            total_debito=Decimal('1000.00'),
            total_credito=Decimal('1000.00'),
            usuario_creacion=usuario
        )
        
        # Crear detalle
        DetalleAsiento.objects.create(
            asiento=asiento,
            cuenta_contable=cuenta,
            orden=1,
            debito=Decimal('1000.00'),
            credito=Decimal('0.00'),
            descripcion_detalle='Detalle original'
        )
        
        # Actualizar totales y hash
        asiento.actualizar_totales()
        asiento.refresh_from_db()
        
        hash_original = asiento.hash_integridad
        
        # Simular manipulación: cambiar descripción sin recalcular hash
        AsientoContable.objects.filter(id=asiento.id).update(
            descripcion='Descripción manipulada'
        )
        
        asiento.refresh_from_db()
        
        # Verificar integridad
        es_valido, hash_almacenado, hash_calculado = asiento.verificar_integridad()
        
        assert es_valido is False, "Debe detectar manipulación"
        assert hash_almacenado == hash_original
        assert hash_calculado != hash_original


@pytest.mark.django_db
class TestSeguridadPeriodo:
    """
    Tests de seguridad de períodos contables
    Previene modificaciones en períodos cerrados
    """
    
    def test_bloquea_periodo_cerrado(self):
        """No debe permitir crear asientos en período cerrado"""
        from app.fiscal.validators import ValidadorPeriodoAbierto
        
        # Crear período cerrado
        periodo = PeriodoContable.objects.create(
            año=2025,
            mes=1,
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 31),
            estado='CERRADO',
            fecha_cierre=datetime.now()
        )
        
        validador = ValidadorPeriodoAbierto()
        
        asiento_data = {
            'fecha_contable': date(2025, 1, 15),
            'periodo_contable': periodo
        }
        
        es_valido, mensaje = validador.validar(asiento_data)
        
        assert es_valido is False
        assert 'CERRADO' in mensaje
    
    def test_asiento_no_puede_modificarse_en_periodo_cerrado(self):
        """Asiento en período cerrado no debe poder modificarse"""
        usuario = User.objects.create_user(username='testuser', password='test123')
        
        # Crear período cerrado
        periodo = PeriodoContable.objects.create(
            año=2025,
            mes=1,
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 31),
            estado='CERRADO'
        )
        
        # Crear asiento
        asiento = AsientoContable.objects.create(
            numero_asiento=1,
            fecha_contable=date(2025, 1, 15),
            tipo_asiento='MANUAL',
            descripcion='Asiento en período cerrado',
            total_debito=Decimal('1000.00'),
            total_credito=Decimal('1000.00'),
            usuario_creacion=usuario,
            periodo_contable=periodo
        )
        
        # Intentar verificar si puede modificarse
        puede_modificar, mensaje = asiento.puede_modificarse()
        
        assert puede_modificar is False
        assert 'cerrado' in mensaje.lower()


@pytest.mark.django_db
class TestSeguridadAnulacion:
    """
    Tests de seguridad de anulación de asientos
    Valida que las anulaciones sean trazables
    """
    
    def test_anulacion_registra_auditoria(self):
        """Anulación debe registrarse en log de auditoría"""
        usuario = User.objects.create_user(username='testuser', password='test123')
        cuenta = CuentaContable.objects.create(
            codigo='1',
            nombre='Activo',
            nivel=1,
            naturaleza='D',
            tipo='ACTIVO',
            acepta_movimiento=True,
            activa=True
        )
        
        # Crear asiento
        asiento = AsientoContable.objects.create(
            numero_asiento=1,
            fecha_contable=date(2025, 1, 15),
            tipo_asiento='MANUAL',
            descripcion='Asiento a anular',
            total_debito=Decimal('1000.00'),
            total_credito=Decimal('1000.00'),
            usuario_creacion=usuario,
            estado='ACTIVO'
        )
        
        # Anular
        motivo = "Error en la contabilización, se requiere corrección"
        asiento.anular(usuario, motivo, ip_origen='192.168.1.1')
        
        # Verificar que se registró en auditoría
        log_anulacion = LogAuditoriaContable.objects.filter(
            tipo_evento='ANULACION_ASIENTO',
            asiento=asiento
        ).first()
        
        assert log_anulacion is not None
        assert log_anulacion.usuario == usuario
        assert motivo in str(log_anulacion.detalles)
    
    def test_no_permite_anular_asiento_ya_anulado(self):
        """No debe permitir anular un asiento ya anulado"""
        usuario = User.objects.create_user(username='testuser', password='test123')
        
        asiento = AsientoContable.objects.create(
            numero_asiento=1,
            fecha_contable=date(2025, 1, 15),
            tipo_asiento='MANUAL',
            descripcion='Asiento',
            total_debito=Decimal('1000.00'),
            total_credito=Decimal('1000.00'),
            usuario_creacion=usuario,
            estado='ACTIVO'
        )
        
        # Primera anulación
        asiento.anular(usuario, "Motivo de anulación válido")
        
        # Intentar anular de nuevo
        with pytest.raises(ValueError, match="ya está anulado"):
            asiento.anular(usuario, "Segundo intento de anulación")
    
    def test_anulacion_requiere_motivo_minimo(self):
        """Anulación debe requerir motivo de al menos 10 caracteres"""
        usuario = User.objects.create_user(username='testuser', password='test123')
        
        asiento = AsientoContable.objects.create(
            numero_asiento=1,
            fecha_contable=date(2025, 1, 15),
            tipo_asiento='MANUAL',
            descripcion='Asiento',
            total_debito=Decimal('1000.00'),
            total_credito=Decimal('1000.00'),
            usuario_creacion=usuario,
            estado='ACTIVO'
        )
        
        # Intentar anular con motivo corto
        with pytest.raises(ValueError, match="al menos 10 caracteres"):
            asiento.anular(usuario, "Corto")


@pytest.mark.django_db
class TestSeguridadEliminacion:
    """
    Tests de seguridad contra eliminación
    Los asientos NO deben poder eliminarse
    """
    
    def test_no_permite_eliminar_asiento(self):
        """Asientos no deben poder eliminarse físicamente"""
        usuario = User.objects.create_user(username='testuser', password='test123')
        
        asiento = AsientoContable.objects.create(
            numero_asiento=1,
            fecha_contable=date(2025, 1, 15),
            tipo_asiento='MANUAL',
            descripcion='Asiento',
            total_debito=Decimal('1000.00'),
            total_credito=Decimal('1000.00'),
            usuario_creacion=usuario
        )
        
        # Intentar eliminar
        with pytest.raises(ValueError, match="no se pueden eliminar"):
            asiento.delete()
        
        # Verificar que sigue existiendo
        assert AsientoContable.objects.filter(id=asiento.id).exists()
    
    def test_no_permite_eliminar_log_auditoria(self):
        """Logs de auditoría no deben poder eliminarse"""
        usuario = User.objects.create_user(username='testuser', password='test123')
        
        log = LogAuditoriaContable.registrar(
            tipo_evento='ACCESO_CONTABILIDAD',
            usuario=usuario,
            detalles={'accion': 'test'}
        )
        
        # Intentar eliminar
        with pytest.raises(ValueError, match="inmutables"):
            log.delete()
        
        # Verificar que sigue existiendo
        assert LogAuditoriaContable.objects.filter(id=log.id).exists()


@pytest.mark.django_db
class TestVerificacionIntegridad:
    """
    Tests de verificación de integridad en lote
    """
    
    def test_verificacion_batch_funciona(self):
        """Verificación en lote debe detectar discrepancias"""
        usuario = User.objects.create_user(username='testuser', password='test123')
        cuenta = CuentaContable.objects.create(
            codigo='1',
            nombre='Activo',
            nivel=1,
            naturaleza='D',
            tipo='ACTIVO',
            acepta_movimiento=True,
            activa=True
        )
        
        # Crear 3 asientos
        asientos = []
        for i in range(1, 4):
            asiento = AsientoContable.objects.create(
                numero_asiento=i,
                fecha_contable=date(2025, 1, 15),
                tipo_asiento='MANUAL',
                descripcion=f'Asiento {i}',
                total_debito=Decimal('1000.00'),
                total_credito=Decimal('1000.00'),
                usuario_creacion=usuario
            )
            
            DetalleAsiento.objects.create(
                asiento=asiento,
                cuenta_contable=cuenta,
                orden=1,
                debito=Decimal('1000.00'),
                credito=Decimal('0.00'),
                descripcion_detalle='Detalle'
            )
            
            asiento.actualizar_totales()
            asientos.append(asiento)
        
        # Manipular el segundo asiento
        AsientoContable.objects.filter(id=asientos[1].id).update(
            descripcion='Descripción manipulada'
        )
        
        # Verificar en lote
        discrepancias = HashManager.verificar_integridad_batch(
            AsientoContable.objects.all()
        )
        
        # Debe detectar 1 discrepancia (el asiento manipulado)
        assert len(discrepancias) == 1
        assert discrepancias[0]['asiento_id'] == asientos[1].id


@pytest.mark.django_db
class TestLogAuditoriaInmutable:
    """
    Tests de inmutabilidad de logs (WORM)
    """
    
    def test_log_no_permite_modificacion(self):
        """Logs de auditoría no deben poder modificarse"""
        usuario = User.objects.create_user(username='testuser', password='test123')
        
        log = LogAuditoriaContable.registrar(
            tipo_evento='ACCESO_CONTABILIDAD',
            usuario=usuario,
            detalles={'accion': 'test'}
        )
        
        # Intentar modificar
        with pytest.raises(ValueError, match="inmutables"):
            log.tipo_evento = 'OTRO_EVENTO'
            log.save()
    
    def test_log_registra_todos_campos_criticos(self):
        """Log debe registrar todos los campos críticos"""
        usuario = User.objects.create_user(
            username='testuser',
            password='test123',
            first_name='Test',
            last_name='User'
        )
        
        log = LogAuditoriaContable.registrar(
            tipo_evento='CREACION_ASIENTO',
            usuario=usuario,
            detalles={'numero': 123},
            ip_origen='192.168.1.1',
            user_agent='Mozilla/5.0',
            endpoint='/contabilidad/asientos/crear/',
            metodo_http='POST'
        )
        
        assert log.usuario == usuario
        assert log.usuario_nombre == 'Test User'
        assert log.ip_origen == '192.168.1.1'
        assert log.user_agent == 'Mozilla/5.0'
        assert log.endpoint == '/contabilidad/asientos/crear/'
        assert log.metodo_http == 'POST'
        assert log.detalles['numero'] == 123


# Configuración de pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
