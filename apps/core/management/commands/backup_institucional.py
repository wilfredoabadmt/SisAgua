import os
import json
import hashlib
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core import serializers
from django.conf import settings
from apps.configuracion.models import Institucion, Menu
from apps.seguridad.models import Rol, Permiso, Usuario
from apps.socios.models import Zona, Socio
from apps.servicios.models import Servicio, Tarifario, TramoTarifario, Obligacion
from apps.medidores.models import Medidor, AsignacionMedidor
from apps.consumo.models import Lectura
from apps.caja.models import CajaTurno, Recibo, DetalleRecibo, Pago
from apps.transcripcion.models import LoteTranscripcion, TranscripcionLectura
from apps.core.models import BitacoraAuditoria


class Command(BaseCommand):
    help = "Genera un respaldo institucional íntegro y verificable con hash criptográfico SHA-256 (Sección 15 de la fuente)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='backups',
            help='Directorio de destino para los archivos de respaldo.'
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        os.makedirs(output_dir, exist_ok=True)

        institucion = Institucion.get_solo()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_sisagua_{timestamp}.json"
        manifest_filename = f"manifest_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        manifest_path = os.path.join(output_dir, manifest_filename)

        self.stdout.write(self.style.MIGRATE_HEADING(f"Iniciando respaldo institucional de {institucion.nombre}..."))

        modelos = [
            Institucion, Rol, Permiso, Menu, Usuario,
            Zona, Socio,
            Servicio, Tarifario, TramoTarifario, Obligacion,
            Medidor, AsignacionMedidor,
            Lectura,
            CajaTurno, Recibo, DetalleRecibo, Pago,
            LoteTranscripcion, TranscripcionLectura,
            BitacoraAuditoria
        ]

        total_registros = {}
        todos_los_objetos = []

        for m in modelos:
            qs = m.objects.all()
            total_registros[m._meta.label] = qs.count()
            todos_los_objetos.extend(list(qs))

        # Serializar a formato JSON
        datos_json = serializers.serialize("json", todos_los_objetos, indent=2)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(datos_json)

        # Calcular Hash SHA-256 de integridad
        sha256 = hashlib.sha256(datos_json.encode('utf-8')).hexdigest()

        # Generar manifiesto institucional
        manifiesto = {
            "sistema": "SisAgua",
            "version_normativa": "Ley 2066 / AAPS / SDD v1.0",
            "institucion": institucion.nombre,
            "moneda": institucion.moneda,
            "fecha_generacion": datetime.now().isoformat(),
            "archivo_datos": filename,
            "sha256_checksum": sha256,
            "total_objetos_serializados": len(todos_los_objetos),
            "desglose_por_modelo": total_registros
        }

        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifiesto, f, indent=2)

        # Registrar evento de auditoría
        from apps.core.services import registrar_auditoria
        registrar_auditoria(
            modulo="SISTEMA",
            accion="BACKUP",
            resultado="EXITO",
            entidad_afectada="BaseDeDatos",
            registro_id=filename,
            detalle={
                "archivo": filename,
                "sha256": sha256,
                "total_objetos": len(todos_los_objetos)
            }
        )

        self.stdout.write(self.style.SUCCESS(f"[OK] Respaldo generado con éxito: {filepath}"))
        self.stdout.write(self.style.SUCCESS(f"[OK] Manifiesto de integridad: {manifest_path}"))
        self.stdout.write(self.style.SUCCESS(f"[OK] Checksum SHA-256: {sha256}"))
        self.stdout.write(self.style.SUCCESS(f"[OK] Total de entidades respaldadas: {len(todos_los_objetos)}"))
