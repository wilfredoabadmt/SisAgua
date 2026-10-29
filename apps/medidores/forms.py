from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError
from .models import Medidor, AsignacionMedidor, EstadoMedidor
from apps.socios.models import Socio


class MedidorForm(forms.ModelForm):
    class Meta:
        model = Medidor
        fields = [
            'codigo', 'numero_serie', 'marca', 'modelo',
            'diametro', 'lectura_inicial', 'ubicacion',
            'estado', 'observaciones'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 uppercase font-mono',
                'placeholder': 'Autogenerado si se deja vacío (ej. MED-0001)'
            }),
            'numero_serie': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 uppercase font-mono',
                'placeholder': 'Serie de fábrica estampada en el reloj',
                'required': 'required'
            }),
            'marca': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ej. Zenner, Elster, Actaris'
            }),
            'modelo': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ej. MNK-N, V200'
            }),
            'diametro': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': '1/2", 3/4", 1"'
            }),
            'lectura_inicial': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono',
                'step': '0.01',
                'min': '0.00',
                'placeholder': '0.00'
            }),
            'ubicacion': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Almacén central / Nicho'
            }),
            'estado': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 2,
                'placeholder': 'Notas sobre calibración o lote'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = False

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '').strip().upper()
        if codigo:
            qs = Medidor.objects.filter(codigo=codigo)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f"Ya existe un medidor con el código '{codigo}'.")
        return codigo

    def clean_numero_serie(self):
        serie = self.cleaned_data.get('numero_serie', '').strip().upper()
        qs = Medidor.objects.filter(numero_serie=serie)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f"Ya existe un medidor registrado con el número de serie '{serie}'.")
        return serie


class AsignarMedidorForm(forms.Form):
    socio = forms.ModelChoiceField(
        queryset=Socio.objects.filter(estado='ACTIVO'),
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
        label="Socio Titular"
    )
    fecha_asignacion = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'type': 'date'}),
        label="Fecha de Instalación / Asignación"
    )
    lectura_instalacion = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono', 'step': '0.01'}),
        label="Lectura de Instalación (m³)"
    )


class RetirarMedidorForm(forms.Form):
    fecha_retiro = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'type': 'date'}),
        label="Fecha de Retiro / Sustitución"
    )
    lectura_retiro = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono', 'step': '0.01'}),
        label="Lectura Final de Retiro (m³)"
    )
    motivo_retiro = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'placeholder': 'Ej. Avería, cambio por mayor caudal, baja'}),
        label="Motivo del Retiro"
    )
    nuevo_estado_medidor = forms.ChoiceField(
        choices=[
            (EstadoMedidor.MANTENIMIENTO, 'En Mantenimiento'),
            (EstadoMedidor.DISPONIBLE, 'Disponible para reasignar'),
            (EstadoMedidor.RETIRADO, 'Retirado / Descartado'),
            (EstadoMedidor.DE_BAJA, 'De Baja definitiva'),
        ],
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
        label="Nuevo Estado del Medidor Físico"
    )

