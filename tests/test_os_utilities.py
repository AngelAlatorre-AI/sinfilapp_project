"""Pruebas de Utilidades del SO (Incremento 3: RF-04, RF-05)."""

import socket
from datetime import date
from unittest.mock import MagicMock

import pytest

from modules import os_utilities as osu

URL = "https://app.cfe.mx/pagos"


# --- T-02: hay_conexion -----------------------------------------------------

def test_hay_conexion_true_si_el_host_responde(monkeypatch):
    llamadas = []

    def conectar(direccion, timeout):
        llamadas.append((direccion, timeout))
        return MagicMock()

    monkeypatch.setattr(socket, "create_connection", conectar)

    assert osu.hay_conexion("app.cfe.mx") is True
    assert llamadas == [(("app.cfe.mx", 443), 3)]


@pytest.mark.parametrize("error", [OSError("sin red"), socket.timeout()])
def test_hay_conexion_false_sin_red(monkeypatch, error):
    def conectar(direccion, timeout):
        raise error

    monkeypatch.setattr(socket, "create_connection", conectar)

    assert osu.hay_conexion("app.cfe.mx") is False


def test_hay_conexion_false_con_host_invalido():
    assert osu.hay_conexion(None) is False


# --- T-02: abrir_url (CA-03.1, CA-03.2, RNF-03) -----------------------------

def test_abrir_url_con_red_lanza_navegador():
    lanzador = MagicMock()
    hosts = []

    exito, _ = osu.abrir_url(f" {URL} ", lanzador,
                             verificar_red=lambda h: hosts.append(h) or True)

    assert exito is True
    lanzador.assert_called_once_with(URL)
    assert hosts == ["app.cfe.mx"]


def test_abrir_url_sin_red_no_lanza_ca_03_2():
    lanzador = MagicMock()

    exito, mensaje = osu.abrir_url(URL, lanzador,
                                   verificar_red=lambda h: False)

    assert (exito, mensaje) == (False, osu.MSG_SIN_CONEXION)
    lanzador.assert_not_called()


@pytest.mark.parametrize("url", ["http://app.cfe.mx", "app.cfe.mx", "", None])
def test_abrir_url_insegura_no_verifica_red_ni_lanza(url):
    lanzador = MagicMock()
    verificar = MagicMock()

    exito, mensaje = osu.abrir_url(url, lanzador, verificar_red=verificar)

    assert (exito, mensaje) == (False, osu.MSG_URL_INSEGURA)
    verificar.assert_not_called()
    lanzador.assert_not_called()


def test_abrir_url_fallo_del_navegador():
    lanzador = MagicMock(side_effect=RuntimeError("sin navegador"))

    exito, mensaje = osu.abrir_url(URL, lanzador,
                                   verificar_red=lambda h: True)

    assert (exito, mensaje) == (False, osu.MSG_NAVEGADOR)


# --- T-03: Notificador (RF-04, CA-02.1, CA-02.4) ----------------------------

HOY = date(2026, 10, 29)


class EstadoFalso:
    def __init__(self, value):
        self.value = value


@pytest.mark.parametrize(
    "estado, esperado",
    [
        (EstadoFalso("granted"), osu.PERMISO_CONCEDIDO),
        (EstadoFalso("provisional"), osu.PERMISO_CONCEDIDO),
        (EstadoFalso("denied"), osu.PERMISO_DENEGADO),
        (EstadoFalso("permanentlyDenied"), osu.PERMISO_DENEGADO),
        (None, osu.PERMISO_NO_SOPORTADO),
    ],
)
def test_estado_permiso(estado, esperado):
    manejador = MagicMock()
    manejador.check_permission.return_value = estado

    notificador = osu.Notificador(manejador, "notification")

    assert notificador.estado_permiso() == esperado
    manejador.check_permission.assert_called_once_with(
        "notification", wait_timeout=osu.TIEMPO_ESPERA_PERMISO)


def test_sin_manejador_es_no_soportado():
    notificador = osu.Notificador()

    assert notificador.estado_permiso() == osu.PERMISO_NO_SOPORTADO
    assert notificador.solicitar_permiso() == osu.PERMISO_NO_SOPORTADO
    assert notificador.abrir_ajustes() is False


def test_manejador_que_falla_es_no_soportado():
    manejador = MagicMock()
    manejador.check_permission.side_effect = TimeoutError()
    manejador.open_app_settings.side_effect = RuntimeError()

    notificador = osu.Notificador(manejador, "notification")

    assert notificador.estado_permiso() == osu.PERMISO_NO_SOPORTADO
    assert notificador.abrir_ajustes() is False


def test_solicitar_permiso_y_abrir_ajustes():
    manejador = MagicMock()
    manejador.request_permission.return_value = EstadoFalso("granted")
    manejador.open_app_settings.return_value = True

    notificador = osu.Notificador(manejador, "notification")

    assert notificador.solicitar_permiso() == osu.PERMISO_CONCEDIDO
    assert notificador.abrir_ajustes() is True


def _servicio(nombre, fecha, dias=3):
    return {"nombre": nombre, "fecha_limite": fecha,
            "dias_anticipacion_alerta": dias}


def test_alertas_activas_ca_02_1():
    servicios = [
        _servicio("Vencido", "2026-10-28"),           # sin aviso
        _servicio("Hoy", "2026-10-29"),               # vence hoy
        _servicio("Frontera", "2026-11-01"),          # aviso exactamente hoy
        _servicio("Fuera", "2026-11-02"),             # aviso mañana
        _servicio("Siete", "2026-11-05", dias=7),     # aviso hoy con 7 días
        _servicio("Lejano", "2026-11-15"),
    ]

    activas = osu.Notificador.alertas_activas(servicios, HOY)

    assert [s["nombre"] for s in activas] == ["Hoy", "Frontera", "Siete"]


def test_alertas_activas_lista_vacia():
    assert osu.Notificador.alertas_activas([]) == []
