from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Lectura, EstadoLectura
from apps.medidores.models import Medidor


class CapturaLecturaForm(forms.Form):
    periodo = forms.CharField(
        max_length=7,
        initial=lambda: timezone.now().strftime('%Y-%m'),
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono',
            'placeholder': 'YYYY-MM (ej. 2026-10)',
            'required': 'required'
        }),
        label="Periodo Mensual"
    )
    medidor = forms.ModelChoiceField(
        queryset=Medidor.objects.filter(estado='INSTALADO', activo=True),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'required': 'required'
        }),
        label="Medidor de Agua (Activo)"
    )
    lectura_actual = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono',
            'step': '0.01',
            'min': '0.00',
            'placeholder': '0.00',
            'required': 'required'
        }),
        label="Lectura Actual de Campo (m³)"
    )
    fecha_lectura = forms.DateField(
        initial=timezone.now,
        widget=forms.DateInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'type': 'date',
            'required': 'required'
        }),
        label="Fecha de la Toma"
    )
    es_reinicio_contador = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 rounded'}),
        label="¿Es reinicio de contador (vuelta a cero tras 99999)?"
    )
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'rows': 2,
            'placeholder': 'Observaciones de campo (ej. perro bravo, nicho cerrado)'
        }),
        label="Observaciones"
    )

    def clean_periodo(self):
        periodo = self.cleaned_data.get('periodo', '').strip()
        parts = periodo.split('-')
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            raise ValidationError("El periodo debe tener el formato YYYY-MM (ej. 2026-10).")
        mes = int(parts[1])
        if mes < 1 or mes > 12:
            raise ValidationError("El mes debe estar entre 01 y 12.")
        return periodo


class CorregirLecturaForm(forms.Form):
    nueva_lectura = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono',
            'step': '0.01',
            'min': '0.00',
            'required': 'required'
        }),
        label="Lectura Corregida Verificada (m³)"
    )
    motivo_correccion = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'rows': 3,
            'placeholder': 'Justificación documentada para la bitácora de auditoría...',
            'required': 'required'
        }),
        label="Motivo / Justificación Documentada"
    )
    es_reinicio_contador = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 rounded'}),
        label="Confirmar reinicio de contador mecánico (Rollover)"
    )


class FacturacionForm(forms.Form):
    periodo = forms.CharField(
        max_length=7,
        initial=lambda: timezone.now().strftime('%Y-%m'),
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono',
            'placeholder': 'YYYY-MM',
            'required': 'required'
        }),
        label="Periodo a Facturar"
    )

