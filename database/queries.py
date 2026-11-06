"""Consultas SQL parametrizadas aisladas (T-05).

Contiene únicamente constantes DDL/DML. Todas las sentencias que reciben
datos usan parámetros con nombre (:campo) para evitar inyección SQL.
Las columnas corresponden exactamente al Diccionario de Datos (Documento 3).
"""

PRAGMA_FOREIGN_KEYS = "PRAGMA foreign_keys = ON;"

CREATE_TABLE_SERVICIOS = """
CREATE TABLE IF NOT EXISTS servicios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL CHECK (categoria IN (
        'Electricidad',
        'Agua',
        'Internet / Telefonía',
        'Gas',
        'Streaming / Entretenimiento',
        'Seguros / Impuestos',
        'Otro'
    )),
    fecha_limite TEXT NOT NULL,
    periodicidad TEXT NOT NULL CHECK (
        periodicidad IN ('MENSUAL', 'BIMESTRAL', 'ANUAL')
    ),
    url_oficial TEXT NOT NULL,
    dias_anticipacion_alerta INTEGER NOT NULL DEFAULT 3 CHECK (
        dias_anticipacion_alerta BETWEEN 1 AND 7
    )
);
"""

CREATE_TABLE_HISTORIAL_PAGOS = """
CREATE TABLE IF NOT EXISTS historial_pagos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    servicio_id INTEGER NULL
        REFERENCES servicios(id) ON DELETE SET NULL,
    nombre_servicio_snapshot TEXT NOT NULL,
    fecha_pago_realizado TEXT NOT NULL,
    fecha_limite_cubierta TEXT NOT NULL
);
"""

INSERT_SERVICIO = """
INSERT INTO servicios (
    nombre, categoria, fecha_limite, periodicidad,
    url_oficial, dias_anticipacion_alerta
) VALUES (
    :nombre, :categoria, :fecha_limite, :periodicidad,
    :url_oficial, :dias_anticipacion_alerta
);
"""

SELECT_SERVICIOS = """
SELECT id, nombre, categoria, fecha_limite, periodicidad,
       url_oficial, dias_anticipacion_alerta
FROM servicios
ORDER BY fecha_limite ASC, id ASC;
"""

SELECT_SERVICIO_POR_ID = """
SELECT id, nombre, categoria, fecha_limite, periodicidad,
       url_oficial, dias_anticipacion_alerta
FROM servicios
WHERE id = :id;
"""

UPDATE_SERVICIO = """
UPDATE servicios SET
    nombre = :nombre,
    categoria = :categoria,
    fecha_limite = :fecha_limite,
    periodicidad = :periodicidad,
    url_oficial = :url_oficial,
    dias_anticipacion_alerta = :dias_anticipacion_alerta
WHERE id = :id;
"""

DELETE_SERVICIO = "DELETE FROM servicios WHERE id = :id;"

# --- Historial de pagos (Incremento 2: RF-03, RF-06) ----------------------

INSERT_PAGO = """
INSERT INTO historial_pagos (
    servicio_id, nombre_servicio_snapshot,
    fecha_pago_realizado, fecha_limite_cubierta
) VALUES (
    :servicio_id, :nombre_servicio_snapshot,
    :fecha_pago_realizado, :fecha_limite_cubierta
);
"""

UPDATE_FECHA_LIMITE = """
UPDATE servicios SET fecha_limite = :nueva_fecha_limite WHERE id = :id;
"""

SELECT_HISTORIAL = """
SELECT id, servicio_id, nombre_servicio_snapshot,
       fecha_pago_realizado, fecha_limite_cubierta
FROM historial_pagos
ORDER BY fecha_pago_realizado DESC, id DESC;
"""
