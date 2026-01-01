from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from datetime import datetime
import json

from app.models.sale import Sale as Venta
from app.models.user_account import UserAccount
from app.models.client import Client
from app.fiscal.services.contador_automatico import ContadorAutomatico
from app.fiscal.models import AsientoContable, PeriodoContable
from .core.reporte_fiscal import ReporteFiscalService
from .core.pdf_generator import PDFGenerator
from .core.cierre_contable import CierreContableService

# Configuración de empresa (Mock - idealmente de DB/Settings)
EMPRESA_NOMBRE = "Mi Empresa SAS"
EMPRESA_NIT = "123456789-0"

def test_integracion(request):
    """
    Endpoint de prueba para verificar la integración completa
    Crea una venta simulada y verifica que se genere el asiento
    """
    try:
        with transaction.atomic():
            # 1. Crear Venta Simulada
            user = UserAccount.objects.first()
            if not user:
                # Fallback para dev
                user = UserAccount.objects.create(
                    username='test_fiscal',
                    email='test_fiscal@example.com',
                    first_name='Test',
                    last_name='User'
                )
                
            cliente = Client.objects.first()
            if not cliente:
                cliente = Client.objects.create(
                    nombre='Cliente Test',
                    documento='123456789',
                    email='cliente@test.com'
                )

            venta = Venta.objects.create(
                numero_factura=f"TEST-{timezone.now().timestamp()}",
                fecha=timezone.now(),
                total=Decimal('50000.00'),
                usuario=user,
                estado='completada',
                cliente=cliente
            )
            
            # 2. La señal debería llamar a ContadorAutomatico
            asiento = AsientoContable.objects.filter(
                documento_origen_numero=str(venta.id)
            ).first()
            
            msg = "Señal automática NO funcionó (o desactivada), ejecutando manual..."
            if not asiento:
                # Si la señal no disparó (ej: error o no conectada), probamos manual
                asiento = ContadorAutomatico.contabilizar_venta(venta)
                msg = "Ejecución manual exitosa"
            else:
                msg = "Señal automática funcionó correctamente"
            
            if not asiento:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No se generó asiento contable'
                }, status=500)
            
            # 3. Verificar Integridad
            es_valido, hash_act, hash_cal = asiento.verificar_integridad()
            
            data = {
                'status': 'success',
                'message': msg,
                'venta_id': venta.id,
                'asiento_id': asiento.id,
                'hash_integridad': asiento.hash_integridad,
                'integridad_valida': es_valido,
                'detalles': list(asiento.detalles.values('orden', 'cuenta_contable__codigo', 'debito', 'credito'))
            }
            
            return JsonResponse(data)
            
    except Exception as e:
        import traceback
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


# === REPORTES ===

