"""
Servicio de Contabilización Automática

Interactúa con el Perfil Fiscal para determinar las cuentas contables
y genera los asientos automáticamente basados en eventos del negocio.
"""
from django.db import transaction
from django.utils import timezone
from app.fiscal.models import AsientoContable, DetalleAsiento, CuentaContable
from app.fiscal.services.hash_manager import HashManager

class ContadorAutomatico:
    
    @classmethod
    def contabilizar_venta(cls, venta):
        """
        Genera el asiento contable para una venta completada
        """
        # Evitar duplicados
        if AsientoContable.objects.filter(
            documento_origen_tipo='FACTURA_VENTA',
            documento_origen_numero=str(venta.id)
        ).exists():
            return
            
        try:
            with transaction.atomic():
                # 1. Crear Asiento (Cabecera)
                asiento = AsientoContable.objects.create(
                    numero_asiento=cls._generar_consecutivo(),
                    fecha_contable=venta.fecha.date() if hasattr(venta.fecha, 'date') else timezone.now().date(),
                    tipo_asiento='VENTA',
                    documento_origen_tipo='FACTURA_VENTA',
                    documento_origen_numero=str(venta.id),
                    tercero_nit=venta.cliente.documento if venta.cliente else '222222222', # Consumidor final
                    tercero_nombre=venta.cliente.nombre if venta.cliente else 'Cuantia Menor',
                    descripcion=f"Venta Factura #{venta.numero_factura} - Cliente: {venta.cliente}",
                    usuario_creacion=venta.usuario,
                    estado='ACTIVO', # O BORRADOR hasta validar
                    total_debito=venta.total, # Se recalculará
                    total_credito=venta.total # Se recalculará
                )
                
                # 2. Detalles (Simplificado para Fase 2)
                # DEBITO: Caja o Bancos (110505)
                # CREDITO: Ingresos (4135)
                # CREDITO: IVA (2408)
                
                # TODO: Obtener cuentas del PerfilFiscal
                cuenta_caja = CuentaContable.objects.filter(codigo__startswith='11', acepta_movimiento=True).first()
                cuenta_ingreso = CuentaContable.objects.filter(codigo__startswith='41', acepta_movimiento=True).first()
                
                if not cuenta_caja or not cuenta_ingreso:
                    # Fallback para pruebas si no hay PUC cargado
                    print("ADVERTENCIA: No se encontraron cuentas contables base. Usando mocks si es necesario.")
                    # return # O lanzar error
                
                # Detalle 1: Ingreso a Caja (Débito)
                if cuenta_caja:
                    DetalleAsiento.objects.create(
                        asiento=asiento,
                        cuenta_contable=cuenta_caja,
                        debito=venta.total,
                        credito=0,
                        descripcion_detalle=f"Pago Venta #{venta.numero_factura}",
                        orden=1
                    )
                
                # Detalle 2: Ingreso por Venta (Crédito)
                if cuenta_ingreso:
                    DetalleAsiento.objects.create(
                        asiento=asiento,
                        cuenta_contable=cuenta_ingreso,
                        debito=0,
                        credito=venta.total, # Asumiendo sin IVA por simplicidad inicial
                        descripcion_detalle=f"Ingreso Venta #{venta.numero_factura}",
                        orden=2
                    )
                
                # 3. Validar y sellar
                # Al finalizar, forzamos la validación completa
                asiento.save(run_validation=True)
                
                return asiento
                
        except Exception as e:
            print(f"Error en contabilización automática: {e}")
            # Log error pero no romper flujo de venta (fail soft)
            return None

    @classmethod
    def _generar_consecutivo(cls):
        """Genera próximo número de asiento"""
        last = AsientoContable.objects.order_by('-numero_asiento').first()
        return (last.numero_asiento + 1) if last else 1
