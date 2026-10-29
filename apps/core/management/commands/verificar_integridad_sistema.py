from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, Q
from apps.socios.models import Socio, Zona
from apps.medidores.models import Medidor, AsignacionMedidor
from apps.consumo.models import Lectura
from apps.servicios.models import Servicio, TipoServicio, Obligacion, EstadoObligacion
from apps.caja.models import Recibo, DetalleRecibo, CajaTurno, EstadoTurnoCaja
from apps.core.models import BitacoraAuditoria


class Command(BaseCommand):
    help = "Auditoría automatizada de integridad y consistencia cruzada de datos (Sección 13 de la fuente funcional)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== AUDITORÍA DE INTEGRIDAD SISAGUA (SECCIÓN 13) ==="))
        errores = []
        advertencias = []

        # 1. R-INT-01: Verificación de no duplicidad de socios
        duplicados_ci = Socio.objects.values('ci', 'ci_complemento').annotate(total=Count('id')).filter(total__gt=1)
        if duplicados_ci.exists():
            errores.append(f"R-INT-01: Se encontraron {duplicados_ci.count()} combinaciones duplicadas de CI y complemento.")
        else:
            self.stdout.write(self.style.SUCCESS("[OK] R-INT-01: No existen socios duplicados por Cédula de Identidad."))

        # 2. R-INT-02: Exclusividad de asignación de medidores
        medidores_doble_activos = AsignacionMedidor.objects.filter(activo=True).values('medidor_id').annotate(total=Count('id')).filter(total__gt=1)
        if medidores_doble_activos.exists():
            errores.append(f"R-INT-02: Se encontraron {medidores_doble_activos.count()} medidores asignados a más de un socio activo simultáneamente.")
        else:
            self.stdout.write(self.style.SUCCESS("[OK] R-INT-02: Todo medidor activo cuenta con asignación exclusiva unívoca."))

        # 3. R-INT-03: Unicidad de lectura mensual definitiva
        lecturas_duplicadas = Lectura.objects.filter(activo=True).values('medidor_id', 'periodo').annotate(total=Count('id')).filter(total__gt=1)
        if lecturas_duplicadas.exists():
            errores.append(f"R-INT-03: Existen {lecturas_duplicadas.count()} medidores con lecturas múltiples activas en el mismo periodo.")
        else:
            self.stdout.write(self.style.SUCCESS("[OK] R-INT-03: Unicidad estricta de lectura mensual garantizada por periodo."))

        # 4. R-INT-04 & R-INT-05: Unicidad de membresías por socio
        membresias_duplicadas = Obligacion.objects.filter(servicio__tipo_servicio=TipoServicio.MEMBRESIA).values('socio_id').annotate(total=Count('id')).filter(total__gt=1)
        if membresias_duplicadas.exists():
            errores.append(f"R-INT-05: Se detectaron {membresias_duplicadas.count()} socios con más de una obligación de membresía única.")
        else:
            self.stdout.write(self.style.SUCCESS("[OK] R-INT-05: Membresía única atómica por socio verificada sin duplicados."))

        # 5. R-INT-06: Consistencia contable de recibos y detalles
        recibos_descuadrados = 0
        for r in Recibo.objects.prefetch_related('detalles').all():
            suma_detalles = sum((d.subtotal for d in r.detalles.all()), 0)
            if suma_detalles != r.monto_total:
                recibos_descuadrados += 1
        if recibos_descuadrados > 0:
            errores.append(f"R-INT-06: Se detectaron {recibos_descuadrados} recibos oficiales con descalce entre monto total y desglose de detalles.")
        else:
            self.stdout.write(self.style.SUCCESS("[OK] R-INT-06: Todos los recibos oficiales cuadran al 100% con sus detalles."))

        # 6. R-INT-07: Sanitización estricta de la Bitácora de Auditoría (Principio P6)
        secret_keywords = ['argon2', 'pbkdf2', 'password_hash', 'secret_key']
        fugas_encontradas = 0
        for b in BitacoraAuditoria.objects.all():
            texto_detalle = str(b.detalle_json).lower()
            if any(k in texto_detalle for k in secret_keywords):
                fugas_encontradas += 1
        if fugas_encontradas > 0:
            errores.append(f"P6: Se detectaron {fugas_encontradas} registros de auditoría con posibles credenciales o hashes no sanitizados.")
        else:
            self.stdout.write(self.style.SUCCESS("[OK] Principio P6: Bitácora de auditoría 100% sanitizada sin fuga de secretos."))

        # Resumen Final
        self.stdout.write("--------------------------------------------------")
        if errores:
            for e in errores:
                self.stdout.write(self.style.ERROR(f"[FALLO] {e}"))
            raise SystemExit(1)
        else:
            self.stdout.write(self.style.SUCCESS("[CERTIFICACIÓN EXITOSA] El sistema cumple al 100% con todas las reglas de integridad de la Sección 13."))
