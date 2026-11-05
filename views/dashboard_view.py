"""Lista principal de servicios con semáforo de estados (T-10, RF-02).

Solo se comunica con ServiceController (RNF-05).
"""

import flet as ft

from modules.service_controller import PENDIENTE, PROXIMO, VENCIDO

COLORES_ESTADO = {
    PENDIENTE: ft.colors.GREEN,
    PROXIMO: ft.colors.AMBER,
    VENCIDO: ft.colors.RED,
}


def texto_dias(dias):
    """Describe los días restantes de forma legible."""
    if dias == 0:
        return "Vence hoy"
    if dias > 0:
        return f"Faltan {dias} día(s)"
    return f"Venció hace {-dias} día(s)"


class DashboardView(ft.View):
    """Pantalla principal: servicios ordenados por fecha límite."""

    def __init__(self, page, controller):
        super().__init__(route="/", padding=12)
        self._page = page
        self._controller = controller
        self.appbar = ft.AppBar(title=ft.Text("SinFilapp"), center_title=True)
        self.floating_action_button = ft.FloatingActionButton(
            icon=ft.icons.ADD,
            tooltip="Agregar servicio",
            on_click=lambda _: page.go("/form"),
        )
        self.scroll = ft.ScrollMode.AUTO
        self.controls = [self._contenido()]

    def _contenido(self):
        _, _, servicios = self._controller.listar_servicios()
        if not servicios:
            return self._estado_vacio()
        return ft.Column([self._tarjeta(s) for s in servicios], spacing=8)

    def _estado_vacio(self):
        return ft.Container(
            alignment=ft.alignment.center,
            padding=40,
            content=ft.Column(
                [
                    ft.Icon(ft.icons.RECEIPT_LONG, size=64,
                            color=ft.colors.GREY),
                    ft.Text("No tienes servicios registrados", size=16),
                    ft.ElevatedButton(
                        "Agregar mi primer servicio",
                        icon=ft.icons.ADD,
                        on_click=lambda _: self._page.go("/form"),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _tarjeta(self, servicio):
        color = COLORES_ESTADO.get(servicio["estado"], ft.colors.GREY)
        detalle = f"{servicio['categoria']} · {servicio['periodicidad']}"
        vence = (f"Vence: {servicio['fecha_limite']} · "
                 f"{texto_dias(servicio['dias_restantes'])}")
        info = ft.Column(
            [
                ft.Text(servicio["nombre"], weight=ft.FontWeight.BOLD,
                        size=16),
                ft.Text(detalle, size=12),
                ft.Text(vence, size=12),
                self._etiqueta_estado(servicio["estado"], color),
            ],
            spacing=2,
            expand=True,
        )
        acciones = ft.Column(
            [
                ft.IconButton(
                    ft.icons.EDIT, tooltip="Editar",
                    on_click=lambda _: self._page.go(
                        f"/form/{servicio['id']}"),
                ),
                ft.IconButton(
                    ft.icons.DELETE, tooltip="Eliminar",
                    icon_color=ft.colors.RED,
                    on_click=lambda _: self._confirmar_eliminar(servicio),
                ),
            ],
            spacing=0,
        )
        return ft.Card(
            content=ft.Container(
                padding=12,
                border=ft.border.only(left=ft.BorderSide(6, color)),
                content=ft.Row([info, acciones]),
            )
        )

    @staticmethod
    def _etiqueta_estado(estado, color):
        return ft.Container(
            content=ft.Text(estado, size=12, color=ft.colors.WHITE,
                            weight=ft.FontWeight.BOLD),
            bgcolor=color,
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=8, vertical=2),
        )

    def _confirmar_eliminar(self, servicio):
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Eliminar servicio"),
            content=ft.Text(
                f"¿Eliminar \"{servicio['nombre']}\" definitivamente? "
                "Los pagos del historial se conservarán."
            ),
        )
        dialogo.actions = [
            ft.TextButton("Cancelar",
                          on_click=lambda _: self._page.close(dialogo)),
            ft.TextButton(
                "Eliminar",
                style=ft.ButtonStyle(color=ft.colors.RED),
                on_click=lambda _: self._eliminar(servicio, dialogo),
            ),
        ]
        self._page.open(dialogo)

    def _eliminar(self, servicio, dialogo):
        self._page.close(dialogo)
        _, mensaje, _ = self._controller.eliminar_servicio(servicio["id"])
        self.controls = [self._contenido()]
        self._page.open(ft.SnackBar(ft.Text(mensaje)))
        self._page.update()
