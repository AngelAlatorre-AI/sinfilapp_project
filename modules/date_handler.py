"""Fechas ISO 8601: estados (RF-02), ciclos (RF-03) y alertas (RF-04)."""

import calendar
import re
from datetime import date, timedelta

_PATRON_ISO = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")

PENDIENTE = "Pendiente"
PROXIMO = "Próximo a vencer"
VENCIDO = "Vencido"

MESES_POR_PERIODO = {"MENSUAL": 1, "BIMESTRAL": 2, "ANUAL": 12}


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


def sumar_periodo(fecha_limite, periodicidad):
    """Avanza la fecha límite cubierta un periodo (RF-03, CA-05.2).

    Si el día no existe en el mes destino se usa el último día válido
    (31/ene + 1 mes = 28 o 29/feb). Retorna 'YYYY-MM-DD'.
    """
    meses = MESES_POR_PERIODO.get(str(periodicidad).upper())
    if meses is None:
        raise ValueError(f"Periodicidad desconocida: {periodicidad!r}")
    fecha = parsear_fecha(fecha_limite)
    indice_mes = fecha.month - 1 + meses
    anio = fecha.year + indice_mes // 12
    mes = indice_mes % 12 + 1
    dia = min(fecha.day, calendar.monthrange(anio, mes)[1])
    return date(anio, mes, dia).isoformat()


def calcular_fecha_alerta(fecha_limite, dias_alerta, hoy=None):
    """Fecha en que debe avisarse al usuario (RF-04, CA-02.1, CA-02.2).

    Retorna (fecha_alerta 'YYYY-MM-DD' | None, insuficiente: bool):
    - Servicio vencido: (None, False); no se avisa ni se advierte.
    - Si faltan menos días que dias_alerta: (hoy, True), es decir,
      "Fecha insuficiente para los días marcados" y aviso el mismo día.
    - En otro caso: (fecha_limite - dias_alerta, False).
    """
    hoy = hoy or date.today()
    limite = parsear_fecha(fecha_limite)
    if limite < hoy:
        return None, False
    alerta = limite - timedelta(days=int(dias_alerta))
    if alerta < hoy:
        return hoy.isoformat(), True
    return alerta.isoformat(), False
