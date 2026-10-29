import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.seguridad.models import Usuario
from apps.socios.models import Socio, Zona
from apps.transcripcion.models import LoteTranscripcion, EstadoLote, TranscripcionLectura, EstadoTranscripcion
from apps.transcripcion.services import (
    crear_lote_transcripcion, transcribir_lectura,
    validar_transcripcion, observar_transcripcion,
    rechazar_transcripcion, calcular_metricas_lote
)
from apps.core.models import BitacoraAuditoria


@pytest.fixture
def zona_trx(db):
    return Zona.objects.create(codigo="ZON-TRX", nombre="Zona Transcripcion")


@pytest.fixture
def socio_trx(db, zona_trx):
    return Socio.objects.create(
        codigo="SOC-TRX-01",
        nombres="Roberto",
        apellidos="Gomez",
        ci="11002233",
        zona=zona_trx
    )


@pytest.fixture
def usuario_transcriptor(db, rol_administrador):
    return Usuario.objects.create_user(
        username="transcriptor1",
        password="Password123!",
        nombres="Juan",
        apellido_paterno="Digitador",
        ci_numero="66778899",
        rol=rol_administrador,
        requiere_cambio_clave=False
    )


@pytest.fixture
def lote_prueba(db, usuario_transcriptor):
    return crear_lote_transcripcion(
        codigo="LOT-2024-TEST",
        nombre="Planilla 2024 Test",
        fuente_documental="Cuaderno histórico empastado",
        responsable=usuario_transcriptor,
        total_estimado=20,
        ip_origen='127.0.0.1'
    )


@pytest.mark.django_db
def test_crear_lote_exitoso_y_auditoria(usuario_transcriptor):
    """Crea un lote documental y verifica auditoría P6."""
    lote = crear_lote_transcripcion(
        codigo="LOT-PRUEBA-01",
        nombre="Cuaderno 2023 - Sector Alto",
        fuente_documental="Cuaderno de actas y lecturas",
        responsable=usuario_transcriptor,
        total_estimado=30,
        ip_origen='10.0.0.1'
    )

    assert lote.id is not None
    assert lote.codigo == "LOT-PRUEBA-01"
    assert lote.estado == EstadoLote.ABIERTO
    assert lote.total_estimado == 30

    audit = BitacoraAuditoria.objects.filter(
        modulo='TRANSCRIPCION',
        accion='CREAR_LOTE',
        registro_id=str(lote.id)
    ).first()
    assert audit is not None
    assert audit.usuario == usuario_transcriptor


@pytest.mark.django_db
def test_transcribir_lectura_valida_calcula_consumo_p8(lote_prueba, socio_trx, usuario_transcriptor):
    """Captura de fila histórica, cálculo automático de consumo y registro de importe documentado (P8)."""
    registro = transcribir_lectura(
        lote=lote_prueba,
        socio=socio_trx,
        periodo="2024-05",
        usuario=usuario_transcriptor,
        lectura_anterior=Decimal('100.00'),
        lectura_actual=Decimal('125.00'),
        importe_documentado=Decimal('35.00'),
        referencia_foja="Libro 1, Foja 22, Fila 4",
        ip_origen='192.168.1.15'
    )

    assert registro.id is not None
    assert registro.codigo.startswith("TRX-")
    assert registro.consumo_calculado == Decimal('25.00')
    assert registro.importe_documentado == Decimal('35.00')
    assert registro.estado == EstadoTranscripcion.TRANSCRITO
    assert registro.referencia_foja == "Libro 1, Foja 22, Fila 4"

    audit = BitacoraAuditoria.objects.filter(
        modulo='TRANSCRIPCION',
        accion='TRANSCRIBIR_LECTURA',
        registro_id=str(registro.id)
    ).first()
    assert audit is not None


@pytest.mark.django_db
def test_transcribir_lectura_menor_dispara_observacion_automatica_r_dom_07(lote_prueba, socio_trx, usuario_transcriptor):
    """Monotonicidad histórica: si lectura actual < anterior, el registro se marca OBSERVADO."""
    registro = transcribir_lectura(
        lote=lote_prueba,
        socio=socio_trx,
        periodo="2024-06",
        usuario=usuario_transcriptor,
        lectura_anterior=Decimal('150.00'),
        lectura_actual=Decimal('140.00'),
        referencia_foja="Foja 30"
    )

    assert registro.estado == EstadoTranscripcion.OBSERVADO
    assert registro.consumo_calculado == Decimal('0.00')
    assert "menor a anterior" in registro.motivo_observacion_rechazo


