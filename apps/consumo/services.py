import calendar
from decimal import Decimal
from typing import Tuple, Optional, List, Dict, Any
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Lectura, EstadoLectura
from apps.medidores.models import Medidor, AsignacionMedidor
from apps.servicios.models import Servicio, Tarifario, Obligacion, ModalidadCobro, EstadoObligacion
from apps.servicios.services import resolver_tarifa_vigente, calcular_costo_consumo
from apps.configuracion.models import Institucion
from apps.core.services import registrar_auditoria


def resolver_lectura_anterior(medidor: Medidor, periodo: str) -> Tuple[Decimal, Optional[object]]:
    """
    Determina la lectura anterior válida de partida para un medidor en un periodo dado.
    Regla R-DOM-06 y Fuente Sección 7.2.
    """
    lectura_previa = Lectura.objects.filter(
        medidor=medidor,
        periodo__lt=periodo,
        estado__in=[EstadoLectura.VALIDADA, EstadoLectura.CORREGIDA],
        activo=True
    ).order_by('-periodo', '-fecha_lectura').first()

    if lectura_previa:
        return lectura_previa.lectura_actual, lectura_previa.fecha_lectura

    asignacion = AsignacionMedidor.objects.filter(medidor=medidor, activo=True).first()
    if asignacion:
        return asignacion.lectura_instalacion, asignacion.fecha_asignacion

    return medidor.lectura_inicial, None


def registrar_lectura(
    medidor: Medidor,
    periodo: str,
    lectura_actual: Decimal,
    fecha_lectura=None,
    observaciones: str = "",
    es_reinicio_contador: bool = False,
    usuario=None,
    ip_origen: str = "127.0.0.1"
) -> Lectura:
    """
    Registra una lectura mensual con validación de monotonicidad e integridad (R-DOM-06, R-DOM-07, R-DOM-08).
    """
    if fecha_lectura is None:
        fecha_lectura = timezone.now().date()

    with transaction.atomic():
        asignacion = AsignacionMedidor.objects.filter(medidor=medidor, activo=True).select_related('socio').first()
        if not asignacion:
            raise ValidationError(
                f"El medidor {medidor.codigo} no está asignado a ningún socio activo. "
                "No se pueden registrar lecturas para medidores sin asignación vigente."
            )
        socio = asignacion.socio

        if Lectura.objects.filter(medidor=medidor, periodo=periodo, activo=True).exists():
            raise ValidationError(
                f"Ya existe una lectura registrada para el medidor {medidor.codigo} en el periodo {periodo} "
                "(Regla R-DOM-08: Unicidad de lectura definitiva)."
            )

        lectura_anterior, fecha_anterior = resolver_lectura_anterior(medidor, periodo)

        lectura = Lectura(
            medidor=medidor,
            socio=socio,
            periodo=periodo,
            lectura_anterior=lectura_anterior,
            fecha_lectura_anterior=fecha_anterior,
            lectura_actual=lectura_actual,
            fecha_lectura=fecha_lectura,
            es_reinicio_contador=es_reinicio_contador,
            observaciones=observaciones,
            lector=usuario
        )

        lectura.full_clean()
        lectura.save()

        registrar_auditoria(
            modulo="LECTURAS",
            accion="CREAR",
            resultado="EXITO",
            usuario=usuario,
            entidad_afectada="Lectura",
            registro_id=str(lectura.id),
            detalle={
                "periodo": periodo,
                "medidor": medidor.codigo,
                "socio": socio.codigo,
                "lectura_anterior": str(lectura.lectura_anterior),
                "lectura_actual": str(lectura.lectura_actual),
                "consumo_m3": str(lectura.consumo_m3),
                "estado": lectura.estado,
                "motivo_observacion": lectura.motivo_observacion
            },
            ip_origen=ip_origen
        )

        return lectura


def corregir_lectura(
    lectura: Lectura,
    nueva_lectura: Decimal,
    motivo: str,
    es_reinicio_contador: bool = False,
    usuario=None,
    ip_origen: str = "127.0.0.1"
) -> Lectura:
    """
    Corrige formalmente una lectura observada o errónea, preservando la trazabilidad histórica (P5, P6).
    """
    if not motivo or not motivo.strip():
        raise ValidationError("Debe proporcionar una justificación documentada para la corrección de lectura.")

    with transaction.atomic():
        valor_anterior = lectura.lectura_actual
        consumo_anterior = lectura.consumo_m3

        lectura.lectura_actual = nueva_lectura
        lectura.es_reinicio_contador = es_reinicio_contador
        lectura.motivo_observacion = motivo.strip()
        lectura.validado_por = usuario
        lectura.fecha_validacion = timezone.now()

        lectura.clean()
        if lectura.estado != EstadoLectura.OBSERVADA:
            lectura.estado = EstadoLectura.CORREGIDA

        lectura.save()

        registrar_auditoria(
            modulo="LECTURAS",
            accion="MODIFICAR",
            resultado="EXITO",
            usuario=usuario,
            entidad_afectada="Lectura",
            registro_id=str(lectura.id),
            detalle={
                "periodo": lectura.periodo,
                "medidor": lectura.medidor.codigo,
                "lectura_anterior_original": str(valor_anterior),
                "lectura_corregida": str(nueva_lectura),
                "consumo_anterior": str(consumo_anterior),
                "consumo_nuevo": str(lectura.consumo_m3),
                "estado": lectura.estado,
                "justificacion": motivo
            },
            ip_origen=ip_origen
        )

        return lectura


