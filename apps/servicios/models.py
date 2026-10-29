from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import BaseAuditableModel


class TipoServicio(models.TextChoices):
    AGUA_POTABLE = 'AGUA_POTABLE', 'Agua Potable'
    MEMBRESIA = 'MEMBRESIA', 'Membresía / Afiliación'
    ALCANTARILLADO = 'ALCANTARILLADO', 'Alcantarillado'
    RECOJO_BASURA = 'RECOJO_BASURA', 'Recojo de Basura'
    OTRO = 'OTRO', 'Otro Servicio Autorizado'


class ModalidadCobro(models.TextChoices):
    LECTURA_VOLUMETRICA = 'LECTURA_VOLUMETRICA', 'Por Lectura (Volumétrica)'
    CUOTA_FIJA_MENSUAL = 'CUOTA_FIJA_MENSUAL', 'Cuota Fija Mensual'
    PAGO_UNICO_MEMBRESIA = 'PAGO_UNICO_MEMBRESIA', 'Pago Único (Membresía)'
    EVENTUAL = 'EVENTUAL', 'Eventual / A Demanda'


class Servicio(BaseAuditableModel):
    """
    Catálogo de servicios ofrecidos por la organización.
    Sección 5.1 de la fuente funcional.
    """
    codigo = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name="Código del Servicio",
        help_text="Identificador único (ej. AGUA, MEMBRESIA, BASURA)."
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre del Servicio"
    )
    descripcion = models.TextField(
        blank=True,
        default='',
        verbose_name="Descripción"
    )
    tipo_servicio = models.CharField(
        max_length=30,
        choices=TipoServicio.choices,
        default=TipoServicio.AGUA_POTABLE,
        verbose_name="Tipo de Servicio"
    )
    modalidad_cobro = models.CharField(
        max_length=30,
        choices=ModalidadCobro.choices,
        default=ModalidadCobro.LECTURA_VOLUMETRICA,
        verbose_name="Modalidad de Cobro"
    )

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.nombre} ({self.get_modalidad_cobro_display()})"

    def clean(self):
        if self.codigo:
            self.codigo = self.codigo.strip().upper()
        if self.nombre:
            self.nombre = self.nombre.strip()

    def delete(self, *args, **kwargs):
        if self.obligaciones.exists():
            raise ValidationError(
                "No se permite eliminar un servicio que tiene obligaciones económicas registradas. "
                "Utilice la desactivación lógica."
            )
        super().delete(*args, **kwargs)


class CategoriaTarifa(models.TextChoices):
    DOMESTICO = 'DOMESTICO', 'Doméstico / Residencial'
    COMERCIAL = 'COMERCIAL', 'Comercial'
    INDUSTRIAL = 'INDUSTRIAL', 'Industrial'
    SOCIAL = 'SOCIAL', 'Social / Institucional'


class Tarifario(BaseAuditableModel):
    """
    Esquema tarifario para un servicio con control de vigencias y bloqueo de retroactividad.
    Sección 5.3 de la fuente y Regla R-DOM-10.
    """
    nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre del Tarifario",
        help_text="Ej. Tarifario Doméstico Base 2026"
    )
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.PROTECT,
        related_name='tarifarios',
        verbose_name="Servicio"
    )
    categoria = models.CharField(
        max_length=30,
        choices=CategoriaTarifa.choices,
        default=CategoriaTarifa.DOMESTICO,
        verbose_name="Categoría de Usuario"
    )
    tarifa_basica = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Tarifa Básica (Bs)",
        help_text="Importe fijo de la tarifa básica."
    )
    consumo_minimo_m3 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Consumo Mínimo Incluido (m³)",
        help_text="Volumen de agua cubierto por la tarifa básica."
    )
    precio_adicional_m3 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Precio por m³ Excedente (Bs)",
        help_text="Precio unitario aplicable al volumen que excede el consumo mínimo."
    )
    fecha_vigencia_desde = models.DateField(
        db_index=True,
        verbose_name="Inicio de Vigencia",
        help_text="Fecha a partir de la cual rige este tarifario."
    )
    fecha_vigencia_hasta = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Fin de Vigencia",
        help_text="Dejar en blanco si este tarifario se encuentra actualmente vigente."
    )

    class Meta:
        verbose_name = "Tarifario"
        verbose_name_plural = "Tarifarios"
        ordering = ['-fecha_vigencia_desde', 'categoria']

    def __str__(self):
        vigencia = f"desde {self.fecha_vigencia_desde}"
        if self.fecha_vigencia_hasta:
            vigencia += f" hasta {self.fecha_vigencia_hasta}"
        else:
            vigencia += " (Vigente)"
        return f"{self.nombre} ({self.get_categoria_display()} - {vigencia})"

    def clean(self):
        if self.fecha_vigencia_hasta and self.fecha_vigencia_desde:
            if self.fecha_vigencia_hasta < self.fecha_vigencia_desde:
                raise ValidationError("La fecha de fin de vigencia no puede ser anterior a la de inicio.")
        if self.tarifa_basica < Decimal('0.00'):
            raise ValidationError("La tarifa básica no puede ser negativa.")
        if self.consumo_minimo_m3 < Decimal('0.00'):
            raise ValidationError("El consumo mínimo no puede ser negativo.")
        if self.precio_adicional_m3 < Decimal('0.00'):
            raise ValidationError("El precio por m³ no puede ser negativo.")


