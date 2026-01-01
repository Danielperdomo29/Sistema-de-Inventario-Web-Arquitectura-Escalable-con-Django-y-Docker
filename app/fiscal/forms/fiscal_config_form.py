from django import forms
from app.fiscal.models.fiscal_config import FiscalConfig

class FiscalConfigForm(forms.ModelForm):
    certificado_archivo = forms.FileField(
        label="Certificado Digital (.p12)",
        help_text="Archivo .p12 proporcionado por la autoridad de certificación (GSE, Andes, etc.)",
        required=True
    )
    certificate_password = forms.CharField(
        label="Contraseña del Certificado",
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••'}),
        help_text="Contraseña para descifrar el almacén de claves",
        required=True
    )

    class Meta:
        model = FiscalConfig
        fields = [
            'nit_emisor', 'dv_emisor', 'razon_social', 
            'software_id', 'pin_software', 'test_set_id', 
            'ambiente'
        ]
        widgets = {
            'nit_emisor': forms.TextInput(attrs={'class': 'form-control'}),
            'dv_emisor': forms.TextInput(attrs={'class': 'form-control', 'style': 'width: 60px;'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control'}),
            'software_id': forms.TextInput(attrs={'class': 'form-control'}),
            'pin_software': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••'}),
            'test_set_id': forms.TextInput(attrs={'class': 'form-control'}),
            'ambiente': forms.Select(attrs={'class': 'form-select'}),
        }
