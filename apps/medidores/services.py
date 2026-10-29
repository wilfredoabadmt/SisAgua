from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Medidor, AsignacionMedidor, EstadoMedidor
from apps.socios.models import Socio
from apps.core.services import registrar_auditoria


def generar_codigo_medidor():
    """
    Genera el siguiente código correlativo de medidor en formato MED-XXXX.
    """
    ultimo = Medidor.objects.order_by('-id').first()
    if not ultimo or not ultimo.id:
        return "MED-0001"
    nuevo_id = ultimo.id + 1
    return f"MED-{nuevo_id:04d}"


def asignar_medidor(
    medidor: Medidor,
    socio: Socio,
    lectura_instalacion: Decimal,
    fecha_asignacion=None,
    usuario=None,
    ip_origen="127.0.0.1"
) -> AsignacionMedidor:
    """
    Asigna exclusivamente un medidor físico a un socio titular (R-DOM-03).
    Un medidor físico solo puede estar asignado a un socio activo a la vez.
    """
    if fecha_asignacion is None:
        fecha_asignacion = timezone.now().date()

    if lectura_instalacion < Decimal('0.00'):
        raise ValidationError("La lectura de instalación no puede ser negativa.")

    with transaction.atomic():
        # Regla R-DOM-03: Exclusividad de asignación activa
        if AsignacionMedidor.objects.filter(medidor=medidor, activo=True).exists():
            raise ValidationError(
                f"El medidor {medidor.codigo} ya se encuentra asignado a una conexión activa. "
                "No se permite asignación concurrente (Regla R-DOM-03)."
            )

        if medidor.estado not in [EstadoMedidor.DISPONIBLE, EstadoMedidor.MANTENIMIENTO]:
            raise ValidationError(
                f"El medidor {medidor.codigo} no está disponible para asignación. "
                f"Estado actual: {medidor.get_estado_display()}."
            )

        asignacion = AsignacionMedidor.objects.create(
            medidor=medidor,
            socio=socio,
            fecha_asignacion=fecha_asignacion,
            lectura_instalacion=lectura_instalacion,
            activo=True
        )

        medidor.estado = EstadoMedidor.INSTALADO
        medidor.save(update_fields=['estado', 'updated_at'])

        registrar_auditoria(
            modulo="MEDIDORES",
            accion="MODIFICAR",
            resultado="EXITO",
            usuario=usuario,
            entidad_afectada="AsignacionMedidor",
            registro_id=str(asignacion.id),
            detalle={
                "medidor": medidor.codigo,
                "serie": medidor.numero_serie,
                "socio": socio.codigo,
                "socio_nombre": socio.nombre_completo,
                "lectura_instalacion": str(lectura_instalacion),
                "accion_detalle": "Asignación exclusiva de medidor a socio"
            },
            ip_origen=ip_origen
        )

        return asignacion


def desasignar_medidor(
    asignacion: AsignacionMedidor,
    lectura_retiro: Decimal,
    fecha_retiro=None,
    motivo_retiro: str = "",
    nuevo_estado: str = EstadoMedidor.MANTENIMIENTO,
    usuario=None,
    ip_origen="127.0.0.1"
) -> AsignacionMedidor:
    """
    Desasigna o retira un medidor registrando obligatoriamente la lectura final de retiro (R-DOM-04).
    Conserva la trazabilidad histórica de lecturas previas.
    """
    if fecha_retiro is None:
        fecha_retiro = timezone.now().date()

    if lectura_retiro < asignacion.lectura_instalacion:
        raise ValidationError(
            f"La lectura de retiro ({lectura_retiro} m³) no puede ser inferior a la de instalación "
            f"({asignacion.lectura_instalacion} m³). Regla R-DOM-04."
        )

    with transaction.atomic():
        asignacion.activo = False
        asignacion.fecha_retiro = fecha_retiro
        asignacion.lectura_retiro = lectura_retiro
        asignacion.motivo_retiro = motivo_retiro
        asignacion.save(update_fields=['activo', 'fecha_retiro', 'lectura_retiro', 'motivo_retiro', 'updated_at'])

        medidor = asignacion.medidor
        medidor.estado = nuevo_estado if nuevo_estado in EstadoMedidor.values else EstadoMedidor.DISPONIBLE
        medidor.save(update_fields=['estado', 'updated_at'])

        registrar_auditoria(
            modulo="MEDIDORES",
            accion="MODIFICAR",
            resultado="EXITO",
            usuario=usuario,
            entidad_afectada="AsignacionMedidor",
            registro_id=str(asignacion.id),
            detalle={
                "medidor": medidor.codigo,
                "socio": asignacion.socio.codigo,
                "lectura_instalacion": str(asignacion.lectura_instalacion),
                "lectura_retiro": str(lectura_retiro),
                "motivo": motivo_retiro,
                "nuevo_estado_medidor": medidor.estado,
                "accion_detalle": "Retiro / sustitución de medidor con lectura final"
            },
            ip_origen=ip_origen
        )

        return asignacion

