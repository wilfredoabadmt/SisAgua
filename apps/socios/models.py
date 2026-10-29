from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import BaseAuditableModel


class Zona(BaseAuditableModel):
    """
    Representa una zona, sector o barrio dentro de la jurisdicción del comité/cooperativa.
    Sección 4.1 de la fuente funcional.
    """
    codigo = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name="Código de Zona",
        help_text="Identificador alfanumérico único (ej. ZON-01, CENTRO)."
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre de la Zona",
        help_text="Nombre oficial de la zona o sector."
    )
    descripcion = models.TextField(
        blank=True,
        default='',
        verbose_name="Descripción o Delimitación"
    )
    responsable = models.CharField(
        max_length=150,
        blank=True,
        default='',
        verbose_name="Responsable o Delegado",
        help_text="Nombre del responsable vecinal o técnico de sector."
    )
    observaciones = models.TextField(
        blank=True,
        default='',
        verbose_name="Observaciones"
    )

    class Meta:
        verbose_name = "Zona"
        verbose_name_plural = "Zonas"
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    def clean(self):
        if self.codigo:
            self.codigo = self.codigo.strip().upper()
        if self.nombre:
            self.nombre = self.nombre.strip()

    def delete(self, *args, **kwargs):
        # Principio P5: Conservación Histórica y Cero Borrado Físico
        if self.socios.exists():
            raise ValidationError(
                "No se permite eliminar físicamente una zona que tiene socios registrados. "
                "Utilice la desactivación lógica (Principio P5)."
            )
        super().delete(*args, **kwargs)


class EstadoSocio(models.TextChoices):
    ACTIVO = 'ACTIVO', 'Activo'
    INACTIVO = 'INACTIVO', 'Inactivo'
    SUSPENDIDO = 'SUSPENDIDO', 'Suspendido'
    RETIRADO = 'RETIRADO', 'Retirado'


class Socio(BaseAuditableModel):
    """
    Representa a un socio titular del servicio de agua potable.
    Secciones 6.1 a 6.7 de la fuente funcional.
    Cumple con R-DOM-01 (Identidad Única) y R-DOM-05 (Inmutabilidad de Estados Históricos).
    """
    codigo = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        verbose_name="Código de Socio",
        help_text="Identificador único correlativo (ej. SOC-0001)."
    )
    ci = models.CharField(
        max_length=20,
        db_index=True,
        verbose_name="Cédula de Identidad (CI)",
        help_text="Documento de identidad boliviano."
    )
    ci_complemento = models.CharField(
        max_length=10,
        blank=True,
        default='',
        verbose_name="Complemento de CI",
        help_text="Alfanumérico para desempate de homónimos (ej. 1A, LP)."
    )
    nombres = models.CharField(
        max_length=100,
        verbose_name="Nombres"
    )
    apellidos = models.CharField(
        max_length=100,
        verbose_name="Apellidos"
    )
    zona = models.ForeignKey(
        Zona,
        on_delete=models.PROTECT,
        related_name='socios',
        verbose_name="Zona o Sector"
    )
    direccion = models.CharField(
        max_length=255,
        verbose_name="Dirección / Predio",
        help_text="Ubicación física del inmueble o conexión."
    )
    telefono = models.CharField(
        max_length=30,
        blank=True,
        default='',
        verbose_name="Teléfono / Celular"
    )
    email = models.EmailField(
        blank=True,
        default='',
        verbose_name="Correo Electrónico"
    )
    fecha_ingreso = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de Afiliación",
        help_text="Fecha oficial de ingreso como socio."
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoSocio.choices,
        default=EstadoSocio.ACTIVO,
        verbose_name="Estado del Socio"
    )
    observaciones = models.TextField(
        blank=True,
        default='',
        verbose_name="Observaciones"
    )
    usuario = models.OneToOneField(
        'seguridad.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='perfil_socio',
        verbose_name="Cuenta de Usuario del Portal",
        help_text="Cuenta de acceso al portal individual de socio."
    )

    class Meta:
        verbose_name = "Socio"
        verbose_name_plural = "Socios"
        ordering = ['apellidos', 'nombres']
        constraints = [
            models.UniqueConstraint(
                fields=['ci', 'ci_complemento'],
                name='unique_socio_ci_complemento'
            )
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre_completo} ({self.ci_formateado})"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}".strip()

    @property
    def ci_formateado(self):
        if self.ci_complemento:
            return f"{self.ci}-{self.ci_complemento}"
        return self.ci

    def clean(self):
        if self.ci:
            self.ci = self.ci.strip()
        if self.ci_complemento:
            self.ci_complemento = self.ci_complemento.strip().upper()
        if self.nombres:
            self.nombres = self.nombres.strip()
        if self.apellidos:
            self.apellidos = self.apellidos.strip()
        if self.codigo:
            self.codigo = self.codigo.strip().upper()

    def delete(self, *args, **kwargs):
        # Principio P5: Cero Borrado Físico
        raise ValidationError(
            "No se permite eliminar físicamente un socio. Utilice el cambio de estado a Inactivo o Retirado (Principio P5)."
        )

