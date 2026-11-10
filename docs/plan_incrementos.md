# Plan de Incrementos - SinFilapp

## Inventario de Requerimientos
| ID | Descripción breve | Tipo | Prioridad | Depende de | Sección | Estado |
|---|---|---|---|---|---|---|
| RF-01 | CRUD físico de servicios local | Funcional | Alta | Ninguna | 5 | Implementado (Inc 1) |
| RF-02 | Panel ordenado con semáforo | Funcional | Alta | RF-01 | 5 | Implementado (Inc 1) |
| RF-03 | Marcar pago y avanzar fecha | Funcional | Alta | RF-01, RF-02 | 5 | Implementado (Inc 2) |
| RF-04 | Notificaciones locales 1-7 días | Funcional | Med/Baja| RF-01 | 5 | Implementado (Inc 3, Opción A: avisos in-app) |
| RF-05 | Redirección HTTPS oficial | Funcional | Media | RF-01, RF-02 | 5 | Implementado (Inc 3) |
| RF-06 | Historial local con snapshot | Funcional | Alta | RF-03 | 5 | Implementado (Inc 2) |
| RF-06.1 | Filtros del historial por mes y servicio | Funcional | Media | RF-06 | — | En desarrollo (refactor-historial) |

## Incremento 2: v0.2.0
* **Objetivo:** Implementar ciclo de pago y actualizar fechas, generando historial local.
* **RF e HU incluidos:** RF-03, RF-06 / HU-05
* **Criterios de Aceptación:** CA-05.1 (Éxito y pago tardío), CA-05.2 (Bisiestos/fin de mes), CA-05.3 (Historial vacío). (Sección 8)
* **Módulos involucrados:** Controladores, Gestión de Datos, Lógica de Fechas, Vistas (history_view.py).
* **Depende de:** Incremento 1 (RF-01, RF-02).
* **Pruebas mínimas:** 
  * Normal: Marcar pago y verificar historial. 
  * Límite: Pago en año bisiesto; historial sin pagos. 
  * Error: Fallo de BD al insertar.
* **Rama de Git:** `incremento-2`

## Incremento 3: v0.3.0
* **Objetivo:** Integrar notificaciones locales OS y redirección web.
* **RF e HU incluidos:** RF-04, RF-05 / HU-02, HU-03
* **Criterios de Aceptación:** CA-02.1 a CA-02.4, CA-03.1 a CA-03.3. (Sección 8)
* **Módulos involucrados:** Utilidades del SO (os_utilities.py), Interfaz (diálogos).
* **Depende de:** Incremento 1 (URLs validadas y días de alerta configurados).
* **Pruebas mínimas:** 
  * Normal: Redirección exitosa; notificación a 72h. 
  * Límite: Cancelar diálogo; fecha insuficiente. 
  * Error: Redirección sin red; permisos de alerta denegados.
* **Rama de Git:** `incremento-3`

## Refactor: filtros del historial (RF-06.1)
* **Motivo:** el historial como lista de scroll infinito no escala; se agregan filtros por **Mes y Año** y por **Servicio**.
* **RF-06.1 (nuevo):** la pantalla de historial permitirá filtrar los pagos por mes/año de `fecha_pago_realizado` y por `nombre_servicio_snapshot`; ambos filtros son opcionales ("Todos") e independientes, y se combinan con AND.
* **Criterios de aceptación propuestos:**
  * CA-06.1.1: Al abrir el historial, el filtro de Mes muestra el mes más reciente con pagos y el de Servicio "Todos".
  * CA-06.1.2: Al cambiar cualquier filtro la lista se actualiza solo con los pagos que cumplen ambos filtros.
  * CA-06.1.3: Si la combinación no tiene pagos se muestra "No hay pagos para los filtros seleccionados".
  * CA-06.1.4: Los pagos de servicios eliminados siguen apareciendo y siendo filtrables por su nombre en snapshot.
  * CA-05.3 se conserva: sin historial se muestra "Aún no tienes pagos registrados en tu historial" y no se muestran filtros.
* **Reglas de arquitectura:** el filtrado se hace en SQLite con `WHERE` y parámetros opcionales (`:param IS NULL OR ...`), sin SQL dinámico; las opciones de los Dropdowns las calcula SQLite (`SELECT DISTINCT`) y las entrega el controlador; la vista no importa `sqlite3` (RNF-05).
* **Decisiones del equipo:** filtro por servicio sobre el snapshot (incluye eliminados); mes según `fecha_pago_realizado` (flujo de caja real); estado inicial = mes más reciente + "Todos"; Dropdowns independientes; sin índices nuevos (sin cambios de esquema).
* **Rama de Git:** `refactor-historial`

## Ambigüedades resueltas
1. Normalización de mayúsculas en periodicidad dentro del controlador.
2. Uso estricto de formato fecha ISO 8601 (YYYY-MM-DD).
3. Desfase a fin de mes aceptado: el ciclo se suma sobre la fecha_limite cubierta ya ajustada (31/ene -> 28/feb -> 28/mar); no se agregan columnas.
4. Tras marcar pagado se muestra el estado calculado real (no se fuerza "Pendiente").
5. "Pagado" es solo una etiqueta visual del historial; no existe columna de estado en BD.
6. Se permite marcar como pagado en cualquier estado, incluso por adelantado.
7. El historial se ordena del pago más reciente al más antiguo y se accede desde un ícono en la barra superior del Dashboard.
8. RF-04 (Opción A aprobada): Flet 0.23.2 no programa notificaciones nativas en segundo plano. CA-02.1 se reinterpreta como aviso in-app (banner) calculado al vuelo a partir de `fecha_limite - dias_anticipacion_alerta`, mostrado al abrir la app y al volver a ella (`on_app_lifecycle_state_change`). La fecha de alerta no se persiste: editar, pagar o eliminar la recalcula automáticamente.
9. CA-02.4 (opción a): el permiso se consulta con `ft.PermissionHandler` solo en Android/iOS; en escritorio es "no soportado" y no se muestra el banner de permisos.
10. Servicios vencidos no generan aviso ni advertencia de "Fecha insuficiente".
11. RF-05: botón dedicado "Ir a pagar"; la red se verifica con una conexión TCP al host del portal (puerto 443, 3 s); `page.launch_url` se inyecta desde la vista hacia `os_utilities`.

## Limitaciones conocidas (Incremento 3)
* Sin notificaciones del SO con la app cerrada (requiere extensión nativa `flutter_local_notifications` y migrar Flet; trabajo futuro, Opción B).
* `flet build` 0.23.2 no permite declarar `POST_NOTIFICATIONS` en el AndroidManifest. En Android 13+ el permiso puede reportarse como denegado y mostrar el banner rojo aunque el usuario no lo haya rechazado. Ver `docs/qa_incremento3.md`.
