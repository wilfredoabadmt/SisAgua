import pytest
from apps.configuracion.models import Institucion
from apps.seguridad.models import Rol, Permiso, Usuario

@pytest.fixture
def institucion(db):
    """Instancia singleton de institución para pruebas."""
    return Institucion.objects.create(
        id=1,
        nombre="Comité de Agua San Pedro",
        direccion="Plaza Principal",
        telefono="71234567",
        nit_personeria="12345678",
        moneda="Bs"
    )

@pytest.fixture
def permisos_base(db):
    """Permisos iniciales para las pruebas."""
    permisos_def = [
        ("INSTITUCION", "VER", "Ver institución"),
        ("INSTITUCION", "MODIFICAR", "Modificar institución"),
        ("USUARIOS", "VER", "Ver usuarios"),
        ("USUARIOS", "CREAR", "Crear usuarios"),
        ("ROLES", "VER", "Ver roles"),
        ("CAJA", "VER", "Ver módulo de caja y recibos"),
        ("CAJA", "CREAR", "Cobrar en caja y abrir turno"),
        ("CAJA", "CERRAR", "Cerrar turno y arquear caja"),
        ("CAJA", "ANULAR", "Anular recibos de pago autorizados"),
        ("ZONAS", "VER", "Ver zonas"),
        ("ZONAS", "CREAR", "Crear zonas"),
        ("ZONAS", "MODIFICAR", "Modificar zonas"),
        ("SOCIOS", "VER", "Ver socios"),
        ("SOCIOS", "CREAR", "Registrar socios y membresía"),
        ("SOCIOS", "MODIFICAR", "Modificar socios"),
        ("SERVICIOS", "VER", "Ver servicios"),
        ("SERVICIOS", "CREAR", "Crear servicios"),
        ("SERVICIOS", "MODIFICAR", "Modificar servicios"),
        ("MEDIDORES", "VER", "Ver medidores"),
        ("MEDIDORES", "CREAR", "Crear medidores"),
        ("MEDIDORES", "MODIFICAR", "Modificar y asignar medidores"),
        ("TARIFARIO", "VER", "Ver tarifarios"),
        ("TARIFARIO", "CREAR", "Crear tarifarios"),
        ("TARIFARIO", "MODIFICAR", "Modificar tarifarios"),
        ("AUDITORIA", "VER", "Ver bitácora de auditoría"),
        ("LECTURAS", "VER", "Ver lecturas y proformas"),
        ("LECTURAS", "CREAR", "Capturar lecturas mensuales"),
        ("LECTURAS", "MODIFICAR", "Corregir lecturas observadas"),
        ("CONSUMO", "GENERAR", "Facturar y calcular obligaciones de consumo"),
        ("TRANSCRIPCION", "VER", "Ver lotes y registros de transcripción"),
        ("TRANSCRIPCION", "CREAR", "Crear lotes y transcribir lecturas históricas"),
        ("TRANSCRIPCION", "VALIDAR", "Validar, observar, rechazar y regularizar transcripciones"),
        ("REPORTES", "VER", "Ver reportes y estados de cuenta"),
        ("REPORTES", "EXPORTAR", "Exportar reportes a CSV"),
        ("PORTAL", "VER", "Acceso al portal individual de socio"),
    ]
    lista = []
    for mod, acc, desc in permisos_def:
        p, _ = Permiso.objects.get_or_create(modulo=mod, accion=acc, defaults={"descripcion": desc})
        lista.append(p)
    return lista

@pytest.fixture
def rol_administrador(db, permisos_base):
    """Rol de Administrador con permisos."""
    rol = Rol.objects.create(
        codigo="ADMINISTRADOR",
        nombre="Administrador General",
        es_sistema=True
    )
    rol.permisos.set(permisos_base)
    return rol

@pytest.fixture
def rol_cajero(db, permisos_base):
    """Rol de Cajero con solo permiso de cobro."""
    rol = Rol.objects.create(
        codigo="CAJERO",
        nombre="Cajero",
        es_sistema=True
    )
    permiso_caja = [p for p in permisos_base if p.modulo == "CAJA"]
    rol.permisos.set(permiso_caja)
    return rol

@pytest.fixture
def usuario_admin(db, rol_administrador):
    """Usuario Administrador para pruebas."""
    return Usuario.objects.create_user(
        username="admin_user",
        password="SuperPassword123!",
        nombres="Carlos",
        apellido_paterno="Admin",
        ci_numero="11223344",
        rol=rol_administrador,
        requiere_cambio_clave=False
    )

@pytest.fixture
def usuario_cajero(db, rol_cajero):
    """Usuario Cajero para pruebas."""
    return Usuario.objects.create_user(
        username="cajero_juan",
        password="CajeroPassword123!",
        nombres="Juan",
        apellido_paterno="Cajero",
        ci_numero="55667788",
        rol=rol_cajero,
        requiere_cambio_clave=False
    )

