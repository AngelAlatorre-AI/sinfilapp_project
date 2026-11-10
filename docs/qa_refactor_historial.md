# Guía de QA manual - Filtros del historial (RF-06.1)

Rama: `refactor-historial`. Verifica los filtros por **Mes** y por
**Categoría** de la pantalla de historial, y la migración de la base de
datos existente.

## Preparación

Desde la UI todos los pagos quedan con la fecha de hoy, así que para tener
pagos en varios meses se usa un script de datos de demostración.

1. Cerrar la app si está abierta.
2. (Opcional) Respaldar o borrar `sinfilapp.db` para empezar desde cero.
3. En la raíz del proyecto:
   ```powershell
   venv\Scripts\python scripts\datos_demo_historial.py
   venv\Scripts\python main.py
   ```
4. Abrir el historial con el ícono de reloj de la barra superior.

Datos que carga el script:

| Servicio | Categoría | Pagos (fecha de pago) | Estado |
|---|---|---|---|
| CFE Hogar | Electricidad | 2026-09-14, 2026-10-15, 2026-11-13 | Activo |
| CFE Oficina | Electricidad | 2026-10-02 | Activo |
| SAPAL | Agua | 2026-10-18, 2026-11-05 | Activo |
| Netflix | Streaming / Entretenimiento | 2026-09-05, 2026-10-05 | **Eliminado** |

## Casos de prueba

| CA | Pasos | Resultado esperado | OK |
|---|---|---|---|
| CA-06.1.1 | Abrir el historial. | Mes = **Noviembre 2026**, Categoría = **Todos**. 2 pagos: CFE Hogar (13/nov) y SAPAL (05/nov). Cada tarjeta muestra su categoría. | ☐ |
| Opciones | Abrir cada Dropdown. | Mes: Todos, Noviembre 2026, Octubre 2026, Septiembre 2026. Categoría: Todos, Electricidad, Agua, Streaming / Entretenimiento (orden del catálogo; solo las que tienen pagos). | ☐ |
| CA-06.1.2 | Cambiar Mes a **Octubre 2026**. | 4 pagos: SAPAL (18/oct), CFE Hogar (15/oct), Netflix (05/oct) y CFE Oficina (02/oct). | ☐ |
| Agrupación | Con Octubre, cambiar Categoría a **Electricidad**. | CFE Hogar y CFE Oficina juntos (dos servicios distintos, misma categoría). | ☐ |
| CA-06.1.3 | Mes **Septiembre 2026** y Categoría **Agua**. | Mensaje "No hay pagos para los filtros seleccionados". | ☐ |
| CA-06.1.4 | Mes **Todos** y Categoría **Streaming / Entretenimiento**. | 2 pagos de Netflix (aunque el servicio fue eliminado). | ☐ |
| Snapshot | Editar SAPAL y cambiar su categoría a **Otro**; volver al historial. | Sus pagos anteriores siguen en **Agua** (la categoría se guardó al pagar). | ☐ |
| Todos | Mes **Todos** y Categoría **Todos**. | Los 8 pagos. | ☐ |
| CA-05.3 | Cerrar la app, borrar `sinfilapp.db`, abrirla y entrar al historial. | "Aún no tienes pagos registrados en tu historial" y **sin** Dropdowns. | ☐ |
| Integración | Registrar un servicio desde la app, marcarlo pagado y volver al historial. | El mes actual aparece seleccionado y la categoría del servicio aparece en el filtro. | ☐ |
| Pantalla chica | Probar en la ventana de 400 px o en el teléfono (`flet run --android`). | Los dos Dropdowns caben lado a lado ("Streaming / Entretenimiento" puede recortarse con "…"). | ☐ |

## Migración de una base de datos existente

Las bases creadas antes de este cambio no tienen la columna
`categoria_snapshot`. Al abrir la app se agrega automáticamente:

| Pasos | Resultado esperado | OK |
|---|---|---|
| Con un `sinfilapp.db` anterior que tenga pagos, abrir la app y el historial. | La app arranca sin errores; los pagos de servicios existentes muestran la categoría actual del servicio y los de servicios eliminados aparecen como **Otro**. | ☐ |
| Cerrar y volver a abrir la app. | Sin errores ni cambios (la migración solo ocurre una vez). | ☐ |

## Registro de resultados

| Fecha | Dispositivo / SO | Probador | Resultado | Observaciones |
|---|---|---|---|---|
|  |  |  |  |  |
