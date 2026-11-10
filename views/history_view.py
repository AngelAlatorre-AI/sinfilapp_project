"""Pantalla del historial de pagos con filtros (RF-06, RF-06.1).

Los filtros por Mes y por Servicio se aplican en SQLite a través del
controlador; las opciones de los Dropdowns también las entrega el
controlador. Solo se comunica con ServiceController (RNF-05).
"""

import flet as ft

MSG_HISTORIAL_VACIO = "Aún no tienes pagos registrados en tu historial"
MSG_SIN_RESULTADOS = "No hay pagos para los filtros seleccionados"
TODOS = "__todos__"


def _opcion_todos():
    return ft.dropdown.Option(key=TODOS, text="Todos")


class HistoryView(ft.View):
    """Pagos del más reciente al más antiguo, filtrables por mes/servicio."""

    def __init__(self, page, controller):
        super().__init__(route="/historial", padding=12,
                         scroll=ft.ScrollMode.AUTO)
        self._page = page
        self._controller = controller
        self.appbar = ft.AppBar(title=ft.Text("Historial de pagos"))
        _, _, opciones = controller.opciones_filtros_historial()
        if not opciones["meses"]:
            self.controls = [self._estado_vacio()]  # CA-05.3: sin filtros
            return
        self._crear_filtros(opciones)
        self._lista = ft.Column(spacing=8)
        self._cargar_lista()
        self.controls = [ft.Column(
            [ft.Row([self.filtro_mes, self.filtro_servicio]), self._lista],
            spacing=12,
        )]

    def _crear_filtros(self, opciones):
        """Mes inicia en el más reciente con pagos; Servicio en Todos."""
        self.filtro_mes = ft.Dropdown(
            label="Mes",
            options=[_opcion_todos()] + [
                ft.dropdown.Option(key=clave, text=etiqueta)
                for clave, etiqueta in opciones["meses"]],
            value=opciones["meses"][0][0],
            on_change=self._al_filtrar,
            expand=True,
        )
        self.filtro_servicio = ft.Dropdown(
            label="Servicio",
            options=[_opcion_todos()] + [
                ft.dropdown.Option(nombre)
                for nombre in opciones["servicios"]],
            value=TODOS,
            on_change=self._al_filtrar,
            expand=True,
        )

    @staticmethod
    def _valor(dropdown):
        """None representa "Todos" para el controlador."""
        return None if dropdown.value in (None, TODOS) else dropdown.value

    def _cargar_lista(self):
        _, _, pagos = self._controller.listar_historial(
            self._valor(self.filtro_mes), self._valor(self.filtro_servicio))
        if pagos:
            self._lista.controls = [self._tarjeta(p) for p in pagos]
        else:
            self._lista.controls = [ft.Text(
                MSG_SIN_RESULTADOS, size=14, italic=True,
                text_align=ft.TextAlign.CENTER)]

    def _al_filtrar(self, _):
        self._cargar_lista()
        self._page.update()

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
