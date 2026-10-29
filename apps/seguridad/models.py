from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from apps.core.models import BaseAuditableModel

class Permiso(models.Model):
    """
    Permisos atómicos por módulo y acción.
    """
    modulo = models.CharField(max_length=50, db_index=True, verbose_name="Módulo")
    accion = models.CharField(max_length=50, db_index=True, verbose_name="Acción")
    descripcion = models.CharField(max_length=150, blank=True, verbose_name="Descripción")

    class Meta:
        db_table = "seguridad_permiso"
        verbose_name = "Permiso"
        verbose_name_plural = "Permisos"
        unique_together = ("modulo", "accion")
        ordering = ["modulo", "accion"]

    def __str__(self):
        return f"{self.modulo}:{self.accion}"


class Rol(BaseAuditableModel):
    """
    Roles del sistema (Administrador, Cajero, Lector, Socio, Auditor, etc.)
    """
    codigo = models.CharField(max_length=50, unique=True, db_index=True, verbose_name="Código")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    es_sistema = models.BooleanField(
        default=False, 
        verbose_name="Es Rol del Sistema",
        help_text="Los roles del sistema son canónicos y no pueden eliminarse ni renombrarse."
    )
    permisos = models.ManyToManyField(
        Permiso,
        related_name="roles",
        blank=True,
        verbose_name="Permisos Asignados"
    )

    class Meta:
        db_table = "seguridad_rol"
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class UsuarioManager(BaseUserManager):
    """
    Manager personalizado para el modelo Usuario de SisAgua.
    """
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("El nombre de usuario es obligatorio.")
        
        email = extra_fields.get("email")
        if email:
            extra_fields["email"] = self.normalize_email(email)
            
        user = self.model(username=username, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("requiere_cambio_clave", False)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")

        return self.create_user(username, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin, BaseAuditableModel):
    """
    Modelo de Usuario institucional de SisAgua.
    Cumple con el Principio P7:
    - Prohibición de CI como clave permanente.
    - Bandera de forzado de cambio de clave inicial (requiere_cambio_clave).
    - Rate limiting y protección contra ataques de fuerza bruta.
    """
    EXPEDIDO_CHOICES = [
        ('LP', 'La Paz'),
        ('CB', 'Cochabamba'),
        ('SC', 'Santa Cruz'),
        ('OR', 'Oruro'),
        ('PT', 'Potosí'),
        ('TJ', 'Tarija'),
        ('CH', 'Chuquisaca'),
        ('BE', 'Beni'),
        ('PD', 'Pando'),
        ('EXT', 'Extranjero'),
    ]

    username = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="Nombre de Usuario"
    )
    nombres = models.CharField(max_length=100, verbose_name="Nombres")
    apellido_paterno = models.CharField(max_length=100, verbose_name="Apellido Paterno")
    apellido_materno = models.CharField(max_length=100, blank=True, verbose_name="Apellido Materno")
    ci_numero = models.CharField(max_length=30, blank=True, db_index=True, verbose_name="N° Carnet de Identidad")
    ci_expedido = models.CharField(max_length=10, choices=EXPEDIDO_CHOICES, blank=True, verbose_name="Expedido")
    
    email = models.EmailField(max_length=100, blank=True, verbose_name="Correo Electrónico")
    telefono = models.CharField(max_length=50, blank=True, verbose_name="Teléfono o Celular")
    foto_perfil = models.ImageField(upload_to="usuarios/fotos/", null=True, blank=True, verbose_name="Foto de Perfil")
    
    rol = models.ForeignKey(
        Rol,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="usuarios",
        verbose_name="Rol Asignado"
    )
    
    # Flags de Seguridad
    requiere_cambio_clave = models.BooleanField(
        default=True,
        verbose_name="Requiere Cambio de Contraseña",
        help_text="Si está activo, obliga a cambiar la clave en el próximo inicio de sesión."
    )
    intentos_fallidos = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Intentos Fallidos Consecutivos"
    )
    bloqueado_hasta = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Bloqueado Temporalmente Hasta"
    )
    
    is_staff = models.BooleanField(default=False, verbose_name="Acceso al Panel")

    objects = UsuarioManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["nombres", "apellido_paterno"]

    class Meta:
        db_table = "seguridad_usuario"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["apellido_paterno", "apellido_materno", "nombres"]

    @property
    def is_active(self):
        """Mapeo para compatibilidad con auth de Django."""
        return self.activo

    @is_active.setter
    def is_active(self, value):
        self.activo = bool(value)

    @property
    def nombre_completo(self):
        partes = [self.nombres, self.apellido_paterno]
        if self.apellido_materno:
            partes.append(self.apellido_materno)
        return " ".join(partes)

    def esta_bloqueado(self):
        """Verifica si la cuenta se encuentra bloqueada por fuerza bruta."""
        if self.bloqueado_hasta and self.bloqueado_hasta > timezone.now():
            return True
        return False

    def registrar_fallo_login(self):
        """Incrementa contador de fallos y bloquea por 15 minutos al 5to fallo."""
        self.intentos_fallidos += 1
        if self.intentos_fallidos >= 5:
            self.bloqueado_hasta = timezone.now() + timezone.timedelta(minutes=15)
        self.save(update_fields=["intentos_fallidos", "bloqueado_hasta"])

    def reiniciar_fallos_login(self):
        """Restablece contadores de login exitoso."""
        if self.intentos_fallidos > 0 or self.bloqueado_hasta:
            self.intentos_fallidos = 0
            self.bloqueado_hasta = None
            self.save(update_fields=["intentos_fallidos", "bloqueado_hasta"])

    def __str__(self):
        return f"{self.nombre_completo} ({self.username})"

