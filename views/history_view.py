"""Pantalla de visualización del historial de pagos (T-05, RF-06).

Solo se comunica con ServiceController (RNF-05).
"""

import flet as ft

MSG_HISTORIAL_VACIO = "Aún no tienes pagos registrados en tu historial"


class HistoryView(ft.View):
    """Lista de pagos registrados, del más reciente al más antiguo."""

    def __init__(self, page, controller):
        super().__init__(route="/historial", padding=12,
                         scroll=ft.ScrollMode.AUTO)
        self._page = page
        self._controller = controller
        self.appbar = ft.AppBar(title=ft.Text("Historial de pagos"))
        self.controls = [self._contenido()]

    def _contenido(self):
        _, _, pagos = self._controller.listar_historial()
        if not pagos:
            return self._estado_vacio()
        return ft.Column([self._tarjeta(p) for p in pagos], spacing=8)

    @staticmethod
    def _estado_vacio():
        return ft.Container(
            alignment=ft.alignment.center,
            padding=40,
            content=ft.Column(
                [
                    ft.Icon(ft.icons.HISTORY, size=64, color=ft.colors.GREY),
                    ft.Text(MSG_HISTORIAL_VACIO, size=16,
                            text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    @staticmethod
    def _tarjeta(pago):
        # "Pagado" es solo una etiqueta visual: todo registro del historial
        # corresponde a un ciclo pagado (no existe columna de estado).
        etiqueta = ft.Container(
            content=ft.Text("Pagado", size=12, color=ft.colors.WHITE,
                            weight=ft.FontWeight.BOLD),
            bgcolor=ft.colors.BLUE,
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=8, vertical=2),
        )
        detalle = ft.Column(
            [
                ft.Text(pago["nombre_servicio_snapshot"],
                        weight=ft.FontWeight.BOLD, size=16),
                ft.Text(f"Fecha límite cubierta: "
                        f"{pago['fecha_limite_cubierta']}", size=12),
                ft.Text(f"Pagado el: {pago['fecha_pago_realizado']}",
                        size=12),
                etiqueta,
            ],
            spacing=2,
            expand=True,
        )
        return ft.Card(
            content=ft.Container(
                padding=12,
                content=ft.Row([
                    ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.BLUE),
                    detalle,
                ]),
            )
        )
