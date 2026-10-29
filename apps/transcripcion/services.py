from decimal import Decimal
from typing import Optional, Dict, Any, List
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.services import registrar_auditoria
from apps.seguridad.models import Usuario
from apps.socios.models import Socio
from apps.medidores.models import Medidor
from apps.servicios.models import Servicio, TipoServicio, Tarifario, Obligacion, EstadoObligacion
from apps.transcripcion.models import LoteTranscripcion, EstadoLote, TranscripcionLectura, EstadoTranscripcion


def generar_codigo_transcripcion() -> str:
    """Genera un correlativo anual inalterable para registros de transcripción."""
    año_actual = timezone.now().year
    prefijo = f"TRX-{año_actual}-"
    ultimo = TranscripcionLectura.objects.filter(
        codigo__startswith=prefijo
    ).order_by('-id').first()

    if ultimo:
        try:
            secuencia = int(ultimo.codigo.split('-')[-1]) + 1
        except (ValueError, IndexError):
            secuencia = TranscripcionLectura.objects.filter(codigo__startswith=prefijo).count() + 1
    else:
        secuencia = 1

    return f"{prefijo}{secuencia:06d}"


def crear_lote_transcripcion(
    codigo: str,
    nombre: str,
    fuente_documental: str,
    responsable: Usuario,
    periodo_predeterminado: str = '',
    total_estimado: int = 0,
    observaciones: str = '',
    ip_origen: Optional[str] = None
) -> LoteTranscripcion:
    """
    Crea un nuevo lote o planilla física de transcripción histórica.
    Sección 8.1 de la fuente.
    """
    codigo_limpio = codigo.strip().upper()
    if LoteTranscripcion.objects.filter(codigo=codigo_limpio).exists():
        raise ValidationError(f"Ya existe un lote con el código '{codigo_limpio}'.")

    lote = LoteTranscripcion.objects.create(
        codigo=codigo_limpio,
        nombre=nombre.strip(),
        periodo_predeterminado=periodo_predeterminado.strip(),
        fuente_documental=fuente_documental.strip(),
        total_estimado=total_estimado if total_estimado >= 0 else 0,
        responsable=responsable,
        estado=EstadoLote.ABIERTO,
        observaciones=observaciones.strip()
    )

    registrar_auditoria(
        modulo='TRANSCRIPCION',
        accion='CREAR_LOTE',
        resultado="EXITO",
        usuario=responsable,
        entidad_afectada='LoteTranscripcion',
        registro_id=str(lote.id),
        detalle={
            'codigo': lote.codigo,
            'nombre': lote.nombre,
            'fuente': lote.fuente_documental,
            'total_estimado': lote.total_estimado
        },
        ip_origen=ip_origen
    )

    return lote


