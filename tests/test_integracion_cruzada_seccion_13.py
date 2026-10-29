import os
import json
import hashlib
import pytest
from io import StringIO
from decimal import Decimal
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from apps.socios.models import Socio, Zona, EstadoSocio
from apps.medidores.models import Medidor, AsignacionMedidor
from apps.servicios.models import Servicio, TipoServicio, Obligacion, EstadoObligacion
from apps.consumo.models import Lectura
from apps.caja.models import CajaTurno, EstadoTurnoCaja, Recibo, EstadoRecibo, Pago, MetodoPago, DetalleRecibo
from apps.caja.services import iniciar_turno_caja, procesar_cobro
from apps.core.models import BitacoraAuditoria
from apps.core.services import sanitizar_detalle


@pytest.fixture
def datos_integridad(db, institucion, usuario_admin, usuario_cajero):
    zona = Zona.objects.create(codigo="Z-NORTE", nombre="Zona Norte")
    socio1 = Socio.objects.create(
        codigo="SOC-001", nombres="Juan", apellidos="Perez",
        ci="11223344", zona=zona, estado=EstadoSocio.ACTIVO
    )
    socio2 = Socio.objects.create(
        codigo="SOC-002", nombres="Maria", apellidos="Gomez",
        ci="22334455", zona=zona, estado=EstadoSocio.ACTIVO
    )

    m1 = Medidor.objects.create(codigo="MED-001", numero_serie="SER-001")
    AsignacionMedidor.objects.create(socio=socio1, medidor=m1, activo=True, lectura_instalacion=Decimal('0.00'))

    serv = Servicio.objects.create(codigo="AGUA", nombre="Consumo Agua", tipo_servicio=TipoServicio.AGUA_POTABLE)
    obl1 = Obligacion.objects.create(
        socio=socio1, servicio=serv, periodo="2026-10",
        monto=Decimal('35.00'), saldo_pendiente=Decimal('35.00'),
        fecha_vencimiento=timezone.now().date(), estado=EstadoObligacion.PENDIENTE
    )

    return {
        'zona': zona,
        'socio1': socio1,
        'socio2': socio2,
        'm1': m1,
        'serv': serv,
        'obl1': obl1,
        'admin': usuario_admin,
        'cajero': usuario_cajero
    }


def test_comando_verificar_integridad_sistema_ejecuta_y_certifica_ok(datos_integridad):
    """
    Verifica que el comando verificar_integridad_sistema audite la base de datos y reporte éxito total.
    """
    out = StringIO()
    call_command('verificar_integridad_sistema', stdout=out)
    output = out.getvalue()

    assert "[OK] R-INT-01" in output
    assert "[OK] R-INT-02" in output
    assert "[OK] R-INT-03" in output
    assert "[OK] R-INT-05" in output
    assert "[OK] R-INT-06" in output
    assert "[OK] Principio P6" in output
    assert "[CERTIFICACIÓN EXITOSA]" in output


def test_comando_backup_institucional_genera_archivo_y_manifiesto(datos_integridad, tmp_path):
    """
    Verifica que el comando backup_institucional genere el volcado de datos,
    el manifiesto con metadatos de auditoría y el checksum SHA-256 coincidente.
    """
    out = StringIO()
    call_command('backup_institucional', output_dir=str(tmp_path), stdout=out)

    archivos = os.listdir(tmp_path)
    backup_file = [a for a in archivos if a.startswith('backup_sisagua_') and a.endswith('.json')][0]
    manifest_file = [a for a in archivos if a.startswith('manifest_') and a.endswith('.json')][0]

    with open(os.path.join(tmp_path, backup_file), 'r', encoding='utf-8') as f:
        datos_raw = f.read()
    with open(os.path.join(tmp_path, manifest_file), 'r', encoding='utf-8') as f:
        manifest_data = json.load(f)

    # Verificar que el hash del archivo de respaldo coincide con el manifiesto
    sha256_calculado = hashlib.sha256(datos_raw.encode('utf-8')).hexdigest()
    assert manifest_data['sha256_checksum'] == sha256_calculado
    assert manifest_data['total_objetos_serializados'] > 0
    assert manifest_data['sistema'] == "SisAgua"


def test_regla_r_int_02_bloqueo_doble_asignacion_activa_medidor(datos_integridad):
    """
    Regla R-INT-02 / R-DOM-03: Exclusividad de asignación.
    Un medidor activo no puede asignarse a un segundo socio mientras su asignación anterior esté activa.
    """
    medidor = datos_integridad['m1']
    socio2 = datos_integridad['socio2']

    # Intentar asignar m1 (ya activo con socio1) a socio2
    with pytest.raises(IntegrityError):
        AsignacionMedidor.objects.create(
            socio=socio2,
            medidor=medidor,
            activo=True,
            lectura_instalacion=Decimal('10.00')
        )


def test_regla_r_int_06_prohibicion_doble_pago_obligacion(datos_integridad):
    """
    Regla R-INT-06 / Principio P4: Prohibición de cobro duplicado.
    Una obligación ya pagada no puede volver a ser cobrada en caja.
    """
    turno = iniciar_turno_caja(datos_integridad['cajero'], Decimal('50.00'))
    obl = datos_integridad['obl1']

    # Primer cobro exitoso
    recibo = procesar_cobro(
        cajero=datos_integridad['cajero'],
        turno=turno,
        socio=datos_integridad['socio1'],
        obligaciones_ids=[obl.id],
        metodo_pago=MetodoPago.EFECTIVO
    )
    assert recibo.estado == EstadoRecibo.EMITIDO

    obl.refresh_from_db()
    assert obl.estado == EstadoObligacion.PAGADA

    # Segundo intento de cobro debe ser rechazado por idempotencia / integridad
    with pytest.raises(ValidationError):
        procesar_cobro(
            cajero=datos_integridad['cajero'],
            turno=turno,
            socio=datos_integridad['socio1'],
            obligaciones_ids=[obl.id],
            metodo_pago=MetodoPago.EFECTIVO
        )


def test_regla_r_int_07_cero_borrado_fisico_en_entidades_clave(datos_integridad):
    """
    Principio P5: Cero Borrado Físico.
    La invocación de .delete() en Socio, Zona con socios, Recibo y CajaTurno es interceptada.
    """
    with pytest.raises(ValidationError):
        datos_integridad['socio1'].delete()

    with pytest.raises(ValidationError):
        datos_integridad['zona'].delete()


def test_principio_p6_sanitizacion_bitacora_cero_fuga_secretos():
    """
    Principio P6: Cero fuga de secretos en bitácora de auditoría.
    La función sanitizar_detalle redacta de forma recursiva claves, tokens y contraseñas.
    """
    datos_sucios = {
        'username': 'admin',
        'password': 'SuperPasswordSecret123!',
        'token': 'bearer_token_xyz',
        'detalles_anidados': {
            'password_nuevo': '1234',
            'monto': '50.00',
            'secret': 'mi_clave_privada'
        }
    }

    limpio = sanitizar_detalle(datos_sucios)

    # Las claves secretas deben haber sido redactadas
    assert limpio['password'] == "[REDACTADO_POR_SEGURIDAD]"
    assert limpio['token'] == "[REDACTADO_POR_SEGURIDAD]"
    assert limpio['detalles_anidados']['password_nuevo'] == "[REDACTADO_POR_SEGURIDAD]"
    assert limpio['detalles_anidados']['secret'] == "[REDACTADO_POR_SEGURIDAD]"

    # Los datos de negocio deben conservarse intactos
    assert limpio['username'] == 'admin'
    assert limpio['detalles_anidados']['monto'] == '50.00'
