"""Pruebas de las vistas Flet con una página simulada (T-05, T-06).

Verifican el contenido construido y el flujo de eventos sin abrir ventana.
"""

from unittest.mock import MagicMock

import pytest

from modules.service_controller import ServiceController
from modules.os_utilities import MSG_SIN_CONEXION
from views.dashboard_view import MSG_SALIR, DashboardView
from views.history_view import MSG_HISTORIAL_VACIO, HistoryView

DATOS_UI = {
    "nombre": "CFE Hogar",
    "categoria": "Electricidad",
    "fecha_limite": "2026-11-15",
    "periodicidad": "Mensual",
    "url_oficial": "https://app.cfe.mx",
    "dias_anticipacion_alerta": "3",
}


@pytest.fixture
def controller():
    ctrl = ServiceController(":memory:")
    ctrl.inicializar()
    yield ctrl
    ctrl.cerrar()


def _textos(control):
    """Recorre el árbol de controles y junta los valores de ft.Text."""
    textos = []
    pendientes = [control]
    while pendientes:
        actual = pendientes.pop()
        if getattr(actual, "value", None) and type(actual).__name__ == "Text":
            textos.append(actual.value)
        for attr in ("content", "controls"):
            hijo = getattr(actual, attr, None)
            if isinstance(hijo, list):
                pendientes.extend(hijo)
            elif hijo is not None:
                pendientes.append(hijo)
    return textos


# --- T-05: HistoryView (RF-06, CA-05.3) ------------------------------------

def test_historial_vacio_muestra_mensaje(controller):
    vista = HistoryView(MagicMock(), controller)

    assert vista.route == "/historial"
    assert MSG_HISTORIAL_VACIO in _textos(vista.controls[0])


def test_historial_lista_pagos_mas_reciente_primero(controller):
    controller.crear_servicio(DATOS_UI)
    servicio_id = controller.listar_servicios()[2][0]["id"]
    controller.marcar_pagado(servicio_id)
    controller.marcar_pagado(servicio_id)

    vista = HistoryView(MagicMock(), controller)

    tarjetas = vista.controls[0].controls
    assert len(tarjetas) == 2
    primera = _textos(tarjetas[0])
    assert "CFE Hogar" in primera and "Pagado" in primera
    assert "Fecha límite cubierta: 2026-12-15" in primera
    assert "Fecha límite cubierta: 2026-11-15" in _textos(tarjetas[1])


# --- T-06: Dashboard con "Marcar pagado" e ícono de historial (RF-03) -----

def _boton(control, texto):
    pendientes = [control]
    while pendientes:
        actual = pendientes.pop()
        if getattr(actual, "text", None) == texto:
            return actual
        for attr in ("content", "controls"):
            hijo = getattr(actual, attr, None)
            if isinstance(hijo, list):
                pendientes.extend(hijo)
            elif hijo is not None:
                pendientes.append(hijo)
    raise AssertionError(f"No se encontró el botón {texto!r}")


def test_icono_historial_navega(controller):
    page = MagicMock()
    vista = DashboardView(page, controller)

    vista.appbar.actions[0].on_click(None)

    page.go.assert_called_once_with("/historial")


def test_marcar_pagado_desde_tarjeta_avanza_fecha(controller):
    controller.crear_servicio(DATOS_UI)
    page = MagicMock()
    vista = DashboardView(page, controller)

    _boton(vista.controls[0], "Marcar pagado").on_click(None)

    textos = _textos(vista.controls[0])
    assert any("Vence: 2026-12-15" in t for t in textos)
    assert len(controller.listar_historial()[2]) == 1
    snack = page.open.call_args[0][0]
    assert "Próximo vencimiento: 2026-12-15" in snack.content.value
    page.update.assert_called()


# --- T-05: "Ir a pagar" con diálogo de confirmación (RF-05) ---------------

def _abrir_dialogo_salida(controller):
    controller.crear_servicio(DATOS_UI)
    page = MagicMock()
    vista = DashboardView(page, controller)
    _boton(vista.controls[0], "Ir a pagar").on_click(None)
    dialogo = page.open.call_args[0][0]
    return page, dialogo


def _accion(dialogo, texto):
    return next(b for b in dialogo.actions if b.text == texto)


def test_ir_a_pagar_muestra_dialogo_ca_03_1(controller):
    page, dialogo = _abrir_dialogo_salida(controller)

    assert dialogo.content.value == MSG_SALIR
    page.launch_url.assert_not_called()


def test_cancelar_no_abre_navegador_ca_03_3(controller):
    page, dialogo = _abrir_dialogo_salida(controller)

    _accion(dialogo, "Cancelar").on_click(None)

    page.close.assert_called_once_with(dialogo)
    page.launch_url.assert_not_called()


def _simular_red(controller, monkeypatch, hay_red):
    original = controller.abrir_portal
    monkeypatch.setattr(
        controller, "abrir_portal",
        lambda sid, lanzador: original(sid, lanzador,
                                       verificar_red=lambda h: hay_red))


def test_continuar_con_red_abre_url_ca_03_1(controller, monkeypatch):
    page, dialogo = _abrir_dialogo_salida(controller)
    _simular_red(controller, monkeypatch, hay_red=True)

    _accion(dialogo, "Continuar").on_click(None)

    page.launch_url.assert_called_once_with("https://app.cfe.mx")


def test_continuar_sin_red_muestra_alerta_ca_03_2(controller, monkeypatch):
    page, dialogo = _abrir_dialogo_salida(controller)
    _simular_red(controller, monkeypatch, hay_red=False)

    _accion(dialogo, "Continuar").on_click(None)

    page.launch_url.assert_not_called()
    alerta = page.open.call_args[0][0]
    assert alerta.content.value == MSG_SIN_CONEXION
