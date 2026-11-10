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
    categoria_snapshot TEXT NOT NULL DEFAULT 'Otro',
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
    servicio_id, nombre_servicio_snapshot, categoria_snapshot,
    fecha_pago_realizado, fecha_limite_cubierta
) VALUES (
    :servicio_id, :nombre_servicio_snapshot, :categoria_snapshot,
    :fecha_pago_realizado, :fecha_limite_cubierta
);
"""

UPDATE_FECHA_LIMITE = """
UPDATE servicios SET fecha_limite = :nueva_fecha_limite WHERE id = :id;
"""

# Filtros opcionales (refactor-historial): si un parámetro es NULL, ese
# filtro no se aplica. :anio_mes usa el formato 'YYYY-MM' sobre la fecha
# real de pago; :categoria compara contra la categoría guardada al pagar
# (snapshot), por lo que incluye pagos de servicios ya eliminados.
SELECT_HISTORIAL = """
SELECT id, servicio_id, nombre_servicio_snapshot, categoria_snapshot,
       fecha_pago_realizado, fecha_limite_cubierta
FROM historial_pagos
WHERE (:anio_mes IS NULL OR substr(fecha_pago_realizado, 1, 7) = :anio_mes)
  AND (:categoria IS NULL OR categoria_snapshot = :categoria)
ORDER BY fecha_pago_realizado DESC, id DESC;
"""

SELECT_MESES_HISTORIAL = """
SELECT DISTINCT substr(fecha_pago_realizado, 1, 7) AS anio_mes
FROM historial_pagos
ORDER BY anio_mes DESC;
"""

SELECT_CATEGORIAS_HISTORIAL = """
SELECT DISTINCT categoria_snapshot AS categoria
FROM historial_pagos;
"""

# --- Migración: categoria_snapshot en BD creadas antes del cambio ---------

PRAGMA_COLUMNAS_HISTORIAL = "PRAGMA table_info(historial_pagos);"

ALTER_HISTORIAL_CATEGORIA = """
ALTER TABLE historial_pagos
ADD COLUMN categoria_snapshot TEXT NOT NULL DEFAULT 'Otro';
"""

# Pagos previos: se copia la categoría actual del servicio; si el servicio
# ya fue eliminado (servicio_id NULL) queda 'Otro'.
BACKFILL_CATEGORIA_SNAPSHOT = """
UPDATE historial_pagos
SET categoria_snapshot = COALESCE(
    (SELECT s.categoria FROM servicios s
     WHERE s.id = historial_pagos.servicio_id),
    'Otro'
);
"""
