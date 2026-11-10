# Guía de QA manual - Filtros del historial (RF-06.1)

Rama: `refactor-historial`. Verifica los filtros por **Mes** y por
**Servicio** de la pantalla de historial.

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

| Servicio | Pagos (fecha de pago) | Estado del servicio |
|---|---|---|
| CFE Hogar | 2026-09-14, 2026-10-15, 2026-11-13 | Activo |
| Agua | 2026-10-18, 2026-11-05 | Activo |
| Netflix | 2026-09-05, 2026-10-05 | **Eliminado** (solo queda su historial) |

## Casos de prueba

| CA | Pasos | Resultado esperado | OK |
|---|---|---|---|
| CA-06.1.1 | Abrir el historial. | Mes = **Noviembre 2026**, Servicio = **Todos**. Se ven 2 pagos: CFE Hogar (13/nov) y Agua (05/nov), el más reciente primero. | ☐ |
| Opciones | Abrir cada Dropdown. | Mes: Todos, Noviembre 2026, Octubre 2026, Septiembre 2026. Servicio: Todos, Agua, CFE Hogar, Netflix (orden alfabético). | ☐ |
| CA-06.1.2 | Cambiar Mes a **Octubre 2026**. | La lista cambia al instante: CFE Hogar (15/oct), Agua (18/oct) y Netflix (05/oct), ordenados del más reciente al más antiguo. | ☐ |
| CA-06.1.2 | Con Octubre, cambiar Servicio a **Agua**. | Solo Agua (18/oct). | ☐ |
| CA-06.1.3 | Mes **Septiembre 2026** y Servicio **Agua**. | Mensaje "No hay pagos para los filtros seleccionados". | ☐ |
| CA-06.1.4 | Mes **Todos** y Servicio **Netflix**. | 2 pagos de Netflix (aunque el servicio fue eliminado). | ☐ |
| Todos | Mes **Todos** y Servicio **Todos**. | Los 7 pagos. | ☐ |
| CA-05.3 | Cerrar la app, borrar `sinfilapp.db`, abrirla y entrar al historial. | "Aún no tienes pagos registrados en tu historial" y **sin** Dropdowns. | ☐ |
| Integración | Registrar un servicio desde la app, marcarlo pagado y volver al historial. | El mes actual aparece en el filtro y queda seleccionado; el nuevo pago aparece en la lista. | ☐ |
| Pantalla chica | Probar en la ventana de 400 px o en el teléfono (`flet run --android`). | Los dos Dropdowns caben lado a lado sin cortarse. | ☐ |

## Registro de resultados

| Fecha | Dispositivo / SO | Probador | Resultado | Observaciones |
|---|---|---|---|---|
|  |  |  |  |  |
