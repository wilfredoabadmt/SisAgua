from decimal import Decimal
from typing import Optional, Dict, Any, List
from django.db.models import Sum, Count, Q
from django.utils import timezone
from apps.socios.models import Socio, Zona, EstadoSocio
from apps.medidores.models import Medidor, AsignacionMedidor
from apps.servicios.models import Servicio, TipoServicio, Obligacion, EstadoObligacion
from apps.consumo.models import Lectura, EstadoLectura
from apps.caja.models import Recibo, EstadoRecibo, Pago, MetodoPago, DetalleRecibo


def obtener_reporte_deudores(
    zona_id: Optional[int] = None,
    antiguedad_minima: Optional[int] = None,
    solo_vencidas: bool = False
) -> Dict[str, Any]:
    """
    Genera el reporte consolidado de socios con deudas pendientes.
    Sección 10.1 de la fuente funcional.
    """
    hoy = timezone.now().date()

    # Obtener obligaciones pendientes
    obligaciones_qs = Obligacion.objects.filter(
        estado=EstadoObligacion.PENDIENTE
    ).select_related('socio', 'socio__zona', 'servicio')

    if zona_id:
        obligaciones_qs = obligaciones_qs.filter(socio__zona_id=zona_id)
    if solo_vencidas:
        obligaciones_qs = obligaciones_qs.filter(fecha_vencimiento__lt=hoy)

    # Agrupar por socio para evitar duplicación y producto cartesiano
    deudores_dict = {}
    for obl in obligaciones_qs:
        sid = obl.socio_id
        if sid not in deudores_dict:
            deudores_dict[sid] = {
                'socio': obl.socio,
                'zona': obl.socio.zona,
                'deuda_agua': Decimal('0.00'),
                'deuda_membresia': Decimal('0.00'),
                'deuda_otros': Decimal('0.00'),
                'total_pendiente': Decimal('0.00'),
                'importe_vencido': Decimal('0.00'),
                'periodos': set(),
                'obligaciones_count': 0
            }

        data = deudores_dict[sid]
        saldo = obl.saldo_pendiente
        data['total_pendiente'] += saldo
        data['obligaciones_count'] += 1
        data['periodos'].add(obl.periodo)

        if obl.fecha_vencimiento < hoy:
            data['importe_vencido'] += saldo

        if obl.servicio.tipo_servicio == TipoServicio.AGUA_POTABLE:
            data['deuda_agua'] += saldo
        elif obl.servicio.tipo_servicio == TipoServicio.MEMBRESIA:
            data['deuda_membresia'] += saldo
        else:
            data['deuda_otros'] += saldo

    # Transformar a lista de resultados con conteo de medidores y filtros de antigüedad
    filas_deudores = []
    total_deuda_general = Decimal('0.00')
    total_deuda_agua = Decimal('0.00')
    total_deuda_membresia = Decimal('0.00')
    total_deuda_vencida = Decimal('0.00')

    # Pre-cargar conteo de medidores de los socios
    socios_ids = list(deudores_dict.keys())
    medidores_por_socio = dict(
        AsignacionMedidor.objects.filter(
            socio_id__in=socios_ids,
            activo=True
        ).values('socio_id').annotate(total=Count('id')).values_list('socio_id', 'total')
    )

    for sid, d in deudores_dict.items():
        antiguedad_meses = len(d['periodos'])
        if antiguedad_minima and antiguedad_meses < antiguedad_minima:
            continue

        item = {
            'socio': d['socio'],
            'zona': d['zona'],
            'cantidad_medidores': medidores_por_socio.get(sid, 0),
            'deuda_agua': d['deuda_agua'],
            'deuda_membresia': d['deuda_membresia'],
            'deuda_otros': d['deuda_otros'],
            'total_pendiente': d['total_pendiente'],
            'importe_vencido': d['importe_vencido'],
            'antiguedad_meses': antiguedad_meses,
            'periodos_str': ", ".join(sorted(d['periodos']))
        }
        filas_deudores.append(item)

        total_deuda_general += d['total_pendiente']
        total_deuda_agua += d['deuda_agua']
        total_deuda_membresia += d['deuda_membresia']
        total_deuda_vencida += d['importe_vencido']

    # Ordenar por mayor deuda de forma descendente
    filas_deudores.sort(key=lambda x: x['total_pendiente'], reverse=True)

    cantidad_socios = len(filas_deudores)
    promedio_deuda = (total_deuda_general / cantidad_socios) if cantidad_socios > 0 else Decimal('0.00')

    return {
        'deudores': filas_deudores,
        'total_socios_deudores': cantidad_socios,
        'total_deuda_general': total_deuda_general,
        'total_deuda_agua': total_deuda_agua,
        'total_deuda_membresia': total_deuda_membresia,
        'total_deuda_vencida': total_deuda_vencida,
        'promedio_deuda': round(promedio_deuda, 2)
    }


