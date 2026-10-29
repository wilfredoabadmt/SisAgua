import pytest
from decimal import Decimal
from datetime import date
from django.core.exceptions import ValidationError
from apps.socios.models import Zona, Socio
from apps.medidores.models import Medidor, AsignacionMedidor, EstadoMedidor
from apps.consumo.models import Lectura, EstadoLectura
from apps.consumo.services import (
    resolver_lectura_anterior, registrar_lectura,
    corregir_lectura, obtener_historial_proforma
)
from apps.core.models import BitacoraAuditoria

@pytest.fixture
def configuracion_medidor_socio(db):
    zona = Zona.objects.create(codigo="ZON-CON", nombre="Zona Consumo")
    socio = Socio.objects.create(
        codigo="SOC-CON-1",
        ci="332211",
        nombres="Beatriz",
        apellidos="Mendoza",
        zona=zona,
        direccion="Av. Costanera"
    )
    medidor = Medidor.objects.create(
        codigo="MED-C1",
        numero_serie="SN-CONS-01",
        lectura_inicial=Decimal('100.00'),
        estado=EstadoMedidor.INSTALADO
    )
    asig = AsignacionMedidor.objects.create(
        medidor=medidor,
        socio=socio,
        fecha_asignacion=date(2026, 9, 1),
        lectura_instalacion=Decimal('100.00'),
        activo=True
    )
    return socio, medidor, asig

@pytest.mark.django_db
def test_captura_lectura_valida_calcula_consumo_r_dom_06(configuracion_medidor_socio, usuario_admin):
    socio, medidor, _ = configuracion_medidor_socio

    # Capturar lectura periodo 2026-10: lectura actual 112.50 (anterior = 100.00)
    lectura = registrar_lectura(
        medidor=medidor,
        periodo="2026-10",
        lectura_actual=Decimal('112.50'),
        fecha_lectura=date(2026, 10, 25),
        usuario=usuario_admin
    )

    assert lectura.lectura_anterior == Decimal('100.00')
    assert lectura.lectura_actual == Decimal('112.50')
    assert lectura.consumo_m3 == Decimal('12.50')
    assert lectura.estado == EstadoLectura.VALIDADA
    assert lectura.socio == socio

    # Verificar auditoría
    audit = BitacoraAuditoria.objects.filter(modulo='LECTURAS', accion='CREAR').latest('fecha_hora_utc')
    assert audit.usuario == usuario_admin
    assert audit.resultado == 'EXITO'

@pytest.mark.django_db
def test_lectura_menor_a_anterior_dispara_observada_r_dom_07(configuracion_medidor_socio, usuario_admin):
    socio, medidor, _ = configuracion_medidor_socio

    # Ingresar lectura menor a la de instalación (anterior = 100.00, actual = 95.00)
    lectura = registrar_lectura(
        medidor=medidor,
        periodo="2026-10",
        lectura_actual=Decimal('95.00'),
        usuario=usuario_admin
    )

    # R-DOM-07: Monotonicidad violada -> OBSERVADA
    assert lectura.estado == EstadoLectura.OBSERVADA
    assert lectura.consumo_m3 == Decimal('0.00')
    assert "inferior a la lectura anterior" in lectura.motivo_observacion

@pytest.mark.django_db
def test_bloqueo_lectura_duplicada_mismo_periodo_r_dom_08(configuracion_medidor_socio, usuario_admin):
    socio, medidor, _ = configuracion_medidor_socio

    registrar_lectura(
        medidor=medidor,
        periodo="2026-10",
        lectura_actual=Decimal('110.00'),
        usuario=usuario_admin
    )

    # Reintentar registrar lectura para el mismo periodo debe ser rechazado
    with pytest.raises(ValidationError) as exc:
        registrar_lectura(
            medidor=medidor,
            periodo="2026-10",
            lectura_actual=Decimal('115.00'),
            usuario=usuario_admin
        )
    assert "Ya existe una lectura registrada para el medidor" in str(exc.value)

@pytest.mark.django_db
def test_correccion_lectura_observada_con_auditoria_p5_p6(configuracion_medidor_socio, usuario_admin):
    socio, medidor, _ = configuracion_medidor_socio

    lectura = registrar_lectura(
        medidor=medidor,
        periodo="2026-10",
        lectura_actual=Decimal('90.00'),  # Observada
        usuario=usuario_admin
    )
    assert lectura.estado == EstadoLectura.OBSERVADA

    # Supervisor corrige la lectura tras contra-lectura en terreno
    corregida = corregir_lectura(
        lectura=lectura,
        nueva_lectura=Decimal('120.00'),
        motivo="Error de lectura de campo. Verificado físicamente en nicho.",
        usuario=usuario_admin
    )

    assert corregida.estado == EstadoLectura.CORREGIDA
    assert corregida.lectura_actual == Decimal('120.00')
    assert corregida.consumo_m3 == Decimal('20.00')
    assert corregida.validado_por == usuario_admin

    audit = BitacoraAuditoria.objects.filter(modulo='LECTURAS', accion='MODIFICAR').latest('fecha_hora_utc')
    assert audit.usuario == usuario_admin
    assert audit.resultado == 'EXITO'

@pytest.mark.django_db
def test_reinicio_contador_rollover(configuracion_medidor_socio, usuario_admin):
    socio, medidor, asig = configuracion_medidor_socio
    asig.lectura_instalacion = Decimal('99990.00')
    asig.save()

    # Lectura actual 15.00 habiendo reiniciado el reloj de 5 dígitos (vuelta a cero)
    lectura = registrar_lectura(
        medidor=medidor,
        periodo="2026-10",
        lectura_actual=Decimal('15.00'),
        es_reinicio_contador=True,
        usuario=usuario_admin
    )

    # Consumo = (100000 - 99990) + 15 = 25.00 m³
    assert lectura.consumo_m3 == Decimal('25.00')
    assert lectura.estado == EstadoLectura.VALIDADA

@pytest.mark.django_db
def test_proforma_muestra_solo_historial_real_sin_inventar_r_dom_09(configuracion_medidor_socio, usuario_admin):
    socio, medidor, _ = configuracion_medidor_socio

    # Solo registrar 1 periodo previo (2026-08)
    registrar_lectura(medidor=medidor, periodo="2026-08", lectura_actual=Decimal('105.00'), usuario=usuario_admin)

    # Para la proforma del periodo 2026-09
    historial = obtener_historial_proforma(medidor, periodo_actual="2026-09")
    
    # R-DOM-09 y Sección 7.4: Muestra solo lo real (1 periodo), sin inventar los otros 2
    assert len(historial) == 1
    assert historial[0].periodo == "2026-08"
    assert historial[0].consumo_m3 == Decimal('5.00')

