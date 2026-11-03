"""Conexión SQLite, creación de tablas y operaciones CRUD (T-06).

Capa de persistencia de SinFilapp. Solo debe ser invocada por
modules/service_controller.py (RNF-05). No contiene reglas de negocio
ni validaciones de fechas/URLs: recibe diccionarios ya validados.
"""

import sqlite3
from contextlib import contextmanager

from database import queries

MEMORIA = ":memory:"


class DBManager:
    """Administra la base de datos local SQLite (sinfilapp.db)."""

    def __init__(self, db_path="sinfilapp.db"):
        self.db_path = db_path
        # Una BD en memoria desaparece al cerrar su conexión, por lo que
        # en ese caso se mantiene una única conexión persistente.
        self._conexion_memoria = None
        if db_path == MEMORIA:
            self._conexion_memoria = self._abrir_conexion()

    def _abrir_conexion(self):
        conexion = sqlite3.connect(self.db_path)
        conexion.row_factory = sqlite3.Row
        conexion.execute(queries.PRAGMA_FOREIGN_KEYS)
        return conexion

    @contextmanager
    def _conectar(self):
        """Entrega una conexión con commit/rollback y cierre garantizado."""
        conexion = self._conexion_memoria or self._abrir_conexion()
        try:
            yield conexion
            conexion.commit()
        except sqlite3.Error:
            conexion.rollback()
            raise
        finally:
            if conexion is not self._conexion_memoria:
                conexion.close()

    def cerrar(self):
        """Cierra la conexión persistente (solo aplica a BD en memoria)."""
        if self._conexion_memoria is not None:
            self._conexion_memoria.close()
            self._conexion_memoria = None

    def inicializar_bd(self):
        """Crea las tablas servicios e historial_pagos si no existen."""
        try:
            with self._conectar() as conexion:
                conexion.execute(queries.CREATE_TABLE_SERVICIOS)
                conexion.execute(queries.CREATE_TABLE_HISTORIAL_PAGOS)
            return True, "Base de datos inicializada correctamente."
        except sqlite3.Error as error:
            return False, f"Error al inicializar la base de datos: {error}"

    def crear_servicio(self, datos):
        """Inserta un servicio. Retorna (exito, mensaje)."""
        parametros = {"dias_anticipacion_alerta": 3, **datos}
        try:
            with self._conectar() as conexion:
                conexion.execute(queries.INSERT_SERVICIO, parametros)
            return True, "Servicio registrado correctamente."
        except sqlite3.Error as error:
            return False, f"Error al registrar el servicio: {error}"

    def leer_servicios(self):
        """Retorna la lista de servicios ordenada por fecha_limite ASC."""
        try:
            with self._conectar() as conexion:
                filas = conexion.execute(queries.SELECT_SERVICIOS).fetchall()
            return [dict(fila) for fila in filas]
        except sqlite3.Error:
            return []

    def leer_servicio(self, servicio_id):
        """Retorna el servicio como diccionario o None si no existe."""
        try:
            with self._conectar() as conexion:
                fila = conexion.execute(
                    queries.SELECT_SERVICIO_POR_ID, {"id": servicio_id}
                ).fetchone()
            return dict(fila) if fila else None
        except sqlite3.Error:
            return None

    def actualizar_servicio(self, servicio_id, datos):
        """Actualiza todos los campos editables. Retorna (exito, mensaje)."""
        parametros = {**datos, "id": servicio_id}
        try:
            with self._conectar() as conexion:
                cursor = conexion.execute(queries.UPDATE_SERVICIO, parametros)
            if cursor.rowcount == 0:
                return False, "El servicio no existe."
            return True, "Servicio actualizado correctamente."
        except sqlite3.Error as error:
            return False, f"Error al actualizar el servicio: {error}"

    def eliminar_servicio(self, servicio_id):
        """Borrado físico (DELETE). El historial conserva su snapshot."""
        try:
            with self._conectar() as conexion:
                cursor = conexion.execute(
                    queries.DELETE_SERVICIO, {"id": servicio_id}
                )
            if cursor.rowcount == 0:
                return False, "El servicio no existe."
            return True, "Servicio eliminado correctamente."
        except sqlite3.Error as error:
            return False, f"Error al eliminar el servicio: {error}"
