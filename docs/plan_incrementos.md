# Plan de Incrementos - SinFilapp

## Inventario de Requerimientos
| ID | Descripción breve | Tipo | Prioridad | Depende de | Sección | Estado |
|---|---|---|---|---|---|---|
| RF-01 | CRUD físico de servicios local | Funcional | Alta | Ninguna | 5 | Implementado (Inc 1) |
| RF-02 | Panel ordenado con semáforo | Funcional | Alta | RF-01 | 5 | Implementado (Inc 1) |
| RF-03 | Marcar pago y avanzar fecha | Funcional | Alta | RF-01, RF-02 | 5 | Pendiente |
| RF-04 | Notificaciones locales 1-7 días | Funcional | Med/Baja| RF-01 | 5 | Pendiente |
| RF-05 | Redirección HTTPS oficial | Funcional | Media | RF-01, RF-02 | 5 | Pendiente |
| RF-06 | Historial local con snapshot | Funcional | Alta | RF-03 | 5 | Pendiente |

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

## Ambigüedades resueltas
1. Normalización de mayúsculas en periodicidad dentro del controlador.
2. Uso estricto de formato fecha ISO 8601 (YYYY-MM-DD).