from django.db import models
from apps.core.models import BaseAuditableModel
from apps.seguridad.models import Permiso

class Institucion(BaseAuditableModel):
    """
    Parametrización Institucional de la Entidad Prestadora de Agua Potable (P9).
    Patrón Singleton: Solo existe una instancia activa que representa a la organización.
    """
    nombre = models.CharField(
        max_length=150,
        default="Comité de Agua Potable y Saneamiento",
        verbose_name="Nombre de la Organización"
    )
    logo = models.ImageField(
        upload_to="institucion/logos/",
        null=True,
        blank=True,
        verbose_name="Logotipo Oficial"
    )
    direccion = models.TextField(
        blank=True,
        verbose_name="Dirección o Ubicación de Sede"
    )
    telefono = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Teléfono o Celular de Contacto"
    )
    correo = models.EmailField(
        max_length=100,
        blank=True,
        verbose_name="Correo Electrónico Institucional"
    )
    nit_personeria = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="NIT o Personería Jurídica"
    )
    moneda = models.CharField(
        max_length=10,
        default="Bs",
        verbose_name="Moneda de Operación",
        help_text="Bolivianos (Bs) conforme al mandato constitucional."
    )
    texto_recibo = models.TextField(
        blank=True,
        default="El agua es vida, cuídela. Recibo oficial de cobranza emitido conforme a estatuto comunal.",
        verbose_name="Leyenda para Recibos y Reportes"
    )
    dia_facturacion = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Día Base de Facturación Mensual"
    )
    dia_vencimiento_default = models.PositiveSmallIntegerField(
        default=15,
        verbose_name="Día Fijo de Vencimiento de Obligaciones"
    )

    class Meta:
        db_table = "configuracion_institucion"
        verbose_name = "Configuración Institucional"
        verbose_name_plural = "Configuración Institucional"

    @classmethod
    def get_solo(cls):
        """Devuelve o crea la única instancia institucional del sistema."""
        obj, _ = cls.objects.get_or_create(id=1)
        return obj

    def __str__(self):
        return self.nombre


class Menu(BaseAuditableModel):
    """
    Árbol dinámico de menús de navegación filtrado por roles y permisos (P12).
    """
    titulo = models.CharField(max_length=100, verbose_name="Título del Menú")
    ruta = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Ruta o URL Name",
        help_text="URL name de Django (ej. 'seguridad:usuarios_list') o ruta relativa."
    )
    icono = models.CharField(
        max_length=50,
        blank=True,
        default="folder",
        verbose_name="Nombre de Icono (Heroicons/Lucide)"
    )
    orden = models.PositiveSmallIntegerField(default=0, verbose_name="Orden de Presentación")
    padre = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="submenus",
        verbose_name="Menú Padre"
    )
    permiso_requerido = models.ForeignKey(
        Permiso,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="menus",
        verbose_name="Permiso Requerido para Visualización"
    )

    class Meta:
        db_table = "configuracion_menu"
        verbose_name = "Opción de Menú"
        verbose_name_plural = "Administración de Menús"
        ordering = ["orden", "titulo"]

    def __str__(self):
        if self.padre:
            return f"{self.padre.titulo} > {self.titulo}"
        return self.titulo