def transcribir_lectura(
    lote: LoteTranscripcion,
    socio: Socio,
    periodo: str,
    usuario: Usuario,
    medidor: Optional[Medidor] = None,
    lectura_anterior: Optional[Decimal] = None,
    lectura_actual: Optional[Decimal] = None,
    tarifario_aplicado: Optional[Tarifario] = None,
    importe_documentado: Optional[Decimal] = None,
    referencia_foja: str = '',
    observaciones: str = '',
    ip_origen: Optional[str] = None
) -> TranscripcionLectura:
    """
    Registra una fila manuscrita proveniente del cuaderno físico.
    Cumple P6 (Auditoría), P8 (Transparencia) y R-DOM-18 (No genera deuda automática).
    """
    if lote.estado == EstadoLote.CERRADO:
        raise ValidationError("No se pueden agregar registros a un lote cerrado.")

    periodo_limpio = periodo.strip().upper()

    # Prevenir duplicación en el mismo lote
    if TranscripcionLectura.objects.filter(lote=lote, socio=socio, periodo=periodo_limpio).exists():
        raise ValidationError(
            f"El socio {socio.codigo} ya tiene un registro de transcripción para el periodo {periodo_limpio} en este lote."
        )

    # Cálculo preliminar de consumo
    consumo_calculado = None
    estado_inicial = EstadoTranscripcion.TRANSCRITO
    motivo_obs = ""

    if lectura_anterior is not None and lectura_actual is not None:
        if lectura_actual >= lectura_anterior:
            consumo_calculado = lectura_actual - lectura_anterior
        else:
            consumo_calculado = Decimal('0.00')
            estado_inicial = EstadoTranscripcion.OBSERVADO
            motivo_obs = (
                f"Lectura actual ({lectura_actual}) menor a anterior ({lectura_anterior}) "
                f"en documento fuente ({referencia_foja}). Requiere revisión."
            )

    # Cálculo por tarifa si está disponible
    importe_calculado = None
    if tarifario_aplicado and consumo_calculado is not None:
        try:
            importe_calculado = tarifario_aplicado.calcular_importe(consumo_calculado)
        except Exception:
            importe_calculado = None

    codigo_reg = generar_codigo_transcripcion()

    registro = TranscripcionLectura.objects.create(
        codigo=codigo_reg,
        lote=lote,
        socio=socio,
        medidor=medidor,
        periodo=periodo_limpio,
        lectura_anterior=lectura_anterior,
        lectura_actual=lectura_actual,
        consumo_calculado=consumo_calculado,
        tarifario_aplicado=tarifario_aplicado,
        importe_calculado=importe_calculado,
        importe_documentado=importe_documentado,
        referencia_foja=referencia_foja.strip(),
        estado=estado_inicial,
        transcrito_por=usuario,
        fecha_transcripcion=timezone.now(),
        observaciones=observaciones.strip(),
        motivo_observacion_rechazo=motivo_obs
    )

    registrar_auditoria(
        modulo='TRANSCRIPCION',
        accion='TRANSCRIBIR_LECTURA',
        resultado="EXITO",
        usuario=usuario,
        entidad_afectada='TranscripcionLectura',
        registro_id=str(registro.id),
        detalle={
            'codigo': registro.codigo,
            'lote': lote.codigo,
            'socio': socio.codigo,
            'periodo': periodo_limpio,
            'lectura_actual': str(lectura_actual) if lectura_actual is not None else None,
            'importe_documentado': str(importe_documentado) if importe_documentado is not None else None,
            'estado': registro.estado
        },
        ip_origen=ip_origen
    )

    return registro


def validar_transcripcion(
    transcripcion: TranscripcionLectura,
    supervisor: Usuario,
    observaciones: str = '',
    ip_origen: Optional[str] = None
) -> TranscripcionLectura:
    """
    Aprueba formalmente un registro histórico digitado.
    Sección 8.3 de la fuente.
    """
    if transcripcion.estado not in [EstadoTranscripcion.TRANSCRITO, EstadoTranscripcion.OBSERVADO]:
        raise ValidationError(f"Solo registros TRANSCRITO u OBSERVADO pueden ser validados (Estado actual: {transcripcion.get_estado_display()}).")

    estado_previo = transcripcion.estado
    transcripcion.estado = EstadoTranscripcion.VALIDADO
    transcripcion.validado_por = supervisor
    transcripcion.fecha_validacion = timezone.now()
    if observaciones.strip():
        transcripcion.observaciones = f"{transcripcion.observaciones} | Val: {observaciones.strip()}".strip(" | ")
    transcripcion.save()

    registrar_auditoria(
        modulo='TRANSCRIPCION',
        accion='VALIDAR_TRANSCRIPCION',
        resultado="EXITO",
        usuario=supervisor,
        entidad_afectada='TranscripcionLectura',
        registro_id=str(transcripcion.id),
        detalle={
            'codigo': transcripcion.codigo,
            'estado_anterior': estado_previo,
            'estado': EstadoTranscripcion.VALIDADO,
            'socio': transcripcion.socio.codigo,
            'periodo': transcripcion.periodo
        },
        ip_origen=ip_origen
    )

    return transcripcion


