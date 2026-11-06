"""Lista principal de servicios con semáforo de estados (RF-02).

Incluye marcar pagado (RF-03), avisos in-app de vencimiento y de permisos
(RF-04) y la redirección al portal oficial (RF-05).

Solo se comunica con ServiceController (RNF-05).
"""

import flet as ft

from modules.service_controller import (
    PENDIENTE,
    PERMISO_DENEGADO,
    PROXIMO,
    VENCIDO,
)

COLORES_ESTADO = {
    PENDIENTE: ft.colors.GREEN,
    PROXIMO: ft.colors.AMBER,
    VENCIDO: ft.colors.RED,
}
MSG_PERMISO_DENEGADO = (
    "Las notificaciones están desactivadas. Los avisos de vencimiento "
    "solo se mostrarán dentro de SinFilapp.")
MSG_SALIR = ("¿Deseas salir de SinFilapp para abrir el sitio oficial "
             "en tu navegador?")


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
        self.appbar = ft.AppBar(
            title=ft.Text("SinFilapp"),
            center_title=True,
            actions=[
                ft.IconButton(
                    ft.icons.HISTORY,
                    tooltip="Historial de pagos",
                    on_click=lambda _: page.go("/historial"),
                ),
            ],
        )
        self.floating_action_button = ft.FloatingActionButton(
            icon=ft.icons.ADD,
            tooltip="Agregar servicio",
            on_click=lambda _: page.go("/form"),
        )
        self.scroll = ft.ScrollMode.AUTO
        self.refrescar()

    def refrescar(self):
        """Recalcula lista, estados y avisos (p. ej. al volver a la app)."""
        self.controls = [self._contenido()]

    def _contenido(self):
        avisos = [b for b in (self._banner_permiso(), self._banner_alertas())
                  if b is not None]
        _, _, servicios = self._controller.listar_servicios()
        if not servicios:
            return ft.Column([*avisos, self._estado_vacio()])
        tarjetas = [self._tarjeta(s) for s in servicios]
        return ft.Column([*avisos, *tarjetas], spacing=8)

    def _banner_permiso(self):
        """Aviso permanente si el SO denegó las notificaciones (CA-02.4)."""
        _, _, estado = self._controller.estado_notificaciones()
        if estado != PERMISO_DENEGADO:
            return None
        return ft.Container(
            bgcolor=ft.colors.RED_50,
            border_radius=8,
            padding=12,
            content=ft.Row(
                [
                    ft.Icon(ft.icons.NOTIFICATIONS_OFF, color=ft.colors.RED),
                    ft.Text(MSG_PERMISO_DENEGADO, size=13, expand=True),
                    ft.TextButton("Activar", on_click=lambda _: (
                        self._controller.abrir_ajustes_notificaciones())),
                ],
            ),
        )

    def _banner_alertas(self):
        """Avisos in-app de servicios por vencer (RF-04, CA-02.1)."""
        _, _, alertas = self._controller.alertas_del_dia()
        if not alertas:
            return None
        lineas = [f"• {a['nombre']}: {texto_dias(a['dias_restantes'])}"
                  for a in alertas]
        return ft.Container(
            bgcolor=ft.colors.AMBER_50,
            border_radius=8,
            padding=12,
            content=ft.Row(
                [
                    ft.Icon(ft.icons.NOTIFICATIONS_ACTIVE,
                            color=ft.colors.AMBER),
                    ft.Column(
                        [ft.Text(f"Tienes {len(alertas)} pago(s) por vencer",
                                 weight=ft.FontWeight.BOLD),
                         *[ft.Text(linea, size=13) for linea in lineas]],
                        spacing=2,
                        expand=True,
                    ),
                ],
            ),
        )

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
                self._botones_pago(servicio),
            ],
            spacing=2,
            expand=True,
        )
        acciones = self._acciones(servicio)
        return ft.Card(
            content=ft.Container(
                padding=12,
                border=ft.border.only(left=ft.BorderSide(6, color)),
                content=ft.Row([info, acciones]),
            )
        )

    def _botones_pago(self, servicio):
        return ft.Row(
            [
                ft.TextButton(
                    "Ir a pagar",
                    icon=ft.icons.OPEN_IN_NEW,
                    on_click=lambda _: self._confirmar_salida(servicio),
                ),
                ft.TextButton(
                    "Marcar pagado",
                    icon=ft.icons.CHECK_CIRCLE_OUTLINE,
                    on_click=lambda _: self._marcar_pagado(servicio),
                ),
            ],
            wrap=True,
            spacing=0,
        )

    def _acciones(self, servicio):
        return ft.Column(
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
        self.refrescar()
        self._page.open(ft.SnackBar(ft.Text(mensaje)))
        self._page.update()

    def _marcar_pagado(self, servicio):
        """Registra el pago (RF-03) y refresca la lista con el nuevo ciclo."""
        _, mensaje, _ = self._controller.marcar_pagado(servicio["id"])
        self.refrescar()
        self._page.open(ft.SnackBar(ft.Text(mensaje)))
        self._page.update()

    def _confirmar_salida(self, servicio):
        """Diálogo previo a abandonar la app (RF-05, CA-03.1, CA-03.3)."""
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Ir al portal de pago"),
            content=ft.Text(MSG_SALIR),
        )
        dialogo.actions = [
            ft.TextButton("Cancelar",
                          on_click=lambda _: self._page.close(dialogo)),
            ft.TextButton(
                "Continuar",
                on_click=lambda _: self._ir_a_pagar(servicio, dialogo),
            ),
        ]
        self._page.open(dialogo)

    def _ir_a_pagar(self, servicio, dialogo):
        """Verifica red y abre el navegador; si falla, alerta (CA-03.2)."""
        self._page.close(dialogo)
        exito, mensaje, _ = self._controller.abrir_portal(
            servicio["id"], self._page.launch_url)
        if not exito:
            self._mostrar_alerta("No se pudo abrir el sitio", mensaje)

    def _mostrar_alerta(self, titulo, mensaje):
        alerta = ft.AlertDialog(
            title=ft.Text(titulo),
            content=ft.Text(mensaje),
        )
        alerta.actions = [
            ft.TextButton("Aceptar",
                          on_click=lambda _: self._page.close(alerta)),
        ]
        self._page.open(alerta)
