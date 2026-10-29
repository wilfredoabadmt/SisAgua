# Modelo de Datos: Fase 7 - Portal Individual de Socios (007-portal-individual-socios)

## 1. Actualización al Modelo `Socio` (`apps/socios/models.py`)

```python
class Socio(BaseAuditableModel):
    # ... campos existentes (codigo, ci, ci_complemento, nombres, apellidos, zona, direccion, etc.) ...
    
    usuario = models.OneToOneField(
        'seguridad.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='perfil_socio',
        verbose_name="Cuenta de Usuario del Portal",
        help_text="Credencial de acceso digital para consultas del socio."
    )
```

## 2. Formularios de Actualización de Datos de Contacto

```python
class ActualizarContactoForm(forms.ModelForm):
    class Meta:
        model = Socio
        fields = ['telefono', 'email']
        widgets = {
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 71234567'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
        }
```

## 3. Relación de Consultas del Portal
- Medidores: `AsignacionMedidor.objects.filter(socio=socio, activo=True)`
- Lecturas: `Lectura.objects.filter(socio=socio).order_by('-periodo')[:12]`
- Obligaciones: `Obligacion.objects.filter(socio=socio).order_by('-periodo')`
- Recibos: `Recibo.objects.filter(socio=socio, estado=EstadoRecibo.EMITIDO).order_by('-fecha_emision')`