def observar_transcripcion(
    transcripcion: TranscripcionLectura,
    usuario: Usuario,
    motivo: str,
    ip_origen: Optional[str] = None
) -> TranscripcionLectura:
    """Marca un registro con discrepancias u omisiones pendientes de resolución."""
    if not motivo or len(motivo.strip()) < 5:
        raise ValidationError("Debe proporcionar un motivo claro para la observación (mínimo 5 caracteres).")

    if transcripcion.estado in [EstadoTranscripcion.MIGRADO, EstadoTranscripcion.RECHAZADO]:
        raise ValidationError("No se puede observar un registro ya migrado o rechazado.")

    estado_previo = transcripcion.estado
    transcripcion.estado = EstadoTranscripcion.OBSERVADO
    transcripcion.motivo_observacion_rechazo = motivo.strip()
    transcripcion.save()

    registrar_auditoria(
        modulo='TRANSCRIPCION',
        accion='OBSERVAR_TRANSCRIPCION',
        resultado="EXITO",
        usuario=usuario,
        entidad_afectada='TranscripcionLectura',
        registro_id=str(transcripcion.id),
        detalle={
            'codigo': transcripcion.codigo,
            'estado_anterior': estado_previo,
            'estado': EstadoTranscripcion.OBSERVADO,
            'motivo': motivo.strip()
        },
        ip_origen=ip_origen
    )

    return transcripcion


def rechazar_transcripcion(
    transcripcion: TranscripcionLectura,
    supervisor: Usuario,
    motivo: str,
    ip_origen: Optional[str] = None
) -> TranscripcionLectura:
    """Descarte formal y definitivo de un registro erróneo o sin respaldo (P5)."""
    if not motivo or len(motivo.strip()) < 10:
        raise ValidationError("El rechazo formal exige un motivo documentado de al menos 10 caracteres.")

    if transcripcion.estado == EstadoTranscripcion.MIGRADO:
        raise ValidationError("No se puede rechazar un registro que ya fue migrado a la base de datos operativa.")

    estado_previo = transcripcion.estado
    transcripcion.estado = EstadoTranscripcion.RECHAZADO
    transcripcion.motivo_observacion_rechazo = motivo.strip()
    transcripcion.save()

    registrar_auditoria(
        modulo='TRANSCRIPCION',
        accion='RECHAZAR_TRANSCRIPCION',
        resultado="EXITO",
        usuario=supervisor,
        entidad_afectada='TranscripcionLectura',
        registro_id=str(transcripcion.id),
        detalle={
            'codigo': transcripcion.codigo,
            'estado_anterior': estado_previo,
            'estado': EstadoTranscripcion.RECHAZADO,
            'motivo': motivo.strip()
        },
        ip_origen=ip_origen
    )

    return transcripcion


