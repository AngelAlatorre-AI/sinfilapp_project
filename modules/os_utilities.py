"""Utilidades del sistema operativo: red, navegador y notificaciones.

RF-05: verificar conexión y abrir el portal oficial (HTTPS) en el
navegador externo. La función que abre el navegador (page.launch_url) se
inyecta desde la vista para no acoplar este módulo a Flet.
"""

import socket
from urllib.parse import urlsplit

from modules.url_validator import es_url_segura

MSG_SIN_CONEXION = "Sin conexión a internet. Por favor revisa tu red"
MSG_URL_INSEGURA = "Formato de enlace inválido o no seguro (use https://)"
MSG_NAVEGADOR = "No se pudo abrir el navegador del dispositivo."
TIEMPO_ESPERA_RED = 3


def hay_conexion(host, puerto=443, timeout=TIEMPO_ESPERA_RED):
    """True si se puede abrir una conexión TCP al host en <= timeout s."""
    try:
        with socket.create_connection((host, puerto), timeout=timeout):
            return True
    except (OSError, ValueError):
        return False


def abrir_url(url, lanzador, verificar_red=hay_conexion):
    """Abre la URL oficial en el navegador externo (RF-05, RNF-03).

    Revalida HTTPS antes de abrir, comprueba que el host responda y solo
    entonces invoca lanzador(url). Retorna (exito, mensaje).
    """
    if not es_url_segura(url):
        return False, MSG_URL_INSEGURA
    url = url.strip()
    if not verificar_red(urlsplit(url).hostname):
        return False, MSG_SIN_CONEXION
    try:
        lanzador(url)
    except Exception:  # El SO puede no tener navegador disponible.
        return False, MSG_NAVEGADOR
    return True, "Abriendo el sitio oficial en tu navegador."
