from django import forms
from .models import Institucion, Menu

class InstitucionForm(forms.ModelForm):
    class Meta:
        model = Institucion
        fields = [
            'nombre', 'logo', 'direccion', 'telefono', 'correo',
            'nit_personeria', 'texto_recibo', 'dia_facturacion', 'dia_vencimiento_default'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:ring focus:ring-blue-200'}),
            'direccion': forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-3 py-2 border rounded-lg'}),
            'telefono': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'correo': forms.EmailInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'nit_personeria': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'texto_recibo': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-3 py-2 border rounded-lg'}),
            'dia_facturacion': forms.NumberInput(attrs={'class': 'w-24 px-3 py-2 border rounded-lg', 'min': 1, 'max': 28}),
            'dia_vencimiento_default': forms.NumberInput(attrs={'class': 'w-24 px-3 py-2 border rounded-lg', 'min': 1, 'max': 31}),
        }

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo and hasattr(logo, 'size'):
            if logo.size > 2 * 1024 * 1024:
                raise forms.ValidationError("El tamaño del logotipo no puede superar los 2 MB.")
        return logo