def regularizar_deuda_historica(
    transcripcion: TranscripcionLectura,
    usuario_autorizador: Usuario,
    motivo_respaldo: str,
    ip_origen: Optional[str] = None
) -> Obligacion:
    """
    Incorpora una deuda histórica respaldada al estado de cuenta del socio,
    creando la Obligacion en servicios y vinculándola para cobro en caja.
    Sección 8.7 de la fuente y Regla R-DOM-19.
    """
    if transcripcion.estado != EstadoTranscripcion.VALIDADO:
        raise ValidationError(
            f"Solo se pueden regularizar deudas con estado VALIDADO. (Estado actual: {transcripcion.get_estado_display()})."
        )

    if not motivo_respaldo or len(motivo_respaldo.strip()) < 10:
        raise ValidationError("Debe proporcionar una justificación o referencia documental de respaldo (mínimo 10 caracteres).")

    # Determinar el monto exigible: prioriza importe documentado en cuaderno
    monto_deuda = transcripcion.importe_documentado
    if monto_deuda is None or monto_deuda <= Decimal('0.00'):
        monto_deuda = transcripcion.importe_calculado

    if monto_deuda is None or monto_deuda <= Decimal('0.00'):
        raise ValidationError(
            "El registro no cuenta con un importe histórico válido para generar una obligación económica."
        )

    # Obtener el servicio de agua potable
    servicio_agua = Servicio.objects.filter(
        tipo_servicio=TipoServicio.AGUA_POTABLE,
        activo=True
    ).first()

    if not servicio_agua:
        raise ValidationError("No existe un servicio activo de Agua Potable configurado en el catálogo.")

    # Verificar que no exista ya una obligación para ese periodo
    if Obligacion.objects.filter(
        socio=transcripcion.socio,
        servicio=servicio_agua,
        periodo=transcripcion.periodo
    ).exists():
        raise ValidationError(
            f"Ya existe una obligación económica registrada para el socio {transcripcion.socio.codigo} en el periodo {transcripcion.periodo}."
        )

    with transaction.atomic():
        concepto_detalle = f"Regularización Deuda Histórica {transcripcion.periodo} - Doc: {transcripcion.referencia_foja or transcripcion.lote.codigo}"

        obligacion = Obligacion.objects.create(
            socio=transcripcion.socio,
            servicio=servicio_agua,
            periodo=transcripcion.periodo,
            concepto=concepto_detalle,
            monto=monto_deuda,
            saldo_pendiente=monto_deuda,
            fecha_emision=timezone.now().date(),
            fecha_vencimiento=timezone.now().date(),
            estado=EstadoObligacion.PENDIENTE
        )

        transcripcion.obligacion_regularizada = obligacion
        transcripcion.estado = EstadoTranscripcion.MIGRADO
        transcripcion.observaciones = f"{transcripcion.observaciones} | Reg: {motivo_respaldo.strip()}".strip(" | ")
        transcripcion.save()

    registrar_auditoria(
        modulo='TRANSCRIPCION',
        accion='REGULARIZAR_DEUDA_HISTORICA',
        resultado="EXITO",
        usuario=usuario_autorizador,
        entidad_afectada='Obligacion',
        registro_id=str(obligacion.id),
        detalle={
            'transcripcion_codigo': transcripcion.codigo,
            'obligacion_id': obligacion.id,
            'socio': transcripcion.socio.codigo,
            'periodo': transcripcion.periodo,
            'monto': str(monto_deuda),
            'motivo_respaldo': motivo_respaldo.strip()
        },
        ip_origen=ip_origen
    )

    return obligacion


def calcular_metricas_lote(lote: LoteTranscripcion) -> Dict[str, Any]:
    """
    Calcula los totales por estado y el porcentaje de avance de migración del lote.
    Sección 8.6 de la fuente funcional.
    """
    qs = TranscripcionLectura.objects.filter(lote=lote)
    total_registrados = qs.count()

    pendientes = qs.filter(estado=EstadoTranscripcion.PENDIENTE).count()
    transcritos = qs.filter(estado=EstadoTranscripcion.TRANSCRITO).count()
    observados = qs.filter(estado=EstadoTranscripcion.OBSERVADO).count()
    validados = qs.filter(estado=EstadoTranscripcion.VALIDADO).count()
    migrados = qs.filter(estado=EstadoTranscripcion.MIGRADO).count()
    rechazados = qs.filter(estado=EstadoTranscripcion.RECHAZADO).count()

    avance_validacion = 0.0
    if total_registrados > 0:
        avance_validacion = round(((validados + migrados) / total_registrados) * 100, 1)

    avance_meta = None
    if lote.total_estimado > 0:
        avance_meta = round((total_registrados / lote.total_estimado) * 100, 1)

    return {
        'total_registrados': total_registrados,
        'total_estimado': lote.total_estimado,
        'pendientes': pendientes,
        'transcritos': transcritos,
        'observados': observados,
        'validados': validados,
        'migrados': migrados,
        'rechazados': rechazados,
        'avance_validacion_pct': avance_validacion,
        'avance_meta_pct': avance_meta
    }

