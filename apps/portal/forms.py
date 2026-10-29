from django import forms
from apps.socios.models import Socio


class ActualizarContactoForm(forms.ModelForm):
    """
    Formulario para que el socio actualice sus propios datos de contacto.
    Sección 11 de la fuente funcional.
    """
    class Meta:
        model = Socio
        fields = ['telefono', 'email']
        widgets = {
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. 71234567'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
        }

    def clean_telefono(self):
        tel = self.cleaned_data.get('telefono', '').strip()
        return tel

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        return email

