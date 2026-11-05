"""Validación de fechas ISO 8601 y cálculo de estados (T-03, RF-02).

La suma de periodos (RF-03) se implementará en el Incremento 2.
"""

import re
from datetime import date

_PATRON_ISO = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")

PENDIENTE = "Pendiente"
PROXIMO = "Próximo a vencer"
VENCIDO = "Vencido"


def parsear_fecha(texto):
    """Convierte 'YYYY-MM-DD' en date. Lanza ValueError si es inválida."""
    if not isinstance(texto, str) or not _PATRON_ISO.match(texto.strip()):
        raise ValueError(f"Fecha inválida (use YYYY-MM-DD): {texto!r}")
    return date.fromisoformat(texto.strip())


def es_fecha_valida(texto):
    """True si el texto es una fecha real en formato estricto YYYY-MM-DD."""
    try:
        parsear_fecha(texto)
        return True
    except ValueError:
        return False


def dias_restantes(fecha_limite, hoy=None):
    """Días entre hoy y la fecha límite (negativo si ya pasó)."""
    hoy = hoy or date.today()
    return (parsear_fecha(fecha_limite) - hoy).days


def calcular_estado(fecha_limite, dias_alerta, hoy=None):
    """Clasifica un servicio según RF-02.

    - Vencido: la fecha límite ya pasó (día siguiente o más).
    - Próximo a vencer: faltan entre 0 (vence hoy) y dias_alerta días.
    - Pendiente: faltan más días que los configurados.
    """
    restantes = dias_restantes(fecha_limite, hoy)
    if restantes < 0:
        return VENCIDO
    if restantes <= dias_alerta:
        return PROXIMO
    return PENDIENTE
