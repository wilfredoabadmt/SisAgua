from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import BaseAuditableModel


class EstadoTurnoCaja(models.TextChoices):
    ABIERTA = 'ABIERTA', 'Abierta'
    CERRADA = 'CERRADA', 'Cerrada'


class MetodoPago(models.TextChoices):
    EFECTIVO = 'EFECTIVO', 'Efectivo'
    QR = 'QR', 'Pago QR'
    TRANSFERENCIA = 'TRANSFERENCIA', 'Transferencia Bancaria'


class EstadoRecibo(models.TextChoices):
    EMITIDO = 'EMITIDO', 'Emitido'
    ANULADO = 'ANULADO', 'Anulado'


class CajaTurno(BaseAuditableModel):
    """
    Control de turnos y sesiones de caja con custodia de efectivo y arqueo.
    Sección 9.5 de la fuente funcional.
    """
    cajero = models.ForeignKey(
        'seguridad.Usuario',
        on_delete=models.PROTECT,
        related_name='turnos_caja',
        verbose_name="Cajero Responsable"
    )
    fecha_apertura = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha y Hora de Apertura"
    )
    monto_apertura = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Monto de Apertura / Fondo de Cambio (Bs)"
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoTurnoCaja.choices,
        default=EstadoTurnoCaja.ABIERTA,
        db_index=True,
        verbose_name="Estado del Turno"
    )
    fecha_cierre = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha y Hora de Cierre"
    )
    total_efectivo_sistema = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Total Efectivo Registrado en Sistema (Bs)"
    )
    total_digital_sistema = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Total Digital (QR/Transf.) en Sistema (Bs)"
    )
    monto_declarado_efectivo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Monto Físico Declarado en Arqueo (Bs)"
    )
    diferencia_efectivo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Diferencia de Caja (Bs)",
        help_text="Declarado menos (Apertura + Cobros Efectivo)."
    )
    observaciones_cierre = models.TextField(
        blank=True,
        default='',
        verbose_name="Observaciones de Cierre / Justificación"
    )
    cerrado_por = models.ForeignKey(
        'seguridad.Usuario',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='turnos_cerrados',
        verbose_name="Cerrado Por"
    )

    class Meta:
        verbose_name = "Turno de Caja"
        verbose_name_plural = "Turnos de Caja"
        ordering = ['-fecha_apertura', '-id']

    def __str__(self):
        return f"Turno #{self.id} - {self.cajero.username} ({self.get_estado_display()}) - {self.fecha_apertura.strftime('%d/%m/%Y %H:%M')}"

    @property
    def efectivo_esperado(self):
        """Monto total de efectivo que debería existir físicamente en gaveta."""
        return self.monto_apertura + self.total_efectivo_sistema

    @property
    def total_recaudado_sistema(self):
        """Total cobrado en el turno sumando todos los métodos de pago."""
        return self.total_efectivo_sistema + self.total_digital_sistema

    def clean(self):
        if self.monto_apertura < Decimal('0.00'):
            raise ValidationError("El monto de apertura no puede ser negativo.")
        if self.estado == EstadoTurnoCaja.ABIERTA and getattr(self, 'cajero_id', None):
            # Validar que el cajero no tenga otro turno abierto
            otros_abiertos = CajaTurno.objects.filter(
                cajero_id=self.cajero_id,
                estado=EstadoTurnoCaja.ABIERTA
            ).exclude(pk=self.pk)
            if otros_abiertos.exists():
                raise ValidationError("El usuario ya tiene un turno de caja abierto.")

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "No se permite eliminar un turno de caja. Los registros de caja son inmutables (Principio P5)."
        )


