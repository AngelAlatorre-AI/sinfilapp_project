"""Carga datos de demostración para la prueba manual de los filtros (QA).

Desde la UI todos los pagos quedan con la fecha de hoy, así que este
script registra pagos en septiembre, octubre y noviembre de 2026 usando
el controlador (misma lógica que la app; no escribe SQL directo).

Uso, desde la raíz del proyecto y con la app cerrada:
    venv\\Scripts\\python scripts\\datos_demo_historial.py [ruta_bd]

Por defecto usa sinfilapp.db. Para empezar desde cero, borra antes ese
archivo.
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.service_controller import ServiceController  # noqa: E402

BASE = {
    "periodicidad": "Mensual",
    "url_oficial": "https://www.ejemplo.com",
    "dias_anticipacion_alerta": "3",
}
DEMO = [
    # (nombre, categoría, fecha límite inicial, fechas de pago, eliminar)
    ("CFE Hogar", "Electricidad", "2026-09-15",
     [date(2026, 9, 14), date(2026, 10, 15), date(2026, 11, 13)], False),
    ("CFE Oficina", "Electricidad", "2026-10-01", [date(2026, 10, 2)], False),
    ("SAPAL", "Agua", "2026-10-20",
     [date(2026, 10, 18), date(2026, 11, 5)], False),
    ("Netflix", "Streaming / Entretenimiento", "2026-09-05",
     [date(2026, 9, 5), date(2026, 10, 5)], True),
]


def cargar(ruta_bd="sinfilapp.db"):
    controller = ServiceController(ruta_bd)
    controller.inicializar()
    for nombre, categoria, fecha, pagos, eliminar in DEMO:
        controller.crear_servicio({**BASE, "nombre": nombre,
                                   "categoria": categoria,
                                   "fecha_limite": fecha})
        # La lista viene ordenada por fecha; el recién creado es el id mayor.
        servicio_id = max(s["id"] for s in controller.listar_servicios()[2])
        for pago in pagos:
            controller.marcar_pagado(servicio_id, hoy=pago)
        if eliminar:
            controller.eliminar_servicio(servicio_id)
    return controller.opciones_filtros_historial()[2]


if __name__ == "__main__":
    opciones = cargar(*sys.argv[1:2])
    print("Datos de demostración cargados.")
    print("Meses:", ", ".join(etiqueta for _, etiqueta in opciones["meses"]))
    print("Categorías:", ", ".join(opciones["categorias"]))
