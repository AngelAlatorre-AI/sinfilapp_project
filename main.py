"""Punto de entrada de la app Flet SinFilapp."""

import os

import flet as ft

from modules.os_utilities import Notificador
from modules.service_controller import PERMISO_DENEGADO, ServiceController
from views.dashboard_view import DashboardView
from views.form_view import FormView
from views.history_view import HistoryView


def ruta_base_datos():
    """Usa el almacenamiento de la app en móvil; la carpeta actual en PC."""
    carpeta = os.getenv("FLET_APP_STORAGE_DATA") or "."
    return os.path.join(carpeta, "sinfilapp.db")


def id_desde_ruta(ruta):
    """Extrae el id de '/form/<id>'; None para '/form'."""
    partes = ruta.strip("/").split("/")
    if len(partes) == 2 and partes[1].isdigit():
        return int(partes[1])
    return None


def crear_notificador(page):
    """PermissionHandler solo en móvil; en escritorio no hay soporte."""
    if page.platform not in (ft.PagePlatform.ANDROID, ft.PagePlatform.IOS):
        return Notificador()
    manejador = ft.PermissionHandler()
    page.overlay.append(manejador)
    page.update()
    return Notificador(manejador, ft.PermissionType.NOTIFICATION)


def pedir_permiso_si_falta(controller):
    """En el primer arranque Android 13+/iOS reportan 'denegado'."""
    if controller.estado_notificaciones()[2] == PERMISO_DENEGADO:
        controller.solicitar_permiso_notificaciones()


def refrescar_al_volver(page, evento):
    """Recalcula avisos al volver a la app (Opción A de RF-04).

    Solo en el Dashboard, para no descartar datos de un formulario abierto.
    """
    vuelve = evento.state in (ft.AppLifecycleState.RESUME,
                              ft.AppLifecycleState.SHOW)
    if vuelve and page.route == "/" and page.views:
        page.views[0].refrescar()
        page.update()


def main(page: ft.Page):
    page.title = "SinFilapp"
    page.window.width = 400
    page.window.height = 760
    controller = ServiceController(ruta_base_datos(),
                                   crear_notificador(page))
    exito, mensaje, _ = controller.inicializar()
    if not exito:
        page.add(ft.Text(mensaje, color=ft.colors.RED))
        return
    pedir_permiso_si_falta(controller)

    def cambiar_ruta(_):
        page.views.clear()
        page.views.append(DashboardView(page, controller))
        if page.route.startswith("/form"):
            servicio_id = id_desde_ruta(page.route)
            page.views.append(FormView(page, controller, servicio_id))
        elif page.route == "/historial":
            page.views.append(HistoryView(page, controller))
        page.update()

    def volver(_):
        page.views.pop()
        page.go(page.views[-1].route)

    page.on_route_change = cambiar_ruta
    page.on_view_pop = volver
    page.on_app_lifecycle_state_change = (
        lambda e: refrescar_al_volver(page, e))
    page.go("/")


if __name__ == "__main__":
    ft.app(target=main)
