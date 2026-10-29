from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Socio, Zona, EstadoSocio
from apps.servicios.models import Servicio, Obligacion, EstadoObligacion, ModalidadCobro
from apps.configuracion.models import Institucion
from apps.core.services import registrar_auditoria


def generar_codigo_socio():
    """
    Genera el siguiente código correlativo de socio en formato SOC-XXXX.
    """
    ultimo = Socio.objects.order_by('-id').first()
    if not ultimo or not ultimo.id:
        return "SOC-0001"
    nuevo_id = ultimo.id + 1
    return f"SOC-{nuevo_id:04d}"


def registrar_socio(datos, usuario, ip_origen="127.0.0.1"):
    """
    Registra un nuevo socio y de forma ATÓMICA emite su obligación de membresía única (R-DOM-13).
    Cumple con el Principio P3 (Integridad Financiera) y P4 (Idempotencia).
    """
    with transaction.atomic():
        codigo = datos.get('codigo')
        if not codigo:
            codigo = generar_codigo_socio()
        else:
            codigo = codigo.strip().upper()

        ci = datos.get('ci', '').strip()
        ci_complemento = datos.get('ci_complemento', '').strip().upper()

        if Socio.objects.filter(ci=ci, ci_complemento=ci_complemento).exists():
            comp_txt = f"-{ci_complemento}" if ci_complemento else ""
            raise ValidationError(f"Ya existe un socio registrado con el CI {ci}{comp_txt}.")

        if Socio.objects.filter(codigo=codigo).exists():
            codigo = generar_codigo_socio()

        zona = datos.get('zona')
        if isinstance(zona, int):
            zona = Zona.objects.get(id=zona)

        socio = Socio.objects.create(
            codigo=codigo,
            ci=ci,
            ci_complemento=ci_complemento,
            nombres=datos.get('nombres', '').strip(),
            apellidos=datos.get('apellidos', '').strip(),
            zona=zona,
            direccion=datos.get('direccion', '').strip(),
            telefono=datos.get('telefono', '').strip(),
            email=datos.get('email', '').strip(),
            fecha_ingreso=datos.get('fecha_ingreso') or timezone.now().date(),
            estado=datos.get('estado', EstadoSocio.ACTIVO),
            observaciones=datos.get('observaciones', '').strip()
        )

        # Regla R-DOM-13: Emisión atómica de la Membresía de Afiliación
        servicio_membresia = Servicio.objects.filter(
            modalidad_cobro=ModalidadCobro.PAGO_UNICO_MEMBRESIA,
            activo=True
        ).first()

        institucion = Institucion.get_solo()
        monto_membresia = getattr(institucion, 'monto_membresia_defecto', Decimal('50.00')) if hasattr(institucion, 'monto_membresia_defecto') else Decimal('50.00')

        if servicio_membresia:
            # Calcular fecha de vencimiento según R-DOM-14 (día configurado o fin de mes)
            dia_venc = getattr(institucion, 'dia_vencimiento_default', 15) or 15
            hoy = timezone.now().date()
            try:
                fecha_venc = hoy.replace(day=dia_venc)
                if fecha_venc < hoy:
                    # Si el día ya pasó este mes, vence el mes siguiente
                    mes_siguiente = hoy.month + 1 if hoy.month < 12 else 1
                    anio_siguiente = hoy.year if hoy.month < 12 else hoy.year + 1
                    try:
                        fecha_venc = hoy.replace(year=anio_siguiente, month=mes_siguiente, day=dia_venc)
                    except ValueError:
                        # Si no existe ese día (ej. 31 en mes de 30 días)
                        import calendar
                        ultimo_dia = calendar.monthrange(anio_siguiente, mes_siguiente)[1]
                        fecha_venc = hoy.replace(year=anio_siguiente, month=mes_siguiente, day=ultimo_dia)
            except ValueError:
                import calendar
                ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]
                fecha_venc = hoy.replace(day=ultimo_dia)

            # Idempotencia: Verificar que no exista obligación previa de membresía
            if not Obligacion.objects.filter(socio=socio, servicio=servicio_membresia).exists():
                Obligacion.objects.create(
                    socio=socio,
                    servicio=servicio_membresia,
                    periodo=f"MEMB-{socio.codigo}",
                    concepto=f"Derecho de Membresía y Afiliación - {socio.nombre_completo}",
                    monto=monto_membresia,
                    saldo_pendiente=monto_membresia,
                    fecha_emision=hoy,
                    fecha_vencimiento=fecha_venc,
                    estado=EstadoObligacion.PENDIENTE
                )

        registrar_auditoria(
            modulo="SOCIOS",
            accion="CREAR",
            resultado="EXITO",
            usuario=usuario,
            entidad_afectada="Socio",
            registro_id=str(socio.id),
            detalle={
                "codigo": socio.codigo,
                "ci": socio.ci_formateado,
                "nombre_completo": socio.nombre_completo,
                "zona": socio.zona.nombre,
                "membresia_generada": bool(servicio_membresia),
                "motivo": "Alta oficial de nuevo socio en padrón"
            },
            ip_origen=ip_origen
        )

        return socio


def habilitar_acceso_portal(socio_id: int, usuario_operador=None, ip_origen="127.0.0.1"):
    """
    Habilita la cuenta de usuario para que el socio acceda de forma autónoma al portal.
    Sección 11 y 12.1 de la fuente funcional.
    """
    from apps.seguridad.models import Usuario, Rol, Permiso
    from apps.seguridad.services import sugerir_username, generar_clave_temporal

    socio = Socio.objects.get(pk=socio_id)
    if socio.usuario:
        raise ValidationError(f"El socio {socio.codigo} ya tiene una cuenta de portal habilitada ({socio.usuario.username}).")

    with transaction.atomic():
        primer_apellido = socio.apellidos.split()[0] if socio.apellidos else "Socio"
        username = sugerir_username(socio.nombres, primer_apellido)
        clave_temporal = generar_clave_temporal(longitud=10)

        # Obtener o crear rol SOCIO
        rol_socio, _ = Rol.objects.get_or_create(
            codigo="SOCIO",
            defaults={"nombre": "Socio Comunitario", "es_sistema": True, "activo": True}
        )
        permiso_portal, _ = Permiso.objects.get_or_create(
            modulo="PORTAL",
            accion="VER",
            defaults={"descripcion": "Acceso al portal individual de socio"}
        )
        rol_socio.permisos.add(permiso_portal)

        # Crear cuenta de usuario con contraseña temporal obligatoria
        user = Usuario.objects.create_user(
            username=username,
            password=clave_temporal,
            nombres=socio.nombres,
            apellido_paterno=primer_apellido,
            ci_numero=socio.ci,
            email=socio.email,
            telefono=socio.telefono,
            rol=rol_socio,
            requiere_cambio_clave=True
        )

        socio.usuario = user
        socio.save(update_fields=['usuario'])

        registrar_auditoria(
            modulo="PORTAL",
            accion="HABILITAR_ACCESO",
            resultado="EXITO",
            usuario=usuario_operador,
            entidad_afectada="Usuario",
            registro_id=str(user.id),
            detalle={
                "socio_id": socio.id,
                "codigo_socio": socio.codigo,
                "username_generado": username,
                "motivo": "Habilitación oficial de credenciales para portal de socio"
            },
            ip_origen=ip_origen
        )

    return user, clave_temporal

