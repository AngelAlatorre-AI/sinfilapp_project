"""Punto de entrada de la app Flet SinFilapp."""

import os

import flet as ft

from modules.service_controller import ServiceController
from views.dashboard_view import DashboardView
from views.form_view import FormView


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


def main(page: ft.Page):
    page.title = "SinFilapp"
    page.window.width = 400
    page.window.height = 760
    controller = ServiceController(ruta_base_datos())
    exito, mensaje, _ = controller.inicializar()
    if not exito:
        page.add(ft.Text(mensaje, color=ft.colors.RED))
        return

    def cambiar_ruta(_):
        page.views.clear()
        page.views.append(DashboardView(page, controller))
        if page.route.startswith("/form"):
            servicio_id = id_desde_ruta(page.route)
            page.views.append(FormView(page, controller, servicio_id))
        page.update()

    def volver(_):
        page.views.pop()
        page.go(page.views[-1].route)

    page.on_route_change = cambiar_ruta
    page.on_view_pop = volver
    page.go("/")


if __name__ == "__main__":
    ft.app(target=main)
