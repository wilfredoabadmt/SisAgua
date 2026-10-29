from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError
from .models import Servicio, Tarifario, TramoTarifario, ModalidadCobro, TipoServicio, CategoriaTarifa


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['codigo', 'nombre', 'tipo_servicio', 'modalidad_cobro', 'descripcion', 'activo']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 uppercase font-mono',
                'placeholder': 'Ej. AGUA, MEMBRESIA, BASURA',
                'required': 'required'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Nombre descriptivo del servicio',
                'required': 'required'
            }),
            'tipo_servicio': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'modalidad_cobro': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Descripción de alcances, condiciones y frecuencia'
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
        qs = Servicio.objects.filter(codigo=codigo)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f"Ya existe un servicio con el código '{codigo}'.")
        return codigo


class TarifarioForm(forms.ModelForm):
    class Meta:
        model = Tarifario
        fields = [
            'nombre', 'servicio', 'categoria', 'tarifa_basica',
            'consumo_minimo_m3', 'precio_adicional_m3',
            'fecha_vigencia_desde', 'fecha_vigencia_hasta', 'activo'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ej. Tarifario General Doméstico 2026',
                'required': 'required'
            }),
            'servicio': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'required': 'required'
            }),
            'categoria': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'tarifa_basica': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'min': '0.00',
                'placeholder': '10.00'
            }),
            'consumo_minimo_m3': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'min': '0.00',
                'placeholder': '10.00'
            }),
            'precio_adicional_m3': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'min': '0.00',
                'placeholder': '2.00'
            }),
            'fecha_vigencia_desde': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'type': 'date',
                'required': 'required'
            }),
            'fecha_vigencia_hasta': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'type': 'date'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-slate-300 rounded'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['activo'].initial = True


class TramoTarifarioForm(forms.ModelForm):
    class Meta:
        model = TramoTarifario
        fields = ['orden', 'desde_m3', 'hasta_m3', 'precio_unitario', 'es_valor_fijo']
        widgets = {
            'orden': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'min': 1}),
            'desde_m3': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'step': '0.01'}),
            'hasta_m3': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'step': '0.01', 'placeholder': 'Abierto si vacío'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'step': '0.01'}),
            'es_valor_fijo': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 rounded'}),
        }

