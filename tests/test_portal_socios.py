import pytest
from decimal import Decimal
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
from apps.seguridad.models import Rol, Permiso, Usuario
from apps.socios.models import Socio, Zona, EstadoSocio
from apps.socios.services import habilitar_acceso_portal
from apps.medidores.models import Medidor, AsignacionMedidor
from apps.servicios.models import Servicio, TipoServicio, Obligacion, EstadoObligacion
from apps.consumo.models import Lectura, EstadoLectura
from apps.caja.models import Recibo, EstadoRecibo, DetalleRecibo, CajaTurno, EstadoTurnoCaja, MetodoPago
from apps.core.models import BitacoraAuditoria


@pytest.fixture
def datos_portal(db, institucion, usuario_admin, usuario_cajero):
    zona = Zona.objects.create(codigo="Z-NORTE", nombre="Zona Norte")
    socio1 = Socio.objects.create(
        codigo="SOC-0001", nombres="Mario", apellidos="Lopez",
        ci="6677889", zona=zona, estado=EstadoSocio.ACTIVO,
        telefono="71234567", email="mario@test.com"
    )
    socio2 = Socio.objects.create(
        codigo="SOC-0002", nombres="Beatriz", apellidos="Quispe",
        ci="7788990", zona=zona, estado=EstadoSocio.ACTIVO
    )

    # Medidor asignado a Socio 1
    m1 = Medidor.objects.create(codigo="MED-101", numero_serie="SER-101")
    AsignacionMedidor.objects.create(socio=socio1, medidor=m1, activo=True, lectura_instalacion=Decimal('0.00'))

    # Lectura para Socio 1
    Lectura.objects.create(
        medidor=m1, socio=socio1, periodo="2026-10",
        lectura_anterior=Decimal('0.00'), lectura_actual=Decimal('15.00'),
        consumo_m3=Decimal('15.00'), estado=EstadoLectura.VALIDADA
    )

    # Obligación para Socio 1
    serv = Servicio.objects.create(codigo="AGUA", nombre="Consumo Agua", tipo_servicio=TipoServicio.AGUA_POTABLE)
    obl1 = Obligacion.objects.create(
        socio=socio1, servicio=serv, periodo="2026-10",
        monto=Decimal('30.00'), saldo_pendiente=Decimal('30.00'),
        fecha_vencimiento=timezone.now().date(), estado=EstadoObligacion.PENDIENTE
    )

    # Recibos emitidos: r1 para socio1, r2 para socio2
    turno = CajaTurno.objects.create(
        cajero=usuario_cajero, monto_apertura=Decimal('100.00'), estado=EstadoTurnoCaja.ABIERTA
    )
    r1 = Recibo.objects.create(
        numero_recibo="REC-2026-000101", socio=socio1, cajero=usuario_cajero, turno=turno,
        monto_total=Decimal('50.00'), monto_literal="Cincuenta 00/100 Bolivianos",
        codigo_verificacion="HASH101", metodo_pago=MetodoPago.EFECTIVO,
        estado=EstadoRecibo.EMITIDO
    )
    DetalleRecibo.objects.create(recibo=r1, obligacion=obl1, concepto="Consumo de Agua", subtotal=Decimal('50.00'))

    obl2 = Obligacion.objects.create(
        socio=socio2, servicio=serv, periodo="2026-10",
        monto=Decimal('40.00'), saldo_pendiente=Decimal('0.00'),
        fecha_vencimiento=timezone.now().date(), estado=EstadoObligacion.PAGADA
    )
    r2 = Recibo.objects.create(
        numero_recibo="REC-2026-000102", socio=socio2, cajero=usuario_cajero, turno=turno,
        monto_total=Decimal('40.00'), monto_literal="Cuarenta 00/100 Bolivianos",
        codigo_verificacion="HASH102", metodo_pago=MetodoPago.EFECTIVO,
        estado=EstadoRecibo.EMITIDO
    )
    DetalleRecibo.objects.create(recibo=r2, obligacion=obl2, concepto="Consumo de Agua", subtotal=Decimal('40.00'))

    # Habilitar cuenta de portal para Socio 1
    user_socio1, clave_socio1 = habilitar_acceso_portal(socio1.id, usuario_operador=usuario_admin)
    # Por comodidad en pruebas, desactivar flag temporal para no interceptar vistas
    user_socio1.requiere_cambio_clave = False
    user_socio1.save(update_fields=['requiere_cambio_clave'])

    # Habilitar cuenta de portal para Socio 2
    user_socio2, clave_socio2 = habilitar_acceso_portal(socio2.id, usuario_operador=usuario_admin)
    user_socio2.requiere_cambio_clave = False
    user_socio2.save(update_fields=['requiere_cambio_clave'])

    return {
        'socio1': socio1,
        'socio2': socio2,
        'user_socio1': user_socio1,
        'user_socio2': user_socio2,
        'r1': r1,
        'r2': r2,
        'admin': usuario_admin
    }


