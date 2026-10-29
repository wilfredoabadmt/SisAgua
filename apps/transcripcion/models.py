from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import BaseAuditableModel


class EstadoLote(models.TextChoices):
    ABIERTO = 'ABIERTO', 'Abierto / En Transcripción'
    EN_REVISION = 'EN_REVISION', 'En Revisión y Validación'
    CERRADO = 'CERRADO', 'Cerrado / Concluido'


class LoteTranscripcion(BaseAuditableModel):
    """
    Agrupa los registros históricos procedentes de una misma fuente documental física
    (cuaderno, empadronamiento de campo, planilla de Excel o formulario de empadronamiento).
    Sección 8 de la fuente funcional.
    """
    codigo = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        verbose_name="Código del Lote / Planilla",
        help_text="Identificador único (ej. LOT-2024-01, CUADERNO-TOMO-2)."
    )
    nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre / Descripción del Lote",
        help_text="Ej. Planilla Histórica 2024 - Sector Norte"
    )
    periodo_predeterminado = models.CharField(
        max_length=30,
        blank=True,
        default='',
        verbose_name="Periodo Predeterminado (YYYY-MM)",
        help_text="Periodo sugerido para acelerar la digitación de registros."
    )
    fuente_documental = models.CharField(
        max_length=200,
        verbose_name="Fuente Documental Física",
        help_text="Ej. Cuaderno de campo manuscrito tomo 1, Planilla empastada 2024."
    )
    total_estimado = models.PositiveIntegerField(
        default=0,
        verbose_name="Total Estimado de Registros",
        help_text="Meta de filas para calcular el avance porcentual de digitación."
    )
    responsable = models.ForeignKey(
        'seguridad.Usuario',
        on_delete=models.PROTECT,
        related_name='lotes_transcripcion',
        verbose_name="Responsable de la Migración"
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoLote.choices,
        default=EstadoLote.ABIERTO,
        db_index=True,
        verbose_name="Estado del Lote"
    )
    observaciones = models.TextField(
        blank=True,
        default='',
        verbose_name="Observaciones"
    )

    class Meta:
        verbose_name = "Lote de Transcripción"
        verbose_name_plural = "Lotes de Transcripción"
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f"{self.codigo} - {self.nombre} ({self.get_estado_display()})"

    def clean(self):
        if self.codigo:
            self.codigo = self.codigo.strip().upper()
        if self.nombre:
            self.nombre = self.nombre.strip()

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "No se permite eliminar físicamente un lote de transcripción (Principio P5 / Conservación Histórica)."
        )


class EstadoTranscripcion(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    TRANSCRITO = 'TRANSCRITO', 'Transcrito'
    OBSERVADO = 'OBSERVADO', 'Observado'
    VALIDADO = 'VALIDADO', 'Validado'
    MIGRADO = 'MIGRADO', 'Migrado'
    RECHAZADO = 'RECHAZADO', 'Rechazado'


class TranscripcionLectura(BaseAuditableModel):
    """
    Fila individual digitada a partir de planillas, cuadernos o archivos históricos.
    Sección 8.2 y Reglas R-DOM-18 y R-DOM-19.
    """
    codigo = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        verbose_name="Código del Registro Histórico"
    )
    lote = models.ForeignKey(
        LoteTranscripcion,
        on_delete=models.PROTECT,
        related_name='registros',
        verbose_name="Lote / Planilla de Origen"
    )
    socio = models.ForeignKey(
        'socios.Socio',
        on_delete=models.PROTECT,
        related_name='transcripciones',
        verbose_name="Socio Titular"
    )
    medidor = models.ForeignKey(
        'medidores.Medidor',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='transcripciones',
        verbose_name="Medidor Histórico"
    )
    periodo = models.CharField(
        max_length=30,
        db_index=True,
        verbose_name="Periodo Histórico (YYYY-MM)"
    )
    lectura_anterior = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Lectura Anterior (m³)"
    )
    lectura_actual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Lectura Actual (m³)"
    )
    consumo_calculado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Consumo Calculado (m³)"
    )
    tarifario_aplicado = models.ForeignKey(
        'servicios.Tarifario',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Tarifario Histórico Aplicado"
    )
    importe_calculado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Importe Calculado por Tarifa (Bs)"
    )
    importe_documentado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Importe Histórico Documentado (Bs)",
        help_text="Monto manuscrito registrado en el cuaderno físico."
    )
    referencia_foja = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name="Referencia Foja / Página",
        help_text="Ej. Libro 2, Foja 14, Fila 8."
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoTranscripcion.choices,
        default=EstadoTranscripcion.TRANSCRITO,
        db_index=True,
        verbose_name="Estado de Revisión"
    )
    transcrito_por = models.ForeignKey(
        'seguridad.Usuario',
        on_delete=models.PROTECT,
        related_name='transcripciones_realizadas',
        verbose_name="Transcrito Por"
    )
    fecha_transcripcion = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha de Transcripción"
    )
    validado_por = models.ForeignKey(
        'seguridad.Usuario',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='transcripciones_validadas',
        verbose_name="Validado Por"
    )
    fecha_validacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Validación"
    )
    observaciones = models.TextField(
        blank=True,
        default='',
        verbose_name="Observaciones"
    )
    motivo_observacion_rechazo = models.TextField(
        blank=True,
        default='',
        verbose_name="Motivo de Observación o Rechazo"
    )
    obligacion_regularizada = models.OneToOneField(
        'servicios.Obligacion',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='transcripcion_origen',
        verbose_name="Obligación Económica Regularizada (R-DOM-19)"
    )
    lectura_migrada = models.OneToOneField(
        'consumo.Lectura',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='transcripcion_origen',
        verbose_name="Lectura Migrada al Historial (R-DOM-18)"
    )

    class Meta:
        verbose_name = "Registro de Transcripción"
        verbose_name_plural = "Registros de Transcripción"
        ordering = ['-fecha_transcripcion', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['lote', 'socio', 'periodo'],
                name='unique_transcripcion_lote_socio_periodo'
            )
        ]

    def __str__(self):
        return f"{self.codigo} - {self.socio.codigo} ({self.periodo}): {self.get_estado_display()}"

    def clean(self):
        if self.lectura_anterior is not None and self.lectura_actual is not None:
            if self.lectura_actual >= self.lectura_anterior:
                self.consumo_calculado = self.lectura_actual - self.lectura_anterior
            else:
                # Monotonicidad histórica: si la actual es menor, advertencia/observación
                self.consumo_calculado = Decimal('0.00')
                if self.estado not in [EstadoTranscripcion.OBSERVADO, EstadoTranscripcion.RECHAZADO]:
                    self.estado = EstadoTranscripcion.OBSERVADO
                    if not self.motivo_observacion_rechazo:
                        self.motivo_observacion_rechazo = (
                            f"Lectura actual ({self.lectura_actual}) menor a anterior ({self.lectura_anterior}). "
                            "Requiere verificación con cuaderno físico."
                        )

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "No se permite eliminar físicamente un registro histórico transcrito. "
            "Utilice el estado RECHAZADO con justificación documentada (Principio P5)."
        )

