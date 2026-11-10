"""Pruebas de CRUD local y snapshot en base de datos SQLite (T-07).

Cubre CA-01.1 (alta exitosa), CA-01.3 / restricciones CHECK (rechazo de
datos inválidos) y CA-01.4 (borrado físico conservando historial_pagos).
"""

import sqlite3
from contextlib import closing

import pytest

from database.db_manager import DBManager

SERVICIO_VALIDO = {
    "nombre": "CFE Hogar",
    "categoria": "Electricidad",
    "fecha_limite": "2026-11-15",
    "periodicidad": "MENSUAL",
    "url_oficial": "https://app.cfe.mx",
    "dias_anticipacion_alerta": 3,
}


@pytest.fixture
def db_path(tmp_path):
    """Ruta a un archivo .db temporal que se elimina al terminar el test."""
    ruta = tmp_path / "sinfilapp_test.db"
    yield ruta
    ruta.unlink(missing_ok=True)


@pytest.fixture
def db(db_path):
    """DBManager con las tablas servicios e historial_pagos creadas."""
    manager = DBManager(str(db_path))
    exito, mensaje = manager.inicializar_bd()
    assert exito, mensaje
    return manager


def contar_servicios(db_path):
    with closing(sqlite3.connect(db_path)) as conexion:
        consulta = "SELECT COUNT(*) FROM servicios"
        return conexion.execute(consulta).fetchone()[0]


# --- CA-01.1: caso normal --------------------------------------------------

def test_crear_servicio_valido_se_guarda_y_se_lee(db):
    exito, mensaje = db.crear_servicio(SERVICIO_VALIDO)

    assert exito is True, mensaje
    servicios = db.leer_servicios()
    assert len(servicios) == 1
    guardado = servicios[0]
    assert guardado["id"] == 1
    for campo, valor in SERVICIO_VALIDO.items():
        assert guardado[campo] == valor


# --- CA-01.3 / CHECK: casos de error ---------------------------------------

@pytest.mark.parametrize(
    "campo, valor_invalido",
    [
        ("nombre", None),               # NOT NULL
        ("periodicidad", "Mensual"),    # CHECK catálogo en mayúsculas
        ("categoria", "Luz"),           # CHECK catálogo cerrado
        ("dias_anticipacion_alerta", 8),  # CHECK rango 1 a 7
        ("dias_anticipacion_alerta", 0),  # CHECK rango 1 a 7
    ],
)
def test_crear_servicio_invalido_retorna_false_sin_excepcion(
    db, db_path, campo, valor_invalido
):
    datos = {**SERVICIO_VALIDO, campo: valor_invalido}

    exito, mensaje = db.crear_servicio(datos)

    assert exito is False
    assert "Error al registrar el servicio" in mensaje
    assert contar_servicios(db_path) == 0


# --- CA-01.4: caso límite, borrado físico e integridad ---------------------

def test_eliminar_servicio_conserva_historial_con_servicio_id_null(
    db, db_path
):
    db.crear_servicio(SERVICIO_VALIDO)
    servicio_id = db.leer_servicios()[0]["id"]
    with sqlite3.connect(db_path) as conexion:
        conexion.execute(
            "INSERT INTO historial_pagos (servicio_id, "
            "nombre_servicio_snapshot, fecha_pago_realizado, "
            "fecha_limite_cubierta) VALUES (?, ?, ?, ?)",
            (servicio_id, "CFE Hogar", "2026-10-18", "2026-10-15"),
        )
    conexion.close()

    exito, mensaje = db.eliminar_servicio(servicio_id)

    assert exito is True, mensaje
    assert db.leer_servicio(servicio_id) is None
    assert contar_servicios(db_path) == 0
    with sqlite3.connect(db_path) as conexion:
        historial = conexion.execute(
            "SELECT servicio_id, nombre_servicio_snapshot, "
            "fecha_pago_realizado, fecha_limite_cubierta "
            "FROM historial_pagos"
        ).fetchall()
    conexion.close()
    assert historial == [(None, "CFE Hogar", "2026-10-18", "2026-10-15")]


# --- Incremento 2: registrar_pago y leer_historial (RF-03, RF-06) ----------