def obtener_historial_proforma(medidor: Medidor, periodo_actual: str, limite: int = 3) -> List[Lectura]:
    """
    Obtiene hasta 3 lecturas anteriores reales del mismo medidor para la proforma informativa.
    Cumple con Sección 7.4 de la fuente: No inventa periodos inexistentes.
    """
    return list(
        Lectura.objects.filter(
            medidor=medidor,
            periodo__lt=periodo_actual,
            estado__in=[EstadoLectura.VALIDADA, EstadoLectura.CORREGIDA],
            activo=True
        ).order_by('-periodo')[:limite]
    )


def facturar_periodo_agua(
    periodo: str,
    usuario=None,
    ip_origen: str = "127.0.0.1"
) -> Dict[str, Any]:
    """
    Motor mensual de facturación de agua potable.
    Cumple con R-DOM-06 (Consumo), R-DOM-10 (No Retroactividad), R-DOM-11 (Snapshot),
    R-DOM-12 (Unicidad Mensual / Idempotencia) y P10 (Validación Previa: excluye observadas).
    """
    servicio_agua = Servicio.objects.filter(
        modalidad_cobro=ModalidadCobro.LECTURA_VOLUMETRICA,
        activo=True
    ).first()

    if not servicio_agua:
        raise ValidationError("No existe un servicio activo configurado para agua potable por lectura volumétrica.")

    institucion = Institucion.get_solo()
    dia_venc = getattr(institucion, 'dia_vencimiento_default', 15) or 15

    # Calcular fecha de vencimiento determinística según R-DOM-14
    # Para el periodo YYYY-MM, vence en el mes subsiguiente en el día configurado o último día
    try:
        anio_p, mes_p = map(int, periodo.split('-'))
    except ValueError:
        raise ValidationError(f"Formato de periodo inválido: '{periodo}'. Se espera YYYY-MM.")

    mes_venc = mes_p + 1 if mes_p < 12 else 1
    anio_venc = anio_p if mes_p < 12 else anio_p + 1
    max_dias = calendar.monthrange(anio_venc, mes_venc)[1]
    dia_venc_real = min(dia_venc, max_dias)
    fecha_vencimiento = timezone.datetime(anio_venc, mes_venc, dia_venc_real).date()

    with transaction.atomic():
        # Consultar lecturas del periodo
        lecturas_validas = Lectura.objects.filter(
            periodo=periodo,
            estado__in=[EstadoLectura.VALIDADA, EstadoLectura.CORREGIDA],
            activo=True
        ).select_related('medidor', 'socio')

        observadas_count = Lectura.objects.filter(
            periodo=periodo,
            estado=EstadoLectura.OBSERVADA,
            activo=True
        ).count()

        generados = 0
        omitidos = 0
        total_bs = Decimal('0.00')

        for lec in lecturas_validas:
            # Regla R-DOM-12: Unicidad e Idempotencia
            if Obligacion.objects.filter(socio=lec.socio, servicio=servicio_agua, periodo=periodo).exists():
                omitidos += 1
                continue

            # Resolver tarifa vigente para la fecha de la lectura (R-DOM-10)
            tarifario = resolver_tarifa_vigente(
                servicio=servicio_agua,
                categoria='DOMESTICO',
                fecha=lec.fecha_lectura
            )
            if not tarifario:
                # Fallback al primer tarifario activo del servicio
                tarifario = servicio_agua.tarifarios.filter(activo=True).first()

            if not tarifario:
                raise ValidationError(f"No existe ningún tarifario configurado para el servicio {servicio_agua.nombre}.")

            # Calcular importe exacto según tramos
            costo = calcular_costo_consumo(tarifario, lec.consumo_m3)
            monto = costo['total']

            # Snapshot detallado de liquidación (R-DOM-11)
            concepto = (
                f"Consumo Agua Potable {periodo} ({lec.consumo_m3} m³ - "
                f"Medidor: {lec.medidor.codigo} - Base: Bs {tarifario.tarifa_basica})"
            )

            Obligacion.objects.create(
                socio=lec.socio,
                servicio=servicio_agua,
                periodo=periodo,
                concepto=concepto,
                monto=monto,
                saldo_pendiente=monto,
                fecha_emision=timezone.now().date(),
                fecha_vencimiento=fecha_vencimiento,
                estado=EstadoObligacion.PENDIENTE
            )

            generados += 1
            total_bs += monto

        resumen = {
            "periodo": periodo,
            "obligaciones_generadas": generados,
            "omitidos_idempotencia": omitidos,
            "lecturas_observadas_omitidas": observadas_count,
            "monto_total_bs": total_bs,
            "fecha_vencimiento": fecha_vencimiento
        }

        registrar_auditoria(
            modulo="CONSUMO",
            accion="GENERAR",
            resultado="EXITO",
            usuario=usuario,
            entidad_afectada="Obligacion",
            registro_id=periodo,
            detalle={
                "periodo": periodo,
                "generadas": generados,
                "omitidas_idempotencia": omitidos,
                "observadas_omitidas": observadas_count,
                "monto_total_bs": str(total_bs),
                "fecha_vencimiento": str(fecha_vencimiento)
            },
            ip_origen=ip_origen
        )

        return resumen
