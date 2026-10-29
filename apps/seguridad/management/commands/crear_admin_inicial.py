"""
Comando administrativo para crear el Administrador General inicial de SisAgua.
"""
from django.core.management.base import BaseCommand
from apps.seguridad.models import Usuario, Rol

class Command(BaseCommand):
    help = "Crea el usuario Administrador General inicial con rol y permisos canónicos."

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin', help='Nombre de usuario')
        parser.add_argument('--password', type=str, default='AdminAgua2026!', help='Contraseña inicial')
        parser.add_argument('--nombres', type=str, default='Administrador', help='Nombres')
        parser.add_argument('--apellido', type=str, default='General', help='Primer apellido')
        parser.add_argument('--ci', type=str, default='1000000', help='Carnet de identidad')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        nombres = options['nombres']
        apellido = options['apellido']
        ci = options['ci']

        if Usuario.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"El usuario '{username}' ya existe."))
            return

        rol_admin = Rol.objects.filter(codigo='ADMINISTRADOR').first()

        user = Usuario.objects.create_superuser(
            username=username,
            password=password,
            nombres=nombres,
            apellido_paterno=apellido,
            ci_numero=ci,
            rol=rol_admin,
            requiere_cambio_clave=False
        )

        self.stdout.write(self.style.SUCCESS(
            f"Usuario Administrador '{username}' creado exitosamente con hash Argon2id."
        ))