def _servicio_registrado(db):
    db.crear_servicio(SERVICIO_VALIDO)
    return db.leer_servicios()[0]["id"]


def test_registrar_pago_guarda_historial_y_avanza_fecha(db):
    servicio_id = _servicio_registrado(db)

    exito, mensaje = db.registrar_pago(
        servicio_id, "CFE Hogar", "2026-11-15", "2026-11-20", "2026-12-15")

    assert exito is True, mensaje
    assert db.leer_servicio(servicio_id)["fecha_limite"] == "2026-12-15"
    historial = db.leer_historial()
    assert len(historial) == 1
    assert historial[0]["servicio_id"] == servicio_id
    assert historial[0]["nombre_servicio_snapshot"] == "CFE Hogar"
    assert historial[0]["fecha_limite_cubierta"] == "2026-11-15"
    assert historial[0]["fecha_pago_realizado"] == "2026-11-20"


def test_registrar_pago_servicio_inexistente_no_escribe(db):
    exito, mensaje = db.registrar_pago(
        999, "Fantasma", "2026-11-15", "2026-11-20", "2026-12-15")

    assert exito is False and "no existe" in mensaje
    assert db.leer_historial() == []


def test_registrar_pago_fallido_revierte_la_fecha(db):
    servicio_id = _servicio_registrado(db)

    # nombre_snapshot=None viola NOT NULL en el INSERT, que ocurre después
    # del UPDATE: la transacción completa debe revertirse.
    exito, mensaje = db.registrar_pago(
        servicio_id, None, "2026-11-15", "2026-11-20", "2026-12-15")

    assert exito is False and "Error al registrar el pago" in mensaje
    assert db.leer_servicio(servicio_id)["fecha_limite"] == "2026-11-15"
    assert db.leer_historial() == []


def test_leer_historial_vacio(db):
    assert db.leer_historial() == []


def test_leer_historial_mas_reciente_primero(db):
    servicio_id = _servicio_registrado(db)
    db.registrar_pago(servicio_id, "CFE Hogar", "2026-11-15", "2026-11-14",
                      "2026-12-15")
    db.registrar_pago(servicio_id, "CFE Hogar", "2026-12-15", "2026-12-20",
                      "2027-01-15")

    historial = db.leer_historial()

    assert [p["fecha_limite_cubierta"] for p in historial] == [
        "2026-12-15", "2026-11-15"]


def test_historial_sobrevive_al_borrado_del_servicio(db):
    servicio_id = _servicio_registrado(db)
    db.registrar_pago(servicio_id, "CFE Hogar", "2026-11-15", "2026-11-20",
                      "2026-12-15")

    db.eliminar_servicio(servicio_id)

    historial = db.leer_historial()
    assert len(historial) == 1
    assert historial[0]["servicio_id"] is None
    assert historial[0]["nombre_servicio_snapshot"] == "CFE Hogar"


def test_registrar_pago_en_memoria_revierte_sin_dejar_pendientes():
    manager = DBManager(":memory:")
    manager.inicializar_bd()
    servicio_id = _servicio_registrado(manager)

    manager.registrar_pago(servicio_id, None, "2026-11-15", "2026-11-20",
                           "2026-12-15")
    manager.crear_servicio({**SERVICIO_VALIDO, "nombre": "Agua"})

    assert manager.leer_servicio(servicio_id)["fecha_limite"] == "2026-11-15"
    assert manager.leer_historial() == []
    manager.cerrar()


# --- refactor-historial: filtros en SQLite (RF-06.1) ------------------------

PAGOS_FILTRO = [
    # (servicio, fecha_limite_cubierta, fecha_pago_realizado)
    ("CFE Hogar", "2026-09-15", "2026-09-14"),
    ("CFE Hogar", "2026-10-15", "2026-10-31"),
    ("Agua", "2026-10-20", "2026-10-18"),
    ("Agua", "2026-11-20", "2026-11-01"),
    ("Netflix", "2026-11-05", "2026-11-05"),
]
CATEGORIA = {
    "CFE Hogar": "Electricidad",
    "Agua": "Agua",
    "Netflix": "Streaming / Entretenimiento",
}