class TramoTarifario(models.Model):
    """
    Tramo escalonado opcional para tarifas por bloques de consumo.
    Permite modelar reglas específicas de la fuente (ej. tramo 0-10, 11-15, >15 m³).
    """
    tarifario = models.ForeignKey(
        Tarifario,
        on_delete=models.CASCADE,
        related_name='tramos',
        verbose_name="Tarifario"
    )
    orden = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Orden de Evaluación"
    )
    desde_m3 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Desde (m³)"
    )
    hasta_m3 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Hasta (m³)",
        help_text="Dejar en blanco si el tramo es abierto hacia el infinito."
    )
    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Precio Unitario / Importe (Bs)"
    )
    es_valor_fijo = models.BooleanField(
        default=False,
        verbose_name="¿Es Importe Total Fijo?",
        help_text="Si es verdadero, el importe no se multiplica por los m³ consumidos."
    )

    class Meta:
        verbose_name = "Tramo Tarifario"
        verbose_name_plural = "Tramos Tarifarios"
        ordering = ['tarifario', 'orden']

    def __str__(self):
        limite = f"{self.hasta_m3} m³" if self.hasta_m3 is not None else "en adelante"
        tipo = "Fijo" if self.es_valor_fijo else "x m³"
        return f"Tramo {self.orden}: {self.desde_m3} a {limite} (Bs {self.precio_unitario} {tipo})"


class EstadoObligacion(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    PAGADA = 'PAGADA', 'Pagada'
    ANULADA = 'ANULADA', 'Anulada'
    EXONERADA = 'EXONERADA', 'Exonerada'


class Obligacion(BaseAuditableModel):
    """
    Cuenta por cobrar devengada para un socio.
    Gobierna la membresía inicial (R-DOM-13) y futuras obligaciones de consumo (R-DOM-12).
    """
    socio = models.ForeignKey(
        'socios.Socio',
        on_delete=models.PROTECT,
        related_name='obligaciones',
        verbose_name="Socio Titular"
    )
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.PROTECT,
        related_name='obligaciones',
        verbose_name="Servicio"
    )
    periodo = models.CharField(
        max_length=30,
        db_index=True,
        verbose_name="Periodo / Referencia",
        help_text="YYYY-MM para consumo mensual, o MEMBRESIA para afiliación única."
    )
    concepto = models.CharField(
        max_length=200,
        verbose_name="Concepto Detallado"
    )
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Monto Total (Bs)"
    )
    saldo_pendiente = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Saldo Pendiente (Bs)"
    )
    fecha_emision = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de Emisión"
    )
    fecha_vencimiento = models.DateField(
        verbose_name="Fecha de Vencimiento"
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoObligacion.choices,
        default=EstadoObligacion.PENDIENTE,
        verbose_name="Estado de Obligación"
    )

    class Meta:
        verbose_name = "Obligación"
        verbose_name_plural = "Obligaciones"
        ordering = ['-fecha_emision', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['socio', 'servicio', 'periodo'],
                name='unique_obligacion_socio_servicio_periodo'
            )
        ]

    def __str__(self):
        return f"Obligación #{self.id} - {self.socio.codigo} - {self.concepto} (Bs {self.monto} - {self.get_estado_display()})"

    def clean(self):
        if self.monto < Decimal('0.00'):
            raise ValidationError("El monto de la obligación no puede ser negativo.")
        if self.saldo_pendiente < Decimal('0.00'):
            raise ValidationError("El saldo pendiente no puede ser negativo.")
        if self.saldo_pendiente > self.monto:
            raise ValidationError("El saldo pendiente no puede superar el monto total.")

    def delete(self, *args, **kwargs):
        if self.estado == EstadoObligacion.PAGADA:
            raise ValidationError(
                "No se permite eliminar una obligación pagada. (Principio P5 / Integridad Financiera)."
            )
        super().delete(*args, **kwargs)

