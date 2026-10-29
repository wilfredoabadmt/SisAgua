from decimal import Decimal
from typing import Optional, Dict, Any
from django.utils import timezone
from .models import Servicio, Tarifario, TramoTarifario, CategoriaTarifa, ModalidadCobro


def resolver_tarifa_vigente(
    servicio: Servicio,
    categoria: str = CategoriaTarifa.DOMESTICO,
    fecha=None
) -> Optional[Tarifario]:
    """
    Resuelve determinísticamente el tarifario vigente para un servicio y categoría en una fecha dada.
    Cumple con el Principio P1 (Fidelidad de Negocio) y Regla R-DOM-10 (No Retroactividad).
    """
    if fecha is None:
        fecha = timezone.now().date()

    return Tarifario.objects.filter(
        servicio=servicio,
        categoria=categoria,
        activo=True,
        fecha_vigencia_desde__lte=fecha
    ).filter(
        models_fecha_vigencia_hasta(fecha)
    ).order_by('-fecha_vigencia_desde').first()


def models_fecha_vigencia_hasta(fecha):
    from django.db.models import Q
    return Q(fecha_vigencia_hasta__isnull=True) | Q(fecha_vigencia_hasta__gte=fecha)


def calcular_costo_consumo(tarifario: Tarifario, consumo_m3: Decimal) -> Dict[str, Any]:
    """
    Calcula el costo del consumo volumétrico según la regla del tarifario y sus tramos.
    Soporta la tarifa básica y tramos escalonados.
    """
    if consumo_m3 < Decimal('0.00'):
        consumo_m3 = Decimal('0.00')

    # Si el tarifario tiene tramos escalonados específicos configurados:
    tramos = list(tarifario.tramos.order_by('orden'))
    if tramos:
        # Evaluar contra tramos
        for tramo in tramos:
            desde = tramo.desde_m3
            hasta = tramo.hasta_m3
            aplica = False
            if hasta is None:
                aplica = consumo_m3 >= desde
            else:
                aplica = desde <= consumo_m3 <= hasta

            if aplica:
                if tramo.es_valor_fijo:
                    total = tramo.precio_unitario
                else:
                    # En tramo por metro cúbico
                    excedente = max(Decimal('0.00'), consumo_m3 - tarifario.consumo_minimo_m3)
                    total = tarifario.tarifa_basica + (excedente * tramo.precio_unitario)
                return {
                    "consumo_m3": consumo_m3,
                    "tarifa_basica": tarifario.tarifa_basica,
                    "tramo_aplicado": tramo.orden,
                    "precio_unitario": tramo.precio_unitario,
                    "total": total
                }

    # Cálculo estándar base + excedente
    excedente = max(Decimal('0.00'), consumo_m3 - tarifario.consumo_minimo_m3)
    costo_excedente = excedente * tarifario.precio_adicional_m3
    total = tarifario.tarifa_basica + costo_excedente

    return {
        "consumo_m3": consumo_m3,
        "tarifa_basica": tarifario.tarifa_basica,
        "consumo_minimo_m3": tarifario.consumo_minimo_m3,
        "excedente_m3": excedente,
        "precio_adicional_m3": tarifario.precio_adicional_m3,
        "costo_excedente": costo_excedente,
        "total": total
    }

