from django.db import models
from django.conf import settings

class BaseAuditableModel(models.Model):
    """
    Modelo base abstracto que garantiza el cumplimiento de los Principios:
    - P5: Conservación Histórica (borrado lógico mediante bandera 'activo')
    - P6: Auditoría y trazabilidad temporal
    """
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el registro está operativo. Los borrados son siempre lógicos."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación",
        help_text="Marca temporal inmutable de registro en UTC."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Modificación",
        help_text="Marca temporal de última modificación en UTC."
    )

    class Meta:
        abstract = True


class BitacoraAuditoria(models.Model):
    """
    Bitacora de Auditoría inmutable (Append-Only) para cumplimiento del Principio P6.
    Registra operaciones relevantes sin incluir secretos, contraseñas ni tokens.
    """
    RESULTADO_CHOICES = [
        ('EXITO', 'Éxito'),
        ('FALLO', 'Fallo'),
        ('ADVERTENCIA', 'Advertencia'),
    ]

    fecha_hora_utc = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Fecha y Hora (UTC)"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auditorias",
        verbose_name="Usuario Responsable"
    )
    ip_origen = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP de Origen"
    )
    modulo = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="Módulo Afectado"
    )
    accion = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="Acción Realizada"
    )
    resultado = models.CharField(
        max_length=20,
        choices=RESULTADO_CHOICES,
        default='EXITO',
        verbose_name="Resultado"
    )
    entidad_afectada = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Entidad Afectada"
    )
    registro_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="ID de Registro Afectado"
    )
    detalle_json = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Detalle de Cambios (JSON limpio)"
    )

    class Meta:
        db_table = "bitacora_auditoria"
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Bitácora de Auditoría"
        ordering = ["-fecha_hora_utc"]
        indexes = [
            models.Index(fields=["fecha_hora_utc", "modulo"]),
            models.Index(fields=["usuario", "fecha_hora_utc"]),
        ]

    def __str__(self):
        usr = self.usuario.username if self.usuario else "Sistema/Anónimo"
        return f"[{self.fecha_hora_utc:%Y-%m-%d %H:%M:%S}] {usr} -> {self.modulo}:{self.accion} ({self.resultado})"

