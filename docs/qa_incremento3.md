# Guía de QA manual - Incremento 3 (RF-04, RF-05)

Pruebas que no se pueden automatizar con pytest porque dependen del
dispositivo (navegador del SO, red real, permisos y ciclo de vida).

## Preparación

1. En la PC: `venv\Scripts\activate` y `pip install -r requirements.txt`.
2. En el teléfono Android: instalar la app **Flet** (Google Play) en la
   misma red Wi-Fi que la PC.
3. En la PC, desde la raíz del proyecto: `flet run --android` y escanear el
   código QR con la app Flet.
4. Tener al menos 3 servicios registrados:
   * A: fecha límite = hoy + 10 días, 3 días de alerta (no debe avisar).
   * B: fecha límite = hoy + 2 días, 3 días de alerta (debe avisar).
   * C: fecha límite = ayer (vencido, no debe avisar).

> En escritorio (`python main.py`) también se puede probar RF-05 y el banner
> de avisos; el banner de permisos nunca aparece en escritorio por diseño.

## RF-05 - Redirección web segura

| CA | Pasos | Resultado esperado | OK |
|---|---|---|---|
| CA-03.1 | Con Wi-Fi/datos activos, tocar **Ir a pagar** en un servicio y luego **Continuar**. | Aparece el diálogo "¿Deseas salir de SinFilapp para abrir el sitio oficial en tu navegador?"; al continuar se abre el navegador predeterminado con la URL registrada. | ☐ |
| CA-03.2 | Activar modo avión, tocar **Ir a pagar** y **Continuar**. | No se abre el navegador; aparece la alerta "Sin conexión a internet. Por favor revisa tu red" (tras máx. 3 s). | ☐ |
| CA-03.3 | Tocar **Ir a pagar** y luego **Cancelar**. | El diálogo se cierra y se permanece en el panel principal. | ☐ |
| RNF-03 | (Cubierto por pruebas automatizadas: el controlador rechaza guardar y `os_utilities` rechaza abrir URLs `http://`.) | `tests/test_os_utilities.py` y `tests/test_service_controller.py` aprobados. | ☐ |

## RF-04 - Avisos in-app (Opción A aprobada)

| CA | Pasos | Resultado esperado | OK |
|---|---|---|---|
| CA-02.1 | Abrir la app con los servicios A, B y C. | Banner ámbar "Tienes 1 pago(s) por vencer" listando solo **B**. | ☐ |
| CA-02.1 (ciclo de vida) | Con la app abierta, enviarla a segundo plano, editar la fecha del sistema o esperar a que cambie el día, y volver a la app. | Al volver (RESUME) el banner se recalcula sin reiniciar la app. | ☐ |
| CA-02.2 | Crear un servicio que vence **mañana** con **3** días de alerta. | SnackBar ámbar "... Fecha insuficiente para los días marcados: el aviso se mostrará hoy."; el servicio se guarda y aparece en el banner. | ☐ |
| CA-02.3 | Abrir el selector "Días de anticipación de alerta". | Solo ofrece 1 a 7; valor inicial 3. | ☐ |
| CA-02.4 | En Ajustes del teléfono > Apps > Flet > Notificaciones: desactivarlas. Volver a abrir SinFilapp. | Banner rojo permanente "Las notificaciones están desactivadas..." con botón **Activar** que abre los ajustes de la app. | ☐ |
| CA-02.4 (inverso) | Reactivar las notificaciones y volver a la app. | El banner rojo desaparece al recargar el panel. | ☐ |
| Pago | Marcar **B** como pagado. | B avanza un periodo y sale del banner de avisos. | ☐ |

## Limitaciones a tener presentes durante la prueba

* **No llegan notificaciones con la app cerrada.** Es la limitación aceptada
  de la Opción A: el aviso se muestra al abrir o volver a la app.
* **Android 13+ y `POST_NOTIFICATIONS`.** `flet build` 0.23.2 no permite
  declarar este permiso. Dentro de la app Flet (`flet run --android`) el
  permiso evaluado es el de la app Flet. En un APK propio (`flet build apk`)
  el permiso podría reportarse siempre como denegado; en ese caso habría que
  agregar `<uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>`
  al `AndroidManifest.xml` generado en `build/flutter`. Registrar el
  comportamiento observado en esta guía.
* **Espera de red.** Si el portal no responde, la verificación espera hasta
  3 s antes de mostrar la alerta.

## Registro de resultados

| Fecha | Dispositivo / SO | Probador | Resultado | Observaciones |
|---|---|---|---|---|
|  |  |  |  |  |
