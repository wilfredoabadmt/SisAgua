from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import BaseAuditableModel


class EstadoLectura(models.TextChoices):
    VALIDADA = 'VALIDADA', 'Validada'
    OBSERVADA = 'OBSERVADA', 'Observada'
    CORREGIDA = 'CORREGIDA', 'Corregida'
    ANULADA = 'ANULADA', 'Anulada'


class Lectura(BaseAuditableModel):
    """
    Registro mensual de lectura de un medidor asignado a un socio titular.
    Sección 7.1 a 7.3 de la fuente funcional.
    Cumple con R-DOM-06 (Fórmula de Consumo), R-DOM-07 (Monotonicidad)
    y R-DOM-08 (Unicidad Definitiva de Lectura).
    """
    medidor = models.ForeignKey(
        'medidores.Medidor',
        on_delete=models.PROTECT,
        related_name='lecturas',
        verbose_name="Medidor de Agua"
    )
    socio = models.ForeignKey(
        'socios.Socio',
        on_delete=models.PROTECT,
        related_name='lecturas',
        verbose_name="Socio Titular"
    )
    periodo = models.CharField(
        max_length=7,
        db_index=True,
        verbose_name="Periodo Mensual",
        help_text="Formato canónico YYYY-MM (ej. 2026-10)."
    )
    lectura_anterior = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Lectura Anterior (m³)",
        help_text="Lectura de partida del periodo anterior o calibración inicial."
    )
    fecha_lectura_anterior = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Lectura Anterior"
    )
    lectura_actual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Lectura Actual (m³)",
        help_text="Lectura tomada en campo en el periodo presente."
    )
    fecha_lectura = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de Toma de Lectura"
    )
    consumo_m3 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Consumo Calculado (m³)"
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoLectura.choices,
        default=EstadoLectura.VALIDADA,
        verbose_name="Estado de la Lectura"
    )
    motivo_observacion = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name="Motivo de Observación / Corrección"
    )
    es_reinicio_contador = models.BooleanField(
        default=False,
        verbose_name="¿Es Reinicio de Contador (Rollover)?",
        help_text="Marcar si el medidor mecánico dio la vuelta a cero tras 99999."
    )
    observaciones = models.TextField(
        blank=True,
        default='',
        verbose_name="Observaciones de Campo"
    )
    lector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lecturas_tomadas',
        verbose_name="Operador / Lector"
    )
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lecturas_validadas',
        verbose_name="Supervisor Validador"
    )
    fecha_validacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha y Hora de Validación"
    )

    class Meta:
        verbose_name = "Lectura de Consumo"
        verbose_name_plural = "Lecturas de Consumo"
        ordering = ['-periodo', '-fecha_lectura', '-id']
        constraints = [
            # Regla R-DOM-08: Unicidad de lectura activa por medidor y periodo
            models.UniqueConstraint(
                fields=['medidor', 'periodo'],
                condition=models.Q(activo=True),
                name='unique_lectura_activa_por_medidor_periodo'
            )
        ]

    def __str__(self):
        return f"{self.periodo} | {self.medidor.codigo} - {self.socio.codigo} | Consumo: {self.consumo_m3} m³ ({self.get_estado_display()})"

    def clean(self):
        if self.lectura_actual is not None and self.lectura_actual < Decimal('0.00'):
            raise ValidationError("La lectura actual no puede ser un valor negativo.")

        if self.lectura_anterior is not None and self.lectura_actual is not None:
            # Regla R-DOM-07: Monotonicidad
            if not self.es_reinicio_contador and self.lectura_actual < self.lectura_anterior:
                self.estado = EstadoLectura.OBSERVADA
                self.motivo_observacion = (
                    f"Lectura actual ({self.lectura_actual} m³) es inferior a la lectura anterior "
                    f"({self.lectura_anterior} m³). Regla R-DOM-07."
                )
                self.consumo_m3 = Decimal('0.00')
            elif self.es_reinicio_contador:
                # Fórmula para contador de 5 cifras que dio la vuelta a cero
                self.consumo_m3 = (Decimal('100000.00') - self.lectura_anterior) + self.lectura_actual
                if self.estado == EstadoLectura.OBSERVADA:
                    self.estado = EstadoLectura.CORREGIDA
            else:
                self.consumo_m3 = self.lectura_actual - self.lectura_anterior
                if self.estado == EstadoLectura.OBSERVADA:
                    self.estado = EstadoLectura.VALIDADA

    def delete(self, *args, **kwargs):
        # Principio P5: Conservación Histórica y Cero Borrado Físico
        raise ValidationError(
            "No se permite eliminar físicamente lecturas registradas. "
            "Utilice la anulación lógica o corrección autorizada (Principio P5)."
        )