@pytest.mark.django_db
def test_validar_transcripcion_por_supervisor_exitoso(lote_prueba, socio_trx, usuario_transcriptor, usuario_admin):
    """Validación formal de registro digitado por un supervisor."""
    registro = transcribir_lectura(
        lote=lote_prueba,
        socio=socio_trx,
        periodo="2024-07",
        usuario=usuario_transcriptor,
        lectura_anterior=Decimal('100.00'),
        lectura_actual=Decimal('115.00'),
        importe_documentado=Decimal('20.00')
    )

    reg_validado = validar_transcripcion(
        transcripcion=registro,
        supervisor=usuario_admin,
        observaciones="Cotejado conforme con cuaderno original.",
        ip_origen='10.0.0.9'
    )

    assert reg_validado.estado == EstadoTranscripcion.VALIDADO
    assert reg_validado.validado_por == usuario_admin
    assert reg_validado.fecha_validacion is not None

    audit = BitacoraAuditoria.objects.filter(
        modulo='TRANSCRIPCION',
        accion='VALIDAR_TRANSCRIPCION',
        registro_id=str(registro.id)
    ).first()
    assert audit is not None


@pytest.mark.django_db
def test_observar_y_rechazar_transcripcion_con_justificacion(lote_prueba, socio_trx, usuario_transcriptor, usuario_admin):
    """Observar y rechazar registros exige justificación documentada."""
    registro = transcribir_lectura(
        lote=lote_prueba,
        socio=socio_trx,
        periodo="2024-08",
        usuario=usuario_transcriptor,
        lectura_anterior=Decimal('100.00'),
        lectura_actual=Decimal('110.00')
    )

    # Observar
    reg_obs = observar_transcripcion(registro, usuario_transcriptor, "Falta firma en el cuaderno de campo")
    assert reg_obs.estado == EstadoTranscripcion.OBSERVADO
    assert "Falta firma" in reg_obs.motivo_observacion_rechazo

    # Rechazo sin motivo falla
    with pytest.raises(ValidationError, match="motivo documentado"):
        rechazar_transcripcion(reg_obs, usuario_admin, "error")

    # Rechazo formal con motivo documentado
    reg_rechazado = rechazar_transcripcion(
        reg_obs,
        usuario_admin,
        "Hoja arrancada e ilegible del cuaderno manuscrito; no se puede verificar."
    )
    assert reg_rechazado.estado == EstadoTranscripcion.RECHAZADO


@pytest.mark.django_db
def test_bloqueo_de_borrado_fisico_en_lote_y_transcripcion_p5(lote_prueba, socio_trx, usuario_transcriptor):
    """Principio P5: Prohibido DELETE físico en lotes y transcripciones."""
    registro = transcribir_lectura(
        lote=lote_prueba,
        socio=socio_trx,
        periodo="2024-09",
        usuario=usuario_transcriptor,
        lectura_anterior=Decimal('10.00'),
        lectura_actual=Decimal('20.00')
    )

    with pytest.raises(ValidationError, match="No se permite eliminar físicamente un registro histórico"):
        registro.delete()

    with pytest.raises(ValidationError, match="No se permite eliminar físicamente un lote"):
        lote_prueba.delete()


@pytest.mark.django_db
def test_calculo_metricas_avance_lote_seccion_8_6(lote_prueba, socio_trx, usuario_transcriptor, usuario_admin):
    """Verifica el cálculo de porcentajes y métricas de avance por etapa (Sección 8.6)."""
    # Crear 2 registros: 1 validado y 1 transcrito
    r1 = transcribir_lectura(
        lote=lote_prueba,
        socio=socio_trx,
        periodo="2024-01",
        usuario=usuario_transcriptor,
        lectura_anterior=Decimal('0'),
        lectura_actual=Decimal('10')
    )
    validar_transcripcion(r1, usuario_admin)

    s2 = Socio.objects.create(codigo="SOC-TRX-02", nombres="Ana", apellidos="Paz", ci="44556677", zona=socio_trx.zona)
    transcribir_lectura(
        lote=lote_prueba,
        socio=s2,
        periodo="2024-01",
        usuario=usuario_transcriptor,
        lectura_anterior=Decimal('0'),
        lectura_actual=Decimal('15')
    )

    metricas = calcular_metricas_lote(lote_prueba)
    assert metricas['total_registrados'] == 2
    assert metricas['validados'] == 1
    assert metricas['transcritos'] == 1
    assert metricas['avance_validacion_pct'] == 50.0
    assert metricas['avance_meta_pct'] == 10.0  # 2 / 20 * 100
