from decimal import Decimal
from django import forms
from apps.caja.models import CajaTurno, Recibo, MetodoPago


class AperturaTurnoForm(forms.ModelForm):
    """Formulario para la apertura de turno de caja con fondo inicial."""
    class Meta:
        model = CajaTurno
        fields = ['monto_apertura']
        widgets = {
            'monto_apertura': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.50',
                'min': '0.00',
                'placeholder': '0.00'
            })
        }
        labels = {
            'monto_apertura': 'Fondo Inicial de Caja / Cambio (Bs)'
        }

    def clean_monto_apertura(self):
        monto = self.cleaned_data.get('monto_apertura')
        if monto is None or monto < Decimal('0.00'):
            raise forms.ValidationError("El monto de apertura no puede ser negativo.")
        return monto


class CierreTurnoForm(forms.ModelForm):
    """Formulario para el arqueo físico y cierre de turno."""
    class Meta:
        model = CajaTurno
        fields = ['monto_declarado_efectivo', 'observaciones_cierre']
        widgets = {
            'monto_declarado_efectivo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.50',
                'min': '0.00',
                'placeholder': '0.00',
                'required': 'required'
            }),
            'observaciones_cierre': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Justificación obligatoria si existe faltante o sobrante de efectivo en gaveta.'
            })
        }
        labels = {
            'monto_declarado_efectivo': 'Monto Físico Contado en Gaveta (Bs)',
            'observaciones_cierre': 'Observaciones / Justificación de Diferencia'
        }


class CobroVentanillaForm(forms.Form):
    """Formulario para procesar el cobro en ventanilla."""
    socio_id = forms.IntegerField(widget=forms.HiddenInput())
    metodo_pago = forms.ChoiceField(
        choices=MetodoPago.choices,
        initial=MetodoPago.EFECTIVO,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Método de Pago'
    )
    referencia_transaccion = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nº de comprobante, transferencia o referencia digital'
        }),
        label='Referencia de Transacción'
    )


class AnularReciboForm(forms.Form):
    """Formulario para anulación autorizada de recibo oficial."""
    motivo = forms.CharField(
        min_length=10,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Explique claramente el motivo documentado por el cual se procede a anular el recibo oficial.'
        }),
        label='Motivo Justificado de Anulación',
        help_text='Mínimo 10 caracteres obligatorios.'
    )

