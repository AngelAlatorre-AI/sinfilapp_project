"""Utilidades del sistema operativo: red, navegador y notificaciones.

RF-05: verificar conexión y abrir el portal oficial (HTTPS) en el
navegador externo. La función que abre el navegador (page.launch_url) se
inyecta desde la vista para no acoplar este módulo a Flet.

RF-04 (estrategia aprobada, Opción A): Flet 0.23.2 no programa
notificaciones nativas en segundo plano, así que los avisos se calculan
al vuelo y se muestran dentro de la app al abrirla o volver a ella. El
permiso de notificaciones se consulta con un PermissionHandler inyectado
(solo móvil), dejando lista la advertencia de CA-02.4.
"""

import socket
from urllib.parse import urlsplit

from modules import date_handler
from modules.url_validator import es_url_segura

MSG_SIN_CONEXION = "Sin conexión a internet. Por favor revisa tu red"
MSG_URL_INSEGURA = "Formato de enlace inválido o no seguro (use https://)"
MSG_NAVEGADOR = "No se pudo abrir el navegador del dispositivo."
TIEMPO_ESPERA_RED = 3
TIEMPO_ESPERA_PERMISO = 5

PERMISO_CONCEDIDO = "concedido"
PERMISO_DENEGADO = "denegado"
PERMISO_NO_SOPORTADO = "no_soportado"
# Valores de flet.PermissionStatus agrupados por resultado.
_ESTADOS_CONCEDIDOS = {"granted", "limited", "provisional"}
_ESTADOS_DENEGADOS = {"denied", "permanentlyDenied", "restricted"}


def hay_conexion(host, puerto=443, timeout=TIEMPO_ESPERA_RED):
    """True si se puede abrir una conexión TCP al host en <= timeout s."""
    if not host:
        return False
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


def _normalizar_estado(estado):
    valor = getattr(estado, "value", estado)
    if valor in _ESTADOS_CONCEDIDOS:
        return PERMISO_CONCEDIDO
    if valor in _ESTADOS_DENEGADOS:
        return PERMISO_DENEGADO
    return PERMISO_NO_SOPORTADO


class Notificador:
    """Avisos in-app de vencimiento y estado del permiso (RF-04).

    manejador: objeto con la interfaz de flet.PermissionHandler, o None en
    plataformas sin soporte (escritorio). tipo_permiso: el valor
    flet.PermissionType.NOTIFICATION, inyectado para no importar Flet.
    """

    def __init__(self, manejador=None, tipo_permiso=None):
        self._manejador = manejador
        self._tipo = tipo_permiso

    def _invocar(self, metodo):
        if self._manejador is None:
            return None
        try:
            return getattr(self._manejador, metodo)(
                self._tipo, wait_timeout=TIEMPO_ESPERA_PERMISO)
        except Exception:  # Plataforma sin soporte o tiempo agotado.
            return None

    def estado_permiso(self):
        """'concedido', 'denegado' o 'no_soportado' (CA-02.4)."""
        return _normalizar_estado(self._invocar("check_permission"))

    def solicitar_permiso(self):
        """Pide el permiso al SO (Android 13+ / iOS) y retorna el estado."""
        return _normalizar_estado(self._invocar("request_permission"))

    def abrir_ajustes(self):
        """Abre los ajustes de la app para reactivar notificaciones."""
        if self._manejador is None:
            return False
        try:
            return bool(self._manejador.open_app_settings())
        except Exception:
            return False

    @staticmethod
    def alertas_activas(servicios, hoy=None):
        """Servicios cuyo aviso ya llegó y aún no vencen (CA-02.1)."""
        hoy_iso = (hoy or date_handler.date.today()).isoformat()
        activas = []
        for servicio in servicios:
            fecha_alerta, _ = date_handler.calcular_fecha_alerta(
                servicio["fecha_limite"],
                servicio["dias_anticipacion_alerta"], hoy)
            if fecha_alerta is not None and fecha_alerta <= hoy_iso:
                activas.append(servicio)
        return activas
