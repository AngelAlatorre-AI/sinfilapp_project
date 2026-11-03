# Punto de entrada de la app Flet
import flet as ft


def main(page: ft.Page):
    page.title = 'SinfilApp'
    page.add(ft.Text('SinfilApp'))


if __name__ == '__main__':
    ft.app(target=main)
