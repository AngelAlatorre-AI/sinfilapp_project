"""Formulario de alta/edición con catálogos cerrados (RF-01).

Muestra la advertencia "Fecha insuficiente para los días marcados"
(RF-04, CA-02.2) sin impedir el guardado.

Solo se comunica con ServiceController (RNF-05).
"""

from datetime import datetime

import flet as ft

from modules.service_controller import (
    CATEGORIAS,
    MSG_FECHA_INSUFICIENTE,
    PERIODICIDADES,
)


def _opciones(valores):
    return [ft.dropdown.Option(str(v)) for v in valores]


class FormView(ft.View):
    """Pantalla única para registrar o editar un servicio."""

    def __init__(self, page, controller, servicio_id=None):
        ruta = f"/form/{servicio_id}" if servicio_id else "/form"
        super().__init__(route=ruta, padding=16, scroll=ft.ScrollMode.AUTO)
        self._page = page
        self._controller = controller
        self._servicio_id = servicio_id
        self._crear_campos()
        titulo = "Editar servicio" if servicio_id else "Nuevo servicio"
        self.appbar = ft.AppBar(title=ft.Text(titulo))
        self.controls = [
            ft.Column(
                [*self._campos.values(), self._botones()],
                spacing=12,
            )
        ]
        if servicio_id:
            self._cargar_servicio()

    def _crear_campos(self):
        self._selector_fecha = ft.DatePicker(
            first_date=datetime(2000, 1, 1),
            last_date=datetime(2100, 12, 31),
            on_change=self._fecha_elegida,
        )
        self._campos = {
            "nombre": ft.TextField(label="Nombre del servicio"),
            "categoria": ft.Dropdown(label="Categoría",
                                     options=_opciones(CATEGORIAS)),
            "fecha_limite": ft.TextField(
                label="Fecha límite de pago",
                hint_text="YYYY-MM-DD",
                suffix=ft.IconButton(
                    ft.icons.CALENDAR_MONTH,
                    on_click=lambda _: self._page.open(self._selector_fecha),
                ),
            ),
            "periodicidad": ft.Dropdown(label="Periodicidad",
                                        options=_opciones(PERIODICIDADES)),
            "url_oficial": ft.TextField(
                label="URL oficial de pago",
                hint_text="https://",
                keyboard_type=ft.KeyboardType.URL,
            ),
            "dias_anticipacion_alerta": ft.Dropdown(
                label="Días de anticipación de alerta",
                options=_opciones(range(1, 8)),
                value="3",
            ),
        }

    def _botones(self):
        return ft.Row(
            [
                ft.OutlinedButton("Cancelar",
                                  on_click=lambda _: self._page.go("/")),
                ft.ElevatedButton("Guardar", icon=ft.icons.SAVE,
                                  on_click=self._guardar),
            ],
            alignment=ft.MainAxisAlignment.END,
        )

    def _fecha_elegida(self, _):
        if self._selector_fecha.value:
            fecha = self._selector_fecha.value.strftime("%Y-%m-%d")
            self._campos["fecha_limite"].value = fecha
            self._page.update()

    def _cargar_servicio(self):
        exito, mensaje, servicio = self._controller.obtener_servicio(
            self._servicio_id)
        if not exito:
            self._page.open(ft.SnackBar(ft.Text(mensaje)))
            return
        for campo, control in self._campos.items():
            control.value = str(servicio[campo])

    def _leer_formulario(self):
        return {campo: control.value
                for campo, control in self._campos.items()}

    def _guardar(self, _):
        datos = self._leer_formulario()
        if self._servicio_id:
            exito, mensaje, errores = self._controller.actualizar_servicio(
                self._servicio_id, datos)
        else:
            exito, mensaje, errores = self._controller.crear_servicio(datos)
        for campo, control in self._campos.items():
            control.error_text = (errores or {}).get(campo)
        self._page.open(self._aviso(mensaje))
        if exito:
            self._page.go("/")
        else:
            self._page.update()

    @staticmethod
    def _aviso(mensaje):
        """SnackBar normal, o ámbar y más duradero si hay advertencia."""
        if MSG_FECHA_INSUFICIENTE in mensaje:
            return ft.SnackBar(
                ft.Text(mensaje, color=ft.colors.BLACK),
                bgcolor=ft.colors.AMBER_200,
                duration=6000,
            )
        return ft.SnackBar(ft.Text(mensaje))