def test_habilitar_acceso_portal_servicio(db, institucion, usuario_admin):
    """
    Verifica que el servicio cree la cuenta con rol SOCIO, clave temporal y vínculo OneToOne.
    """
    zona = Zona.objects.create(codigo="Z-ESTE", nombre="Zona Este")
    socio = Socio.objects.create(
        codigo="SOC-9999", nombres="Carlos", apellidos="Condori",
        ci="8899001", zona=zona, estado=EstadoSocio.ACTIVO
    )

    user, clave = habilitar_acceso_portal(socio.id, usuario_operador=usuario_admin)
    assert user.username == "ccondori"
    assert user.rol.codigo == "SOCIO"
    assert user.requiere_cambio_clave is True
    assert len(clave) >= 8

    socio.refresh_from_db()
    assert socio.usuario == user

    # Segundo intento debe fallar impidiendo duplicación
    with pytest.raises(ValidationError):
        habilitar_acceso_portal(socio.id)


def test_socio_accede_a_su_portal_exitosamente(client, datos_portal):
    """
    Verifica que el socio autenticado pueda ver su dashboard, medidores, deudas y recibos (200 OK).
    """
    client.force_login(datos_portal['user_socio1'])

    rutas = [
        reverse('portal:dashboard'),
        reverse('portal:medidores'),
        reverse('portal:deudas'),
        reverse('portal:recibos'),
        reverse('portal:perfil'),
    ]

    for r in rutas:
        resp = client.get(r)
        assert resp.status_code == 200, f"Ruta {r} debió responder 200 para el socio autenticado."
        assert datos_portal['socio1'].codigo in resp.content.decode('utf-8')


def test_aislamiento_idor_estricto_recibo_propio_vs_ajeno(client, datos_portal):
    """
    Principio P7: Aislamiento estricto de identidad.
    El socio 1 puede ver su propio recibo r1, pero recibe 404 al intentar ver r2 del socio 2.
    """
    client.force_login(datos_portal['user_socio1'])

    # Acceso a su propio recibo
    resp_propio = client.get(reverse('portal:recibo_detalle', args=[datos_portal['r1'].id]))
    assert resp_propio.status_code == 200
    assert datos_portal['r1'].numero_recibo in resp_propio.content.decode('utf-8')

    # Intento de acceso a recibo de otro socio (IDOR)
    resp_ajeno = client.get(reverse('portal:recibo_detalle', args=[datos_portal['r2'].id]))
    assert resp_ajeno.status_code == 404


def test_proforma_informativa_portal_r_dom_09(client, datos_portal):
    """
    Verifica la visualización de la proforma informativa del periodo con la leyenda de no-recibo.
    """
    client.force_login(datos_portal['user_socio1'])

    resp = client.get(reverse('portal:proforma', args=['2026-10']))
    assert resp.status_code == 200
    contenido = resp.content.decode('utf-8')
    assert "PROFORMA INFORMATIVA" in contenido
    assert "NO TIENE VALOR DE RECIBO OFICIAL" in contenido
    assert "15" in contenido  # consumo m3


def test_socio_actualiza_sus_datos_de_contacto_con_auditoria(client, datos_portal):
    """
    Verifica que el socio pueda actualizar su teléfono y correo desde el portal,
    sincronizando su usuario y registrando auditoría.
    """
    client.force_login(datos_portal['user_socio1'])

    resp = client.post(reverse('portal:perfil'), {
        'telefono': '79998877',
        'email': 'nuevomario@ejemplo.com'
    })
    assert resp.status_code == 302

    datos_portal['socio1'].refresh_from_db()
    assert datos_portal['socio1'].telefono == '79998877'
    assert datos_portal['socio1'].email == 'nuevomario@ejemplo.com'

    datos_portal['user_socio1'].refresh_from_db()
    assert datos_portal['user_socio1'].telefono == '79998877'
    assert datos_portal['user_socio1'].email == 'nuevomario@ejemplo.com'

    # Verificar bitácora de auditoría
    bitacora = BitacoraAuditoria.objects.filter(
        modulo="PORTAL",
        accion="MODIFICAR_PERFIL"
    ).latest('id')
    assert bitacora.resultado == "EXITO"
    assert bitacora.usuario == datos_portal['user_socio1']


def test_usuario_sin_ficha_socio_bloqueado_en_portal(client, db, permisos_base):
    """
    Un usuario que tiene permiso PORTAL:VER pero no está vinculado a un Socio
    recibe 403 Forbidden.
    """
    rol_socio = Rol.objects.create(codigo="ROL_PORTAL_TEST", nombre="Rol Test")
    permiso_portal = Permiso.objects.get(modulo="PORTAL", accion="VER")
    rol_socio.permisos.add(permiso_portal)

    usuario_huerfano = Usuario.objects.create_user(
        username="huerfano",
        password="Password123!",
        nombres="Sin",
        apellido_paterno="Socio",
        rol=rol_socio,
        requiere_cambio_clave=False
    )

    client.force_login(usuario_huerfano)
    resp = client.get(reverse('portal:dashboard'))
    assert resp.status_code == 403
