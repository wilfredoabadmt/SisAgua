from decimal import Decimal
from django import forms
from apps.socios.models import Socio
from apps.medidores.models import Medidor
from apps.transcripcion.models import LoteTranscripcion, TranscripcionLectura


class LoteTranscripcionForm(forms.ModelForm):
    """Formulario para la creación de lotes de transcripción histórica."""
    class Meta:
        model = LoteTranscripcion
        fields = ['codigo', 'nombre', 'periodo_predeterminado', 'fuente_documental', 'total_estimado', 'observaciones']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. LOT-2024-NORTE',
                'style': 'text-transform: uppercase;'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Planilla Manuscrita 2024 - Sector Norte'
            }),
            'periodo_predeterminado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'YYYY-MM (ej. 2024-05)'
            }),
            'fuente_documental': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Cuaderno empastado tomo 1, archivo parroquial'
            }),
            'total_estimado': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones o notas preliminares sobre el estado físico del documento'
            })
        }


class TranscripcionLecturaForm(forms.ModelForm):
    """Formulario para digitación de lecturas históricas individuales."""
    class Meta:
        model = TranscripcionLectura
        fields = [
            'socio', 'medidor', 'periodo',
            'lectura_anterior', 'lectura_actual',
            'importe_documentado', 'referencia_foja', 'observaciones'
        ]
        widgets = {
            'socio': forms.Select(attrs={'class': 'form-select select2-socio'}),
            'medidor': forms.Select(attrs={'class': 'form-select'}),
            'periodo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'YYYY-MM'
            }),
            'lectura_anterior': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.00',
                'placeholder': '0.00'
            }),
            'lectura_actual': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.00',
                'placeholder': '0.00'
            }),
            'importe_documentado': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.50',
                'min': '0.00',
                'placeholder': '0.00 (opcional)'
            }),
            'referencia_foja': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Libro 2, Foja 14, Fila 5'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Detalles sobre tachaduras, enmiendas o datos dudosos'
            })
        }


class ObservarTranscripcionForm(forms.Form):
    """Formulario para registrar una observación sobre un registro histórico."""
    motivo = forms.CharField(
        min_length=5,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Detalle la discrepancia o duda detectada en el registro.'
        }),
        label='Motivo de la Observación',
        help_text='Mínimo 5 caracteres obligatorios.'
    )


class RechazarTranscripcionForm(forms.Form):
    """Formulario para descartar formalmente un registro histórico sin respaldo."""
    motivo = forms.CharField(
        min_length=10,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Explique la causal insalvable por la que este registro no puede incorporarse al sistema.'
        }),
        label='Motivo Justificado de Rechazo',
        help_text='Mínimo 10 caracteres obligatorios.'
    )


class RegularizarDeudaForm(forms.Form):
    """Formulario para autorizar la incorporación de la deuda histórica a la cuenta corriente del socio."""
    motivo_respaldo = forms.CharField(
        min_length=10,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Documento, acta de asamblea o resolución del comité que respalda la exigibilidad de la deuda.'
        }),
        label='Documento o Justificación de Respaldo',
        help_text='Mínimo 10 caracteres obligatorios conforme a la regla R-DOM-19.'
    )

