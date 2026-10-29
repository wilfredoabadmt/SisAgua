from django import forms
from django.core.exceptions import ValidationError
from .models import Zona, Socio, EstadoSocio


class ZonaForm(forms.ModelForm):
    class Meta:
        model = Zona
        fields = ['codigo', 'nombre', 'descripcion', 'responsable', 'observaciones', 'activo']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 uppercase',
                'placeholder': 'Ej. ZON-CENTRO',
                'required': 'required'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Nombre oficial de la zona o sector',
                'required': 'required'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Delimitación territorial o linderos'
            }),
            'responsable': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Nombre del delegado o contacto vecinal'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 2,
                'placeholder': 'Notas adicionales'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-slate-300 rounded'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['activo'].initial = True

    def clean_activo(self):
        if not self.instance.pk and 'activo' not in self.data:
            return True
        return self.cleaned_data.get('activo', False)

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '').strip().upper()
        qs = Zona.objects.filter(codigo=codigo)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f"Ya existe una zona registrada con el código '{codigo}'.")
        return codigo


class SocioForm(forms.ModelForm):
    class Meta:
        model = Socio
        fields = [
            'codigo', 'ci', 'ci_complemento', 'nombres', 'apellidos',
            'zona', 'direccion', 'telefono', 'email', 'fecha_ingreso',
            'estado', 'observaciones'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 uppercase font-mono',
                'placeholder': 'Autogenerado si se deja en blanco'
            }),
            'ci': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono',
                'placeholder': 'Ej. 4892019',
                'required': 'required'
            }),
            'ci_complemento': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 uppercase font-mono',
                'placeholder': 'Ej. 1A, LP (opcional)'
            }),
            'nombres': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Nombres',
                'required': 'required'
            }),
            'apellidos': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Apellidos',
                'required': 'required'
            }),
            'zona': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'required': 'required'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Calle, número de casa, manzana, lote o referencia',
                'required': 'required'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Número celular o fijo'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'correo@ejemplo.com'
            }),
            'fecha_ingreso': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'type': 'date'
            }),
            'estado': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 2,
                'placeholder': 'Observaciones o notas'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = False
        # Filtrar solo zonas activas
        self.fields['zona'].queryset = Zona.objects.filter(activo=True)

    def clean(self):
        cleaned_data = super().clean()
        ci = cleaned_data.get('ci', '').strip()
        ci_complemento = cleaned_data.get('ci_complemento', '').strip().upper()

        if ci:
            qs = Socio.objects.filter(ci=ci, ci_complemento=ci_complemento)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                comp_txt = f"-{ci_complemento}" if ci_complemento else ""
                raise ValidationError(f"Ya existe un socio registrado con el CI {ci}{comp_txt}.")

        return cleaned_data
