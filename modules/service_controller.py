"""Controlador intermediario entre Vistas y Datos (T-08, RNF-05).

Las vistas solo hablan con ServiceController; nunca con SQLite.
Todas las operaciones retornan la tupla (exito, mensaje, datos).
"""

from database.db_manager import DBManager
from modules import date_handler
from modules.date_handler import PENDIENTE, PROXIMO, VENCIDO
from modules.url_validator import CATEGORIAS, PERIODICIDADES, es_url_segura

# Constantes reexportadas para que las vistas solo dependan del controlador.
__all__ = [
    "ServiceController",
    "CATEGORIAS",
    "PERIODICIDADES",
    "PENDIENTE",
    "PROXIMO",
    "VENCIDO",
]

CAMPOS = (
    "nombre",
    "categoria",
    "fecha_limite",
    "periodicidad",
    "url_oficial",
    "dias_anticipacion_alerta",
)
MSG_REQUERIDO = "Campo requerido"
MSG_URL = "Formato de enlace inválido o no seguro (use https://)"


def _dias_validos(valor):
    try:
        return 1 <= int(valor) <= 7
    except (TypeError, ValueError):
        return False


_VALIDADORES = {
    "categoria": (lambda v: v in CATEGORIAS, "Seleccione una categoría"),
    "fecha_limite": (
        date_handler.es_fecha_valida,
        "Fecha inválida (use YYYY-MM-DD)",
    ),
    "periodicidad": (
        lambda v: str(v).capitalize() in PERIODICIDADES,
        "Seleccione una periodicidad",
    ),
    "url_oficial": (es_url_segura, MSG_URL),
    "dias_anticipacion_alerta": (_dias_validos, "Seleccione de 1 a 7 días"),
}


def validar_servicio(datos):
    """Retorna {campo: mensaje_error}; vacío si los datos son válidos."""
    errores = {}
    for campo in CAMPOS:
        valor = datos.get(campo)
        if valor is None or str(valor).strip() == "":
            errores[campo] = MSG_REQUERIDO
            continue
        validador = _VALIDADORES.get(campo)
        if validador and not validador[0](valor):
            errores[campo] = validador[1]
    return errores


def normalizar_servicio(datos):
    """Prepara datos validados para SQLite (periodicidad en mayúsculas)."""
    return {
        "nombre": str(datos["nombre"]).strip(),
        "categoria": datos["categoria"],
        "fecha_limite": str(datos["fecha_limite"]).strip(),
        "periodicidad": str(datos["periodicidad"]).upper(),
        "url_oficial": str(datos["url_oficial"]).strip(),
        "dias_anticipacion_alerta": int(datos["dias_anticipacion_alerta"]),
    }


def _mensaje_errores(errores):
    if MSG_REQUERIDO in errores.values():
        return "Completa los campos requeridos marcados en rojo."
    return "Revisa los campos marcados en rojo."


class ServiceController:
    """Orquesta validaciones, persistencia y cálculo de estados."""

    def __init__(self, db_path="sinfilapp.db"):
        self._db = DBManager(db_path)

    def inicializar(self):
        exito, mensaje = self._db.inicializar_bd()
        return exito, mensaje, None

    def cerrar(self):
        """Libera la conexión persistente (solo aplica a BD en memoria)."""
        self._db.cerrar()

    def crear_servicio(self, datos):
        errores = validar_servicio(datos)
        if errores:
            return False, _mensaje_errores(errores), errores
        exito, mensaje = self._db.crear_servicio(normalizar_servicio(datos))
        return exito, mensaje, {}

    def actualizar_servicio(self, servicio_id, datos):
        errores = validar_servicio(datos)
        if errores:
            return False, _mensaje_errores(errores), errores
        exito, mensaje = self._db.actualizar_servicio(
            servicio_id, normalizar_servicio(datos)
        )
        return exito, mensaje, {}

    def eliminar_servicio(self, servicio_id):
        exito, mensaje = self._db.eliminar_servicio(servicio_id)
        return exito, mensaje, None

    def obtener_servicio(self, servicio_id):
        servicio = self._db.leer_servicio(servicio_id)
        if servicio is None:
            return False, "El servicio no existe.", None
        return True, "", self._para_vista(servicio)

    def listar_servicios(self, hoy=None):
        """Servicios ordenados por fecha_limite ASC con su estado."""
        servicios = [
            self._para_vista(s, hoy) for s in self._db.leer_servicios()
        ]
        return True, f"{len(servicios)} servicio(s).", servicios

    @staticmethod
    def _para_vista(servicio, hoy=None):
        fecha = servicio["fecha_limite"]
        dias_alerta = servicio["dias_anticipacion_alerta"]
        return {
            **servicio,
            "periodicidad": servicio["periodicidad"].capitalize(),
            "dias_restantes": date_handler.dias_restantes(fecha, hoy),
            "estado": date_handler.calcular_estado(fecha, dias_alerta, hoy),
        }
