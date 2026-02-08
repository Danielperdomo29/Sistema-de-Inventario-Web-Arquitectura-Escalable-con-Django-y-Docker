"""
Servicio orquestador de facturación electrónica DIAN.
Integra todos los componentes para generar facturas electrónicas completas.
"""
from typing import Tuple, Optional
from decimal import Decimal
from django.db import transaction
from django.core.files.base import ContentFile
from django.utils import timezone
import logging

from app.models.sale import Sale
from app.fiscal.models import FiscalConfig, RangoNumeracion, FacturaElectronica
from app.fiscal.services.numeracion_service import NumeracionService
from app.fiscal.core.dian.ubl_mapper import UBLMapper
from app.fiscal.core.dian.ubl_generator import UBLGeneratorService
from app.fiscal.core.dian.crypto_manager import FiscalCryptoManager
from app.fiscal.core.dian.formatters import DIANFormatter

logger = logging.getLogger(__name__)


class InvoiceGenerationService:
    """
    Servicio principal para generar facturas electrónicas DIAN.
    
    Orquesta todo el flujo:
    1. Validación de datos
    2. Asignación de numeración
    3. Mapeo de datos
    4. Cálculo de CUFE
    5. Generación de XML
    6. Firma digital (placeholder)
    7. Persistencia
    """
    
    @staticmethod
    @transaction.atomic
    def generar_factura_electronica(
        sale: Sale,
        fiscal_config_id: Optional[int] = None
    ) -> Tuple[FacturaElectronica, str]:
        """
        Genera una factura electrónica completa para una venta.
        
        Args:
            sale: Instancia de Sale a facturar
            fiscal_config_id: ID de configuración fiscal (usa la activa si es None)
            
        Returns:
            Tuple (FacturaElectronica, xml_string)
            
        Raises:
            ValidationError: Si hay errores de validación
            RuntimeError: Si hay errores en el proceso de generación
        """
        logger.info(f"Iniciando generación de factura electrónica para venta {sale.id}")
        
        try:
            # 1. Obtener configuración fiscal
            fiscal_config = InvoiceGenerationService._get_fiscal_config(fiscal_config_id)
            logger.debug(f"Configuración fiscal: {fiscal_config.id}")
            
            # 2. Validar datos de la venta
            InvoiceGenerationService._validar_venta(sale)
            
            # 3. Obtener siguiente número de factura
            numero_factura, rango = NumeracionService.obtener_siguiente_numero(
                fiscal_config_id=fiscal_config.id
            )
            logger.info(f"Número de factura asignado: {numero_factura}")
            
            # 4. Preparar datos para CUFE
            cufe_data = InvoiceGenerationService._preparar_datos_cufe(
                sale, fiscal_config, numero_factura, rango
            )
            
            # 5. Generar CUFE
            cufe = InvoiceGenerationService._generar_cufe(
                fiscal_config, cufe_data, rango.clave_tecnica
            )
            logger.info(f"CUFE generado: {cufe[:32]}...")
            
            # 6. Mapear datos Sale → UBL
            ubl_data = UBLMapper.map_sale_to_ubl_data(
                sale=sale,
                fiscal_config=fiscal_config,
                numero_factura=numero_factura,
                cufe=cufe
            )
            
            # 7. Generar XML UBL 2.1
            ubl_generator = UBLGeneratorService(fiscal_config)
            xml_string = ubl_generator.generar_xml(ubl_data)
            logger.info(f"XML UBL generado: {len(xml_string)} bytes")
            
            # 8. Firmar XML (placeholder - por ahora sin firma para desarrollo)
            xml_firmado = InvoiceGenerationService._firmar_xml(
                xml_string, fiscal_config
            )
            
            # 9. Generar PDF
            pdf_buffer = InvoiceGenerationService._generar_pdf(
                ubl_data, fiscal_config
            )
            
            # 10. Crear registro de factura electrónica
            factura = InvoiceGenerationService._crear_factura_electronica(
                sale=sale,
                numero_factura=numero_factura,
                cufe=cufe,
                xml_string=xml_firmado,
                pdf_buffer=pdf_buffer,
                rango=rango,
                fiscal_config=fiscal_config
            )
            
            logger.info(
                f"Factura electrónica {factura.numero_factura} "
                f"generada exitosamente (ID: {factura.id})"
            )
            
            return factura, xml_firmado
            
        except Exception as e:
            logger.error(f"Error al generar factura electrónica: {e}", exc_info=True)
            raise
    
    @staticmethod
    def _get_fiscal_config(config_id: Optional[int]) -> FiscalConfig:
        """Obtiene la configuración fiscal activa o crea una por defecto."""
        if config_id:
            try:
                return FiscalConfig.objects.get(id=config_id, is_active=True)
            except FiscalConfig.DoesNotExist:
                pass  # Intentar obtener cualquier config activa
        
        # Obtener la primera configuración activa
        config = FiscalConfig.objects.filter(is_active=True).first()
        if config:
            return config
        
        # AUTO-CREAR CONFIGURACIÓN DE PRUEBA
        logger.warning("⚠️ No hay configuraciones fiscales activas. Creando configuración de prueba...")
        
        try:
            from django.core.files.base import ContentFile
            import os
            
            # Crear certificado ficticio para desarrollo
            dummy_cert_content = b"DUMMY_CERTIFICATE_FOR_DEVELOPMENT"
            
            config = FiscalConfig(
                nit_emisor="900123456",
                dv_emisor="7",
                razon_social="EMPRESA DE DESARROLLO S.A.S. (MODO PRUEBA)",
                software_id="SOFTWARE_DEV_001",
                pin_software="12345",
                ambiente=2,  # Habilitación/Pruebas
                test_set_id="TEST_SET_DESARROLLO",
                numero_resolucion="18760000001",
                prefijo="SETP",
                rango_desde=1,
                rango_hasta=1000000,
                clave_tecnica="fc8eac422eba16e22ffd8c6f94b3f40a6e38162c",
                is_active=True,
            )
            
            # Guardar certificado ficticio
            config.certificado_archivo.save(
                'dev_cert.p12',
                ContentFile(dummy_cert_content),
                save=False
            )
            
            # Establecer password ficticio
            config._certificado_password = "dev_password_encrypted"
            
            config.save()
            
            logger.info(f"✅ Configuración fiscal de prueba creada automáticamente (ID: {config.id})")
            logger.info(f"   Prefijo: {config.prefijo}, Ambiente: Habilitación")
            
            # Crear rango de numeración asociado
            from app.fiscal.models import RangoNumeracion
            from datetime import date, timedelta
            
            hoy = date.today()
            rango, created = RangoNumeracion.objects.get_or_create(
                fiscal_config=config,
                prefijo=config.prefijo,
                defaults={
                    'numero_resolucion': config.numero_resolucion,
                    'fecha_resolucion': hoy,
                    'fecha_inicio_vigencia': hoy,
                    'fecha_fin_vigencia': hoy + timedelta(days=365),
                    'rango_desde': config.rango_desde,
                    'rango_hasta': config.rango_hasta,
                    'consecutivo_actual': config.rango_desde,
                    'clave_tecnica': config.clave_tecnica,
                    'estado': 'activo',
                    'is_default': True,
                }
            )
            
            if created:
                logger.info(f"✅ Rango de numeración creado: {rango.prefijo} ({rango.rango_desde}-{rango.rango_hasta})")
            
            return config
            
        except Exception as e:
            logger.error(f"❌ Error al crear configuración fiscal automática: {e}")
            raise ValueError(f"No hay configuraciones fiscales activas y no se pudo crear una: {e}")
    
    @staticmethod
    def _validar_venta(sale: Sale):
        """Valida que la venta tenga los datos necesarios."""
        if not sale:
            raise ValueError("Sale no puede ser None")
        
        # Verificar que tenga items - usar detalles relacionados
        items = sale.detalles.all() if hasattr(sale, 'detalles') else []
        if not items or len(list(items)) == 0:
            raise ValueError(f"La venta {sale.id} no tiene ítems")
        
        # Verificar que tenga cliente
        if not hasattr(sale, 'cliente') or not sale.cliente:
            raise ValueError(f"La venta {sale.id} no tiene cliente asignado")
        
        logger.debug(f"Venta {sale.id} validada correctamente")
    
    @staticmethod
    def _preparar_datos_cufe(
        sale: Sale,
        fiscal_config: FiscalConfig,
        numero_factura: str,
        rango: RangoNumeracion
    ) -> dict:
        """
        Prepara datos para el cálculo del CUFE.
        
        Returns:
            Dict con datos formateados para generar_cufe()
        """
        # Obtener timestamp
        ahora = timezone.now()
        fecha_str, hora_str = DIANFormatter.formatear_datetime_completo(ahora)
        
        # Usar campos reales del modelo
        subtotal = sale.subtotal or Decimal('0')
        total_iva = sale.iva_total or Decimal('0')
        total = sale.total or Decimal('0')
        
        # Si no tiene subtotal, calcular desde detalles
        if not subtotal:
            items = sale.detalles.all()
            for item in items:
                subtotal_sin_iva = item.subtotal_sin_iva or Decimal('0')
                iva_valor = item.iva_valor or Decimal('0')
                subtotal += subtotal_sin_iva
                total_iva += iva_valor
            total = subtotal + total_iva
        
        # Obtener datos del cliente
        customer = sale.cliente
        tipo_doc_cliente = DIANFormatter.obtener_codigo_tipo_documento('NIT')
        
        if hasattr(customer, 'documento') and customer.documento:
            num_cliente = DIANFormatter.limpiar_nit(customer.documento)
        else:
            num_cliente = '222222222222'
        
        return {
            'numero_factura': numero_factura,
            'fecha_emision': fecha_str,
            'hora_emision': hora_str,
            'valor_total': float(total),
            'cod_imp1': '01',  # IVA
            'val_imp1': float(total_iva),
            'cod_imp2': '04',  # Consumo
            'val_imp2': 0.0,
            'cod_imp3': '03',  # ICA
            'val_imp3': 0.0,
            'valor_pagar': float(total),
            'nit_emisor': fiscal_config.nit_emisor,
            'tipo_adquirente': tipo_doc_cliente,
            'num_adquirente': num_cliente,
            'clave_tecnica': rango.clave_tecnica,
            'tipo_ambiente': str(fiscal_config.ambiente),
        }
    
    @staticmethod
    def _generar_cufe(
        fiscal_config: FiscalConfig,
        cufe_data: dict,
        clave_tecnica: str
    ) -> str:
        """Genera el CUFE usando FiscalCryptoManager."""
        try:
            # CUFE generation doesn't need the certificate, only SHA-384 hash
            # So we create the crypto manager without loading the certificate
            crypto_manager = FiscalCryptoManager(load_cert=False)
            
            # Generar CUFE
            cufe = crypto_manager.generar_cufe(**cufe_data)
            
            # Validar formato
            if not DIANFormatter.validar_formato_cufe(cufe):
                raise ValueError("CUFE generado tiene formato inválido")
            
            return cufe
            
        except Exception as e:
            logger.error(f"Error al generar CUFE: {e}")
            raise RuntimeError(f"Error al generar CUFE: {e}")
    
    @staticmethod
    def _firmar_xml(xml_string: str, fiscal_config: FiscalConfig) -> str:
        """
        Firma digitalmente el XML (placeholder).
        
        Args:
            xml_string: XML a firmar
            fiscal_config: Configuración fiscal
            
        Returns:
            XML firmado (por ahora retorna el mismo XML)
        """
        # TODO: Implementar firma digital XAdES-BES
        # Por ahora en desarrollo local, retornamos el XML sin firmar
        
        logger.warning("Firma digital no implementada. XML sin firmar.")
        return xml_string
    
    @staticmethod
    def _generar_pdf(ubl_data: dict, fiscal_config: FiscalConfig):
        """
        Genera PDF de representación gráfica de la factura.
        
        Args:
            ubl_data: Datos UBL de la factura
            fiscal_config: Configuración fiscal
            
        Returns:
            BytesIO con el PDF generado
        """
        try:
            from app.fiscal.services.pdf_generator import InvoicePDFGenerator
            
            pdf_gen = InvoicePDFGenerator(ubl_data, fiscal_config)
            pdf_buffer = pdf_gen.generar_pdf()
            
            logger.info(f"PDF generado exitosamente: {pdf_buffer.tell()} bytes")
            return pdf_buffer
            
        except Exception as e:
            logger.error(f"Error al generar PDF: {e}", exc_info=True)
            # No falla la factura si el PDF falla
            logger.warning("Continuando sin PDF")
            return None
    
    @staticmethod
    def _crear_factura_electronica(
        sale: Sale,
        numero_factura: str,
        cufe: str,
        xml_string: str,
        pdf_buffer,
        rango: RangoNumeracion,
        fiscal_config: FiscalConfig
    ) -> FacturaElectronica:
        """
        Crea y persiste el registro de FacturaElectronica.
        
        Args:
            sale: Venta asociada
            numero_factura: Número de factura asignado
            cufe: CUFE calculado
            xml_string: XML UBL generado
            pdf_buffer: Buffer con PDF generado
            rango: Rango de numeración utilizado
            fiscal_config: Configuración fiscal
            
        Returns:
            Instancia de FacturaElectronica creada
        """
        # Crear o actualizar factura electrónica
        factura, created = FacturaElectronica.objects.update_or_create(
            venta_id=sale.id,
            defaults={
                'numero_factura': numero_factura,
                'cufe': cufe,
                'prefijo': rango.prefijo,
                'ambiente': fiscal_config.ambiente,
                'estado': 'generada',
            }
        )
        
        # Guardar archivo XML
        xml_filename = f"{numero_factura}.xml"
        factura.archivo_xml.save(
            xml_filename,
            ContentFile(xml_string.encode('utf-8')),
            save=False
        )
        
        # Guardar archivo PDF si existe
        if pdf_buffer:
            pdf_filename = f"{numero_factura}.pdf"
            factura.archivo_pdf.save(
                pdf_filename,
                ContentFile(pdf_buffer.getvalue()),
                save=False
            )
        
        factura.save()
        
        logger.info(f"Registro FacturaElectronica creado: {factura.id}")
        
        return factura
    
    @staticmethod
    def obtener_estado_factura(sale_id: int) -> Optional[dict]:
        """
        Obtiene el estado de facturación de una venta.
        
        Args:
            sale_id: ID de la venta
            
        Returns:
            Dict con estado de facturación o None si no está facturada
        """
        try:
            factura = FacturaElectronica.objects.get(venta_id=sale_id)
            return {
                'numero_factura': factura.numero_factura,
                'cufe': factura.cufe,
                'estado': factura.estado,
                'fecha_generacion': factura.fecha_creacion,
                'archivo_xml': factura.archivo_xml.url if factura.archivo_xml else None,
                'archivo_pdf': factura.archivo_pdf.url if factura.archivo_pdf else None,
            }
        except FacturaElectronica.DoesNotExist:
            return None