@pytest.fixture
def db_con_pagos(db):
    """Historial con pagos de 3 categorías en septiembre a noviembre."""
    ids = {}
    for nombre, categoria in CATEGORIA.items():
        db.crear_servicio({**SERVICIO_VALIDO, "nombre": nombre,
                           "categoria": categoria})
        ids[nombre] = max(s["id"] for s in db.leer_servicios())
    for nombre, cubierta, pagado in PAGOS_FILTRO:
        db.registrar_pago(ids[nombre], nombre, cubierta, pagado, "2027-01-01",
                          categoria_snapshot=CATEGORIA[nombre])
    return db, ids


def _resumen(pagos):
    return [(p["nombre_servicio_snapshot"], p["fecha_pago_realizado"])
            for p in pagos]


def test_registrar_pago_guarda_categoria_snapshot(db_con_pagos):
    db, _ = db_con_pagos

    categorias = {p["nombre_servicio_snapshot"]: p["categoria_snapshot"]
                  for p in db.leer_historial()}

    assert categorias == CATEGORIA


def test_historial_sin_filtros_trae_todo(db_con_pagos):
    db, _ = db_con_pagos

    assert len(db.leer_historial()) == 5
    assert db.leer_historial(None, None) == db.leer_historial()


def test_filtrar_por_mes_respeta_frontera(db_con_pagos):
    db, _ = db_con_pagos

    octubre = db.leer_historial(anio_mes="2026-10")
    noviembre = db.leer_historial(anio_mes="2026-11")

    assert _resumen(octubre) == [("CFE Hogar", "2026-10-31"),
                                 ("Agua", "2026-10-18")]
    assert _resumen(noviembre) == [("Netflix", "2026-11-05"),
                                   ("Agua", "2026-11-01")]


def test_filtrar_por_mes_usa_fecha_de_pago_no_la_cubierta(db_con_pagos):
    db, _ = db_con_pagos

    # El ciclo de CFE con fecha límite 2026-10-15 se pagó en octubre;
    # el de Agua con fecha límite 2026-11-20 se pagó el 2026-11-01.
    septiembre = db.leer_historial(anio_mes="2026-09")

    assert _resumen(septiembre) == [("CFE Hogar", "2026-09-14")]


def test_filtrar_por_categoria(db_con_pagos):
    db, _ = db_con_pagos

    agua = db.leer_historial(categoria="Agua")

    assert _resumen(agua) == [("Agua", "2026-11-01"), ("Agua", "2026-10-18")]


def test_categoria_agrupa_servicios_de_distinto_nombre(db_con_pagos):
    db, ids = db_con_pagos
    db.crear_servicio({**SERVICIO_VALIDO, "nombre": "CFE Oficina"})
    oficina = max(s["id"] for s in db.leer_servicios())
    db.registrar_pago(oficina, "CFE Oficina", "2026-10-01", "2026-10-02",
                      "2026-11-01", categoria_snapshot="Electricidad")

    luz = db.leer_historial(anio_mes="2026-10", categoria="Electricidad")

    assert _resumen(luz) == [("CFE Hogar", "2026-10-31"),
                             ("CFE Oficina", "2026-10-02")]


def test_filtros_combinados(db_con_pagos):
    db, _ = db_con_pagos

    pagos = db.leer_historial(anio_mes="2026-10", categoria="Agua")

    assert _resumen(pagos) == [("Agua", "2026-10-18")]


def test_combinacion_sin_resultados(db_con_pagos):
    db, _ = db_con_pagos

    assert db.leer_historial(anio_mes="2026-09",
                             categoria="Streaming / Entretenimiento") == []


def test_filtro_por_categoria_incluye_eliminados(db_con_pagos):
    db, ids = db_con_pagos

    db.eliminar_servicio(ids["Netflix"])

    pagos = db.leer_historial(categoria="Streaming / Entretenimiento")
    assert _resumen(pagos) == [("Netflix", "2026-11-05")]
    assert pagos[0]["servicio_id"] is None
    assert "Streaming / Entretenimiento" in db.leer_categorias_historial()


