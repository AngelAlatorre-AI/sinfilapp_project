"""Pruebas del ServiceController (T-08, RF-01, RF-02, RNF-05)."""

from datetime import date

import pytest

from modules.service_controller import (
    MSG_REQUERIDO,
    MSG_URL,
    ServiceController,
)

HOY = date(2026, 10, 29)

DATOS_UI = {
    "nombre": "  CFE Hogar ",
    "categoria": "Electricidad",
    "fecha_limite": "2026-11-15",
    "periodicidad": "Mensual",
    "url_oficial": "https://app.cfe.mx",
    "dias_anticipacion_alerta": "3",
}


@pytest.fixture
def controller():
    ctrl = ServiceController(":memory:")
    exito, mensaje, _ = ctrl.inicializar()
    assert exito, mensaje
    yield ctrl
    ctrl.cerrar()


def test_crear_normaliza_y_lista(controller):
    exito, _, errores = controller.crear_servicio(DATOS_UI)

    assert exito is True and errores == {}
    _, _, servicios = controller.listar_servicios(HOY)
    assert len(servicios) == 1
    servicio = servicios[0]
    assert servicio["nombre"] == "CFE Hogar"
    assert servicio["periodicidad"] == "Mensual"
    assert servicio["dias_anticipacion_alerta"] == 3
    assert servicio["estado"] == "Pendiente"
    assert servicio["dias_restantes"] == 17


def test_url_http_rechazada_ca_01_2(controller):
    datos = {**DATOS_UI, "url_oficial": "http://app.cfe.mx"}

    exito, _, errores = controller.crear_servicio(datos)

    assert exito is False
    assert errores == {"url_oficial": MSG_URL}
    assert controller.listar_servicios(HOY)[2] == []


def test_campos_vacios_marcados_ca_01_3(controller):
    datos = {**DATOS_UI, "nombre": "   ", "categoria": None}

    exito, mensaje, errores = controller.crear_servicio(datos)

    assert exito is False
    assert "requeridos" in mensaje
    assert errores == {"nombre": MSG_REQUERIDO, "categoria": MSG_REQUERIDO}
    assert controller.listar_servicios(HOY)[2] == []


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("dias_anticipacion_alerta", "0"),
        ("dias_anticipacion_alerta", "8"),
        ("dias_anticipacion_alerta", "tres"),
        ("fecha_limite", "15/11/2026"),
        ("periodicidad", "Semanal"),
        ("categoria", "Luz"),
    ],
)
def test_valores_fuera_de_catalogo_o_rango(controller, campo, valor):
    exito, _, errores = controller.crear_servicio({**DATOS_UI, campo: valor})

    assert exito is False
    assert list(errores) == [campo]


def test_listado_ordenado_con_semaforo_ca_04_2(controller):
    for nombre, fecha in [("Lejano", "2026-11-15"), ("Hoy", "2026-10-29"),
                          ("Ayer", "2026-10-28"), ("Dos", "2026-10-31")]:
        controller.crear_servicio(
            {**DATOS_UI, "nombre": nombre, "fecha_limite": fecha})

    _, _, servicios = controller.listar_servicios(HOY)

    assert [(s["nombre"], s["estado"]) for s in servicios] == [
        ("Ayer", "Vencido"),
        ("Hoy", "Próximo a vencer"),
        ("Dos", "Próximo a vencer"),
        ("Lejano", "Pendiente"),
    ]


def test_editar_y_eliminar_ca_01_4(controller):
    controller.crear_servicio(DATOS_UI)
    servicio_id = controller.listar_servicios(HOY)[2][0]["id"]

    exito, _, _ = controller.actualizar_servicio(
        servicio_id, {**DATOS_UI, "periodicidad": "Anual",
                      "fecha_limite": "2026-10-30"})
    assert exito is True
    _, _, editado = controller.obtener_servicio(servicio_id)
    assert editado["periodicidad"] == "Anual"
    assert editado["fecha_limite"] == "2026-10-30"

    exito, _, _ = controller.eliminar_servicio(servicio_id)
    assert exito is True
    assert controller.obtener_servicio(servicio_id)[0] is False
    assert controller.listar_servicios(HOY)[2] == []


def test_actualizar_invalido_no_modifica(controller):
    controller.crear_servicio(DATOS_UI)
    servicio_id = controller.listar_servicios(HOY)[2][0]["id"]

    exito, _, errores = controller.actualizar_servicio(
        servicio_id, {**DATOS_UI, "url_oficial": "http://x.mx"})

    assert exito is False and "url_oficial" in errores
    assert controller.obtener_servicio(servicio_id)[2]["url_oficial"] == (
        "https://app.cfe.mx")


def test_eliminar_inexistente(controller):
    exito, mensaje, _ = controller.eliminar_servicio(999)

    assert exito is False and "no existe" in mensaje
