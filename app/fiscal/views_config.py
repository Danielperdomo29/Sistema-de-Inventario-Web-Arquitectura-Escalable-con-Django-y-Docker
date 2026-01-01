
# === CONFIGURACIÓN FISCAL (FACTURACIÓN ELECTRÓNICA) ===

from django.contrib.auth.decorators import login_required

from app.fiscal.forms.fiscal_config_form import FiscalConfigForm
from app.fiscal.models.fiscal_config import FiscalConfig
from app.fiscal.core.security.encryption import FiscalEncryptionManager
from django.contrib import messages
from django.shortcuts import render, redirect

@login_required
def configuracion_fiscal(request):
    """
    Vista para configurar la Facturación Electrónica.
    Permite subir el certificado .p12 y configurar credenciales.
    """
    try:
        config = FiscalConfig.objects.first()
    except FiscalConfig.DoesNotExist:
        config = None

    if request.method == 'POST':
        form = FiscalConfigForm(request.POST, request.FILES, instance=config)
        
        if form.is_valid():
            try:
                fiscal_config = form.save(commit=False)
                
                # Cifrar contraseña del certificado
                raw_password = form.cleaned_data.get('certificate_password')
                if raw_password:
                     fiscal_config.set_password(raw_password)
                
                fiscal_config.save()
                
                messages.success(request, 'Configuración fiscal guardada exitosamente.')
                return redirect('configuracion_fiscal')
                
            except Exception as e:
                messages.error(request, f'Error al guardar: {str(e)}')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        if config:
            form = FiscalConfigForm(instance=config)
        else:
            form = FiscalConfigForm()

    return render(request, 'fiscal/configuracion.html', {
        'form': form,
        'title': 'Configuración DIAN',
        'config_exists': config is not None
    })