def obtener_reporte_recaudacion(
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    cajero_id: Optional[int] = None,
    metodo_pago: Optional[str] = None
) -> Dict[str, Any]:
    """
    Concilia los ingresos efectivamente cobrados por medio de pago y discrimina anulaciones.
    Sección 10.5 de la fuente funcional.
    """
    recibos_qs = Recibo.objects.select_related('cajero', 'socio')
    anulados_qs = Recibo.objects.filter(estado=EstadoRecibo.ANULADO)

    if fecha_desde:
        recibos_qs = recibos_qs.filter(fecha_emision__date__gte=fecha_desde)
        anulados_qs = anulados_qs.filter(fecha_anulacion__date__gte=fecha_desde)
    if fecha_hasta:
        recibos_qs = recibos_qs.filter(fecha_emision__date__lte=fecha_hasta)
        anulados_qs = anulados_qs.filter(fecha_anulacion__date__lte=fecha_hasta)
    if cajero_id:
        recibos_qs = recibos_qs.filter(cajero_id=cajero_id)
        anulados_qs = anulados_qs.filter(usuario_anulacion_id=cajero_id)
    if metodo_pago:
        recibos_qs = recibos_qs.filter(metodo_pago=metodo_pago)

    # Recaudación neta real (solo recibos EMITIDOS)
    recibos_emitidos = recibos_qs.filter(estado=EstadoRecibo.EMITIDO)
    total_neto = Decimal('0.00')
    total_efectivo = Decimal('0.00')
    total_qr = Decimal('0.00')
    total_transferencia = Decimal('0.00')

    for r in recibos_emitidos:
        total_neto += r.monto_total
        if r.metodo_pago == MetodoPago.EFECTIVO:
            total_efectivo += r.monto_total
        elif r.metodo_pago == MetodoPago.QR:
            total_qr += r.monto_total
        elif r.metodo_pago == MetodoPago.TRANSFERENCIA:
            total_transferencia += r.monto_total

    # Desglose por servicio a partir de DetalleRecibo
    detalles = DetalleRecibo.objects.filter(
        recibo__in=recibos_emitidos
    ).values('concepto').annotate(total=Sum('subtotal'))

    recaudacion_por_concepto = {d['concepto']: d['total'] for d in detalles}

    # Recibos anulados
    cantidad_anulados = anulados_qs.count()
    monto_anulado = sum(r.monto_total for r in anulados_qs)

    return {
        'recibos': recibos_emitidos.order_by('-fecha_emision')[:150],
        'recibos_anulados_lista': anulados_qs.order_by('-fecha_anulacion')[:50],
        'total_neto': total_neto,
        'total_efectivo': total_efectivo,
        'total_qr': total_qr,
        'total_transferencia': total_transferencia,
        'cantidad_emitidos': recibos_emitidos.count(),
        'cantidad_anulados': cantidad_anulados,
        'monto_anulado': monto_anulado,
        'recaudacion_por_concepto': recaudacion_por_concepto
    }


