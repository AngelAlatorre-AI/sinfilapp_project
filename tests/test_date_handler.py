"""Pruebas de DateHandler (estados RF-02) y UrlValidator (RNF-03) (T-04)."""

from datetime import date

import pytest

from modules import date_handler as dh
from modules.url_validator import es_url_segura

HOY = date(2026, 10, 29)


# --- Validación de fechas ISO 8601 -----------------------------------------

@pytest.mark.parametrize("texto", ["2026-10-29", "2024-02-29", " 2026-01-01 "])
def test_fecha_iso_valida(texto):
    assert dh.es_fecha_valida(texto) is True


@pytest.mark.parametrize(
    "texto",
    ["29/10/2026", "2026-13-01", "2025-02-29", "20261029", "2026-W44-4",
     "", None, "mañana"],
)
def test_fecha_invalida_rechazada(texto):
    assert dh.es_fecha_valida(texto) is False


def test_parsear_fecha_invalida_lanza_value_error():
    with pytest.raises(ValueError):
        dh.parsear_fecha("2026/10/29")


# --- Días restantes y estados (CA-04.1, CA-04.2) ---------------------------

def test_dias_restantes():
    assert dh.dias_restantes("2026-10-31", HOY) == 2
    assert dh.dias_restantes("2026-10-28", HOY) == -1


def test_dias_restantes_usa_hoy_por_defecto():
    assert dh.dias_restantes(date.today().isoformat()) == 0


@pytest.mark.parametrize(
    "fecha, dias_alerta, esperado",
    [
        ("2026-10-28", 3, dh.VENCIDO),    # ayer (CA-04.1)
        ("2026-10-29", 1, dh.PROXIMO),    # vence HOY: 0 días (CA-04.2)
        ("2026-10-31", 3, dh.PROXIMO),    # 2 días, dentro del umbral
        ("2026-11-01", 3, dh.PROXIMO),    # frontera exacta: 3 días
        ("2026-11-02", 3, dh.PENDIENTE),  # 4 días, fuera del umbral
        ("2026-11-05", 7, dh.PROXIMO),    # 7 días con alerta máxima
        ("2026-11-15", 7, dh.PENDIENTE),  # lejano
    ],
)
def test_calcular_estado(fecha, dias_alerta, esperado):
    assert dh.calcular_estado(fecha, dias_alerta, HOY) == esperado


# --- Suma de periodos (RF-03, CA-05.1, CA-05.2) ---------------------------

@pytest.mark.parametrize(
    "fecha, periodicidad, esperado",
    [
        ("2026-05-15", "MENSUAL", "2026-06-15"),    # CA-05.1
        ("2027-01-31", "MENSUAL", "2027-02-28"),    # fin de mes
        ("2028-01-31", "MENSUAL", "2028-02-29"),    # fin de mes bisiesto
        ("2026-03-31", "MENSUAL", "2026-04-30"),    # "30 de abril"
        ("2024-02-29", "ANUAL", "2025-02-28"),      # bisiesto anual
        ("2026-12-31", "BIMESTRAL", "2027-02-28"),  # cambio de año
        ("2026-11-15", "BIMESTRAL", "2027-01-15"),
        ("2026-12-15", "MENSUAL", "2027-01-15"),
        ("2026-05-15", "Mensual", "2026-06-15"),    # etiqueta de la UI
    ],
)
def test_sumar_periodo(fecha, periodicidad, esperado):
    assert dh.sumar_periodo(fecha, periodicidad) == esperado


@pytest.mark.parametrize(
    "fecha, periodicidad",
    [("2026-05-15", "SEMANAL"), ("2026-05-15", None),
     ("15/05/2026", "MENSUAL")],
)
def test_sumar_periodo_invalido_lanza_value_error(fecha, periodicidad):
    with pytest.raises(ValueError):
        dh.sumar_periodo(fecha, periodicidad)


# --- UrlValidator (RNF-03, CA-01.2) ----------------------------------------

@pytest.mark.parametrize(
    "url",
    ["https://app.cfe.mx", "https://www.sapal.gob.mx/pagos?id=1",
     " https://telmex.com/ "],
)
def test_url_https_aceptada(url):
    assert es_url_segura(url) is True


@pytest.mark.parametrize(
    "url",
    ["http://app.cfe.mx", "app.cfe.mx", "texto plano", "https://",
     "https://sin-punto", "https://app cfe.mx", "ftp://cfe.mx",
     "HTTPS//cfe.mx", "", None],
)
def test_url_insegura_rechazada(url):
    assert es_url_segura(url) is False
