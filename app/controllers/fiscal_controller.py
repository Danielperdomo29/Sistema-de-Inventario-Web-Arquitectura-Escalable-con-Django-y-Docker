"""
Controlador para el Módulo Fiscal - Fase A.

Gestiona las vistas del módulo fiscal incluyendo perfiles fiscales,
cuentas PUC e impuestos.
"""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404

from app.fiscal.models import PerfilFiscal, CuentaContable, Impuesto
from app.views.fiscal_view import FiscalView


class FiscalController:
    """Controlador del Módulo Fiscal"""

    @staticmethod
    @login_required(login_url="/login/")
    def index(request):
        """Dashboard del módulo fiscal con estadísticas"""
        user = request.user

        # Obtener estadísticas del módulo fiscal
        stats = {
            "total_perfiles": PerfilFiscal.objects.count(),
            "total_cuentas_puc": CuentaContable.objects.count(),
            "total_impuestos": Impuesto.objects.count(),
            "perfiles_activos": PerfilFiscal.objects.filter(activo=True).count(),
            "cuentas_activas": CuentaContable.objects.filter(activa=True).count(),
            "impuestos_activos": Impuesto.objects.filter(activo=True).count(),
        }

        # Obtener últimos perfiles creados
        ultimos_perfiles = PerfilFiscal.objects.select_related(
            'cliente', 'proveedor'
        ).order_by('-fecha_creacion')[:5]

        # Convertir a diccionarios para la vista
        perfiles_data = []
        for perfil in ultimos_perfiles:
            perfiles_data.append({
                'id': perfil.id,
                'nombre': perfil.get_nombre_completo(),
                'tipo_documento': perfil.get_tipo_documento_display(),
                'numero_documento': perfil.numero_documento,
                'dv': perfil.dv,
                'regimen': perfil.get_regimen_display(),
                'fecha_creacion': perfil.fecha_creacion.strftime('%Y-%m-%d'),
            })

        return HttpResponse(
            FiscalView.index(user, request.path, stats, perfiles_data)
        )

    @staticmethod
    @login_required(login_url="/login/")
    def perfiles_fiscales(request):
        """Listado de perfiles fiscales"""
        user = request.user

        # Obtener todos los perfiles fiscales
        perfiles = PerfilFiscal.objects.select_related(
            'cliente', 'proveedor'
        ).order_by('-fecha_creacion')

        # Convertir a diccionarios para la vista
        perfiles_data = []
        for perfil in perfiles:
            perfiles_data.append({
                'id': perfil.id,
                'nombre': perfil.get_nombre_completo(),
                'tipo_documento': perfil.get_tipo_documento_display(),
                'numero_documento': perfil.numero_documento,
                'dv': perfil.dv,
                'tipo_persona': perfil.get_tipo_persona_display(),
                'regimen': perfil.get_regimen_display(),
                'email': perfil.email_facturacion,
                'activo': perfil.activo,
            })

        return HttpResponse(
            FiscalView.perfiles_list(user, request.path, perfiles_data)
        )

    @staticmethod
    @login_required(login_url="/login/")
    def perfil_fiscal_crear(request):
        """Formulario para crear perfil fiscal"""
        user = request.user

        if request.method == 'POST':
            # TODO: Implementar creación de perfil fiscal
            # Por ahora redirigir al listado
            return HttpResponseRedirect('/fiscal/perfiles/')

        return HttpResponse(
            FiscalView.perfil_form(user, request.path, None)
        )

    @staticmethod
    @login_required(login_url="/login/")
    def perfil_fiscal_editar(request, perfil_id):
        """Formulario para editar perfil fiscal"""
        user = request.user
        perfil = get_object_or_404(PerfilFiscal, id=perfil_id)

        if request.method == 'POST':
            # TODO: Implementar edición de perfil fiscal
            # Por ahora redirigir al listado
            return HttpResponseRedirect('/fiscal/perfiles/')

        # Convertir perfil a diccionario para la vista
        perfil_data = {
            'id': perfil.id,
            'nombre': perfil.get_nombre_completo(),
            'tipo_documento': perfil.tipo_documento,
            'numero_documento': perfil.numero_documento,
            'dv': perfil.dv,
            'tipo_persona': perfil.tipo_persona,
            'regimen': perfil.regimen,
            'responsabilidades': perfil.responsabilidades,
            'departamento_codigo': perfil.departamento_codigo,
            'municipio_codigo': perfil.municipio_codigo,
            'nombre_comercial': perfil.nombre_comercial,
            'email_facturacion': perfil.email_facturacion,
            'telefono': perfil.telefono,
            'direccion': perfil.direccion,
            'activo': perfil.activo,
        }

        return HttpResponse(
            FiscalView.perfil_form(user, request.path, perfil_data)
        )

    @staticmethod
    @login_required(login_url="/login/")
    def cuentas_puc(request):
        """Listado jerárquico de cuentas PUC"""
        user = request.user

        # Obtener cuentas de nivel 1 (clases)
        cuentas_nivel_1 = CuentaContable.objects.filter(nivel=1).order_by('codigo')

        # Construir árbol jerárquico
        cuentas_tree = []
        for cuenta_clase in cuentas_nivel_1:
            # Obtener subcuentas de nivel 2
            subcuentas_nivel_2 = CuentaContable.objects.filter(
                padre=cuenta_clase
            ).order_by('codigo')

            subcuentas_data = []
            for subcuenta in subcuentas_nivel_2:
                # Obtener subcuentas de nivel 3
                subcuentas_nivel_3 = CuentaContable.objects.filter(
                    padre=subcuenta
                ).order_by('codigo')

                subcuentas_nivel_3_data = []
                for sub3 in subcuentas_nivel_3:
                    subcuentas_nivel_3_data.append({
                        'codigo': sub3.codigo,
                        'nombre': sub3.nombre,
                        'naturaleza': sub3.naturaleza,
                        'activa': sub3.activa,
                    })

                subcuentas_data.append({
                    'codigo': subcuenta.codigo,
                    'nombre': subcuenta.nombre,
                    'naturaleza': subcuenta.naturaleza,
                    'activa': subcuenta.activa,
                    'subcuentas': subcuentas_nivel_3_data,
                })

            cuentas_tree.append({
                'codigo': cuenta_clase.codigo,
                'nombre': cuenta_clase.nombre,
                'naturaleza': cuenta_clase.naturaleza,
                'activa': cuenta_clase.activa,
                'subcuentas': subcuentas_data,
            })

        return HttpResponse(
            FiscalView.cuentas_puc_list(user, request.path, cuentas_tree)
        )

    @staticmethod
    @login_required(login_url="/login/")
    def impuestos(request):
        """Listado de impuestos configurados"""
        user = request.user

        # Obtener todos los impuestos
        impuestos = Impuesto.objects.select_related('cuenta_por_pagar').order_by('codigo')

        # Convertir a diccionarios para la vista
        impuestos_data = []
        for impuesto in impuestos:
            impuestos_data.append({
                'id': impuesto.id,
                'codigo': impuesto.codigo,
                'nombre': impuesto.nombre,
                'tipo': impuesto.get_tipo_display(),
                'porcentaje': float(impuesto.porcentaje),
                'base_minima': float(impuesto.base_minima) if impuesto.base_minima else None,
                'cuenta_por_pagar': f"{impuesto.cuenta_por_pagar.codigo} - {impuesto.cuenta_por_pagar.nombre}",
                'aplica_ventas': impuesto.aplica_ventas,
                'aplica_compras': impuesto.aplica_compras,
                'activo': impuesto.activo,
            })

        return HttpResponse(
            FiscalView.impuestos_list(user, request.path, impuestos_data)
        )