def obtener_reporte_consumo(
    periodo: Optional[str] = None,
    zona_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Analiza el volumen de agua consumido y detecta lecturas anómalas u observadas.
    Sección 10.4 de la fuente funcional.
    """
    periodo_consulta = periodo or timezone.now().strftime('%Y-%m')

    lecturas_qs = Lectura.objects.filter(
        periodo=periodo_consulta
    ).select_related('medidor', 'socio', 'socio__zona', 'lector')

    if zona_id:
        lecturas_qs = lecturas_qs.filter(socio__zona_id=zona_id)

    total_lecturas = lecturas_qs.count()
    total_m3 = Decimal('0.00')
    consumos_cero = 0
    observadas_lista = []

    for l in lecturas_qs:
        total_m3 += l.consumo_m3
        if l.consumo_m3 == Decimal('0.00'):
            consumos_cero += 1
        if l.estado == EstadoLectura.OBSERVADA:
            observadas_lista.append(l)

    promedio_m3 = (total_m3 / total_lecturas) if total_lecturas > 0 else Decimal('0.00')

    # Identificar medidores activos que no tienen lectura registrada en este periodo
    asignaciones_activas = AsignacionMedidor.objects.filter(activo=True)
    if zona_id:
        asignaciones_activas = asignaciones_activas.filter(socio__zona_id=zona_id)

    medidores_leidos_ids = set(lecturas_qs.values_list('medidor_id', flat=True))
    medidores_sin_lectura = [
        a for a in asignaciones_activas.select_related('medidor', 'socio')
        if a.medidor_id not in medidores_leidos_ids
    ]

    return {
        'periodo': periodo_consulta,
        'lecturas': lecturas_qs.order_by('-consumo_m3')[:100],
        'total_lecturas': total_lecturas,
        'total_m3': total_m3,
        'promedio_m3': round(promedio_m3, 2),
        'consumos_cero': consumos_cero,
        'observadas_count': len(observadas_lista),
        'observadas_lista': observadas_lista,
        'medidores_sin_lectura_count': len(medidores_sin_lectura),
        'medidores_sin_lectura': medidores_sin_lectura[:50]
    }


def obtener_reporte_zonas(periodo: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Balance integral por sector territorial: padrón, medidores, facturado vs recaudado y mora.
    Sección 10.2 de la fuente funcional.
    """
    zonas = Zona.objects.filter(activo=True).order_by('codigo')
    resumen_zonas = []

    for z in zonas:
        socios_zona = Socio.objects.filter(zona=z)
        total_socios = socios_zona.count()
        socios_activos = socios_zona.filter(estado=EstadoSocio.ACTIVO).count()
        socios_inactivos = total_socios - socios_activos

        total_medidores = AsignacionMedidor.objects.filter(socio__in=socios_zona, activo=True).count()

        # Obligaciones de la zona
        obligs = Obligacion.objects.filter(socio__in=socios_zona)
        if periodo:
            obligs = obligs.filter(periodo=periodo)

        total_facturado = sum((o.monto for o in obligs), Decimal('0.00'))
        total_mora = sum((o.saldo_pendiente for o in obligs.filter(estado=EstadoObligacion.PENDIENTE)), Decimal('0.00'))
        total_recaudado = max(Decimal('0.00'), total_facturado - total_mora)

        eficacia = (float(total_recaudado) / float(total_facturado) * 100.0) if total_facturado > Decimal('0.00') else 100.0

        resumen_zonas.append({
            'zona': z,
            'total_socios': total_socios,
            'socios_activos': socios_activos,
            'socios_inactivos': socios_inactivos,
            'total_medidores': total_medidores,
            'total_facturado': total_facturado,
            'total_recaudado': total_recaudado,
            'total_mora': total_mora,
            'eficacia_pct': round(eficacia, 1)
        })

    return resumen_zonas


def obtener_reporte_membresias(
    zona_id: Optional[int] = None,
    estado_filtro: Optional[str] = None
) -> Dict[str, Any]:
    """
    Reporte específico de cuotas de incorporación/afiliación única de socios.
    Sección 10.6 de la fuente funcional.
    """
    membresias_qs = Obligacion.objects.filter(
        servicio__tipo_servicio=TipoServicio.MEMBRESIA
    ).select_related('socio', 'socio__zona')

    if zona_id:
        membresias_qs = membresias_qs.filter(socio__zona_id=zona_id)
    if estado_filtro:
        membresias_qs = membresias_qs.filter(estado=estado_filtro)

    total_generadas = membresias_qs.count()
    pagadas_qs = membresias_qs.filter(estado=EstadoObligacion.PAGADA)
    pendientes_qs = membresias_qs.filter(estado=EstadoObligacion.PENDIENTE)

    total_pagadas = pagadas_qs.count()
    total_pendientes = pendientes_qs.count()

    monto_recaudado = sum((m.monto for m in pagadas_qs), Decimal('0.00'))
    monto_pendiente = sum((m.saldo_pendiente for m in pendientes_qs), Decimal('0.00'))

    return {
        'membresias': membresias_qs.order_by('-fecha_emision')[:150],
        'total_generadas': total_generadas,
        'total_pagadas': total_pagadas,
        'total_pendientes': total_pendientes,
        'monto_recaudado': monto_recaudado,
        'monto_pendiente': monto_pendiente
    }


def obtener_estado_cuenta_socio(socio_id: int) -> Dict[str, Any]:
    """
    Estado de cuenta integral 360° de un socio particular.
    Sección 10.3 de la fuente funcional.
    """
    socio = Socio.objects.select_related('zona').get(pk=socio_id)
    medidores = AsignacionMedidor.objects.filter(socio=socio).select_related('medidor')

    obligaciones = Obligacion.objects.filter(socio=socio).select_related('servicio').order_by('-fecha_emision')
    recibos = Recibo.objects.filter(socio=socio).select_related('cajero').order_by('-fecha_emision')

    total_facturado = sum((o.monto for o in obligaciones), Decimal('0.00'))
    total_pendiente = sum((o.saldo_pendiente for o in obligaciones if o.estado == EstadoObligacion.PENDIENTE), Decimal('0.00'))
    total_pagado = max(Decimal('0.00'), total_facturado - total_pendiente)

    return {
        'socio': socio,
        'medidores': medidores,
        'obligaciones': obligaciones,
        'recibos': recibos,
        'total_facturado': total_facturado,
        'total_pagado': total_pagado,
        'total_pendiente': total_pendiente
    }
