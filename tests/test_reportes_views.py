import pytest
from decimal import Decimal
from django.urls import reverse
from django.utils import timezone
from apps.seguridad.models import Rol, Permiso, Usuario
from apps.socios.models import Socio, Zona, EstadoSocio
from apps.servicios.models import Servicio, TipoServicio, Obligacion, EstadoObligacion
from apps.medidores.models import Medidor, AsignacionMedidor
from apps.caja.models import Recibo, EstadoRecibo, DetalleRecibo, CajaTurno, EstadoTurnoCaja, MetodoPago
from apps.core.models import BitacoraAuditoria


@pytest.fixture
def datos_reportes_views(db, institucion, usuario_admin, usuario_cajero):
    zona = Zona.objects.create(codigo="Z-NORTE", nombre="Zona Norte")
    socio = Socio.objects.create(
        codigo="SOC-001", nombres="Juan", apellidos="Perez",
        ci="1234567", zona=zona, estado=EstadoSocio.ACTIVO
    )
    m = Medidor.objects.create(codigo="MED-001", numero_serie="SERIE-001")
    AsignacionMedidor.objects.create(socio=socio, medidor=m, activo=True, lectura_instalacion=Decimal('0.00'))

    serv = Servicio.objects.create(codigo="AGUA", nombre="Consumo Agua", tipo_servicio=TipoServicio.AGUA_POTABLE)
    obl = Obligacion.objects.create(
        socio=socio, servicio=serv, periodo="2026-10",
        monto=Decimal('50.00'), saldo_pendiente=Decimal('50.00'),
        fecha_vencimiento=timezone.now().date(), estado=EstadoObligacion.PENDIENTE
    )

    turno = CajaTurno.objects.create(
        cajero=usuario_cajero, monto_apertura=Decimal('100.00'), estado=EstadoTurnoCaja.ABIERTA
    )
    recibo = Recibo.objects.create(
        numero_recibo="REC-2026-000001", socio=socio, cajero=usuario_cajero, turno=turno,
        monto_total=Decimal('50.00'), monto_literal="Cincuenta 00/100 Bolivianos",
        codigo_verificacion="HASH999", metodo_pago=MetodoPago.EFECTIVO,
        estado=EstadoRecibo.EMITIDO
    )
    DetalleRecibo.objects.create(recibo=recibo, obligacion=obl, concepto="Consumo Agua", subtotal=Decimal('50.00'))

    return {
        'zona': zona,
        'socio': socio,
        'usuario_admin': usuario_admin,
        'usuario_cajero': usuario_cajero
    }


def test_usuario_sin_permiso_reportes_recibe_403(client, datos_reportes_views):
    """
    Verifica que un usuario sin el permiso REPORTES:VER (e.g. cajero) reciba 403 Forbidden.
    Principio P7: Verificación en Servidor.
    """
    client.force_login(datos_reportes_views['usuario_cajero'])

    rutas = [
        reverse('reportes:dashboard'),
        reverse('reportes:deudores'),
        reverse('reportes:recaudacion'),
        reverse('reportes:consumo'),
        reverse('reportes:zonas'),
        reverse('reportes:membresias'),
        reverse('reportes:socio_estado_cuenta', args=[datos_reportes_views['socio'].id]),
    ]

    for ruta in rutas:
        resp = client.get(ruta)
        assert resp.status_code == 403, f"Ruta {ruta} debió devolver 403 Forbidden para usuario sin permiso."


def test_admin_con_permiso_accede_a_todos_los_reportes(client, datos_reportes_views):
    """
    Verifica que un usuario con permiso REPORTES:VER acceda exitosamente a las 7 vistas analíticas.
    """
    client.force_login(datos_reportes_views['usuario_admin'])

    rutas = [
        reverse('reportes:dashboard'),
        reverse('reportes:deudores'),
        reverse('reportes:recaudacion'),
        reverse('reportes:consumo'),
        reverse('reportes:zonas'),
        reverse('reportes:membresias'),
        reverse('reportes:socio_estado_cuenta', args=[datos_reportes_views['socio'].id]),
    ]

    for ruta in rutas:
        resp = client.get(ruta)
        assert resp.status_code == 200, f"Ruta {ruta} debió responder 200 OK para el administrador."


def test_exportacion_csv_con_permiso_genera_archivo_y_auditoria_p6(client, datos_reportes_views):
    """
    Verifica que la exportación con format=csv genere el archivo CSV y registre la auditoría correspondiente.
    """
    client.force_login(datos_reportes_views['usuario_admin'])

    url_csv = reverse('reportes:deudores') + '?format=csv'
    resp = client.get(url_csv)

    assert resp.status_code == 200
    assert 'text/csv' in resp['Content-Type']
    assert 'attachment;' in resp['Content-Disposition']
    assert 'reporte_deudores_' in resp['Content-Disposition']

    # Contenido del CSV debe incluir al socio
    contenido = resp.content.decode('utf-8')
    assert datos_reportes_views['socio'].codigo in contenido

    # Verificar que se registró auditoría de la exportación (Principio P6)
    bitacora = BitacoraAuditoria.objects.filter(
        modulo="REPORTES",
        accion="EXPORTAR"
    ).latest('id')
    assert bitacora.resultado == "EXITO"
    assert bitacora.usuario == datos_reportes_views['usuario_admin']


def test_exportacion_csv_bloqueada_sin_permiso_exportar(client, datos_reportes_views, db):
    """
    Verifica que un usuario que solo tiene REPORTES:VER pero NO tiene REPORTES:EXPORTAR
    sea bloqueado con 403 al intentar descargar el CSV.
    """
    # Crear un rol de solo lectura (sin exportar)
    rol_lector = Rol.objects.create(codigo="LECTOR_REPORTES", nombre="Solo Ver Reportes")
    permiso_ver = Permiso.objects.get(modulo="REPORTES", accion="VER")
    rol_lector.permisos.add(permiso_ver)

    usuario_solo_ver = Usuario.objects.create_user(
        username="solo_ver",
        password="Password123!",
        nombres="Ana",
        apellido_paterno="Lector",
        ci_numero="99887766",
        rol=rol_lector,
        requiere_cambio_clave=False
    )

    client.force_login(usuario_solo_ver)

    # Puede ver el reporte en HTML
    resp_html = client.get(reverse('reportes:deudores'))
    assert resp_html.status_code == 200

    # Intento de exportar CSV debe ser bloqueado con 403
    resp_csv = client.get(reverse('reportes:deudores') + '?format=csv')
    assert resp_csv.status_code == 403

