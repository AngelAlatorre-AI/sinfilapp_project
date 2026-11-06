"""Pruebas de Utilidades del SO (Incremento 3: RF-04, RF-05)."""

import socket
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
