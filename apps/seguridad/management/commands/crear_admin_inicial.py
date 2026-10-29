"""
Comando administrativo para crear el Administrador General y perfiles demostrativos de SisAgua.
"""
from django.core.management.base import BaseCommand
from apps.seguridad.models import Usuario, Rol

class Command(BaseCommand):
    help = "Crea el usuario Administrador General inicial y perfiles operativos con roles canónicos."

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin', help='Nombre de usuario administrador')
        parser.add_argument('--password', type=str, default='AdminAgua2026!', help='Contraseña inicial administrador')
        parser.add_argument('--nombres', type=str, default='Administrador', help='Nombres')
        parser.add_argument('--apellido', type=str, default='General', help='Primer apellido')
        parser.add_argument('--ci', type=str, default='1000000', help='Carnet de identidad')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        nombres = options['nombres']
        apellido = options['apellido']
        ci = options['ci']

        # 1. Administrador General
        if not Usuario.objects.filter(username=username).exists():
            rol_admin = Rol.objects.filter(codigo='ADMINISTRADOR').first()
            Usuario.objects.create_superuser(
                username=username,
                password=password,
                nombres=nombres,
                apellido_paterno=apellido,
                ci_numero=ci,
                rol=rol_admin,
                requiere_cambio_clave=False
            )
            self.stdout.write(self.style.SUCCESS(f"Usuario Administrador '{username}' creado exitosamente."))
        else:
            self.stdout.write(self.style.WARNING(f"El usuario '{username}' ya existe."))

        # 2. Perfiles Demostrativos Operativos
        perfiles_demo = [
            {
                'username': 'cajero',
                'password': 'CajeroAgua2026!',
                'nombres': 'Carlos',
                'apellido': 'Cajero',
                'ci': '2000000',
                'rol_codigo': 'CAJERO',
                'is_staff': True,
            },
            {
                'username': 'lector',
                'password': 'LectorAgua2026!',
                'nombres': 'Luis',
                'apellido': 'Lector',
                'ci': '3000000',
                'rol_codigo': 'LECTOR',
                'is_staff': True,
            },
            {
                'username': 'auditor',
                'password': 'AuditorAgua2026!',
                'nombres': 'Ana',
                'apellido': 'Auditora',
                'ci': '4000000',
                'rol_codigo': 'AUDITOR',
                'is_staff': True,
            },
        ]

        for p in perfiles_demo:
            if not Usuario.objects.filter(username=p['username']).exists():
                rol = Rol.objects.filter(codigo=p['rol_codigo']).first()
                Usuario.objects.create_user(
                    username=p['username'],
                    password=p['password'],
                    nombres=p['nombres'],
                    apellido_paterno=p['apellido'],
                    ci_numero=p['ci'],
                    rol=rol,
                    is_staff=p['is_staff'],
                    requiere_cambio_clave=False
                )
                self.stdout.write(self.style.SUCCESS(f"Usuario operativo '{p['username']}' ({p['rol_codigo']}) creado exitosamente."))
