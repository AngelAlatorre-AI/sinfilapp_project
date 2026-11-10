"""Pruebas del ServiceController (T-08, RF-01, RF-02, RNF-05)."""

from datetime import date
from unittest.mock import MagicMock

import pytest

from modules.os_utilities import MSG_SIN_CONEXION
from modules.service_controller import (
    MSG_FECHA_INSUFICIENTE,
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


# --- Incremento 2: marcar_pagado y listar_historial (RF-03, RF-06) ---------

def _registrar(controller, **cambios):
    controller.crear_servicio({**DATOS_UI, **cambios})
    return controller.listar_servicios(HOY)[2][-1]["id"]


def test_pago_tardio_ca_05_1(controller):
    servicio_id = _registrar(controller, fecha_limite="2026-05-15")

    exito, mensaje, servicio = controller.marcar_pagado(
        servicio_id, hoy=date(2026, 5, 20))

    assert exito is True
    assert "2026-06-15" in mensaje
    assert servicio["fecha_limite"] == "2026-06-15"
    assert servicio["estado"] == "Pendiente"
    _, _, historial = controller.listar_historial()
    assert len(historial) == 1
    pago = historial[0]
    assert pago["nombre_servicio_snapshot"] == "CFE Hogar"
    assert pago["fecha_limite_cubierta"] == "2026-05-15"
    assert pago["fecha_pago_realizado"] == "2026-05-20"


def test_fin_de_mes_ca_05_2(controller):
    servicio_id = _registrar(controller, fecha_limite="2027-01-31")

    _, _, servicio = controller.marcar_pagado(servicio_id,
                                              hoy=date(2027, 1, 30))

    assert servicio["fecha_limite"] == "2027-02-28"


def test_bisiesto_anual_ca_05_2(controller):
    servicio_id = _registrar(controller, fecha_limite="2028-02-29",
                             periodicidad="Anual")

    _, _, servicio = controller.marcar_pagado(servicio_id,
                                              hoy=date(2028, 2, 29))

    assert servicio["fecha_limite"] == "2029-02-28"


def test_estado_calculado_tras_pago_muy_atrasado(controller):
    servicio_id = _registrar(controller, fecha_limite="2026-05-15")

    _, _, servicio = controller.marcar_pagado(servicio_id,
                                              hoy=date(2026, 7, 20))

    # Decisión del equipo: no se fuerza "Pendiente"; se muestra el real.
    assert servicio["fecha_limite"] == "2026-06-15"
    assert servicio["estado"] == "Vencido"


def test_pago_adelantado_permitido(controller):
    servicio_id = _registrar(controller, fecha_limite="2026-12-15")

    exito, _, servicio = controller.marcar_pagado(servicio_id, hoy=HOY)

    assert exito is True
    assert servicio["fecha_limite"] == "2027-01-15"


def test_marcar_pagado_inexistente(controller):
    exito, mensaje, datos = controller.marcar_pagado(999, hoy=HOY)

    assert (exito, mensaje, datos) == (False, "El servicio no existe.", None)
    assert controller.listar_historial()[2] == []


def test_historial_vacio_ca_05_3(controller):
    exito, _, historial = controller.listar_historial()

    assert exito is True and historial == []


def test_historial_conserva_snapshot_tras_eliminar_rf_06(controller):
    servicio_id = _registrar(controller)
    controller.marcar_pagado(servicio_id, hoy=HOY)
    controller.actualizar_servicio(servicio_id,
                                   {**DATOS_UI, "nombre": "CFE Renombrado"})

    controller.eliminar_servicio(servicio_id)

    _, _, historial = controller.listar_historial()
    assert len(historial) == 1
    assert historial[0]["nombre_servicio_snapshot"] == "CFE Hogar"
    assert historial[0]["servicio_id"] is None


def test_fallo_de_bd_al_registrar_pago(controller, monkeypatch):
    servicio_id = _registrar(controller, fecha_limite="2026-11-15")
    monkeypatch.setattr(
        controller._db, "registrar_pago",
        lambda *args: (False, "Error al registrar el pago: disco lleno"))

    exito, mensaje, datos = controller.marcar_pagado(servicio_id, hoy=HOY)

    assert exito is False and "disco lleno" in mensaje and datos is None
    assert controller.obtener_servicio(servicio_id)[2]["fecha_limite"] == (
        "2026-11-15")


# --- Incremento 3: alertas, permisos y portal (RF-04, RF-05) ---------------

def test_fecha_insuficiente_advierte_sin_bloquear_ca_02_2(controller):
    exito, mensaje, errores = controller.crear_servicio(
        {**DATOS_UI, "fecha_limite": "2026-10-30"}, hoy=HOY)

    assert exito is True and errores == {}
    assert MSG_FECHA_INSUFICIENTE in mensaje
    assert len(controller.listar_servicios(HOY)[2]) == 1


def test_sin_advertencia_con_fecha_suficiente(controller):
    _, mensaje, _ = controller.crear_servicio(DATOS_UI, hoy=HOY)

    assert MSG_FECHA_INSUFICIENTE not in mensaje


def test_sin_advertencia_para_servicio_vencido(controller):
    _, mensaje, _ = controller.crear_servicio(
        {**DATOS_UI, "fecha_limite": "2026-10-01"}, hoy=HOY)

    assert MSG_FECHA_INSUFICIENTE not in mensaje


def test_actualizar_con_fecha_insuficiente_advierte(controller):
    servicio_id = _registrar(controller)

    exito, mensaje, _ = controller.actualizar_servicio(
        servicio_id, {**DATOS_UI, "fecha_limite": "2026-10-29",
                      "dias_anticipacion_alerta": "7"}, hoy=HOY)

    assert exito is True and MSG_FECHA_INSUFICIENTE in mensaje


def test_alertas_del_dia_ca_02_1(controller):
    _registrar(controller, nombre="Lejano", fecha_limite="2026-11-15")
    _registrar(controller, nombre="Pronto", fecha_limite="2026-11-01")
    _registrar(controller, nombre="Vencido", fecha_limite="2026-10-01")

    _, _, alertas = controller.alertas_del_dia(HOY)

    assert [a["nombre"] for a in alertas] == ["Pronto"]
    assert alertas[0]["estado"] == "Próximo a vencer"


def test_permisos_delegan_en_notificador():
    notificador = MagicMock()
    notificador.estado_permiso.return_value = "denegado"
    notificador.solicitar_permiso.return_value = "concedido"
    notificador.abrir_ajustes.return_value = False
    ctrl = ServiceController(":memory:", notificador=notificador)

    assert ctrl.estado_notificaciones() == (True, "", "denegado")
    assert ctrl.solicitar_permiso_notificaciones()[2] == "concedido"
    assert ctrl.abrir_ajustes_notificaciones()[0] is False
    ctrl.cerrar()


def test_permiso_no_soportado_por_defecto(controller):
    assert controller.estado_notificaciones()[2] == "no_soportado"


def test_abrir_portal_con_red_ca_03_1(controller):
    servicio_id = _registrar(controller)
    lanzador = MagicMock()

    exito, _, _ = controller.abrir_portal(servicio_id, lanzador,
                                          verificar_red=lambda h: True)

    assert exito is True
    lanzador.assert_called_once_with("https://app.cfe.mx")


def test_abrir_portal_sin_red_ca_03_2(controller):
    servicio_id = _registrar(controller)
    lanzador = MagicMock()

    exito, mensaje, _ = controller.abrir_portal(
        servicio_id, lanzador, verificar_red=lambda h: False)

    assert (exito, mensaje) == (False, MSG_SIN_CONEXION)
    lanzador.assert_not_called()


def test_abrir_portal_inexistente(controller):
    lanzador = MagicMock()

    exito, mensaje, _ = controller.abrir_portal(999, lanzador)

    assert exito is False and "no existe" in mensaje
    lanzador.assert_not_called()


# --- refactor-historial: filtros (RF-06.1) ---------------------------------

@pytest.fixture
def controller_con_pagos(controller):
    """CFE pagado en oct y nov; Agua en nov y luego eliminado."""
    cfe = _registrar(controller, nombre="CFE Hogar",
                     fecha_limite="2026-10-15")
    agua = _registrar(controller, nombre="Agua", fecha_limite="2026-11-20")
    controller.marcar_pagado(cfe, hoy=date(2026, 10, 14))
    controller.marcar_pagado(cfe, hoy=date(2026, 11, 14))
    controller.marcar_pagado(agua, hoy=date(2026, 11, 18))
    controller.eliminar_servicio(agua)
    return controller


def test_opciones_filtros_historial(controller_con_pagos):
    exito, _, opciones = controller_con_pagos.opciones_filtros_historial()

    assert exito is True
    assert opciones == {
        "meses": [("2026-11", "Noviembre 2026"),
                  ("2026-10", "Octubre 2026")],
        "servicios": ["Agua", "CFE Hogar"],
    }


def test_opciones_filtros_sin_historial(controller):
    _, _, opciones = controller.opciones_filtros_historial()

    assert opciones == {"meses": [], "servicios": []}


def test_listar_historial_por_mes(controller_con_pagos):
    _, mensaje, pagos = controller_con_pagos.listar_historial(
        anio_mes="2026-11")

    assert [p["nombre_servicio_snapshot"] for p in pagos] == [
        "Agua", "CFE Hogar"]
    assert mensaje == "2 pago(s)."


def test_listar_historial_por_servicio_eliminado(controller_con_pagos):
    _, _, pagos = controller_con_pagos.listar_historial(servicio="Agua")

    assert len(pagos) == 1 and pagos[0]["servicio_id"] is None


def test_listar_historial_combinado_sin_resultados(controller_con_pagos):
    exito, _, pagos = controller_con_pagos.listar_historial(
        anio_mes="2026-10", servicio="Agua")

    assert exito is True and pagos == []


@pytest.mark.parametrize("servicio", [None, ""])
def test_servicio_vacio_equivale_a_todos(controller_con_pagos, servicio):
    _, _, pagos = controller_con_pagos.listar_historial(
        anio_mes="2026-11", servicio=servicio)

    assert len(pagos) == 2


@pytest.mark.parametrize("mes", ["2026-13", "noviembre", "2026-11-01", ""])
def test_mes_invalido_no_consulta_la_bd(controller_con_pagos, mes,
                                        monkeypatch):
    leer = MagicMock()
    monkeypatch.setattr(controller_con_pagos._db, "leer_historial", leer)

    exito, mensaje, pagos = controller_con_pagos.listar_historial(
        anio_mes=mes)

    assert (exito, pagos) == (False, [])
    assert "Mes inválido" in mensaje
    leer.assert_not_called()
