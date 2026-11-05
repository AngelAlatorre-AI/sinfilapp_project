"""Validación de URLs seguras y catálogos cerrados (T-02, RNF-03, RF-01)."""

import re

CATEGORIAS = (
    "Electricidad",
    "Agua",
    "Internet / Telefonía",
    "Gas",
    "Streaming / Entretenimiento",
    "Seguros / Impuestos",
    "Otro",
)

# Etiquetas visibles en la UI. El controlador las normaliza con .upper()
# antes de enviarlas a SQLite (resolución 1 del plan de implementación).
PERIODICIDADES = ("Mensual", "Bimestral", "Anual")

# https:// seguido de un host (sin espacios) y ruta opcional sin espacios.
_PATRON_HTTPS = re.compile(r"^https://[^\s/?#]+\.[^\s/?#]+(?:[/?#]\S*)?$")


def es_url_segura(url):
    """True solo si la URL usa exclusivamente el esquema https://."""
    if not isinstance(url, str):
        return False
    return bool(_PATRON_HTTPS.match(url.strip()))