def test_categoria_snapshot_no_cambia_al_editar_el_servicio(db_con_pagos):
    db, ids = db_con_pagos

    db.actualizar_servicio(ids["Agua"], {**SERVICIO_VALIDO, "nombre": "Agua",
                                         "categoria": "Otro"})

    assert len(db.leer_historial(categoria="Agua")) == 2
    assert db.leer_historial(categoria="Otro") == []


def test_filtro_resistente_a_inyeccion_sql(db_con_pagos):
    db, _ = db_con_pagos

    assert db.leer_historial(categoria="x' OR '1'='1") == []
    assert db.leer_historial(anio_mes="2026-10' OR '1'='1") == []
    assert len(db.leer_historial()) == 5


def test_opciones_de_meses_sin_repetir_y_recientes_primero(db_con_pagos):
    db, _ = db_con_pagos

    assert db.leer_meses_historial() == ["2026-11", "2026-10", "2026-09"]


def test_opciones_de_categorias_sin_repetir(db_con_pagos):
    db, _ = db_con_pagos

    assert sorted(db.leer_categorias_historial()) == sorted(
        CATEGORIA.values())


def test_opciones_vacias_sin_historial(db):
    assert db.leer_meses_historial() == []
    assert db.leer_categorias_historial() == []


def test_lecturas_ante_error_de_sqlite_retornan_listas_vacias(db, db_path):
    with sqlite3.connect(db_path) as conexion:
        conexion.execute("DROP TABLE historial_pagos")
    conexion.close()

    assert db.leer_historial(anio_mes="2026-10") == []
    assert db.leer_meses_historial() == []


# --- Migración de BD existentes (categoria_snapshot) -----------------------

ESQUEMA_ANTERIOR = """
CREATE TABLE servicios (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL,
    categoria TEXT NOT NULL, fecha_limite TEXT NOT NULL,
    periodicidad TEXT NOT NULL, url_oficial TEXT NOT NULL,
    dias_anticipacion_alerta INTEGER NOT NULL DEFAULT 3
);
CREATE TABLE historial_pagos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    servicio_id INTEGER NULL REFERENCES servicios(id) ON DELETE SET NULL,
    nombre_servicio_snapshot TEXT NOT NULL,
    fecha_pago_realizado TEXT NOT NULL,
    fecha_limite_cubierta TEXT NOT NULL
);
INSERT INTO servicios VALUES
    (1, 'Agua Casa', 'Agua', '2026-12-01', 'MENSUAL', 'https://a.mx', 3);
INSERT INTO historial_pagos VALUES
    (1, 1, 'Agua Casa', '2026-10-30', '2026-11-01'),
    (2, NULL, 'Netflix', '2026-10-05', '2026-10-05');
"""


@pytest.fixture
def db_anterior(db_path):
    """Archivo .db creado con el esquema previo a categoria_snapshot."""
    with closing(sqlite3.connect(db_path)) as conexion:
        conexion.executescript(ESQUEMA_ANTERIOR)
    return db_path


def _columnas_historial(db_path):
    with closing(sqlite3.connect(db_path)) as conexion:
        return [fila[1] for fila in conexion.execute(
            "PRAGMA table_info(historial_pagos)")]


def test_migracion_agrega_columna_y_rellena_categorias(db_anterior):
    manager = DBManager(str(db_anterior))

    exito, mensaje = manager.inicializar_bd()

    assert exito is True, mensaje
    assert "categoria_snapshot" in _columnas_historial(db_anterior)
    categorias = {p["nombre_servicio_snapshot"]: p["categoria_snapshot"]
                  for p in manager.leer_historial()}
    # Servicio existente: copia su categoría; eliminado: 'Otro'.
    assert categorias == {"Agua Casa": "Agua", "Netflix": "Otro"}


def test_migracion_es_idempotente(db_anterior):
    manager = DBManager(str(db_anterior))
    manager.inicializar_bd()

    exito, _ = manager.inicializar_bd()

    assert exito is True
    assert _columnas_historial(db_anterior).count("categoria_snapshot") == 1
    assert len(manager.leer_historial()) == 2


def test_bd_nueva_ya_trae_la_columna(db, db_path):
    assert "categoria_snapshot" in _columnas_historial(db_path)