class Recibo(models.Model):
    """
    Recibo Oficial de Cobranza emitido a un socio.
    Inalterable, numerado correlativamente y trazable.
    Sección 9.4 y Regla R-DOM-17.
    """
    numero_recibo = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        verbose_name="Número de Recibo Oficial"
    )
    socio = models.ForeignKey(
        'socios.Socio',
        on_delete=models.PROTECT,
        related_name='recibos',
        verbose_name="Socio Titular"
    )
    turno = models.ForeignKey(
        CajaTurno,
        on_delete=models.PROTECT,
        related_name='recibos',
        verbose_name="Turno de Caja"
    )
    cajero = models.ForeignKey(
        'seguridad.Usuario',
        on_delete=models.PROTECT,
        related_name='recibos_cobrados',
        verbose_name="Cajero Cobrador"
    )
    fecha_emision = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name="Fecha y Hora de Emisión"
    )
    metodo_pago = models.CharField(
        max_length=20,
        choices=MetodoPago.choices,
        default=MetodoPago.EFECTIVO,
        verbose_name="Forma de Pago"
    )
    monto_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Monto Total Pagado (Bs)"
    )
    monto_literal = models.CharField(
        max_length=255,
        verbose_name="Monto en Literal (Bolivianos)"
    )
    saldo_anterior = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Saldo Pendiente Anterior (Bs)"
    )
    saldo_posterior = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Saldo Pendiente Remanente (Bs)"
    )
    codigo_verificacion = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name="Código de Verificación / QR"
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoRecibo.choices,
        default=EstadoRecibo.EMITIDO,
        db_index=True,
        verbose_name="Estado del Recibo"
    )
    fecha_anulacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha y Hora de Anulación"
    )
    usuario_anulacion = models.ForeignKey(
        'seguridad.Usuario',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='recibos_anulados',
        verbose_name="Anulado Por"
    )
    motivo_anulacion = models.TextField(
        blank=True,
        default='',
        verbose_name="Motivo Justificado de Anulación"
    )

    class Meta:
        verbose_name = "Recibo Oficial"
        verbose_name_plural = "Recibos Oficiales"
        ordering = ['-fecha_emision', '-id']

    def __str__(self):
        return f"{self.numero_recibo} - {self.socio.codigo} - Bs {self.monto_total} ({self.get_estado_display()})"

    def clean(self):
        if self.monto_total <= Decimal('0.00'):
            raise ValidationError("El monto total del recibo debe ser mayor a cero.")
        if self.estado == EstadoRecibo.ANULADO and not self.motivo_anulacion.strip():
            raise ValidationError("Debe proporcionar un motivo documentado para anular el recibo.")

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "No se permite eliminar físicamente un recibo oficial. "
            "Utilice el procedimiento de anulación autorizada (Principio P5 / Regla R-DOM-17)."
        )


class DetalleRecibo(models.Model):
    """
    Desglose ítem por ítem de cada obligación saldada en el recibo.
    """
    recibo = models.ForeignKey(
        Recibo,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Recibo"
    )
    obligacion = models.ForeignKey(
        'servicios.Obligacion',
        on_delete=models.PROTECT,
        related_name='detalles_recibo',
        verbose_name="Obligación Cancelada"
    )
    concepto = models.CharField(
        max_length=200,
        verbose_name="Concepto"
    )
    periodo = models.CharField(
        max_length=30,
        verbose_name="Periodo"
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Subtotal (Bs)"
    )

    class Meta:
        verbose_name = "Detalle de Recibo"
        verbose_name_plural = "Detalles de Recibo"
        ordering = ['id']

    def __str__(self):
        return f"{self.recibo.numero_recibo} - {self.concepto} ({self.periodo}): Bs {self.subtotal}"


class Pago(models.Model):
    """
    Transacción financiera que respalda el ingreso de fondos al turno de caja.
    """
    turno = models.ForeignKey(
        CajaTurno,
        on_delete=models.PROTECT,
        related_name='pagos',
        verbose_name="Turno de Caja"
    )
    recibo = models.OneToOneField(
        Recibo,
        on_delete=models.PROTECT,
        related_name='pago',
        verbose_name="Recibo Asociado"
    )
    socio = models.ForeignKey(
        'socios.Socio',
        on_delete=models.PROTECT,
        related_name='pagos',
        verbose_name="Socio Pagador"
    )
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Monto del Pago (Bs)"
    )
    metodo_pago = models.CharField(
        max_length=20,
        choices=MetodoPago.choices,
        default=MetodoPago.EFECTIVO,
        verbose_name="Método de Pago"
    )
    referencia_transaccion = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name="Referencia Digital / Depósito / QR"
    )
    fecha_pago = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name="Fecha y Hora de Pago"
    )

    class Meta:
        verbose_name = "Pago Financiero"
        verbose_name_plural = "Pagos Financieros"
        ordering = ['-fecha_pago', '-id']

    def __str__(self):
        return f"Pago #{self.id} - {self.recibo.numero_recibo} - Bs {self.monto} ({self.get_metodo_pago_display()})"

    def clean(self):
        if self.monto <= Decimal('0.00'):
            raise ValidationError("El monto del pago debe ser mayor a cero.")

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "No se permite eliminar físicamente un registro de pago (Principio P5)."
        )
