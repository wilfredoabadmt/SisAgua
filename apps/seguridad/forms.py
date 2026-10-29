from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import Usuario

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none',
            'placeholder': 'Nombre de usuario',
            'autocomplete': 'username',
            'required': 'required'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none',
            'placeholder': 'Contraseña',
            'autocomplete': 'current-password',
            'required': 'required'
        })
    )


class CambiarClaveForm(forms.Form):
    password_actual = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Contraseña actual (solo si no es primer ingreso)'
        })
    )
    password_nuevo = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Nueva contraseña (mínimo 8 caracteres)'
        })
    )
    password_confirmar = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Confirmar nueva contraseña'
        })
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        # Si el usuario NO requiere cambio forzado, se exige ingresar la contraseña actual
        if not getattr(self.user, 'requiere_cambio_clave', False):
            self.fields['password_actual'].required = True

    def clean_password_actual(self):
        password_actual = self.cleaned_data.get('password_actual')
        if not getattr(self.user, 'requiere_cambio_clave', False):
            if not self.user.check_password(password_actual):
                raise ValidationError("La contraseña actual no es correcta.")
        return password_actual

    def clean_password_nuevo(self):
        nuevo = self.cleaned_data.get('password_nuevo')
        if not nuevo:
            return nuevo

        if len(nuevo) < 8:
            raise ValidationError("La nueva contraseña debe tener al menos 8 caracteres.")

        if not any(char.isdigit() for char in nuevo):
            raise ValidationError("La contraseña debe incluir al menos un número.")

        if not any(char.isalpha() for char in nuevo):
            raise ValidationError("La contraseña debe incluir al menos una letra.")

        # Prohibición de CI como contraseña (Principio P7)
        if self.user.ci_numero and (nuevo.strip() == self.user.ci_numero.strip()):
            raise ValidationError("Por seguridad, la contraseña no puede ser igual a su número de carnet de identidad.")

        # Prohibición de Username como contraseña
        if nuevo.lower().strip() == self.user.username.lower().strip():
            raise ValidationError("La contraseña no puede coincidir con su nombre de usuario.")

        return nuevo

    def clean(self):
        cleaned_data = super().clean()
        nuevo = cleaned_data.get('password_nuevo')
        confirmar = cleaned_data.get('password_confirmar')

        if nuevo and confirmar and nuevo != confirmar:
            self.add_error('password_confirmar', "Las contraseñas no coinciden.")

        return cleaned_data


class UsuarioCrearForm(forms.ModelForm):
    """Formulario administrativo para dar de alta a nuevo personal (US5)."""
    class Meta:
        model = Usuario
        fields = [
            'nombres', 'apellido_paterno', 'apellido_materno', 
            'ci_numero', 'ci_expedido', 'username', 'email', 'telefono', 'rol'
        ]
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'required': 'required'}),
            'apellido_paterno': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'required': 'required'}),
            'apellido_materno': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'ci_numero': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'required': 'required'}),
            'ci_expedido': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'username': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg', 'placeholder': 'Dejar en blanco para autogenerar'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'telefono': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'rol': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].required = False


class PerfilForm(forms.ModelForm):
    """Formulario de autoservicio para actualizar datos permitidos (US6)."""
    class Meta:
        model = Usuario
        fields = ['telefono', 'email', 'foto_perfil']
        widgets = {
            'telefono': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg'}),
        }

    def clean_foto_perfil(self):
        foto = self.cleaned_data.get('foto_perfil')
        if foto and hasattr(foto, 'size'):
            if foto.size > 2 * 1024 * 1024:
                raise ValidationError("La foto de perfil no puede superar los 2 MB.")
        return foto

