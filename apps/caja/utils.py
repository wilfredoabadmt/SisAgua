import hashlib
import uuid
from decimal import Decimal

UNIDADES = {
    0: '',
    1: 'UN ',
    2: 'DOS ',
    3: 'TRES ',
    4: 'CUATRO ',
    5: 'CINCO ',
    6: 'SEIS ',
    7: 'SIETE ',
    8: 'OCHO ',
    9: 'NUEVE ',
    10: 'DIEZ ',
    11: 'ONCE ',
    12: 'DOCE ',
    13: 'TRECE ',
    14: 'CATORCE ',
    15: 'QUINCE ',
    16: 'DIECISÉIS ',
    17: 'DIECISIETE ',
    18: 'DIECIOCHO ',
    19: 'DIECINUEVE ',
    20: 'VEINTE '
}

DECENAS = {
    2: 'VEINTI',
    3: 'TREINTA ',
    4: 'CUARENTA ',
    5: 'CINCUENTA ',
    6: 'SESENTA ',
    7: 'SETENTA ',
    8: 'OCHENTA ',
    9: 'NOVENTA '
}

CENTENAS = {
    1: 'CIENTO ',
    2: 'DOSCIENTOS ',
    3: 'TRESCIENTOS ',
    4: 'CUATROCIENTOS ',
    5: 'QUINIENTOS ',
    6: 'SEISCIENTOS ',
    7: 'SETECIENTOS ',
    8: 'OCHOCIENTOS ',
    9: 'NOVECIENTOS '
}


def _seccion_a_letras(numero: int) -> str:
    """Convierte un bloque de tres dígitos (0 a 999) a letras."""
    c = numero // 100
    resto = numero % 100
    d = resto // 10
    u = resto % 10

    resultado = ''
    if c > 0:
        if c == 1 and resto == 0:
            return 'CIEN '
        resultado += CENTENAS.get(c, '')

    if resto > 0:
        if resto <= 20:
            resultado += UNIDADES.get(resto, '')
        elif resto < 30:
            if u == 0:
                resultado += 'VEINTE '
            else:
                resultado += 'VEINTI' + UNIDADES.get(u, '')
        else:
            decena_str = DECENAS.get(d, '')
            if u > 0:
                resultado += decena_str + 'Y ' + UNIDADES.get(u, '')
            else:
                resultado += decena_str

    return resultado


def numero_a_letras(numero: int) -> str:
    """Convierte un entero positivo hasta 999,999,999 a letras en mayúsculas."""
    if numero == 0:
        return 'CERO '

    millones = numero // 1_000_000
    miles = (numero % 1_000_000) // 1_000
    unidades = numero % 1_000

    resultado = ''

    if millones > 0:
        if millones == 1:
            resultado += 'UN MILLÓN '
        else:
            resultado += f"{_seccion_a_letras(millones).strip()} MILLONES "

    if miles > 0:
        if miles == 1:
            resultado += 'MIL '
        else:
            resultado += f"{_seccion_a_letras(miles).strip()} MIL "

    if unidades > 0:
        resultado += _seccion_a_letras(unidades)

    return resultado.strip()


def monto_a_literal(monto: Decimal) -> str:
    """
    Convierte un monto decimal a formato literal financiero en bolivianos.
    Ejemplo: Decimal('135.50') -> 'CIENTO TREINTA Y CINCO 50/100 BOLIVIANOS'
    """
    monto_redondeado = round(Decimal(str(monto)), 2)
    entero = int(monto_redondeado)
    centavos = int((monto_redondeado - entero) * 100)

    letras_entero = numero_a_letras(entero)
    return f"{letras_entero} {centavos:02d}/100 BOLIVIANOS"


def generar_codigo_verificacion(numero_recibo: str, socio_codigo: str, monto: Decimal) -> str:
    """
    Genera un hash criptográfico único para verificar la autenticidad del recibo.
    """
    semilla = f"{numero_recibo}:{socio_codigo}:{monto}:{uuid.uuid4().hex}"
    return hashlib.sha256(semilla.encode('utf-8')).hexdigest()[:24].upper()