@require_http_methods(["GET"])
@login_required
def libro_diario(request):
    """
    Endpoint para generar libro diario en PDF o mostrar interfaz
    """
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    formato = request.GET.get('formato', 'pdf')
    
    # Si no hay parámetros, renderizar la interfaz
    if not fecha_inicio and not fecha_fin:
        return render(request, 'fiscal/libro_diario.html', {
            'title': 'Libro Diario',
            'current_date': datetime.now().strftime('%Y-%m-%d')
        })
    
    if not fecha_inicio or not fecha_fin:
        return JsonResponse({'error': 'Se requieren fecha_inicio y fecha_fin'}, status=400)
    
    try:
        # Convertir fechas
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        
        # Generar datos del reporte
        reporte_service = ReporteFiscalService()
        libro_diario_data = reporte_service.generar_libro_diario(fecha_inicio_dt, fecha_fin_dt)
        
        if formato.lower() == 'json':
            return JsonResponse(libro_diario_data, safe=False)
        
        # Generar PDF
        pdf_generator = PDFGenerator(
            titulo="LIBRO DIARIO",
            empresa_nombre=EMPRESA_NOMBRE,
            empresa_nit=EMPRESA_NIT
        )
        
        pdf_buffer = pdf_generator.generar_libro_diario_pdf(
            libro_diario_data, 
            fecha_inicio, 
            fecha_fin
        )
        
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="libro_diario_{fecha_inicio}_{fecha_fin}.pdf"'
        return response
        
    except ValueError as e:
        return JsonResponse({'error': f'Formato de fecha inválido: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def balance_prueba(request):
    """
    Endpoint para generar balance de prueba en PDF o mostrar interfaz
    """
    fecha_corte = request.GET.get('fecha_corte')
    formato = request.GET.get('formato', 'pdf')
    
    # Si no hay parámetros, renderizar la interfaz
    if not fecha_corte:
        return render(request, 'fiscal/balance_prueba.html', {
            'title': 'Balance de Prueba',
            'current_date': datetime.now().strftime('%Y-%m-%d')
        })
    
    try:
        fecha_corte_dt = datetime.strptime(fecha_corte, '%Y-%m-%d').date()
        
        reporte_service = ReporteFiscalService()
        balance_data = reporte_service.generar_balance_prueba(fecha_corte_dt)
        
        if formato.lower() == 'json':
            return JsonResponse(balance_data)
        
        pdf_generator = PDFGenerator(
            titulo="BALANCE DE PRUEBA",
            empresa_nombre=EMPRESA_NOMBRE,
            empresa_nit=EMPRESA_NIT
        )
        
        pdf_buffer = pdf_generator.generar_balance_prueba_pdf(balance_data)
        
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="balance_prueba_{fecha_corte}.pdf"'
        return response
        
    except ValueError as e:
        return JsonResponse({'error': f'Formato de fecha inválido: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def estado_resultados(request):
    """
    Endpoint para generar estado de resultados en PDF
    """
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    formato = request.GET.get('formato', 'pdf')
    
    if not fecha_inicio or not fecha_fin:
        return JsonResponse({'error': 'Se requieren fecha_inicio y fecha_fin'}, status=400)
    
    try:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        
        reporte_service = ReporteFiscalService()
        estado_data = reporte_service.generar_estado_resultados(fecha_inicio_dt, fecha_fin_dt)
        
        if formato.lower() == 'json':
            return JsonResponse(estado_data)
        
        pdf_generator = PDFGenerator(
            titulo="ESTADO DE RESULTADOS",
            empresa_nombre=EMPRESA_NOMBRE,
            empresa_nit=EMPRESA_NIT
        )
        
        pdf_buffer = pdf_generator.generar_estado_resultados_pdf(estado_data)
        
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="estado_resultados_{fecha_inicio}_{fecha_fin}.pdf"'
        return response
        
    except ValueError as e:
        return JsonResponse({'error': f'Formato de fecha inválido: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def libro_mayor(request):
    """
    Endpoint para generar libro mayor (JSON)
    """
    anio = request.GET.get('anio')
    mes = request.GET.get('mes')
    
    if not anio:
        return JsonResponse({'error': 'Se requiere el parámetro anio'}, status=400)
    
    try:
        anio_int = int(anio)
        mes_int = int(mes) if mes else None
        
        reporte_service = ReporteFiscalService()
        libro_mayor_data = reporte_service.generar_libro_mayor(anio_int, mes_int)
        
        return JsonResponse(libro_mayor_data)
        
    except ValueError as e:
        return JsonResponse({'error': f'Parámetros inválidos: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# === CIERRE CONTABLE ===

@csrf_exempt # Permitir POST sin CSRF para pruebas (idealmente usar token)
@require_http_methods(["POST"])
@login_required
def ejecutar_cierre(request):
    """
    Endpoint para ejecutar cierre contable de un período
    """
    try:
        body = json.loads(request.body)
        periodo_id = body.get('periodo_id')
        forzar = body.get('forzar', False)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    
    if not periodo_id:
        return JsonResponse({'error': 'Se requiere periodo_id'}, status=400)
    
    try:
        cierre_service = CierreContableService(periodo_id)
        
        # Validar que período anterior esté cerrado (a menos que se fuerce)
        if not forzar and not cierre_service.validar_cierre_periodo_anterior():
            return JsonResponse({
                'error': 'El período anterior no está cerrado',
                'detalle': 'Debe cerrar el período anterior antes de cerrar el actual'
            }, status=400)
        
        # Ejecutar cierre
        resultado = cierre_service.cerrar_periodo(request.user)
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Cierre contable ejecutado exitosamente',
            'data': resultado
        })
        
    except PeriodoContable.DoesNotExist:
        return JsonResponse({'error': 'Período no encontrado'}, status=404)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def verificar_cierre(request):
    """
    Endpoint para verificar estado de cierre de un período
    """
    periodo_id = request.GET.get('periodo_id')
    
    if not periodo_id:
        return JsonResponse({'error': 'Se requiere periodo_id'}, status=400)
    
    try:
        periodo = PeriodoContable.objects.get(id=periodo_id)
        
        cierre_service = CierreContableService(periodo_id)
        cuadre_ok = cierre_service.validar_cuadre_periodo()
        resultado = cierre_service.calcular_resultado()
        
        return JsonResponse({
            'periodo': periodo.nombre,
            'estado': periodo.estado,
            'cuadre_ok': cuadre_ok,
            'resultado': resultado,
            'puede_cerrar': cuadre_ok and periodo.estado == 'ABIERTO'
        })
        
    except PeriodoContable.DoesNotExist:
        return JsonResponse({'error': 'Período no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def dashboard_resumen(request):
    """Dummy view for now"""
    return JsonResponse({'status': 'ok'})

@require_http_methods(["GET"])
@login_required
def validar_xml(request):
    """
    Endpoint para generar y visualizar el XML de una factura (Simulando validación)
    """
    venta_id = request.GET.get('venta_id')
    if not venta_id:
        return JsonResponse({'error': 'Se requiere venta_id'}, status=400)

    try:
        if not venta_id.isdigit():
             return JsonResponse({'error': 'venta_id debe ser numérico'}, status=400)
             
        # Buscar Venta
        try:
            venta = Venta.objects.get(id=int(venta_id))
        except Venta.DoesNotExist:
            return JsonResponse({'error': 'Venta no encontrada'}, status=404)

        # Buscar o Crear Factura Electrónica
        factura, created = FacturaElectronica.objects.get_or_create(
            venta=venta,
            defaults={
                'ambiente': 2, # Pruebas
                'estado_dian': 'PENDIENTE'
            }
        )

        # Generar XML
        from app.fiscal.core.factura_xml_generator import GeneradorXMLDIAN
        from app.fiscal.core.firma_digital import FirmadorDIAN
        from app.fiscal.core.cufe import GeneradorCUFE

        # 1. Generar XML Base
        generador = GeneradorXMLDIAN()
        xml_base = generador.generar_xml_factura(factura)

        # 2. Calcular CUFE (Si no tiene)
        if not factura.cufe:
             # Necesitamos impuetos y total para CUFE real, por ahora usamos mock o datos de venta
             # El generador de CUFE requiere datos precisos.
             # Para este endpoint, actualizamos el XML con el CUFE si logramos calcularlo.
             # Por simplicidad del MVP, asumimos que el GeneradorXML ya inyectó algo o lo hará.
             pass

        # 3. Firmar XML (Mock)
        firmador = FirmadorDIAN()
        xml_firmado = firmador.firmar_xml(xml_base)

        # Actualizar estado (simulado)
        if factura.estado_dian == 'PENDIENTE':
            factura.estado_dian = 'GENERADO'
            factura.save()

        return HttpResponse(xml_firmado, content_type='application/xml')

    except Exception as e:
        import traceback
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)

# === DECLARACIÓN DE IVA (Formulario 300) ===

from .services.tax_service import TaxCalculatorService

@login_required
def declaracion_iva(request):
    """
    Vista principal para la declaración de IVA (Formulario 300)
    """
    context = {
        'title': 'Declaración de IVA - Formulario 300',
        'current_year': datetime.now().year,
        'period_types': [
            {'value': 'bimestral', 'label': 'Bimestral (6 períodos/año)'},
            {'value': 'cuatrimestral', 'label': 'Cuatrimestral (3 períodos/año)'},
        ],
        'range': range(datetime.now().year - 2, datetime.now().year + 2), # Add range context
    }
    
    # Si hay parámetros GET, generar el reporte
    if request.method == 'GET' and 'year' in request.GET:
        try:
            year = int(request.GET.get('year', datetime.now().year))
            period_type = request.GET.get('period_type', 'bimestral')
            period_number = int(request.GET.get('period_number', 1))
            
            # Obtener la declaración
            declaracion = TaxCalculatorService.get_declaracion_iva(
                year, period_type, period_number
            )
            
            context['declaracion'] = declaracion
            context['selected_year'] = year
            context['selected_period_type'] = period_type
            context['selected_period_number'] = period_number
            
            # Mensaje según el resultado
            if declaracion['resumen']['iva_neto_a_pagar'] > 0:
                context['resultado_mensaje'] = f"IVA a Pagar: ${declaracion['resumen']['iva_neto_a_pagar']:,.2f}"
                context['resultado_clase'] = 'warning'
            elif declaracion['resumen']['iva_neto_a_pagar'] < 0:
                context['resultado_mensaje'] = f"Saldo a Favor: ${abs(declaracion['resumen']['iva_neto_a_pagar']):,.2f}"
                context['resultado_clase'] = 'success'
            else:
                context['resultado_mensaje'] = "IVA en Cero - No hay pago ni saldo a favor"
                context['resultado_clase'] = 'info'
                
        except ValueError as e:
            context['error'] = f"Error en los parámetros: {str(e)}"
        except Exception as e:
            context['error'] = f"Error generando la declaración: {str(e)}"
    
    return render(request, 'fiscal/declaracion_iva.html', context)

@login_required
def declaracion_iva_detalle(request):
    """
    API para obtener detalles de la declaración de IVA
    """
    if request.method == 'GET':
        try:
            year = int(request.GET.get('year', datetime.now().year))
            period_type = request.GET.get('period_type', 'bimestral')
            period_number = int(request.GET.get('period_number', 1))
            detalle_tipo = request.GET.get('tipo', 'ventas')  # 'ventas' o 'compras'
            
            # Obtener fechas del período
            start_date, end_date = TaxCalculatorService.get_period_dates(
                year, period_type, period_number
            )
            
            if detalle_tipo == 'ventas':
                detalle = TaxCalculatorService.get_iva_generado(start_date, end_date)
            else:
                detalle = TaxCalculatorService.get_iva_descontable(start_date, end_date)
            
            return JsonResponse({
                'success': True,
                'detalle': detalle,
                'periodo': f"{start_date} al {end_date}",
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def declaracion_iva_export(request):
    """
    Exportar declaración de IVA a formato JSON o CSV
    """
    if request.method == 'GET':
        try:
            year = int(request.GET.get('year', datetime.now().year))
            period_type = request.GET.get('period_type', 'bimestral')
            period_number = int(request.GET.get('period_number', 1))
            formato = request.GET.get('formato', 'json')
            
            declaracion = TaxCalculatorService.get_declaracion_iva(
                year, period_type, period_number
            )
            
            if formato == 'csv':
                # Generar CSV (simplificado)
                import csv
                from django.http import HttpResponse
                
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="declaracion_iva_{year}_{period_type}_{period_number}.csv"'
                
                writer = csv.writer(response)
                
                # Escribir encabezados
                writer.writerow(['Concepto', 'Base Gravable', 'IVA', 'Tarifa'])
                
                # IVA Generado
                writer.writerow(['IVA GENERADO (VENTAS)', '', '', ''])
                for tarifa_key, tarifa in declaracion['iva_generado']['tarifas'].items():
                    if tarifa['tax'] > 0:
                        writer.writerow([
                            f'Ventas {tarifa_key}%',
                            f"${tarifa['base']:,.2f}",
                            f"${tarifa['tax']:,.2f}",
                            f"{tarifa_key}%"
                        ])
                
                writer.writerow([
                    'TOTAL IVA GENERADO',
                    f"${declaracion['iva_generado']['total_base']:,.2f}",
                    f"${declaracion['iva_generado']['total_tax']:,.2f}",
                    ''
                ])
                
                # IVA Descontable
                writer.writerow(['IVA DESCONTABLE (COMPRAS)', '', '', ''])
                for tarifa_key, tarifa in declaracion['iva_descontable']['tarifas'].items():
                    if tarifa['tax'] > 0:
                        writer.writerow([
                            f'Compras {tarifa_key}%',
                            f"${tarifa['base']:,.2f}",
                            f"${tarifa['tax']:,.2f}",
                            f"{tarifa_key}%"
                        ])
                
                writer.writerow([
                    'TOTAL IVA DESCONTABLE',
                    f"${declaracion['iva_descontable']['total_base']:,.2f}",
                    f"${declaracion['iva_descontable']['total_tax']:,.2f}",
                    ''
                ])
                
                # Resultado
                writer.writerow(['IVA NETO A PAGAR', '', f"${declaracion['resumen']['iva_neto_a_pagar']:,.2f}", ''])
                
                return response
            
            else:
                # JSON por defecto
                return JsonResponse({
                    'success': True,
                    'declaracion': declaracion
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

# === RETENCIÓN EN LA FUENTE (Formulario 350) ===

from .services.retention_service import WithholdingTaxService

@login_required
def declaracion_retefuente(request):
    """
    Vista principal para la declaración de retención en la fuente (Formulario 350)
    """
    context = {
        'title': 'Declaración de Retención en la Fuente - Formulario 350',
        'current_year': datetime.now().year,
        'current_month': datetime.now().month,
        'months': [
            {'value': 1, 'label': 'Enero'},
            {'value': 2, 'label': 'Febrero'},
            {'value': 3, 'label': 'Marzo'},
            {'value': 4, 'label': 'Abril'},
            {'value': 5, 'label': 'Mayo'},
            {'value': 6, 'label': 'Junio'},
            {'value': 7, 'label': 'Julio'},
            {'value': 8, 'label': 'Agosto'},
            {'value': 9, 'label': 'Septiembre'},
            {'value': 10, 'label': 'Octubre'},
            {'value': 11, 'label': 'Noviembre'},
            {'value': 12, 'label': 'Diciembre'},
        ],
        'range': range(datetime.now().year - 2, datetime.now().year + 2),
    }
    
    # Si hay parámetros GET, generar el reporte
    if request.method == 'GET' and 'year' in request.GET:
        try:
            year = int(request.GET.get('year', datetime.now().year))
            month = int(request.GET.get('month', datetime.now().month))
            
            # Validar mes
            if not 1 <= month <= 12:
                raise ValueError("El mes debe estar entre 1 y 12")
            
            # Obtener la declaración
            declaracion = WithholdingTaxService.get_declaracion_retefuente(year, month)
            
            # Obtener formato Formulario 350
            formulario_350 = WithholdingTaxService.export_formulario_350_format(declaracion)
            
            context['declaracion'] = declaracion
            context['formulario_350'] = formulario_350
            context['selected_year'] = year
            context['selected_month'] = month
            
            # Resumen de UVT
            uvt_value = WithholdingTaxService.get_uvt_value(year)
            context['uvt_info'] = {
                'value': uvt_value,
                'year': year,
            }
            
            # Calcular umbrales
            thresholds = {}
            for concept_key in WithholdingTaxService.RETENTION_CONCEPTS:
                threshold = WithholdingTaxService.calculate_threshold_amount(year, concept_key)
                thresholds[concept_key] = threshold
            context['thresholds'] = thresholds
            
        except ValueError as e:
            context['error'] = f"Error en los parámetros: {str(e)}"
        except Exception as e:
            context['error'] = f"Error generando la declaración: {str(e)}"
    
    return render(request, 'fiscal/declaracion_retefuente.html', context)

@login_required
def declaracion_retefuente_detalle(request):
    """
    API para obtener detalles específicos de la declaración
    """
    if request.method == 'GET':
        try:
            year = int(request.GET.get('year', datetime.now().year))
            month = int(request.GET.get('month', datetime.now().month))
            concepto = request.GET.get('concepto', None)
            
            declaracion = WithholdingTaxService.get_declaracion_retefuente(year, month)
            
            if concepto and concepto in declaracion['conceptos']:
                # Filtrar por concepto específico
                response_data = {
                    'success': True,
                    'concepto': concepto,
                    'data': declaracion['conceptos'][concepto],
                    'periodo': declaracion['periodo']['label'],
                }
            else:
                # Enviar todo
                response_data = {
                    'success': True,
                    'declaracion': declaracion,
                }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def declaracion_retefuente_export(request):
    """
    Exportar declaración de retención a diferentes formatos
    """
    if request.method == 'GET':
        try:
            year = int(request.GET.get('year', datetime.now().year))
            month = int(request.GET.get('month', datetime.now().month))
            formato = request.GET.get('formato', 'json')
            
            declaracion = WithholdingTaxService.get_declaracion_retefuente(year, month)
            formulario_350 = WithholdingTaxService.export_formulario_350_format(declaracion)
            
            if formato == 'csv':
                # Generar CSV
                import csv
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="formulario_350_{year}_{month:02d}.csv"'
                
                writer = csv.writer(response)
                
                # Encabezado
                writer.writerow(['FORMULARIO 350 - DECLARACIÓN DE RETENCIÓN EN LA FUENTE'])
                writer.writerow(['Período', f"{month:02d}/{year}"])
                writer.writerow(['Fecha generación', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow(['Valor UVT', declaracion['metadata']['uvt_value']])
                writer.writerow([])
                
                # Conceptos
                writer.writerow(['Concepto', 'Código', 'Base Gravable', 'Valor Retenido', 'Transacciones', 'Declarantes', 'No Declarantes'])
                
                for concept_key, data in declaracion['conceptos'].items():
                    if data['retention_amount'] > 0:
                        writer.writerow([
                            data['concept']['name'],
                            data['concept']['code'],
                            data['base_amount'],
                            data['retention_amount'],
                            len(data['transactions']),
                            data['declarant_count'],
                            data['non_declarant_count'],
                        ])
                
                writer.writerow([])
                writer.writerow(['TOTAL GENERAL', '', 
                               declaracion['totales']['total_base'],
                               declaracion['totales']['total_retencion'],
                               declaracion['totales']['total_transacciones'],
                               '', ''])
                
                # Detalle (segundo sheet simulado)
                writer.writerow([])
                writer.writerow(['DETALLE DE TRANSACCIONES'])
                writer.writerow(['Concepto', 'Factura', 'Proveedor', 'Fecha', 'Producto', 'Base', 'Retención'])
                
                for transaccion in declaracion['detalle_completo']:
                    writer.writerow([
                        transaccion['concept_name'],
                        transaccion['invoice_number'],
                        transaccion['supplier'],
                        transaccion['date'].strftime('%Y-%m-%d'),
                        transaccion['product'],
                        transaccion['base'],
                        transaccion['retention'],
                    ])
                
                return response
            
            elif formato == 'pdf':
                # Para PDF necesitaríamos ReportLab o similar
                # Por ahora devolver JSON con mensaje
                return JsonResponse({
                    'success': True,
                    'message': 'Exportación PDF en desarrollo',
                    'formulario': formulario_350
                })
            
            else:
                # JSON por defecto
                return JsonResponse({
                    'success': True,
                    'formulario_350': formulario_350
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def declaracion_retefuente_resumen_anual(request):
    """
    Vista para resumen anual de retenciones
    """
    if request.method == 'GET':
        try:
            year = int(request.GET.get('year', datetime.now().year))
            
            summary = WithholdingTaxService.get_monthly_summary(year)
            uvt_value = WithholdingTaxService.get_uvt_value(year)
            
            return JsonResponse({
                'success': True,
                'summary': summary,
                'uvt_value': float(uvt_value),
                'year': year,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})
