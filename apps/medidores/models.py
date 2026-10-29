from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import BaseAuditableModel


class EstadoMedidor(models.TextChoices):
    DISPONIBLE = 'DISPONIBLE', 'Disponible'
    INSTALADO = 'INSTALADO', 'Instalado'
    MANTENIMIENTO = 'MANTENIMIENTO', 'En Mantenimiento'
    RETIRADO = 'RETIRADO', 'Retirado'
    DE_BAJA = 'DE_BAJA', 'De Baja'


class Medidor(BaseAuditableModel):
    """
    Inventario de medidores de agua físicos.
    Sección 5.2 de la fuente funcional.
    """
    codigo = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        verbose_name="Código Interno",
        help_text="Código asignado por el comité (ej. MED-0001)."
    )
    numero_serie = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="Número de Serie / Fábrica",
        help_text="Serie estampada en el dispositivo por el fabricante."
    )
    marca = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name="Marca"
    )
    modelo = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name="Modelo"
    )
    diametro = models.CharField(
        max_length=20,
        default='1/2"',
        verbose_name="Diámetro Nominal"
    )
    lectura_inicial = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Lectura Inicial de Calibración (m³)",
        help_text="Lectura de partida al ingresar el medidor a inventario."
    )
    ubicacion = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name="Ubicación Física / Referencia de Nicho"
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoMedidor.choices,
        default=EstadoMedidor.DISPONIBLE,
        verbose_name="Estado del Medidor"
    )
    observaciones = models.TextField(
        blank=True,
        default='',
        verbose_name="Observaciones"
    )

    class Meta:
        verbose_name = "Medidor"
        verbose_name_plural = "Medidores"
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} (Serie: {self.numero_serie}) - {self.get_estado_display()}"

    def clean(self):
        if self.codigo:
            self.codigo = self.codigo.strip().upper()
        if self.numero_serie:
            self.numero_serie = self.numero_serie.strip().upper()
        if self.lectura_inicial < Decimal('0.00'):
            raise ValidationError("La lectura inicial no puede ser negativa.")

    def delete(self, *args, **kwargs):
        if self.asignaciones.exists():
            raise ValidationError(
                "No se permite eliminar un medidor que tiene historial de asignaciones. "
                "Utilice el estado DE_BAJA o RETIRADO."
            )
        super().delete(*args, **kwargs)


class AsignacionMedidor(BaseAuditableModel):
    """
    Asignación histórica y vigente de un medidor a un socio titular.
    Cumple R-DOM-02 (Multi-medición por socio), R-DOM-03 (Exclusividad de Asignación)
    y R-DOM-04 (Trazabilidad de Sustitución y Lectura de Retiro).
    """
    medidor = models.ForeignKey(
        Medidor,
        on_delete=models.PROTECT,
        related_name='asignaciones',
        verbose_name="Medidor Físico"
    )
    socio = models.ForeignKey(
        'socios.Socio',
        on_delete=models.PROTECT,
        related_name='asignaciones_medidor',
        verbose_name="Socio Titular"
    )
    fecha_asignacion = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de Asignación / Instalación"
    )
    lectura_instalacion = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Lectura de Instalación (m³)",
        help_text="Lectura registrada en el momento exacto de la conexión al predio."
    )
    fecha_retiro = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Retiro / Sustitución"
    )
    lectura_retiro = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Lectura de Retiro (m³)",
        help_text="Lectura final acumulada al retirar el medidor de la conexión."
    )
    motivo_retiro = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name="Motivo de Retiro / Desasignación"
    )

    class Meta:
        verbose_name = "Asignación de Medidor"
        verbose_name_plural = "Asignaciones de Medidores"
        ordering = ['-fecha_asignacion', '-id']
        constraints = [
            # Regla R-DOM-03: Exclusividad de asignación activa a nivel base de datos
            models.UniqueConstraint(
                fields=['medidor'],
                condition=models.Q(activo=True),
                name='unique_asignacion_activa_por_medidor'
            )
        ]

    def __str__(self):
        estado = "Activa" if self.activo else f"Retirado el {self.fecha_retiro}"
        return f"{self.medidor.codigo} -> {self.socio.codigo} ({estado})"

    def clean(self):
        if self.lectura_instalacion < Decimal('0.00'):
            raise ValidationError("La lectura de instalación no puede ser negativa.")
        if self.lectura_retiro is not None:
            if self.lectura_retiro < self.lectura_instalacion:
                raise ValidationError(
                    f"La lectura de retiro ({self.lectura_retiro} m³) no puede ser inferior a la de instalación ({self.lectura_instalacion} m³)."
                )
        if not self.activo and not self.fecha_retiro:
            self.fecha_retiro = timezone.now().date()

