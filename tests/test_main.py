"""Pruebas del cableado de main.py (T-06, RF-04)."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import flet as ft
import pytest

import main as app
from modules.os_utilities import PERMISO_NO_SOPORTADO


def test_id_desde_ruta():
    assert app.id_desde_ruta("/form/12") == 12
    assert app.id_desde_ruta("/form") is None


def test_escritorio_no_usa_permission_handler():
    page = MagicMock()
    page.platform = ft.PagePlatform.WINDOWS

    notificador = app.crear_notificador(page)

    assert notificador.estado_permiso() == PERMISO_NO_SOPORTADO
    page.overlay.append.assert_not_called()


def test_movil_agrega_permission_handler_al_overlay():
    page = MagicMock()
    page.platform = ft.PagePlatform.ANDROID

    app.crear_notificador(page)

    manejador = page.overlay.append.call_args[0][0]
    assert isinstance(manejador, ft.PermissionHandler)


@pytest.mark.parametrize("estado, solicita", [
    ("denegado", True), ("concedido", False), ("no_soportado", False)])
def test_pedir_permiso_si_falta(estado, solicita):
    controller = MagicMock()
    controller.estado_notificaciones.return_value = (True, "", estado)

    app.pedir_permiso_si_falta(controller)

    assert controller.solicitar_permiso_notificaciones.called is solicita


@pytest.mark.parametrize("estado, ruta, refresca", [
    (ft.AppLifecycleState.RESUME, "/", True),
    (ft.AppLifecycleState.SHOW, "/", True),
    (ft.AppLifecycleState.PAUSE, "/", False),
    (ft.AppLifecycleState.RESUME, "/form", False),
])
def test_refrescar_al_volver(estado, ruta, refresca):
    dashboard = MagicMock()
    page = MagicMock(route=ruta, views=[dashboard])

    app.refrescar_al_volver(page, SimpleNamespace(state=estado))

    assert dashboard.refrescar.called is refresca
    assert page.update.called is refresca
